param(
    [Parameter(Mandatory=$true)]
    [int]$ResumeId
)

Write-Host "=== Reprocessing Resume ===" -ForegroundColor Green
Write-Host ""

Write-Host "1. Restarting Celery worker..." -ForegroundColor Yellow
docker-compose restart celery-worker

Write-Host ""
Write-Host "2. Waiting 15 seconds for Celery to restart..." -ForegroundColor Yellow
Start-Sleep -Seconds 15

Write-Host ""
Write-Host "3. Reprocessing Resume ID $ResumeId..." -ForegroundColor Yellow
docker-compose exec backend python scripts/reprocess_single_resume.py $ResumeId

Write-Host ""
Write-Host "✅ Reprocessing queued! Wait 1-2 minutes, then check results." -ForegroundColor Green
Write-Host ""
Write-Host "To check results:" -ForegroundColor Cyan
Write-Host "  docker-compose exec backend python scripts/check_experience_data.py $ResumeId" -ForegroundColor Gray

