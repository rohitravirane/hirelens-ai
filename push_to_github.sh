#!/bin/bash

# Git configuration
echo "Setting git config..."
git config user.email "rohitravikantrane@gmail.com"
git config user.name "Rohit Rane"

# Check if git is initialized
if [ ! -d .git ]; then
    echo "Initializing git repository..."
    git init
fi

# Check remote
echo "Checking remote..."
if git remote | grep -q origin; then
    echo "Remote 'origin' already exists. Updating..."
    git remote set-url origin https://github.com/rohitravirane/hirelens-ai.git
else
    echo "Adding remote 'origin'..."
    git remote add origin https://github.com/rohitravirane/hirelens-ai.git
fi

# Add all files
echo "Adding all files..."
git add .

# Commit
echo "Committing changes..."
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

# Force push to replace existing code
echo "Pushing to GitHub (force push to replace existing)..."
git push -f origin main

# If main branch doesn't exist, try master
if [ $? -ne 0 ]; then
    echo "Trying 'master' branch..."
    git push -f origin master
fi

echo "✅ Push complete!"

