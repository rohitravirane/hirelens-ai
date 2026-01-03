Write-Host "=== Checking Ollama Models ===" -ForegroundColor Green
Write-Host ""

docker-compose exec backend python scripts/check_ollama_models.py

