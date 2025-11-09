# Deploying to Vercel with Hugging Face Model Hosting

This guide explains how to deploy your app to Vercel while hosting the ML model on Hugging Face (since the model is too large for Vercel).

## 📋 Overview

- **App Hosting**: Vercel (Flask app, frontend)
- **Model Hosting**: Hugging Face (prompt injection detector model)
- **Communication**: Hugging Face Inference API

## 🚀 Step-by-Step Setup

### **Step 1: Prepare Your Hugging Face Account**

1. **Create account**: https://huggingface.co/join
2. **Get API Token**:
   - Go to https://huggingface.co/settings/tokens
   - Click "New token"
   - Name it something like "vercel-app-token"
   - Select "Read" permission
   - Copy the token (you'll need it later!)

### **Step 2: Upload Your Model to Hugging Face**

1. **Install dependencies** (if not already installed):
   ```powershell
   pip install huggingface_hub
   ```

2. **Login to Hugging Face**:
   ```powershell
   huggingface-cli login
   ```
   Paste your API token when prompted.

3. **Edit the upload script**:
   - Open `upload_model_to_hf.py`
   - Change `USERNAME = "your-username"` to your actual Hugging Face username

4. **Run the upload script**:
   ```powershell
   python upload_model_to_hf.py
   ```

5. **Note your model ID**: After upload, you'll get a URL like:
   ```
   https://huggingface.co/your-username/prompt-injection-detector
   ```
   Your model ID is: `your-username/prompt-injection-detector`

### **Step 3: Configure Environment Variables**

1. **Local testing** - Update your `.env` file:
   ```env
   GEMINI_API_KEY=your_gemini_key
   HF_API_TOKEN=your_huggingface_token
   HF_MODEL_ID=your-username/prompt-injection-detector
   USE_LOCAL_MODEL=false
   ```

2. **Vercel deployment** - Add environment variables in Vercel:
   - Go to your Vercel project dashboard
   - Settings → Environment Variables
   - Add these variables:
     - `GEMINI_API_KEY` = your Gemini API key
     - `HF_API_TOKEN` = your Hugging Face API token
     - `HF_MODEL_ID` = your-username/prompt-injection-detector

### **Step 4: Update Your Dependencies**

Make sure your `requirements.txt` includes:
```
huggingface_hub>=0.20.0
```

**Important**: You can remove heavy dependencies for Vercel deployment:
- `transformers`, `torch`, `tqdm`, `matplotlib`, `seaborn` are NOT needed on Vercel
- They're only needed for local model training/testing
- Keep them if you want to use `USE_LOCAL_MODEL=true` locally

### **Step 5: Deploy to Vercel**

1. **Test locally first**:
   ```powershell
   python app.py
   ```
   Make sure the app works with the HF API.

2. **Commit your changes**:
   ```powershell
   git add .
   git commit -m "Add Hugging Face model integration"
   git push
   ```

3. **Deploy** (if you have Vercel CLI):
   ```powershell
   vercel --prod
   ```
   Or push to your connected GitHub repository and Vercel will auto-deploy.

### **Step 6: Verify Deployment**

1. Visit your Vercel app URL
2. Test the prompt injection detector
3. Check the response - it should show:
   ```json
   {
     "model_available": true,
     "using_hf_api": true
   }
   ```

## 🔧 How It Works

### **Before (Won't work on Vercel)**
```
Vercel → Load 500MB+ model locally → Out of memory! ❌
```

### **After (Works perfectly)**
```
Vercel → Call HF API → HF runs model → Return results ✅
```

## 📊 Architecture

```
┌─────────────────┐
│   User Browser  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Vercel (Flask) │  ← Your app runs here
└────────┬────────┘
         │
         ├──────────────────────┐
         │                      │
         ▼                      ▼
┌─────────────────┐    ┌──────────────────┐
│   Gemini API    │    │  Hugging Face    │  ← Model runs here
│  (Explanations) │    │  (ML Detection)  │
└─────────────────┘    └──────────────────┘
```

## ⚙️ Local vs Production

| Environment | Model Loading | Use Case |
|-------------|--------------|----------|
| **Local Dev** | `USE_LOCAL_MODEL=true` | Testing model changes |
| **Production** | `USE_LOCAL_MODEL=false` | Vercel deployment |

## 🐛 Troubleshooting

### Model returns "Model Loading"
The first API call "wakes up" the model on HF. Wait 30-60 seconds and try again.

### "API Token Missing" error
Make sure `HF_API_TOKEN` is set in Vercel environment variables.

### "Config Missing" error
Make sure both `HF_API_TOKEN` and `HF_MODEL_ID` are set.

### Slow response times
- First request is slow (cold start)
- Consider HF Pro ($9/month) for faster inference
- Or use HF Inference Endpoints for dedicated hosting

## 💰 Cost Considerations

| Service | Free Tier | Paid Option |
|---------|-----------|-------------|
| **Vercel** | ✅ Hobby (generous limits) | $20/mo Pro |
| **Hugging Face** | ✅ Inference API (rate limited) | $9/mo Pro (faster) |
| **Gemini API** | ✅ Free tier available | Pay per use |

## 🔒 Security Notes

- ✅ Never commit `.env` file to git
- ✅ Use environment variables for all secrets
- ✅ Rotate API tokens periodically
- ✅ Use HF private repos if your model is sensitive

## 📚 Additional Resources

- [Hugging Face Inference API Docs](https://huggingface.co/docs/api-inference/index)
- [Vercel Environment Variables](https://vercel.com/docs/environment-variables)
- [Flask on Vercel](https://vercel.com/docs/frameworks/flask)

## ✅ Checklist

- [ ] Hugging Face account created
- [ ] API token generated
- [ ] Model uploaded to HF
- [ ] `.env` file configured locally
- [ ] Tested locally with HF API
- [ ] Environment variables added to Vercel
- [ ] Deployed to Vercel
- [ ] Verified deployment works

---

**Need help?** Check the console logs in your browser and Vercel function logs for detailed error messages.
