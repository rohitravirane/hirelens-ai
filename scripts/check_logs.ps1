param(
    [Parameter(Mandatory=$false)]
    [string]$Service = "all",
    [Parameter(Mandatory=$false)]
    [int]$Lines = 50
)

Write-Host "=== Checking HireLens AI Logs ===" -ForegroundColor Green
Write-Host ""

if ($Service -eq "all") {
    $linesText = "last $Lines lines"
    Write-Host "Backend Logs ($linesText):" -ForegroundColor Yellow
    Write-Host "----------------------------------------" -ForegroundColor Gray
    docker-compose logs --tail=$Lines backend
    
    Write-Host ""
    Write-Host "Celery Worker Logs ($linesText):" -ForegroundColor Yellow
    Write-Host "----------------------------------------" -ForegroundColor Gray
    docker-compose logs --tail=$Lines celery-worker
    
    Write-Host ""
    Write-Host "Frontend Logs ($linesText):" -ForegroundColor Yellow
    Write-Host "----------------------------------------" -ForegroundColor Gray
    docker-compose logs --tail=$Lines frontend
} else {
    $linesText = "last $Lines lines"
    Write-Host "$Service Logs ($linesText):" -ForegroundColor Yellow
    Write-Host "----------------------------------------" -ForegroundColor Gray
    docker-compose logs --tail=$Lines $Service
}

Write-Host ""
Write-Host "💡 Tip: Use 'docker-compose logs -f <service>' to follow logs in real-time" -ForegroundColor Cyan
Write-Host ""

