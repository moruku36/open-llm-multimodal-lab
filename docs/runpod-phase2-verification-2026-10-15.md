# RunPod Phase 2: one Qwen3.8-27B reply from Open WebUI

[日本語](runpod-phase2-verification-2026-10-15.ja.md)

On 2026-10-15, a local Open WebUI sent one question through RunPod's HTTPS proxy to `Qwen/Qwen3.8-27B` (BF16, one A100 SXM 80GB) and displayed the instructed Japanese reply **「接続確認できました」** ("Connection confirmed"). From the measurement start just before Deploy to the $0/hr display after Stop took 875 seconds, about **$0.44** at the listed rate. The final invoice was still pending.

This is the [Phase 1 path (2026-10-09, Qwen2.5-1.5B)](runpod-phase1-verification-2026-10-09.md) with a larger model: a single short connection test. It does not evaluate answer quality, speed, long context or image input, and it does not prove the Open WebUI manual-hook route or lifecycle automation.

## Configuration

| Item | Value |
| --- | --- |
| GPU | 1× A100 SXM 80GB (Secure cloud, on-demand) |
| Host | NVIDIA driver 580 series, CUDA 13.0 (filtered to CUDA 13.x at deploy) |
| Model | `Qwen/Qwen3.8-27B` (BF16, ~55 GB of weights) |
| Inference image | `vllm/vllm-openai:v0.31.0` (digest `sha256:c1c9f6fd5c10…`, full digest not captured) |
| vLLM args | `--served-model-name qwen3.8-27b-runpod --dtype bfloat16 --max-model-len 8192 --max-num-seqs 4 --gpu-memory-utilization 0.90 --reasoning-parser qwen3 --enforce-eager` |
| Disk | 100 GB container disk, no persistent volume (`HF_HOME` moved to the container disk) |
| Auth | vLLM API key injected from a RunPod Secret reference. Unauthenticated `/v1/models` returned 401 |
| UI | Open WebUI 0.12.2, OpenAI-compatible connection, Function Calling = Legacy, max_tokens 64, temperature 0, `chat_template_kwargs = {"enable_thinking": false}` |
| Rate | GPU $1.79/hr + container disk $0.014/hr = **$1.80/hr** |
| Pre-approved limits | 45 minutes, $3 |

`--enforce-eager` avoids kernel compilation and CUDA-graph capture risk for the new Gated DeltaNet attention on A100 (sm80). The startup log selected Triton/FLA for GDN prefill, a CUDA kernel for GDN decode, and FlashAttention 2.

## Timeline (JST, 2026-10-15)

| Event | Time |
| --- | --- |
| Measurement start, just before Deploy | 21:59:40.761 |
| Restart loop from an argument error, fixed by editing the pod (issue 1) | 22:00–22:03:58 |
| vLLM started, model loading | 22:05 |
| `/health` 200 (weights fetched and loaded, GPU memory 87%) | 22:10:03 |
| Unauthenticated `/v1/models` → 401 | 22:11:07 |
| First send rejected by an Open WebUI setting (issue 2) | 22:12:02 |
| Regenerated with Function Calling = Legacy | 22:12:41 |
| Reply displayed | 22:13:43 |
| Stopped, $0.00/hr shown | 22:14:15.9 |
| Terminated; 0 pods, spend rate $0.000/hr | 22:14–22:16 |

Fetching ~55 GB of weights took about 5 minutes (~11 GB/min). After the fix, start to ready took about 6 minutes.

## Cost

875.1 s × $1.80/hr ≈ $0.438, about **$0.44**, consistent with a ~$0.42 drop in the displayed balance. This includes ~4 minutes (~$0.12) lost to issue 1. The final invoice was pending.

## Issues and fixes

1. **RunPod's start command strips quotes.** `--limit-mm-per-prompt {"image":0,"video":0}` arrived as `{image:0,video:0}`; vLLM exited on the argument error and restarted in a loop. The argument was removed by editing the pod (before weights were fetched, so only time was lost).
2. **Open WebUI 0.12.2 defaults Function Calling to Native.** Enabled tools were sent with `tool_choice: "auto"` and vLLM rejected the request because `--enable-auto-tool-choice` and `--tool-call-parser` were not set. As in Phase 1, setting the chat's Function Calling to **Legacy** and regenerating worked.
3. **Thinking models and small max_tokens.** Qwen3.8 starts with thinking, so 64 tokens could end before any answer. Sending `chat_template_kwargs = {"enable_thinking": false}` as an Open WebUI custom parameter returned only the answer.
4. **Template defaults must be overridden.** RunPod's "vLLM Latest" template defaults to `VLLM_API_KEY=sk-$RUNPOD_POD_ID` (guessable) and `HF_HOME=/workspace/...` (assumes a recommended 25 GB volume). They were replaced with a Secret reference and a container-disk path.
5. **Open WebUI model IDs.** To prepare the chat before the endpoint existed, the model name had to be listed explicitly under the connection's Model IDs.

## Lessons for the next run

- **Check argument splitting locally first.** Do not put JSON-valued arguments in the RunPod start command; use environment variables or a config file instead.
- **Read the System and Container logs in the first minute.** A restart loop is not distinguishable from slow loading by `/health` 404/502 alone.
- **Finish all UI settings before the GPU starts** (Function Calling, max_tokens, thinking off, Model IDs). This kept GPU time minimal.
- **Prepare everything, get the owner's final approval right before Deploy, then run start → one request → Stop → $0 check → Terminate in one sequence.** About 4 of the 875 seconds went to issue 1.
- **Confirm an unauthenticated request is rejected (401) before sending.**

## Cautions for Phase 3

Additions to the [Phase 3 design](phase3-glm-evaluation.md) based on this run:

- **GPU generation vs precision.** A100 (sm80) has no native FP8. Track C (Cybersecurity-FP8) assumes Hopper or newer (H100/H200). Use A100 only for the GGUF/BF16 tracks A/B.
- **Image CUDA vs host.** Filter hosts by the image's CUDA version at deploy (CUDA 13 here). A driver mismatch fails right at startup.
- **Disk and download time.** At ~11 GB/min, hundreds of GB of weights take tens of minutes. Size the container disk for weights + image + headroom, and include download time in cost per successful job. If runs repeat, compare against a persistent volume (billed separately).
- **Readiness.** Treat `/health` 200 as ready and poll for it. The async job API design (`POST /v1/jobs` → 202) fits this.
- **Thinking and tool calling.** Budget thinking tokens inside max_tokens, keep thinking on/off identical across compared models, and configure the server-side tool parser explicitly if tools are used.
- **Argument validation and watchdog.** Validate each model's arguments before deploy, and stop automatically on a restart loop (e.g. N restarts).
- **Proof of shutdown.** A job is complete only when the spend rate is $0 after Stop, there are 0 pods after Terminate, and the external endpoint is unreachable (404).
- **Secrets.** Inject API keys from RunPod Secret references, always override template default keys, and keep keys, endpoint URLs and pod IDs out of results, logs and public docs.
- **Model-name collisions.** Do not reuse a model name already routed elsewhere in Open WebUI (e.g. a manual-hook route) for an OpenAI-compatible connection.

## Not yet verified

- Answer quality, instruction following, tokens/s, long context, image input.
- A real request through the Open WebUI manual-hook (`qwen-27b` route) and lifecycle automation.
- The final invoice and the full image digest.

RunPod lifecycle code lives in [qwen-runpod-operations](https://github.com/moruku36/qwen-runpod-operations). This record contains no secret values, real endpoint URLs, account details, pod IDs, personal file paths or screenshots.
