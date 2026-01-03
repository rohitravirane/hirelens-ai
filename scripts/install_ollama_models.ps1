Write-Host "=== Installing Required Ollama Models ===" -ForegroundColor Green
Write-Host ""

Write-Host "Note: Vision models may have different names in Ollama." -ForegroundColor Yellow
Write-Host "We'll try common Qwen vision model names..." -ForegroundColor Gray
Write-Host ""

# Try different vision model names
$visionModels = @(
    "qwen2-vl:7b",
    "qwen2-vl:7b-instruct",
    "qwen2.5-vl:7b-instruct-q4_K_M"
)

$visionInstalled = $false
foreach ($model in $visionModels) {
    Write-Host "Trying: $model..." -ForegroundColor Cyan
    $result = ollama pull $model 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Successfully installed: $model" -ForegroundColor Green
        $visionInstalled = $true
        break
    } else {
        Write-Host "❌ Failed: $model" -ForegroundColor Red
    }
}

if (-not $visionInstalled) {
    Write-Host ""
    Write-Host "⚠️  Vision model installation failed." -ForegroundColor Yellow
    Write-Host "The system will use text-only model (qwen2.5:7b-instruct-q4_K_M) which is already available." -ForegroundColor Gray
    Write-Host "You can check available models with: ollama list" -ForegroundColor Gray
}

Write-Host ""
Write-Host "Verifying installation..." -ForegroundColor Yellow
.\scripts\check_ollama.ps1

