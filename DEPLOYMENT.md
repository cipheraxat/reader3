# Free Cloud Deployment Guide

This app can be deployed for FREE on multiple platforms. Choose the one that suits you best!

## 🚀 Quick Deploy Options

### Option 1: Render.com (Recommended - Easiest)

**FREE tier includes:**
- 512 MB RAM
- Shared CPU
- Auto-deploy from GitHub
- HTTPS included
- Custom domain support

**Steps:**

1. **Push code to GitHub:**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/YOUR_USERNAME/reader3.git
   git push -u origin master
   ```

2. **Deploy on Render:**
   - Go to https://render.com
   - Sign up/login with GitHub
   - Click "New +" → "Web Service"
   - Connect your repository
   - Render will auto-detect the `render.yaml` file
   - Click "Create Web Service"
   - Wait 2-3 minutes for deployment

3. **Access your app:**
   - URL: `https://reader3-XXXX.onrender.com`
   - Upload EPUBs via command line or copy to repo

**Note:** Free tier sleeps after 15 min inactivity (first request takes ~30s to wake up)

---

### Option 2: Railway.app

**FREE tier includes:**
- $5 credit/month
- 512 MB RAM
- Auto-deploy from GitHub
- HTTPS included

**Steps:**

1. Push code to GitHub (same as above)

2. **Deploy on Railway:**
   - Go to https://railway.app
   - Login with GitHub
   - Click "New Project" → "Deploy from GitHub repo"
   - Select your repository
   - Railway auto-detects configuration
   - Click "Deploy"

3. **Generate domain:**
   - Click "Settings" → "Generate Domain"
   - Access at: `https://reader3-production-XXXX.up.railway.app`

---

### Option 3: Fly.io

**FREE tier includes:**
- 3 shared-cpu-1x VMs
- 3GB persistent storage
- Auto-scaling

**Steps:**

1. **Install Fly CLI:**
   ```bash
   curl -L https://fly.io/install.sh | sh
   ```

2. **Login and launch:**
   ```bash
   fly auth login
   fly launch
   ```

3. **Follow prompts:**
   - Choose app name
   - Select region
   - Don't add PostgreSQL
   - Deploy!

4. **Access:** `https://your-app-name.fly.dev`

---

### Option 4: Heroku

**Steps:**

1. **Install Heroku CLI:**
   ```bash
   curl https://cli-assets.heroku.com/install.sh | sh
   ```

2. **Deploy:**
   ```bash
   heroku login
   heroku create reader3-app
   git push heroku master
   heroku open
   ```

---

### Option 5: Google Cloud Run

**FREE tier includes:**
- 2 million requests/month
- 360,000 GB-seconds memory
- 180,000 vCPU-seconds

**Steps:**

1. **Install gcloud CLI:**
   ```bash
   curl https://sdk.cloud.google.com | bash
   ```

2. **Deploy:**
   ```bash
   gcloud init
   gcloud run deploy reader3 --source . --region us-central1 --allow-unauthenticated
   ```

---

## 📚 Adding Books to Cloud Instance

### Method 1: Include in Repository
```bash
# Add sample book
cp your-book.epub .
git add your-book.epub
git commit -m "Add sample book"
git push
```

Then SSH/exec into container:
```bash
# For Render/Railway
uv run reader3.py your-book.epub
```

### Method 2: Upload via API (Create upload endpoint)

Add this to `server.py`:
```python
from fastapi import UploadFile, File
import subprocess

@app.post("/admin/upload")
async def upload_epub(file: UploadFile = File(...)):
    # Save uploaded file
    file_path = f"/tmp/{file.filename}"
    with open(file_path, "wb") as f:
        f.write(await file.read())
    
    # Process it
    subprocess.run(["python", "reader3.py", file_path])
    
    return {"status": "processed", "filename": file.filename}
```

### Method 3: Cloud Storage
Mount a cloud storage bucket (S3, Google Cloud Storage) to persist books.

---

## 🔒 Security Recommendations

For public deployment:

1. **Add authentication:**
   ```python
   from fastapi.security import HTTPBasic, HTTPBasicCredentials
   
   security = HTTPBasic()
   
   @app.get("/")
   async def library(credentials: HTTPBasicCredentials = Depends(security)):
       # Verify credentials
       ...
   ```

2. **Rate limiting:**
   ```bash
   pip install slowapi
   ```

3. **Environment secrets:**
   - Set ADMIN_PASSWORD in environment
   - Never commit .env file

---

## 📊 Monitoring

All platforms provide logs:

**Render:**
```
Dashboard → Logs
```

**Railway:**
```
Project → Deployments → View Logs
```

**Fly.io:**
```bash
fly logs
```

---

## 💰 Cost Comparison

| Platform | Free Tier | Limitations | Best For |
|----------|-----------|-------------|----------|
| **Render** | 512MB RAM | Sleeps after 15min | Simple apps |
| **Railway** | $5/month credit | ~500 hours | Active development |
| **Fly.io** | 3 VMs | 3GB storage | Always-on apps |
| **Heroku** | 1 dyno | Sleeps after 30min | Quick demos |
| **Cloud Run** | 2M requests | Pay per use | Scalable apps |

---

## 🎯 Recommended: Render.com

**Why?**
- Zero config with `render.yaml`
- Free HTTPS
- GitHub auto-deploy
- Easy to use
- Generous free tier

**Live in 5 minutes!**

---

## 🌐 Custom Domain (Free)

1. **Get free domain:**
   - Freenom.com (free .tk, .ml, .ga)
   - GitHub Student Pack (free .me domain)

2. **Configure DNS:**
   - Add CNAME record pointing to your Render/Railway URL
   - Enable in platform settings

---

## 📝 Post-Deployment Checklist

- [ ] App is accessible via HTTPS
- [ ] Health check endpoint works: `/health`
- [ ] Sample book is loaded
- [ ] Dark mode works
- [ ] Reading features work
- [ ] Check logs for errors
- [ ] Set up monitoring alerts
- [ ] Add authentication if needed

---

## 🆘 Troubleshooting

**App won't start:**
- Check logs for Python errors
- Verify `requirements.txt` has all dependencies
- Check `PORT` environment variable

**Slow first load:**
- Free tiers sleep when inactive
- Consider paid tier for always-on

**Books not persisting:**
- Use cloud storage for persistence
- Include books in git repository

**Out of memory:**
- Reduce `MAX_BOOK_CACHE_SIZE`
- Use smaller EPUB files
- Upgrade to paid tier

---

## 📞 Support

- Render: https://render.com/docs
- Railway: https://docs.railway.app
- Fly.io: https://fly.io/docs

Happy reading! 📚✨
