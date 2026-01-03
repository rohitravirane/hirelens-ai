FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    poppler-utils \
    tesseract-ocr \
    tesseract-ocr-eng \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
# Install PyTorch with CUDA support (will use CPU if CUDA not available)
COPY requirements.txt .
# Try CUDA version first, fallback to CPU if needed
# Remove torch from requirements.txt temporarily to avoid conflicts
RUN sed 's/^torch>=.*$//' requirements.txt > requirements_no_torch.txt && \
    pip install --no-cache-dir torch>=2.3.0 torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121 || \
    pip install --no-cache-dir torch>=2.3.0 --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir -r requirements_no_torch.txt || \
    pip install --no-cache-dir -r requirements_no_torch.txt

# Download spaCy language model (required for NER-based parsing)
RUN pip install https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.7.1/en_core_web_sm-3.7.1-py3-none-any.whl || echo "spaCy model download failed, will use fallback"

# Copy application code
COPY . .

# Create uploads directory
RUN mkdir -p /app/uploads

# Expose port
EXPOSE 8000

# Default command (can be overridden in docker-compose)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

