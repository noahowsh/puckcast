# ⚡ Quick Deploy - Puckcast.ai

## 🚀 Get Live in 10 Minutes

### Step 1: Push to GitHub (3 min)

```bash
cd /Users/noahowsiany/Desktop/Predictive\ Model\ 3.3/NHLpredictionmodel

# Add all files
git add .

# Commit
git commit -m "🚀 Deploy Puckcast.ai"

# Push to GitHub (create repo first at github.com/new)
git remote add origin https://github.com/YOUR_USERNAME/puckcast-ai.git
git branch -M main
git push -u origin main
```

---

### Step 2: Deploy on Streamlit Cloud (5 min)

1. **Go to:** [share.streamlit.io](https://share.streamlit.io)
2. **Sign in** with GitHub
3. **Click "New app"**
4. **Fill in:**
   - Repository: `YOUR_USERNAME/puckcast-ai`
   - Branch: `main`
   - Main file: `dashboard_billion.py`
5. **Click "Deploy"**
6. **Wait 2-3 minutes**
7. **🎉 LIVE at:** `https://puckcast-ai.streamlit.app`

---

### Step 3: Share! (2 min)

Your app is now live! Share the URL:
```
https://puckcast-ai.streamlit.app
```

---

## 🎯 That's It!

- ✅ **Free forever** (public apps)
- ✅ **Auto-updates** on every git push
- ✅ **Professional URL**
- ✅ **No server management**

---

## 🔗 Custom Domain (Optional)

Want `puckcast.ai` instead of `puckcast-ai.streamlit.app`?

1. Buy domain at [Namecheap](https://namecheap.com) (~$10/year)
2. In Streamlit Cloud: Settings → Custom Domain
3. Add CNAME record in your domain registrar
4. Wait 10-30 minutes
5. ✅ Live at `puckcast.ai`!

---

## 📊 What You Get (Free)

- ✅ Unlimited bandwidth
- ✅ HTTPS/SSL included
- ✅ Auto-scaling
- ✅ 99.9% uptime
- ✅ GitHub integration
- ✅ Easy rollbacks

---

## 💡 Pro Tips

1. **Test locally first:**
   ```bash
   streamlit run dashboard_billion.py
   ```

2. **Watch deployment logs** in Streamlit Cloud dashboard

3. **Set up auto-deploy:**
   - Already configured! Push to main branch = auto-deploy

4. **Monitor usage:**
   - Check Streamlit Cloud analytics dashboard

---

## 🆘 Need Help?

See `DEPLOYMENT_GUIDE.md` for:
- Detailed troubleshooting
- Alternative platforms (Railway, Render)
- Advanced configurations
- Custom domain setup

---

**Ready? Run Step 1 above! 🚀**

