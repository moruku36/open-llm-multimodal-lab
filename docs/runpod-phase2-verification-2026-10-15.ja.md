# RunPod Phase 2：Open WebUI から Qwen3.8-27B の1回答を確認

[English](runpod-phase2-verification-2026-10-15.md)

2026年10月15日、ローカルの Open WebUI から RunPod の HTTPS 接続を通じて `Qwen/Qwen3.8-27B`（BF16、A100 SXM 80GB ×1）に1回質問し、指示どおりの日本語の回答 **「接続確認できました」** を表示できた。Deploy 直前の計測開始から停止（$0/時表示）まで 875 秒、稼働費の概算は約 **$0.44**。確定請求は反映待ち。

これは [Phase 1（2026-10-09、Qwen2.5-1.5B）](runpod-phase1-verification-2026-10-09.md) と同じ経路をモデルだけ大型化した、1回の短い接続試験である。回答品質・速度・長文・画像入力の評価、Open WebUI の manual-hook 経由の経路、ライフサイクル自動化の実証は含まない。

## 試験構成

| 項目 | 確認した構成 |
| --- | --- |
| GPU | A100 SXM 80GB ×1（Secure cloud、On-Demand） |
| ホスト | NVIDIA ドライバ 580 系、CUDA 13.0（デプロイ時に CUDA 13.x で絞り込み） |
| モデル | `Qwen/Qwen3.8-27B`（BF16、重み約 55GB） |
| 推論コンテナ | `vllm/vllm-openai:v0.31.0`（digest `sha256:c1c9f6fd5c10…`、全桁は未取得） |
| vLLM 引数 | `--served-model-name qwen3.8-27b-runpod --dtype bfloat16 --max-model-len 8192 --max-num-seqs 4 --gpu-memory-utilization 0.90 --reasoning-parser qwen3 --enforce-eager` |
| ディスク | container disk 100GB、永続 volume なし（`HF_HOME` を container disk 側に変更） |
| 認証 | vLLM の API キー（RunPod Secret 参照で環境変数に注入）。未認証の `/v1/models` は 401 を確認 |
| 画面 | Open WebUI 0.12.2、OpenAI 互換接続、Function Calling = Legacy、max_tokens 64、Temperature 0、`chat_template_kwargs = {"enable_thinking": false}` |
| 時間単価 | GPU $1.79/時 + container disk $0.014/時 = **$1.80/時** |
| 事前承認 | 最大 45 分・上限 $3 |

`--enforce-eager` は、A100（sm80）での新しい注意機構（Gated DeltaNet）向けカーネルのコンパイルや CUDA graph 取得による起動時間・失敗リスクを避けるため。起動ログでは GDN の prefill に Triton/FLA、decode に CUDA カーネル、注意機構に FlashAttention 2 が選ばれた。

## 経過

以下は2026年10月15日の日本時間（JST）。

| 記録点 | 時刻 |
| --- | --- |
| Deploy 直前の計測開始 | 21:59:40.761 |
| 起動引数エラーで再起動ループ → Pod を編集して修正（後述1） | 22:00〜22:03:58 |
| vLLM 起動、モデル読込開始 | 22:05 |
| `/health` 200（重みの取得・読込完了、GPU メモリ 87%） | 22:10:03 |
| 未認証 `/v1/models` が 401 | 22:11:07 |
| 1回目の送信 → Open WebUI 側の設定で拒否（後述2） | 22:12:02 |
| Function Calling を Legacy にして再生成 | 22:12:41 |
| 回答の表示を確認 | 22:13:43 |
| Stop、$0.00/時の表示を確認 | 22:14:15.9 |
| Terminate、Pod 0台・支出速度 $0.000/時を確認 | 22:14〜22:16 |

重み約 55GB の取得は 22:05〜22:10 の約5分（約 11GB/分）。修正後の起動から応答可能まで約6分。

## 費用

計測開始から $0/時表示まで 875.1 秒。`875.1 / 3600 × 1.80 ≈ $0.438`、丸めて約 **$0.44**。残高表示の差も約 $0.42 で整合した。起動失敗の約4分（約 $0.12）を含む。確定請求は RunPod の反映待ち。

## 起きた問題と対処

1. **RunPod の start command は引用符を取り除く**。`--limit-mm-per-prompt {"image":0,"video":0}` が `{image:0,video:0}` として渡り、vLLM が引数エラーで即終了・再起動を繰り返した。引数を削除して Pod を編集した（重みの取得前だったため損失は時間のみ）。
2. **Open WebUI 0.12.2 の Function Calling 既定は Native**。有効なツールが `tool_choice: "auto"` で送られ、vLLM が「`--enable-auto-tool-choice` と `--tool-call-parser` が必要」と拒否した。Phase 1 と同じくチャットの Function Calling を **Legacy** にして再生成し、回答が返った。
3. **思考モデルと短い max_tokens**。Qwen3.8 は思考から始まるため、max_tokens 64 では本文が空になり得る。`chat_template_kwargs = {"enable_thinking": false}` を Open WebUI のカスタムパラメータで送り、本文だけが返った。
4. **テンプレート既定値の上書き**。RunPod の「vLLM Latest」テンプレートは `VLLM_API_KEY=sk-$RUNPOD_POD_ID`（推測可能）と `HF_HOME=/workspace/...`（推奨 25GB の永続 volume 前提）を既定にしている。前者は Secret 参照に、後者は container disk 側に変更した。
5. **Open WebUI のモデル ID**。接続先がまだ存在しない状態で画面を先に準備するには、接続設定の「Model IDs」にモデル名を明示する必要があった。

## 反省点（次の試験の手順に入れる）

- 起動引数は**事前にローカルで分割結果を確認**する。JSON 値を取る引数は start command に書かない。代替が必要なら環境変数か設定ファイルにする。
- Pod 起動直後の **System / Container ログを最初の1分で必ず見る**。再起動ループは `/health` の 404/502 だけでは区別できない。
- 画面側の設定（Function Calling、max_tokens、思考オフ、Model IDs）は **GPU 起動前**に済ませる。今回もこれで GPU 稼働時間を最小にできた。
- 準備（Open WebUI 設定・Secret 作成・Deploy 入力）を GPU 起動前に終え、**Deploy の直前に本人の最終承認**、その後は「起動→1回→Stop→$0確認→Terminate」を一続きで行う。今回の 875 秒のうち約4分は1の修正だった。
- 未認証の要求が拒否されること（401）を、送信前に1回確認する。

## Phase 3 に向けて気をつける点

[Phase 3 設計](phase3-glm-evaluation.ja.md) の GLM 3系列比較に、今回の実測から次を加える。

- **GPU 世代と精度形式**：A100（sm80）は FP8 をネイティブに扱えない。C（Cybersecurity-FP8）は Hopper 以降（H100/H200）が前提。A100 で試すのは A/B の GGUF/BF16 系に限る。
- **CUDA とイメージの組み合わせ**：イメージの CUDA 版（今回は 13 系）に合うホストへ、デプロイ時の CUDA フィルタで絞る。ドライバ不一致は起動直後に失敗する。
- **ディスク容量と取得時間の見積り**：今回は約 11GB/分。数百GB 級の重みでは取得だけで数十分かかり、container disk は重み＋イメージ＋余裕で確保する。取得時間を「成功ジョブ当たりコスト」に必ず含める。繰り返すなら永続 volume（別料金）との損益を比較する。
- **準備完了の判定**：`/health` 200 を準備完了とし、ポーリングで待つ。同期 API で長時間待たない設計（`POST /v1/jobs` → 202）は妥当。
- **思考・ツール呼び出しの扱い**：思考モデルは思考トークンを max_tokens に含めて見積もる。比較時は思考の有無をモデル間でそろえ、ツール呼び出しは使うならサーバー側の parser 設定を明示する。
- **起動引数の検証**：モデルごとの引数を事前に分割・検証し、Pod 上で再起動ループになったら即 Stop する watchdog 条件（例：N 回再起動）を入れる。
- **停止の確認**：Stop 後に支出速度 $0、Terminate 後に Pod 0台、外部からのエンドポイント不達（404）までを1ジョブの完了条件にする。
- **秘密情報**：API キーは RunPod Secret 参照で注入し、テンプレート既定のキーは必ず上書きする。結果ファイル・ログ・公開文書にキー・接続先 URL・Pod ID を残さない。
- **モデル名の衝突**：Open WebUI 側で別経路（manual-hook 等）に割り当てたモデル名と、OpenAI 互換接続のモデル名を重ねない。

## 残っている検証

- 回答品質・指示遵守・生成速度（tokens/s）・長文コンテキスト・画像入力。
- Open WebUI の manual-hook（`qwen-27b` 経路）とライフサイクル自動化を通した実接続。
- 確定請求額と、イメージ digest の全桁。

RunPod 運用の実装は別リポジトリの [qwen-runpod-operations](https://github.com/moruku36/qwen-runpod-operations) を参照する。本記録に秘密値、接続先の実URL、アカウント情報、Pod ID、個人のファイルパス、画面画像は含めていない。
