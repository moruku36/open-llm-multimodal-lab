# Run the P3 evaluation for one track against the RunPod pod.
#   pwsh -File run_track.ps1 -PodId <podid> -Track A
# The API key is typed hidden, lives only in this process's environment, and is cleared at the end.
param([Parameter(Mandatory)][string]$PodId, [Parameter(Mandatory)][ValidateSet('A','B')][string]$Track)
$ErrorActionPreference = 'Stop'
if ($PodId -notmatch '^[a-z0-9]{8,20}$') { throw 'PodId looks wrong' }
$base  = "https://$PodId-8000.proxy.runpod.net/v1"
$model = "glm53-flash-$Track"
$here  = $PSScriptRoot
$out   = Join-Path $here "responses-$Track.jsonl"
if (Test-Path $out) { throw "$out already exists; refusing to overwrite" }

$secure = Read-Host -AsSecureString "API key (hidden, same as RunPod secret vllm_api_key)"
$env:P3_API_KEY = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure))
try {
  # Auth sanity: no key must be rejected, the key must be accepted.
  $noauth = (Invoke-WebRequest "$base/models" -SkipHttpErrorCheck -TimeoutSec 20).StatusCode
  $auth   = (Invoke-WebRequest "$base/models" -Headers @{ Authorization = "Bearer $env:P3_API_KEY" } -SkipHttpErrorCheck -TimeoutSec 20).StatusCode
  "auth check: without key=$noauth (want 401), with key=$auth (want 200)"
  if ($noauth -ne 401 -or $auth -ne 200) { throw 'auth check failed; not running the evaluation' }
  python -I -B (Join-Path $here 'run_eval.py') --base-url $base --model $model --key-env P3_API_KEY --track $Track --out $out --timeout 110
  "saved $out"
} finally {
  $env:P3_API_KEY = $null; $secure.Dispose()
}
