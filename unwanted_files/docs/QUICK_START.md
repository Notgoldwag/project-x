# 🎯 Quick Start: Deploying with Hugging Face

## What We Did

Your app is now configured to use **Hugging Face Inference API** instead of loading the model locally. This solves the Vercel size limit problem!

## 📝 Next Steps (In Order)

### 1. **Edit Upload Script**
Open `upload_model_to_hf.py` and change:
```python
USERNAME = "your-username"  # ← Change this to your HF username
```

### 2. **Upload Your Model**
```powershell
python upload_model_to_hf.py
```
This will upload your model from `models/prompt_injection_detector/` to Hugging Face.

### 3. **Update .env File**
Create or update your `.env` file with these values:
```env
GEMINI_API_KEY=your_gemini_key
HF_API_TOKEN=hf_...your_token_here
HF_MODEL_ID=your-username/prompt-injection-detector
USE_LOCAL_MODEL=false
```

Get your HF token from: https://huggingface.co/settings/tokens

### 4. **Test Locally**
```powershell
# Install the new dependency
pip install huggingface_hub

# Test the HF API connection
python test_hf_api.py

# Run your app
python app.py
```

### 5. **Configure Vercel**
In your Vercel dashboard → Settings → Environment Variables, add:
- `GEMINI_API_KEY`
- `HF_API_TOKEN`
- `HF_MODEL_ID`

### 6. **Deploy**
```powershell
git add .
git commit -m "Configure HF model hosting"
git push
```
Vercel will auto-deploy.

## 📁 New Files Created

1. **`upload_model_to_hf.py`** - Script to upload model to Hugging Face
2. **`test_hf_api.py`** - Test your HF API setup
3. **`.env.example`** - Template for environment variables
4. **`DEPLOYMENT_GUIDE.md`** - Comprehensive deployment guide

## 🔧 Files Modified

- **`app.py`** - Updated to use HF Inference API
- **`requirements.txt`** - Added `huggingface_hub`

## ✅ How It Works Now

**Before (Failed on Vercel):**
```
App loads → Try to load 500MB model → Vercel runs out of memory ❌
```

**After (Works perfectly):**
```
App loads → Make API call to HF → HF runs model → Return results ✅
```

## 💡 Key Points

1. **Local Development**: You can still use `USE_LOCAL_MODEL=true` for testing
2. **Production**: Always use `USE_LOCAL_MODEL=false` (or omit it)
3. **First Call**: HF models "cold start" - first request may be slow
4. **Cost**: HF Inference API has a free tier with rate limits

## 🆘 Need Help?

1. **Run the test script**: `python test_hf_api.py`
2. **Check the deployment guide**: Open `DEPLOYMENT_GUIDE.md`
3. **Check logs**: Look at Vercel function logs for errors

## 🎉 Benefits

✅ No model size limits on Vercel
✅ Faster deployments (no large files to upload)
✅ Easier model updates (just re-upload to HF)
✅ Better for serverless architecture
✅ Can use more powerful models without Vercel constraints

---

**Ready to start?** Begin with Step 1 above! 🚀
