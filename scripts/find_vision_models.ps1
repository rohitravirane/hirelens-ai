Write-Host "=== Finding Available Qwen Vision Models ===" -ForegroundColor Green
Write-Host ""

Write-Host "Checking Ollama for Qwen vision models..." -ForegroundColor Yellow
Write-Host ""

$models = ollama list | Select-String -Pattern "qwen" -CaseSensitive:$false

if ($models) {
    Write-Host "Found Qwen models:" -ForegroundColor Green
    $models | ForEach-Object { Write-Host "  - $_" -ForegroundColor Cyan }
    
    $visionModels = $models | Where-Object { $_ -match "vl|vision" -CaseSensitive:$false }
    if ($visionModels) {
        Write-Host ""
        Write-Host "✅ Vision models found:" -ForegroundColor Green
        $visionModels | ForEach-Object { Write-Host "  ✅ $_" -ForegroundColor Green }
    } else {
        Write-Host ""
        Write-Host "❌ No vision models found. Available Qwen models are text-only." -ForegroundColor Yellow
        Write-Host ""
        Write-Host "Try installing a vision model:" -ForegroundColor Cyan
        Write-Host "  ollama pull qwen2-vl:7b" -ForegroundColor Gray
        Write-Host "  (or check: https://ollama.com/library for available models)" -ForegroundColor Gray
    }
} else {
    Write-Host "❌ No Qwen models found in Ollama" -ForegroundColor Red
    Write-Host ""
    Write-Host "Install text model:" -ForegroundColor Cyan
    Write-Host "  ollama pull qwen2.5:7b-instruct-q4_K_M" -ForegroundColor Gray
}

Write-Host ""
Write-Host "All available models:" -ForegroundColor Yellow
ollama list

