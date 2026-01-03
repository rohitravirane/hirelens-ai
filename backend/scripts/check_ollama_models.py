#!/usr/bin/env python3
"""Check if Ollama models are available"""
import requests
import json

OLLAMA_ENDPOINT = "http://host.docker.internal:11434"

try:
    response = requests.get(f"{OLLAMA_ENDPOINT}/api/tags", timeout=5)
    if response.status_code == 200:
        models = response.json().get("models", [])
        print("\n" + "="*80)
        print("OLLAMA MODELS AVAILABLE")
        print("="*80 + "\n")
        
        if models:
            for model in models:
                name = model.get("name", "unknown")
                size = model.get("size", 0)
                size_gb = size / (1024**3) if size > 0 else 0
                print(f"✅ {name}")
                print(f"   Size: {size_gb:.2f} GB")
                print()
            
            # Check for required models
            model_names = [m.get("name", "") for m in models]
            required_text = "qwen2.5:7b-instruct-q4_K_M"
            
            # Check for vision models (try multiple possible names)
            vision_models_to_try = [
                "qwen2-vl:7b",
                "qwen2-vl:7b-instruct",
                "qwen2.5-vl:7b-instruct-q4_K_M",
                "qwen-vl:7b",
            ]
            
            has_vision = False
            found_vision_model = None
            for vision_model in vision_models_to_try:
                # Check if any model name contains the vision model identifier
                matching = [name for name in model_names if vision_model.split(":")[0] in name.lower() and ('vl' in name.lower() or 'vision' in name.lower())]
                if matching:
                    has_vision = True
                    found_vision_model = matching[0]
                    break
            
            has_text = any(required_text in name for name in model_names)
            
            print("="*80)
            print("REQUIRED MODELS STATUS:")
            print("="*80)
            if has_vision:
                print(f"Vision Model: ✅ FOUND ({found_vision_model})")
            else:
                print(f"Vision Model: ❌ NOT FOUND")
                print(f"\n⚠️  Try installing a vision model:")
                print(f"   ollama pull qwen2-vl:7b")
                print(f"   (or check available models: ollama list)")
                print(f"   Note: Vision models may not be available in Ollama yet.")
                print(f"   The system will use text-only model which works fine.")
            print(f"Text Model ({required_text}): {'✅ FOUND' if has_text else '❌ NOT FOUND'}")
            
            if not has_text:
                print(f"\n⚠️  Install text model:")
                print(f"   ollama pull {required_text}")
        else:
            print("❌ No models found in Ollama")
            print(f"\nInstall models:")
            print(f"  ollama pull qwen2.5-vl:7b-instruct-q4_K_M")
            print(f"  ollama pull qwen2.5:7b-instruct-q4_K_M")
    else:
        print(f"❌ Ollama API error: {response.status_code}")
        print(f"   Make sure Ollama is running and accessible at {OLLAMA_ENDPOINT}")
        
except requests.exceptions.ConnectionError:
    print(f"❌ Cannot connect to Ollama at {OLLAMA_ENDPOINT}")
    print("   Make sure Ollama is installed and running")
    print("   Install from: https://ollama.ai")
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "="*80)

