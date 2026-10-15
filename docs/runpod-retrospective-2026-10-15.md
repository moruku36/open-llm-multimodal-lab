# RunPod evaluation: final retrospective (2026-10-15)

[日本語](runpod-retrospective-2026-10-15.ja.md)

## Status

The owner has **ended this RunPod evaluation**; Phase 3 was aborted partway. The Qwen application, code, historical reports and the Phase 3 design are kept as they are. **No restart is planned or newly authorized.** Costs below are estimates and observed shutdown rates, not finalized invoices. Storage/volume deletion and final-bill closure beyond the reports are unverified.

## What was measured

| Phase | Measured result | Not established | Evidence |
| --- | --- | --- | --- |
| 1 (2026-10-09) | RTX PRO 4000 24GB, Qwen2.5-1.5B: Open WebUI over authenticated HTTPS displayed an English `Connected successfully.` despite a Japanese instruction. | Model-quality ranking (connectivity only). | [Phase 1](runpod-phase1-verification-2026-10-09.md) |
| 2 (2026-10-15) | A100 SXM 80GB, Qwen3.8-27B BF16 on vLLM: one answer through Open WebUI's OpenAI-compatible HTTPS path; 875.1 s is the deployment-to-Stop measurement window (not answer latency or GPU-only time), about USD 0.44 (estimate); Pod terminated, spend rate 0 recorded. | Manual-hook path, Q8, VRAM, speed, quality, long-context and multimodal benchmarks. | [Phase 2](runpod-phase2-verification-2026-10-15.md) |
| 3 (2026-10-15) | P3-0 preparation done (registry, pinned revisions, image compatibility, evaluation fixtures, mock scorer). Track A on H200 SXM 141GB: the container image download completed (digest matched) with no restart loop, but the model weights did not finish: the 108.7 GB weight download slowed from ~9 to ~1.6 GB/min and the owner stopped it as 25-minute readiness looked impossible. 1381.7 s (deployment-to-Stop measurement window), about USD 2.04 (estimate); Stop, then Terminate; Pod 0, endpoint 404, spend rate 0 recorded. | **Zero model outputs; no A/B evaluation.** B not run, C cost-estimated only. Billing reconciliation remains uncertain. | [Phase 3 trial](phase3-trial-2026-10-15.md), [design](phase3-glm-evaluation.md) |

Mock-scorer numbers in the trial record are test-fixture results, **never GLM measurements**. Phase 3 was not an image-download failure, and it is not evidence that the model is poor or that RunPod is generally unusable.

## Lessons

The Colab/Gradio Qwen application is retained in the repository, and remote inference was explored via RunPod; this does not mean the whole existing app or multimodal workflow was deployed and verified on RunPod. The RunPod exploration also needed: environment/dependency compatibility, authentication setup, quote/argument handling, Open WebUI settings, GPU supply, large weight transfer/storage, and shutdown/billing confirmation. The Phase 2 report documents quote stripping with a restart loop, Open WebUI Native vs Legacy tool calling, thinking-token/max-token limits and `HF_HOME`/storage issues. **These are operational faults, distinct from reasoning/answer capability**; platform or security restrictions should not be read as model inability. The H200 NVL shortage (re-approved as H200 SXM) shows GPU supply is also a variable.

"About two weeks" is the owner's experienced calendar and preparation effort, **not** measured wall time, GPU hours or a benchmark duration.

Improvement ideas in the earlier reports (pre-staged weights, download-rate checks, pinned digests) remain lessons, not scheduled work.

## Direction: MiMo-V2.6-Pro API (owner policy, unverified)

The owner's workload-specific choice is to consider the **MiMo-V2.6-Pro API (`mimo-v2.6-pro`)** as an operational candidate, using ordinary code, document and final-artifact review. This is a policy direction, **not a verified deployment**: no API account, key, call or result has been verified, and no integration is implemented here. It is not a universal recommendation, nor a claim of cheapest/best or any national/world ranking.

Official open weights are published, so the model is not API-only. Sources: [pricing](https://mimo.mi.com/docs/en-US/price/pay-as-you-go) (page updated 2026-10-08), [introduction](https://mimo.mi.com/docs/en-US/news/latest/v2-6), [weights](https://huggingface.co/collections/XiaomiMiMo/mimo-v26).

| Overseas standard realtime pay-as-you-go (checked 2026-10-15) | USD per 1M tokens |
| --- | --- |
| Input, cache miss | 0.435 |
| Input, cache hit | 0.0036 |
| Output | 0.87 |

Rates may change; TokenPlan pricing is separate. Compare per-token pricing against usage assumptions; do not compare dollars per hour (Pod) directly with dollars per token. **No same-workload measured API-vs-self-hosted comparison exists.**

## Privacy and self-hosting

- The official overseas [Xiaomi MiMo platform privacy policy](https://privacy.mi.com/XiaomiMiMoPlatformos/en_GB/) (updated 2026-06-25) states in section 3 that provided content is not used for model training or other purposes. That is a stated nontraining policy, **not a zero-retention promise**: section 6 keeps data for necessary periods or as applicable law requires, with no fixed number of days. Verify the applicable contract, permissions, region and retention **before** sending confidential code or artifacts. No actual API account, key, call or contract acceptance has been done.
- Self-hosting may suit pinned reproducibility, weight control, custom requirements, privacy architecture or sustained high utilization. It still needs verified data handling and a measured workload cost comparison. An API is not inherently private, and self-hosting is not inherently secure.

## Remaining limits

- Phase 2: only one reply was verified; quality and benchmarks are open.
- Phase 3: no model inference outputs or evaluation; registry/mock preparation results exist, and mock scores are fixtures.
- MiMo: pricing is from documentation only; no behavior or data-handling verification.
- Historical planned designs stay as reference, not commitments.
