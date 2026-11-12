# Converts every master MP4 in .\masters to ProRes 422 HQ in .\prores (same folder layout).
# Easiest: double-click MAKE_PRORES.bat in the main LEDCONTENT folder.
# Optional: -ProResProfile 2 for plain 422 (smaller). 0=Proxy 1=LT 2=422 3=HQ
param([int]$ProResProfile = 3)

$root = Split-Path -Parent $PSScriptRoot
$masters = Join-Path $root "masters"
$proresDir = Join-Path $root "prores"

if (-not (Get-Command ffmpeg -ErrorAction SilentlyContinue)) {
    Write-Host ""
    Write-Host "ffmpeg is not installed (or this window was opened before it was installed)." -ForegroundColor Red
    Write-Host "Install it by pasting this into PowerShell, then close and reopen everything:" -ForegroundColor Yellow
    Write-Host "    winget install --id Gyan.FFmpeg -e" -ForegroundColor Cyan
    exit 1
}

$files = @(Get-ChildItem -Path $masters -Recurse -Filter *.mp4 | Sort-Object FullName)
if ($files.Count -eq 0) { Write-Host "No .mp4 files found in $masters" -ForegroundColor Red; exit 1 }

Write-Host ""
Write-Host "Converting $($files.Count) files to ProRes (profile $ProResProfile). This can take a while." -ForegroundColor Green
Write-Host ""

$n = 0; $failed = 0
foreach ($f in $files) {
    $n++
    $rel = $f.FullName.Substring($masters.Length).TrimStart('\', '/')
    $relNoExt = $rel.Substring(0, $rel.Length - $f.Extension.Length)
    $out = Join-Path $proresDir ($relNoExt + "_PRORES.mov")
    $tmp = Join-Path $proresDir ($relNoExt + "_PRORES.partial.mov")
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $out) | Out-Null

    if (Test-Path $out) { Write-Host "[$n/$($files.Count)] already done: $rel" -ForegroundColor DarkGray; continue }

    Write-Host "[$n/$($files.Count)] converting: $rel"
    & ffmpeg -hide_banner -loglevel error -stats -nostdin -y -i $f.FullName `
        -c:v prores_ks -profile:v $ProResProfile -vendor apl0 -pix_fmt yuv422p10le -an $tmp
    if ($LASTEXITCODE -eq 0) {
        Move-Item -Force $tmp $out
    } else {
        $failed++
        Write-Host "    FAILED: $rel" -ForegroundColor Red
        Remove-Item $tmp -ErrorAction SilentlyContinue
    }
}

Write-Host ""
if ($failed -eq 0) {
    Write-Host "All done. ProRes files are in: $proresDir" -ForegroundColor Green
} else {
    Write-Host "Finished with $failed failure(s). Run it again to retry; finished files are skipped." -ForegroundColor Yellow
}
