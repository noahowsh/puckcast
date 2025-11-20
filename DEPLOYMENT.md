# Puckcast V2.0 - Vercel Deployment Guide

## Quick Deploy to Vercel

### 1. Import Project to Vercel
```bash
# Connect your GitHub repo to Vercel
# Go to: https://vercel.com/new
# Select: noahowsh/puckcast repository
```

### 2. Configure Build Settings

**Framework Preset:** Next.js
**Root Directory:** `web`
**Build Command:** `npm run build`
**Output Directory:** `.next` (default)
**Install Command:** `npm install`

### 3. Environment Variables (Optional)
No environment variables required for basic deployment.
All data is served from static JSON files in `web/src/data/`.

### 4. Custom Domain Setup
If you have a custom domain (like puckcast.ai):

1. Go to **Project Settings → Domains**
2. Add your domain: `puckcast.ai` and `www.puckcast.ai`
3. Configure DNS:
   - **A Record**: `@` → `76.76.21.21`
   - **CNAME**: `www` → `cname.vercel-dns.com`
4. Wait for DNS propagation (~5-10 minutes)

### 5. Deploy!

Vercel auto-deploys on every push to your main branch. For this branch:
```bash
# Merge to main when ready
git checkout main
git merge claude/v6.0-development-01G4v8EPZsJn31QKaeeM83Uj
git push origin main
```

Auto-deployment triggers immediately on push!

---

## Daily Data Updates

To keep predictions fresh, you'll need to update the JSON data files daily:

### Option 1: Manual Updates (Simple)
1. Run Python scripts locally to generate new predictions
2. Copy updated JSON files to `web/src/data/`
3. Commit and push to trigger auto-deploy

### Option 2: GitHub Actions (Automated - Recommended)
Create `.github/workflows/daily-predictions.yml`:

```yaml
name: Daily Predictions Update

on:
  schedule:
    - cron: '0 14 * * *'  # 10am ET (2pm UTC)
  workflow_dispatch:  # Manual trigger

jobs:
  update-predictions:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt

      - name: Generate predictions
        run: |
          python scripts/generate_daily_predictions.py
          # This should output JSON to web/src/data/

      - name: Commit and push updates
        run: |
          git config user.name "Puckcast Bot"
          git config user.email "bot@puckcast.ai"
          git add web/src/data/*.json
          git commit -m "Update predictions for $(date +%Y-%m-%d)" || exit 0
          git push
```

---

## Performance Checklist

- ✅ **Static Generation**: All pages pre-rendered (super fast)
- ✅ **CDN Distribution**: Vercel Edge Network (global)
- ✅ **Image Optimization**: Next.js Image component
- ✅ **System Fonts**: Using local fonts (no Google Fonts blocking)
- ✅ **Build Size**: ~500KB gzipped

**Expected Load Time**: <1s on 4G, <500ms on fiber

---

## Monitoring & Analytics

### Built-in Vercel Analytics
Enable in Project Settings → Analytics (free tier available)

### Performance Metrics to Watch
- **LCP** (Largest Contentful Paint): Target <2.5s
- **FID** (First Input Delay): Target <100ms
- **CLS** (Cumulative Layout Shift): Target <0.1

---

## Troubleshooting

### Build fails with "Module not found"
- Check that all imports use `@/` alias (configured in tsconfig.json)
- Verify all JSON data files exist in `web/src/data/`

### Fonts not loading
- Currently using system fonts as fallback
- To re-enable Google Fonts: uncomment lines in `web/src/app/layout.tsx`

### Predictions not updating
- Verify JSON files in `web/src/data/` are being updated
- Check GitHub Actions logs if using automated updates
- Trigger manual redeployment in Vercel dashboard

---

## Next Steps After Deployment

1. **Set up X/Twitter automation** (see V2_SITE_PLAN_REVISED.md)
2. **Configure GitHub Actions** for daily data updates
3. **Monitor performance** in Vercel Analytics
4. **Test on mobile** devices (site is mobile-first)

---

**Questions?** Check the [Next.js Vercel docs](https://nextjs.org/docs/deployment) or [Vercel support](https://vercel.com/support).
