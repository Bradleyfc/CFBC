#!/usr/bin/env python
"""
Script to check if the sentence-transformer model is available locally
"""
import os
import sys

def check_model_locations():
    """Check various locations where the model might be stored"""
    
    model_name = "paraphrase-multilingual-MiniLM-L12-v2"
    
    print(f"Checking locations for model: {model_name}")
    print("=" * 60)
    
    # 1. Check cache directory
    cache_dir = os.path.expanduser("~/.cache/torch/sentence_transformers")
    model_cache_path = os.path.join(cache_dir, model_name.replace('/', '_'))
    
    print(f"1. Cache directory: {cache_dir}")
    print(f"   Model path: {model_cache_path}")
    print(f"   Exists: {os.path.exists(model_cache_path)}")
    
    if os.path.exists(model_cache_path):
        print(f"   Contents: {os.listdir(model_cache_path)}")
    print()
    
    # 2. Check HuggingFace cache
    hf_cache = os.path.expanduser("~/.cache/huggingface")
    print(f"2. HuggingFace cache: {hf_cache}")
    print(f"   Exists: {os.path.exists(hf_cache)}")
    
    if os.path.exists(hf_cache):
        # Look for transformers cache
        transformers_cache = os.path.join(hf_cache, "transformers")
        if os.path.exists(transformers_cache):
            print(f"   Transformers cache: {transformers_cache}")
            print(f"   Contents: {os.listdir(transformers_cache)[:5]}...")  # First 5 items
        
        # Look for hub cache
        hub_cache = os.path.join(hf_cache, "hub")
        if os.path.exists(hub_cache):
            print(f"   Hub cache: {hub_cache}")
            # Look for model-specific folders
            for item in os.listdir(hub_cache):
                if model_name.replace('/', '--') in item:
                    print(f"   Found model folder: {item}")
    print()
    
    # 3. Check site-packages
    try:
        import site
        print("3. Site-packages directories:")
        for site_dir in site.getsitepackages():
            print(f"   {site_dir}")
            
            # Check for sentence_transformers
            st_path = os.path.join(site_dir, "sentence_transformers")
            if os.path.exists(st_path):
                print(f"   Found sentence_transformers at: {st_path}")
                
                # Check for models subdirectory
                models_path = os.path.join(st_path, "models")
                if os.path.exists(models_path):
                    print(f"   Models directory: {models_path}")
                    print(f"   Contents: {os.listdir(models_path)}")
        print()
    except Exception as e:
        print(f"   Error checking site-packages: {e}")
        print()
    
    # 4. Check current venv
    venv_path = sys.prefix
    print(f"4. Current virtual environment: {venv_path}")
    
    venv_site_packages = os.path.join(venv_path, "Lib", "site-packages")  # Windows
    if not os.path.exists(venv_site_packages):
        venv_site_packages = os.path.join(venv_path, "lib", "python*/site-packages")  # Linux/Mac
    
    print(f"   Site-packages: {venv_site_packages}")
    print(f"   Exists: {os.path.exists(venv_site_packages)}")
    
    if os.path.exists(venv_site_packages):
        st_path = os.path.join(venv_site_packages, "sentence_transformers")
        print(f"   SentenceTransformers: {os.path.exists(st_path)}")
    print()
    
    # 5. Try to import and check default cache
    try:
        print("5. Trying to import sentence_transformers...")
        from sentence_transformers import SentenceTransformer
        
        # Check default cache location
        import torch
        default_cache = torch.hub.get_dir()
        print(f"   PyTorch hub cache: {default_cache}")
        print(f"   Exists: {os.path.exists(default_cache)}")
        
        # Try to get model info without loading
        print(f"   Attempting to check model availability...")
        
    except Exception as e:
        print(f"   Import error: {e}")
    
    print("\n" + "=" * 60)
    print("Recommendation:")
    print("If no model found locally, you can download it with:")
    print(f'python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer(\'{model_name}\')"')

if __name__ == "__main__":
    check_model_locations()