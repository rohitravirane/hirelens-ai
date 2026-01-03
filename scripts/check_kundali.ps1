param(
    [Parameter(Mandatory=$false)]
    [int]$ResumeId = 42
)

Write-Host "=== Checking Candidate Kundali Data ===" -ForegroundColor Green
Write-Host ""

docker-compose exec backend python scripts/check_experience_data.py $ResumeId

