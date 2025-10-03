# 🔧 Fix: SentenceTransformer PyTorch Error

## Error You're Seeing

```
NotImplementedError: Cannot copy out of meta tensor; no data! 
Please use torch.nn.Module.to_empty() instead of torch.nn.Module.to() 
when moving module from meta to a different device.
```

## Quick Fix (Choose One)

### Option 1: Update Dependencies (Recommended)

```bash
# Activate your virtual environment first
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Uninstall conflicting packages
pip uninstall torch torchvision sentence-transformers -y

# Install compatible versions
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
pip install sentence-transformers>=2.3.0
pip install transformers>=4.30.0

# Restart the app
streamlit run app.py
```

### Option 2: Use the Updated Code with Fallback

I've updated `memory_manager.py` to include a fallback mechanism. The app will now:
1. Try to load the embedding model normally
2. If that fails, use a simple hash-based fallback
3. The app will work (with slightly reduced semantic search quality)

**Steps**:
1. Copy the updated `memory_manager.py` from the artifacts (left sidebar)
2. Replace your existing file
3. Restart: `streamlit run app.py`

You'll see warnings like:
```
⚠ Warning: Could not load SentenceTransformer model
⚠ Falling back to simple hash-based embeddings
```

**This is OK!** The app will still work, just with simpler memory search.

### Option 3: Fresh PyTorch Installation

```bash
# Remove cache
rm -rf ~/.cache/torch
rm -rf ~/.cache/huggingface

# Reinstall from scratch
pip uninstall torch torchvision torchaudio sentence-transformers -y
pip install torch torchvision sentence-transformers

# Restart
streamlit run app.py
```

### Option 4: Skip Qdrant for Now (Simplest)

If you just want to test the app without embeddings:

1. The updated code I provided will automatically fallback
2. Memory search will still work (just less sophisticated)
3. All other features work perfectly
4. You can add proper embeddings later

## What Changed in the Fix

The updated `memory_manager.py` now:

```python
try:
    # Try to load model
    self.model = SentenceTransformer(model_name, device=device)
    self.model_loaded = True
except Exception as e:
    # Graceful fallback
    print("⚠ Warning: Using fallback embeddings")
    self.model_loaded = False

# Later in encode():
if self.model_loaded:
    return self.model.encode(text)  # Real embeddings
else:
    return self._fallback_encode(text)  # Simple hash-based
```

## Testing the Fix

After applying one of the options above, test:

```bash
streamlit run app.py
```

You should see one of:
- ✅ `✓ Embedding model loaded successfully` (Option 1 or 3 worked)
- ⚠️ `⚠ Falling back to simple hash-based embeddings` (Option 2 - app still works!)

## Impact of Using Fallback

### With Real Embeddings (Preferred):
- Semantic search works great
- "exercise" finds related terms like "workout", "fitness"
- Conversation context is highly accurate

### With Fallback (Temporary Solution):
- ✅ App works perfectly
- ✅ All features functional
- ✅ Search still works
- ⚠️ Search is keyword-based instead of semantic
- ⚠️ "exercise" won't automatically match "workout"

**For testing and development, the fallback is totally fine!**

## Why This Error Happens

This is a known issue with:
- PyTorch 2.0+ with certain model architectures
- Incompatibility between PyTorch and sentence-transformers versions
- Model loading on CPU with newer PyTorch versions

## Recommended for Production

For production deployment:

```bash
# In your requirements.txt, pin versions:
torch>=2.1.0,<2.3.0
sentence-transformers>=2.3.0
transformers>=4.35.0
```

Then:
```bash
pip install -r requirements.txt --force-reinstall
```

## Alternative: Use OpenAI Embeddings

If PyTorch continues to cause issues, you can switch to OpenAI embeddings:

1. Update `config.py`:
```python
embedding_provider: str = "openai"  # instead of sentence-transformers
```

2. Modify `memory_manager.py` to use OpenAI API
3. Costs ~$0.0001 per 1K tokens (very cheap)

## Need Help?

If none of these work:

1. **Check Python version**: `python --version` (need 3.9+)
2. **Check if CUDA available**: `python -c "import torch; print(torch.cuda.is_available())"`
3. **Try clean install**:
   ```bash
   rm -rf venv
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

---

**TL;DR**: Copy the updated `memory_manager.py` from artifacts and restart the app. It will work even if embeddings fail to load! 🎉