# Production Setup Guide - Mistral Model

## Best Quality Resume Parsing with Mistral-7B

This guide shows how to deploy the system with Mistral-7B model for best quality resume parsing in production.

## Requirements

### Minimum Requirements (CPU)
- **RAM**: 16GB+ (recommended: 32GB)
- **Storage**: 20GB+ free space (for model download)
- **CPU**: Multi-core processor (4+ cores recommended)

### Recommended Requirements (GPU)
- **GPU**: NVIDIA GPU with 8GB+ VRAM (16GB+ recommended)
- **RAM**: 16GB+ system RAM
- **Storage**: 20GB+ free space
- **CUDA**: 11.8+ installed

## Configuration

### Option 1: GPU with Quantization (Best Performance)

```bash
# .env file
USE_GPU=true
HUGGINGFACE_PARSER_MODEL=mistralai/Mistral-7B-Instruct-v0.1
USE_QUANTIZATION=true
```

**Benefits:**
- Best quality parsing
- 8-bit quantization reduces memory by ~50%
- Fast inference on GPU
- Production-ready

### Option 2: GPU without Quantization (Maximum Quality)

```bash
# .env file
USE_GPU=true
HUGGINGFACE_PARSER_MODEL=mistralai/Mistral-7B-Instruct-v0.1
USE_QUANTIZATION=false
```

**Benefits:**
- Maximum quality (full precision)
- Requires more VRAM (14GB+)
- Best for high-end GPUs

### Option 3: CPU (Slower but Works)

```bash
# .env file
USE_GPU=false
HUGGINGFACE_PARSER_MODEL=mistralai/Mistral-7B-Instruct-v0.1
USE_QUANTIZATION=false
```

**Note:** CPU inference is slow (30-60 seconds per resume). Not recommended for production.

## Memory Management

### Set Memory Limits (Optional)

```python
# In config.py or .env
MODEL_MAX_MEMORY = {"0": "10GiB", "cpu": "20GiB"}
```

This prevents OOM errors by limiting model memory usage.

## Docker Setup

### GPU Support in Docker

```yaml
# docker-compose.yml
services:
  celery-worker:
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    environment:
      - USE_GPU=true
      - HUGGINGFACE_PARSER_MODEL=mistralai/Mistral-7B-Instruct-v0.1
      - USE_QUANTIZATION=true
```

### Install NVIDIA Container Toolkit

```bash
# Ubuntu/Debian
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list

sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit
sudo systemctl restart docker
```

## First Run

1. **Model Download**: On first resume processing, Mistral-7B will auto-download (~14GB)
   - Download time: 10-30 minutes depending on internet speed
   - Model cached in `~/.cache/huggingface/` (or Docker volume)

2. **Memory Check**: Ensure sufficient memory before processing
   ```bash
   # Check GPU memory
   nvidia-smi
   
   # Check system RAM
   free -h
   ```

3. **Test Processing**: Process a test resume to verify setup
   - First run: Slow (model loading + download)
   - Subsequent runs: Fast (cached model)

## Performance Expectations

### GPU (with quantization)
- **First resume**: 30-60 seconds (model loading)
- **Subsequent resumes**: 5-15 seconds per resume
- **Memory usage**: ~8-10GB VRAM

### GPU (without quantization)
- **First resume**: 30-60 seconds
- **Subsequent resumes**: 5-10 seconds per resume
- **Memory usage**: ~14-16GB VRAM

### CPU
- **First resume**: 2-5 minutes
- **Subsequent resumes**: 30-60 seconds per resume
- **Memory usage**: ~16-20GB RAM

## Fallback Strategy

The system automatically falls back to smaller models if Mistral fails:

1. **Mistral-7B** (primary, best quality)
2. **Phi-2** (fallback, good quality, smaller)
3. **TinyLlama** (final fallback, fast, lower quality)

## Production Recommendations

### 1. Use GPU with Quantization
```bash
USE_GPU=true
USE_QUANTIZATION=true
```

### 2. Set Memory Limits
```python
MODEL_MAX_MEMORY = {"0": "10GiB"}
```

### 3. Use Model Caching
- Models are cached after first download
- Mount cache directory as Docker volume for persistence

### 4. Monitor Resources
```bash
# GPU monitoring
watch -n 1 nvidia-smi

# Memory monitoring
docker stats
```

### 5. Scale Horizontally
- Run multiple Celery workers on different GPUs
- Use Redis for task distribution

## Troubleshooting

### Out of Memory (OOM)
- Enable quantization: `USE_QUANTIZATION=true`
- Set memory limits: `MODEL_MAX_MEMORY`
- Use smaller model: `microsoft/phi-2`

### Slow Processing
- Enable GPU: `USE_GPU=true`
- Check GPU utilization: `nvidia-smi`
- Use quantization for faster inference

### Model Download Fails
- Check internet connection
- Increase timeout in Docker
- Manually download model to cache directory

## Alternative Models

If Mistral is too large, use these alternatives:

### Phi-2 (Good Balance)
```bash
HUGGINGFACE_PARSER_MODEL=microsoft/phi-2
```
- Size: ~2.7GB
- Quality: ⭐⭐⭐⭐
- Works on: GPU/CPU

### TinyLlama (Fast)
```bash
HUGGINGFACE_PARSER_MODEL=TinyLlama/TinyLlama-1.1B-Chat-v1.0
```
- Size: ~600MB
- Quality: ⭐⭐⭐
- Works on: CPU

## Cost Comparison

| Setup | Initial Cost | Running Cost | Quality |
|-------|-------------|--------------|---------|
| GPU + Mistral | GPU hardware | Electricity | ⭐⭐⭐⭐⭐ |
| CPU + Mistral | None | None | ⭐⭐⭐⭐ (slow) |
| CPU + Phi-2 | None | None | ⭐⭐⭐⭐ |
| CPU + TinyLlama | None | None | ⭐⭐⭐ |

## Summary

**Best Production Setup:**
- GPU with 8GB+ VRAM
- Mistral-7B with 8-bit quantization
- Memory limits configured
- Model caching enabled

This gives you **world-class resume parsing quality** with **production-ready performance**!

