# GitHub Push Steps

## Step-by-Step Commands

**PowerShell mein ye commands run karo:**

```powershell
# Step 1: Git initialize (pehle ye karo)
git init

# Step 2: Git config set karo
git config user.email "rohitravikantrane@gmail.com"
git config user.name "Rohit Rane"

# Step 3: Remote add karo
git remote add origin https://github.com/rohitravirane/hirelens-ai.git
# Agar already hai to:
# git remote set-url origin https://github.com/rohitravirane/hirelens-ai.git

# Step 4: Sab files add karo
git add .

# Step 5: Commit karo
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

# Step 6: Force push (existing code replace hoga)
git branch -M main
git push -f origin main
```

## Important Notes

- **Force push (`-f`)** existing code ko completely replace kar dega
- `.env` file automatically ignore hogi (`.gitignore` mein hai)
- `uploads/` folder bhi ignore hogi
- Personal information already removed hai

## Verification

Push ke baad verify karo:
```powershell
git remote -v
git log --oneline -1
```

