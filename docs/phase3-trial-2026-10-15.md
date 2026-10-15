# Phase 3 trial record (2026-10-15): prepared; track A aborted on download speed

[日本語](phase3-trial-2026-10-15.ja.md) / design: [phase3-glm-evaluation.md](phase3-glm-evaluation.md)

> **Closure note (2026-10-15):** The owner has ended this RunPod evaluation; no restart is planned or newly authorized. The improvement proposals in section 6 are retained as **lessons, not a resumed plan**. See the [final retrospective](runpod-retrospective-2026-10-15.md).

## Outcome

- **P3-0 (preparation) done**: model registry, pinned revisions, llama.cpp image support check, evaluation set and scorer (verified against a mock server).
- **P3-A (Original) aborted**: an H200 SXM ×1 pod started, but fetching weights from Hugging Face slowed to ~1.6 GB/min and was going to breach stop condition 3 (ready within 25 minutes of model start), so the owner ordered **Stop → Terminate**. **Zero model outputs** (no evaluation ran).
- **P3-B (Uncensored) not run**: the owner narrowed this round to track A.
- **P3-C (Security-FP8) cost estimate only**: not executed.

## 1. Model registry (public Hugging Face API, no downloads)

| Track | Repository | Pinned revision | Size | License |
|---|---|---|---|---|
| A Original | `unsloth/GLM-5.3-Flash-GGUF` (GGUF of official `zai-org/GLM-5.3-Flash`) | `a38483c8cd5df544f53d70fb281afe97369d5ab6` | 321B MoE, UD-Q2_K_XL 108.7 GB (4 shards) | MIT |
| B Uncensored | `huihui-ai/Huihui-GLM-5.3-Flash-abliterated-GGUF` | `c43a994637c10f5c376b7a471b3afc7663f80b9b` | same quant names and sizes as A | MIT |
| C Security | `dealignai/GLM-5.3-CYBERSECURITY-FP8` | `5915c1b88f998a9c1e1a0c83688e285a08ae3ca5` | 753B (full GLM-5.3, `glm_moe_dsa`), FP8 756 GB | MIT |

- GGUF headers (first 8 MB only): both A and B are `general.architecture = glm5-next`, 46 layers, 8 of 288 experts.
- **B's weights differ from A's** (43 of 46 shared files have different hashes; all four UD-Q2_K_XL shards differ), but the GGUF display name and tags are identical to Unsloth's, so **always label results by repository**.
- The official repo was updated on the same day; pinning revisions is required.

## 2. Inference stack

- `ghcr.io/ggml-org/llama.cpp:server-cuda12-b11641` (`sha256:9dfa49ca795363f5fff96f501469e3565e757951f04701a8ad8a5dc5e3ee916d`, CUDA ≥ 12.8).
- `glm5-next` support landed in PR #27773 (2026-09-30), with fixes #29745, #29958, #30042 and #30480 (10-14). b11641 includes #30480. `libllama.so` was confirmed locally to contain the `glm5-next` implementation (no GPU), and the pod pulled the same digest.
- To avoid open issues: default `-ub`, no speculative decoding/MTP/mmproj, `-c 8192`.
- API key via the `LLAMA_API_KEY` environment variable from a RunPod Secret reference.

## 3. Evaluation set (`evaluation/phase3/`)

| # | Content | Metric |
|---|---|---|
| T1 | 3 functions with one bug each (with tests) | tests passing after the fix |
| T2 | practice vulnerable file `practice_app.py` (5 planted issues, 1 SHA-256 decoy) | precision / recall on line ±1 and type |
| T3 | 3 safe files | false positives |
| T4 | 10 defensive questions | refusals (quality rated by a human) |

- Temperature 0, seed 1234, thinking off, one request at a time. All material is self-authored; nothing targets external systems.
- Model-written code (T1) runs **only inside `docker run --network none --read-only` (256 MB, 20 s)**, never on the host.
- End-to-end check with `mock_server.py` reproduced the planted scores: **T1 2/3, T2 P=0.667 R=0.8, T3 1 FP, T4 1 refusal**. A wrong key gave 401 on all 17 requests and HTTP errors are excluded from scoring (the first version counted them as refusals; fixed).

## 4. P3-A run

| Item | Value |
|---|---|
| GPU | 1× H200 SXM 141GB (Secure cloud; the planned H200 NVL was out of capacity) |
| Rate | GPU $5.29/hr + 150 GB container disk $0.021/hr = **$5.31/hr** |
| Pre-approved limits | 75 minutes, $7, six stop conditions |
| Args | `-hf unsloth/GLM-5.3-Flash-GGUF:UD-Q2_K_XL --alias glm53-flash-A --host 0.0.0.0 --port 8000 -c 8192 -ngl 999 -np 1 --jinja` |

| Event (JST) | Time | Container disk used |
|---|---|---|
| Measurement start before Deploy | 23:08:35.5 | — |
| Image pulled (digest matches), container created | 23:10:45 | — |
| Fetching weights | 23:13 | ~16 GB |
| 〃 | 23:15 | ~35 GB (~9 GB/min) |
| 〃 | 23:18 | ~51 GB (~5.5 GB/min) |
| 〃 | 23:29 | ~69 GB (**~1.6 GB/min**) |
| Owner abort → Stop, $0.00/hr shown | 23:31:12 → 23:31:37 | — |
| Terminated; 0 pods, endpoint 404, spend rate $0.000/hr | 23:32–23:34 | — |

- 1,381.7 s from start to $0 display: `1381.7 / 3600 × 5.31 ≈ $2.04`. The displayed balance dropped $3.17; the ~$1.1 gap may be billing lag (unconfirmed). **Reconcile the final invoice.**
- `/health` stayed 502 throughout (llama-server does not listen until `-hf` finishes). No server errors or restart loop.
- Projection at abort: download done ~23:54, ready ~23:58.

## 5. Track C cost estimate (not run)

FP8 756 GB needs ~900 GB+ of VRAM: **8× H200 SXM 141GB (1,128 GB) = $42.32/hr** at listed prices. At the observed 1.6–9 GB/min, fetching 756 GB alone could take **~1.4–8 hours**, so fetch + load + evaluation would cost **~$70 to $350+**. Engine support for `glm_moe_dsa` is also unverified. Conclusion: **not feasible without a larger budget and a better weight-fetch path.**

## 6. Lessons and next steps

1. **Weight fetching is the main risk.** Pulling 100 GB-class weights with `-hf` while paying for a GPU is wasteful, and speed was unstable (9 → 1.6 GB/min). Next time:
   - **Pre-fetch into a network volume in the same region from a cheap CPU pod**, then start the GPU pod with the volume mounted (the volume costs extra but removes GPU idle time).
   - Use a parallel downloader and verify SHA-256 against the registry.
   - Keep the GPU region (EUR-IS-4 this time) and the volume in the same region.
2. **Split stop condition 3 into fetch and load.** It was meant for startup failures but fired on download speed. For example: abort if throughput stays below N GB/min for 5 minutes; require load within 10 minutes of fetch completion.
3. **Plan for stock changes.** The H200 NVL went out of stock right after approval; switching to H200 SXM (1.4× the rate) needed re-approval. Approving a fallback GPU and limit up front avoids the stall.
4. **A vs B remains a fair comparison** (same quant and size, different weights). With pre-fetched weights, A then B on one pod should take ~20 minutes each.
5. All GPU-free preparation (registry, header checks, image implementation check, scorer mock test) is done; only the fetch path needs fixing before a rerun.

## Not done / unconfirmed

- Model outputs and scores for A and B (zero).
- VRAM use, load time and tokens/s on H200.
- Final invoice (~$1.1 gap between the balance change and the computed cost).

This record contains no secret values, real endpoint URLs, account details, pod IDs, personal file paths or screenshots.
