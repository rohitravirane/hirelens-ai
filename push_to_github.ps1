# Check if git is initialized
if (-not (Test-Path .git)) {
    Write-Host "Initializing git repository..." -ForegroundColor Yellow
    git init
}

# Fix WSL path ownership issue (PowerShell accessing WSL paths)
Write-Host "Fixing WSL path ownership issue..." -ForegroundColor Yellow
$currentPath = (Get-Location).Path
git config --global --add safe.directory $currentPath

# Git configuration (must be after git init, use --global for WSL paths)
Write-Host "Setting git config..." -ForegroundColor Green
git config --global user.email "rohitravikantrane@gmail.com"
git config --global user.name "Rohit Rane"

# Also set local config
git config user.email "rohitravikantrane@gmail.com"
git config user.name "Rohit Rane"

# Check remote
Write-Host "Checking remote..." -ForegroundColor Green
$remoteExists = git remote | Select-String -Pattern "origin"
if ($remoteExists) {
    Write-Host "Remote 'origin' already exists. Updating..." -ForegroundColor Yellow
    git remote set-url origin https://github.com/rohitravirane/hirelens-ai.git
} else {
    Write-Host "Adding remote 'origin'..." -ForegroundColor Yellow
    git remote add origin https://github.com/rohitravirane/hirelens-ai.git
}

# Add all files
Write-Host "Adding all files..." -ForegroundColor Green
git add .

# Commit
Write-Host "Committing changes..." -ForegroundColor Green
git commit -m "feat: Vision-first document AI system with LayoutLMv3-large, Ollama integration, and GPU acceleration

- Implemented vision-first architecture with LayoutLMv3-large
- Added Ollama integration for fast semantic normalization
- Upgraded PyTorch to 2.5.1+cu121 with safetensors support
- Fixed dtype matching for GPU/CPU compatibility
- Added PyTesseract OCR support for scanned PDFs
- Configured Celery with solo pool for CUDA compatibility
- Enhanced quality scoring with layout confidence bonuses
- Removed personal/sensitive information
- Updated comprehensive documentation"

# Set main branch
Write-Host "Setting main branch..." -ForegroundColor Green
git branch -M main

# Force push to replace existing code
Write-Host "Pushing to GitHub (force push to replace existing)..." -ForegroundColor Green
git push -f origin main

# If main branch doesn't exist, try master
if ($LASTEXITCODE -ne 0) {
    Write-Host "Trying 'master' branch..." -ForegroundColor Yellow
    git branch -M master
    git push -f origin master
}

Write-Host "✅ Push complete!" -ForegroundColor Green

