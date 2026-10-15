# Phase 3 evaluation set (T1–T4)

> **Status (2026-10-15): frozen fixtures and mock-scorer results only.** The owner has ended the real RunPod evaluation; no GLM model outputs or benchmark results exist, and no restart is planned. The commands below are kept as **archival examples**, not an active procedure. See the [final retrospective](../../docs/runpod-retrospective-2026-10-15.md).

Self-authored, small evaluation set designed for comparing GLM-5.3-Flash variants. See [the trial record](../../docs/phase3-trial-2026-10-15.md).

| File | Purpose |
|---|---|
| `tasks.json` | Prompts, answer key, generation settings (temperature 0, seed 1234, thinking off) |
| `practice_app.py` | **Deliberately vulnerable practice file. Never deploy or execute.** Line numbers are the T2 answer key |
| `safe_1.py`–`safe_3.py` | Safe code for T3 (false-positive check) |
| `run_eval.py` | Sends the set to an OpenAI-compatible endpoint; key read from a named env var |
| `run_track.ps1` | Windows wrapper: hidden key prompt, 401/200 auth check, then `run_eval.py` |
| `score.py` | Scores responses; T1 code runs only in `docker run --network none --read-only` |
| `mock_server.py` | Deterministic local mock used to verify the scorer (expected: T1 2/3, T2 P=0.667 R=0.8, T3 1 FP, T4 1 refusal) |

Quick self-test (no GPU):

```bash
python mock_server.py 18765 mock-key &
MOCK_KEY=mock-key python run_eval.py --base-url http://127.0.0.1:18765/v1 --model mock --key-env MOCK_KEY --track mock --out mock.jsonl
python score.py mock.jsonl --out mock-report.json
```
