# Nightly refresh: pull products from Wix, commit if changed, push to GitHub.
# Triggered by Windows Task Scheduler entry "KyCreekers-Products-Daily" at 3 AM.
# Netlify auto-deploys on push.

$ErrorActionPreference = 'Continue'
$projectDir = 'C:\Users\Owner\Projects\KyCreekers Landing Page'
$logFile = Join-Path $projectDir 'refresh.log'
$pythonExe = 'C:\Python314\python.exe'

function Write-Log {
    param([string]$msg)
    $ts = (Get-Date).ToString('yyyy-MM-dd HH:mm:ss')
    Add-Content -Path $logFile -Value "$ts  $msg" -Encoding utf8
}

Set-Location -LiteralPath $projectDir
Write-Log "=== refresh started ==="

# 1) Run the Python refresh
try {
    $pyOut = & $pythonExe update_products.py 2>&1
    foreach ($line in $pyOut) { Write-Log "py: $line" }
} catch {
    Write-Log "ERROR running python: $_"
}

# 2) Check if products.json changed in git's view
& git diff --quiet products.json
$changed = ($LASTEXITCODE -ne 0)

if (-not $changed) {
    Write-Log "no changes to products.json, nothing to commit"
    Write-Log "=== refresh complete ==="
    exit 0
}

Write-Log "products.json changed, committing and pushing"

# 3) Commit
& git add products.json 2>&1 | ForEach-Object { Write-Log "git: $_" }
$commitMsg = "Daily product refresh: $((Get-Date).ToString('yyyy-MM-dd'))"
& git commit -m $commitMsg 2>&1 | ForEach-Object { Write-Log "git: $_" }

# 4) Push to GitHub (triggers Netlify auto-deploy)
$pushOut = & git push 2>&1
foreach ($line in $pushOut) { Write-Log "git: $line" }

if ($LASTEXITCODE -eq 0) {
    Write-Log "pushed to GitHub successfully, Netlify will redeploy"
} else {
    Write-Log "ERROR pushing to GitHub (exit code $LASTEXITCODE)"
}

Write-Log "=== refresh complete ==="
