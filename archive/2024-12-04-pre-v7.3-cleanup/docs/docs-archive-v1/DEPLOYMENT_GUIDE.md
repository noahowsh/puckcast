# 🚀 Puckcast.ai Deployment Guide

## Overview
This guide will walk you through deploying **Puckcast.ai** to the web using **Streamlit Cloud** (recommended) or alternative platforms.

---

## 🏆 Option 1: Streamlit Cloud (RECOMMENDED)

### ⚡ Why Streamlit Cloud?
- ✅ **100% FREE** for public apps
- ✅ Auto-deploy from GitHub
- ✅ Custom domain support
- ✅ Built-in secrets management
- ✅ Takes 5-10 minutes

### 📋 Prerequisites
1. GitHub account
2. Streamlit Cloud account (free at [share.streamlit.io](https://share.streamlit.io))
3. Your code pushed to GitHub

---

## 🎯 Step-by-Step Deployment

### Step 1: Push to GitHub

```bash
cd /Users/noahowsiany/Desktop/Predictive\ Model\ 3.3/NHLpredictionmodel

# Initialize git (if not already done)
git init

# Add all files
git add .

# Commit
git commit -m "🚀 Puckcast.ai - Ready for deployment"

# Create a new repository on GitHub (do this in browser first)
# Then:
git remote add origin https://github.com/YOUR_USERNAME/puckcast-ai.git
git branch -M main
git push -u origin main
```

### Step 2: Deploy on Streamlit Cloud

1. **Go to:** [share.streamlit.io](https://share.streamlit.io)

2. **Sign in** with GitHub

3. **Click "New app"**

4. **Configure:**
   - **Repository:** `YOUR_USERNAME/puckcast-ai`
   - **Branch:** `main`
   - **Main file path:** `dashboard_billion.py`
   - **App URL:** `puckcast-ai` (or your preferred subdomain)

5. **Click "Deploy"**

6. **Wait 2-5 minutes** for deployment

7. **🎉 DONE!** Your app will be live at:
   ```
   https://puckcast-ai.streamlit.app
   ```

---

### Step 3: Custom Domain (Optional)

To use **puckcast.ai** as your domain:

1. **In Streamlit Cloud:**
   - Go to App Settings
   - Click "Custom Domain"
   - Enter: `puckcast.ai`

2. **In your domain registrar (e.g., GoDaddy, Namecheap):**
   - Add a CNAME record:
     ```
     Type: CNAME
     Name: @
     Value: [provided by Streamlit Cloud]
     TTL: 3600
     ```

3. **Wait 5-30 minutes** for DNS propagation

4. **✅ DONE!** App will be live at `puckcast.ai`

---

## 🔒 Managing Secrets

If you add API keys or secrets in the future:

1. **In Streamlit Cloud Dashboard:**
   - Go to App Settings → Secrets
   - Add secrets in TOML format:
     ```toml
     [secrets]
     api_key = "your_api_key_here"
     ```

2. **In your code:**
   ```python
   import streamlit as st
   api_key = st.secrets["api_key"]
   ```

---

## 🚂 Option 2: Railway (Alternative)

### Steps:
1. **Go to:** [railway.app](https://railway.app)
2. **Sign in** with GitHub
3. **Click "New Project" → "Deploy from GitHub repo"**
4. **Select:** `puckcast-ai` repository
5. **Add start command:**
   ```bash
   streamlit run dashboard_billion.py --server.port $PORT
   ```
6. **Deploy** (takes 3-5 minutes)

**Cost:** $5/month after free credits

---

## 🎨 Option 3: Render (Alternative)

### Steps:
1. **Go to:** [render.com](https://render.com)
2. **Sign in** with GitHub
3. **Click "New" → "Web Service"**
4. **Select:** `puckcast-ai` repository
5. **Configure:**
   - **Environment:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `streamlit run dashboard_billion.py --server.port $PORT --server.address 0.0.0.0`
6. **Deploy**

**Cost:** Free tier available

---

## ⚡ Option 4: Vercel

### ⚠️ Important Note:
Vercel is **NOT RECOMMENDED** for Streamlit apps because:
- ❌ Optimized for static sites & serverless functions (10s timeout)
- ❌ Streamlit needs persistent WebSocket connections
- ❌ Will experience frequent disconnects
- ❌ More complex setup than other options

### If You Still Want to Try:

**Better Alternative:** Deploy as a Docker container on Vercel's edge network

1. **Create `Dockerfile`:**
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8501
CMD ["streamlit", "run", "dashboard_billion.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

2. **Create `vercel.json`:**
```json
{
  "builds": [
    {
      "src": "dashboard_billion.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "dashboard_billion.py"
    }
  ]
}
```

3. **Deploy:**
```bash
npm i -g vercel
vercel --prod
```

**Issues You'll Face:**
- 🔴 10-second serverless timeout (Streamlit needs longer)
- 🔴 WebSocket limitations
- 🔴 Cold starts on every request
- 🔴 Not designed for interactive dashboards

**Verdict:** ❌ **Don't use Vercel for Streamlit**

---

## 🎯 Platform Comparison

| Platform | Streamlit Support | Free Tier | Best For | Rating |
|----------|------------------|-----------|----------|--------|
| **Streamlit Cloud** | ✅ Perfect | ✅ Yes | Streamlit apps | ⭐⭐⭐⭐⭐ |
| **Railway** | ✅ Good | $5 credit/mo | Full control | ⭐⭐⭐⭐ |
| **Render** | ✅ Good | ✅ Yes (limited) | Medium traffic | ⭐⭐⭐⭐ |
| **Vercel** | ❌ Poor | ✅ Yes | Static sites only | ⭐ |
| **Netlify** | ❌ Poor | ✅ Yes | Static sites only | ⭐ |
| **AWS/GCP** | ✅ Good | ❌ No | Enterprise | ⭐⭐⭐⭐ |

### Why Streamlit Apps Don't Work Well on Vercel/Netlify:

**Streamlit Architecture:**
```
Browser ←→ WebSocket ←→ Streamlit Server (persistent)
```

**Vercel/Netlify Architecture:**
```
Browser → Serverless Function (10s max, then dies)
```

**The Problem:**
- Streamlit needs to maintain state between interactions
- Vercel/Netlify kill connections after 10-30 seconds
- Every click would restart your entire app
- Data caching wouldn't work properly

---

## 📊 Monitoring Your App

### Streamlit Cloud Dashboard:
- **Logs:** View real-time logs
- **Analytics:** Track app usage
- **Resources:** Monitor CPU/memory
- **Errors:** See error traces

---

## 🔧 Troubleshooting

### Issue: "File not found: assets/logo.png"
**Solution:**
```bash
git add assets/logo.png assets/favicon.png -f
git commit -m "Add logo assets"
git push
```

### Issue: "Module not found"
**Solution:** Check `requirements.txt` has all dependencies

### Issue: "App is slow"
**Solution:** Streamlit Cloud free tier has limited resources. Consider:
- Caching more data with `@st.cache_data`
- Upgrading to Streamlit Cloud Pro
- Moving to Railway/Render with more resources

### Issue: "Data not updating"
**Solution:** 
- Check cache TTL in `@st.cache_data(ttl=3600)`
- Add a manual refresh button
- Schedule data updates with GitHub Actions

---

## 🎯 Next Steps After Deployment

1. **✅ Test the live app** thoroughly
2. **📱 Share the URL** with your team
3. **📊 Monitor performance** in first 24 hours
4. **🔄 Set up auto-updates** (Streamlit Cloud auto-deploys on push)
5. **🎨 Consider custom domain** for professional branding
6. **📈 Track analytics** to see usage

---

## 💰 Costs Summary

| Platform | Free Tier | Paid Tier | Best For |
|----------|-----------|-----------|----------|
| **Streamlit Cloud** | ✅ Unlimited public apps | $20/mo (private) | Public dashboards |
| **Railway** | $5 credit/mo | $5-20/mo | Full control |
| **Render** | ✅ Limited hours | $7/mo (unlimited) | Medium traffic |
| **AWS/GCP** | ❌ | $20-100/mo | Enterprise |

---

## 🚨 Important Notes

1. **Data Privacy:** All data is public on Streamlit Cloud free tier
2. **Resources:** Free tier has CPU/memory limits
3. **Uptime:** Free tier may have cold starts (2-3 second delay)
4. **Custom Domain:** Requires paid Streamlit Cloud plan ($20/mo)

---

## 📞 Support

- **Streamlit Docs:** [docs.streamlit.io](https://docs.streamlit.io)
- **Community Forum:** [discuss.streamlit.io](https://discuss.streamlit.io)
- **Discord:** [streamlit.io/community](https://streamlit.io/community)

---

## ✨ Recommended: Streamlit Cloud

For your use case (class project, portfolio piece), **Streamlit Cloud is perfect:**
- ✅ Free
- ✅ Easy
- ✅ Professional URL
- ✅ Auto-updates
- ✅ Great for sharing with professors/recruiters

---

**Ready to deploy? Follow Step 1 above! 🚀**

