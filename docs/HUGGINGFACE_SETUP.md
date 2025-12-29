# Hugging Face Setup Guide

## 🎯 Why Hugging Face?

- ✅ **Free** - No API costs
- ✅ **Local** - Runs on your machine/server
- ✅ **Private** - Data never leaves your infrastructure
- ✅ **Production Ready** - Works in both development and production
- ✅ **Flexible** - Choose models based on your hardware

## 🚀 Quick Setup

### Option 1: Use Hugging Face (Recommended for Local)

In `.env` file:
```env
AI_PROVIDER=auto
# or explicitly
AI_PROVIDER=huggingface

# Models (automatically downloads on first use)
HUGGINGFACE_EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
HUGGINGFACE_LLM_MODEL=TinyLlama/TinyLlama-1.1B-Chat-v1.0
USE_GPU=false
MODEL_DEVICE=cpu
```

### Option 2: Use OpenAI (API-based)

In `.env` file:
```env
AI_PROVIDER=openai
OPENAI_API_KEY=your-api-key-here
```

### Option 3: Auto (Smart Selection)

```env
AI_PROVIDER=auto
# Uses HuggingFace if no OpenAI key, else uses OpenAI
```

## 📦 Model Recommendations

### For CPU (Default - Works Everywhere)

**Embeddings:**
- `sentence-transformers/all-MiniLM-L6-v2` (80MB) - Fast, good quality
- `sentence-transformers/all-mpnet-base-v2` (420MB) - Better quality

**Text Generation:**
- `TinyLlama/TinyLlama-1.1B-Chat-v1.0` (637MB) - Fast, small
- `microsoft/DialoGPT-small` (117MB) - Very fast, basic

### For GPU (Better Performance)

**Text Generation:**
- `mistralai/Mistral-7B-Instruct-v0.1` (14GB) - High quality
- `meta-llama/Llama-2-7b-chat-hf` (13GB) - Excellent quality

**Settings:**
```env
USE_GPU=true
MODEL_DEVICE=cuda
```

## 💾 First Run

Models will be automatically downloaded on first use:
- Embedding model: ~80-400MB
- Text generation model: ~100MB-14GB (depending on model)

Download location: `~/.cache/huggingface/`

## ⚡ Performance

### CPU Performance
- Embeddings: ~50-100ms per text
- Text generation: ~2-5 seconds per explanation

### GPU Performance
- Embeddings: ~10-20ms per text
- Text generation: ~0.5-1 second per explanation

## 🔧 Configuration

### Memory Optimization

For limited RAM, use smaller models:
```env
HUGGINGFACE_LLM_MODEL=TinyLlama/TinyLlama-1.1B-Chat-v1.0
```

Models use 8-bit quantization on CPU to reduce memory.

### Speed Optimization

1. **Use GPU** if available:
   ```env
   USE_GPU=true
   MODEL_DEVICE=cuda
   ```

2. **Use smaller models** for faster inference

3. **Enable caching** (already enabled) - embeddings cached for 24 hours

## 🆚 Hugging Face vs OpenAI

| Feature | Hugging Face | OpenAI |
|---------|--------------|--------|
| Cost | Free | Paid per token |
| Privacy | 100% local | Data sent to API |
| Speed | Fast (local) | Fast (API) |
| Setup | Auto-download | API key needed |
| Quality | Good | Excellent |
| Offline | Yes | No |

## 🎯 Best Practices

1. **Development**: Use Hugging Face (free, fast iteration)
2. **Production (Low Volume)**: Use Hugging Face (cost-effective)
3. **Production (High Volume)**: Use OpenAI (better quality, faster API)
4. **Privacy-Sensitive**: Always use Hugging Face

## 🔍 Troubleshooting

### Model Download Fails

```bash
# Manual download
python -c "from transformers import AutoModel; AutoModel.from_pretrained('sentence-transformers/all-MiniLM-L6-v2')"
```

### Out of Memory

Use smaller models:
```env
HUGGINGFACE_LLM_MODEL=TinyLlama/TinyLlama-1.1B-Chat-v1.0
```

### Slow Performance

1. Enable GPU if available
2. Use smaller models
3. Increase system RAM

## 📝 Example .env Configuration

```env
# Use Hugging Face (Local, Free)
AI_PROVIDER=auto

# Embeddings (Fast, Good Quality)
HUGGINGFACE_EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

# Text Generation (Small, Fast for CPU)
HUGGINGFACE_LLM_MODEL=TinyLlama/TinyLlama-1.1B-Chat-v1.0

# Hardware
USE_GPU=false
MODEL_DEVICE=cpu

# OpenAI (Optional - only if you want to use it)
# OPENAI_API_KEY=
```

---

**Hugging Face = Free, Local, Private AI! 🚀**

