# REAPER TRADE COPIER - Deployment Guide

## OPTION 1: Quick Share (ngrok) - FREE, Temporary

Best for: Testing, showing to friends, temporary access

```bash
cd ~/.openclaw/reaper-copier
chmod +x start-public.sh
./start-public.sh
```

You'll get a link like: `https://abc123.ngrok.io`

**Share this link with anyone** - they can see your dashboard.

⚠️ Link changes every time you restart.

---

## OPTION 2: Permanent Hosting (Render) - FREE

Best for: 24/7 access, permanent link, sharing with others

### Step 1: Push to GitHub
```bash
# Create a new repo on GitHub, then:
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/YOURNAME/reaper-copier.git
git push -u origin main
```

### Step 2: Deploy to Render
1. Go to https://render.com
2. Sign up (free)
3. Click "New +" → "Web Service"
4. Connect your GitHub repo
5. Settings:
   - **Name:** reaper-copier
   - **Runtime:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python trade_copier.py`
6. Click "Create Web Service"
7. Add Environment Variables:
   - `WEBHOOK_SECRET` = your-secret
   - `ACTIVE_BROKER` = tradovate
   - `TRADOVATE_USERNAME` = your-username
   - `TRADOVATE_PASSWORD` = your-password
   - `TRADOVATE_ACCOUNT_ID` = your-account
   - `TRADOVATE_DEMO` = True

**Your permanent URL:** `https://reaper-copier.onrender.com`

---

## OPTION 3: Railway - FREE

Alternative to Render with easier setup.

### Step 1: Install Railway CLI
```bash
brew install railway
```

### Step 2: Deploy
```bash
cd ~/.openclaw/reaper-copier
railway login
railway init
railway up
```

### Step 3: Set Environment Variables
```bash
railway variables set WEBHOOK_SECRET=your-secret
railway variables set ACTIVE_BROKER=tradovate
railway variables set TRADOVATE_USERNAME=your-username
railway variables set TRADOVATE_PASSWORD=your-password
# ... etc
```

**Your permanent URL:** `https://reaper-copier.up.railway.app`

---

## OPTION 4: Desktop App (Electron)

Package as desktop app like Mission Control.

```bash
cd ~/.openclaw/reaper-copier
npm init -y
npm install electron
```

Then create `main.js` to wrap the web UI.

**Pros:** No hosting needed, runs locally
**Cons:** Can't share link with others

---

## COMPARISON

| Option | Cost | Permanent | Shareable | Setup |
|--------|------|-----------|-----------|-------|
| **ngrok** | Free | ❌ | ✅ | 1 minute |
| **Render** | Free | ✅ | ✅ | 10 minutes |
| **Railway** | Free | ✅ | ✅ | 10 minutes |
| **Desktop** | Free | ✅ | ❌ | 15 minutes |

---

## RECOMMENDATION

1. **Start with ngrok** - Test everything works
2. **Deploy to Render** - Get permanent link to share
3. **Optional: Desktop app** - For personal use only

---

## SECURITY WARNING

⚠️ **Before sharing your link:**

1. Change default `WEBHOOK_SECRET`
2. Use demo/paper trading mode
3. Don't expose real broker credentials in public repos
4. Consider adding password protection for the dashboard

---

**Ready? Run `./start-public.sh` for immediate sharing.**