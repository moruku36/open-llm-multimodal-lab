"""Send the P3 evaluation set to an OpenAI-compatible endpoint and save raw responses.

  python run_eval.py --base-url URL/v1 --model NAME --key-env ENVVAR --track A --out responses-A.jsonl

The API key is read from the named environment variable (never from argv, never written out).
Temperature 0, fixed seed, thinking disabled; one request at a time.
"""
import argparse,json,os,time,urllib.request
from pathlib import Path
HERE=Path(__file__).resolve().parent

def prompts(tasks):
    g=tasks['generation']
    for t in tasks['T1']:yield t['id'],'T1',t['prompt'],g['max_tokens']['T1']
    code=(HERE/tasks['T2']['file']).read_text(encoding='utf-8')
    yield tasks['T2']['id'],'T2',tasks['T2']['prompt_template'].replace('{CODE}',code),g['max_tokens']['T2']
    for t in tasks['T3']:
        c=(HERE/t['file']).read_text(encoding='utf-8')
        yield t['id'],'T3',tasks['T2']['prompt_template'].replace('{CODE}',c),g['max_tokens']['T3']
    for t in tasks['T4']:yield t['id'],'T4',t['prompt'],g['max_tokens']['T4']

def main():
    p=argparse.ArgumentParser();p.add_argument('--base-url',required=True);p.add_argument('--model',required=True)
    p.add_argument('--key-env',required=True);p.add_argument('--track',required=True);p.add_argument('--out',required=True)
    p.add_argument('--timeout',type=int,default=300)
    a=p.parse_args()
    key=os.environ.get(a.key_env,'')
    tasks=json.loads((HERE/'tasks.json').read_text(encoding='utf-8'));g=tasks['generation']
    with open(a.out,'w',encoding='utf-8') as out:
        for tid,kind,text,mt in prompts(tasks):
            body={'model':a.model,'messages':[{'role':'system','content':tasks['system']},{'role':'user','content':text}],
                  'temperature':g['temperature'],'seed':g['seed'],'max_tokens':mt,'stream':False,
                  'chat_template_kwargs':g['chat_template_kwargs']}
            req=urllib.request.Request(a.base_url.rstrip('/')+'/chat/completions',data=json.dumps(body).encode(),
                headers={'Content-Type':'application/json',**({'Authorization':'Bearer '+key} if key else {})})
            t0=time.time();rec={'id':tid,'kind':kind,'track':a.track}
            try:
                with urllib.request.urlopen(req,timeout=a.timeout) as r:resp=json.load(r)
                rec.update(status=200,text=resp['choices'][0]['message'].get('content') or '',
                           finish=resp['choices'][0].get('finish_reason'),usage=resp.get('usage'),timings=resp.get('timings'))
            except urllib.error.HTTPError as e:
                rec.update(status=e.code,text='',error=e.read(300).decode('utf-8','replace'))
            except Exception as e:
                rec.update(status=None,text='',error=type(e).__name__)
            rec['seconds']=round(time.time()-t0,2)
            out.write(json.dumps(rec,ensure_ascii=False)+'\n');out.flush()
            print(tid,rec['status'],rec['seconds'])
    key=None

if __name__=='__main__':main()
