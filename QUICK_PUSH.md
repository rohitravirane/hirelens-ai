# Quick GitHub Push Commands

## PowerShell Commands (WSL Path Fix Included)

**PowerShell mein ye commands run karo:**

```powershell
# Step 1: Fix WSL path ownership issue
git config --global --add safe.directory '%(prefix)///wsl.localhost/Ubuntu/home/rohit/projects/hirelens-ai'

# Step 2: Git config (already done if you ran --global)
git config --global user.email "rohitravikantrane@gmail.com"
git config --global user.name "Rohit Rane"

# Step 3: Remote add/update
git remote remove origin
git remote add origin https://github.com/rohitravirane/hirelens-ai.git

# Step 4: Add all files
git add .

# Step 5: Commit
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

# Step 6: Push
git branch -M main
git push -f origin main
```

## Alternative: Use WSL Terminal (Recommended)

**WSL2 Ubuntu terminal mein:**

```bash
cd /home/rohit/projects/hirelens-ai

git config user.email "rohitravikantrane@gmail.com"
git config user.name "Rohit Rane"

git remote remove origin 2>/dev/null || true
git remote add origin https://github.com/rohitravirane/hirelens-ai.git

git add .
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

git branch -M main
git push -f origin main
```

