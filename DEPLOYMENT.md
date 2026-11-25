# 🚀 DAKSHU AI: How to Publish & Share With Others

Here are the two best ways to publish DAKSHU AI so anyone on mobile, laptop, or anywhere on the internet can access it:

---

## ⚡ Method 1: Instant Public Link (From Your PC)
### *100% Free • Keeps Your Local Ollama Model • Zero External API Keys!*

Since you already trained and run the local `dakshu` model on your computer, this is the quickest way to share your live app with friends, family, or your phone:

### How it works:
1. **Start the Server:** Double-click `start_server.bat` in `c:\Dharsheni\DAKSHU AI\`.
2. **Start the Public Tunnel:** Double-click `share_online.bat` (or open Command Prompt and run):
   ```bash
   npx localtunnel --port 8000
   ```
3. **You get a public HTTPS link**, e.g.:
   ```
   your url is: https://dakshu-ai.loca.lt
   ```
4. **Send that link to anyone!**
   - When opened on any phone or laptop, it connects directly to your local DAKSHU AI app and uses your local fine-tuned Ollama `dakshu` model.
   - *(Note: Your PC must stay on while friends are using it).*

---

## 🌐 Method 2: 24/7 Cloud Deployment on Vercel
### *Always Online 24/7 Even When Your PC is Turned Off*

If you want a permanent link like `https://dakshu-ai.vercel.app` that runs forever in the cloud:

### Step 1: Push your code to GitHub
Open Command Prompt in `c:\Dharsheni\DAKSHU AI`:
```bash
git init
git add .
git commit -m "DAKSHU AI Full-Stack Release"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/DAKSHU-AI.git
git push -u origin main
```

### Step 2: Import into Vercel
1. Go to [https://vercel.com](https://vercel.com) and sign in with GitHub.
2. Click **"Add New..."** → **"Project"**.
3. Select your **DAKSHU-AI** repository.
4. Framework Preset: Leave as **Other** (Vercel automatically detects `vercel.json`).
5. Click **Deploy**.

### Step 3: Cloud AI Engine (Optional)
- By default, Vercel uses the built-in DAKSHU Companion engine (100% offline, requires **zero API keys**).
- If you want ultra-fast cloud LLM inference on Vercel, you can add a free Groq API key in **Settings → Environment Variables**:
  - `AI_BACKEND`: `groq`
  - `GROQ_API_KEY`: `gsk_...` (from [console.groq.com](https://console.groq.com))
  - `GROQ_MODEL`: `qwen/qwen3.8-27b`

---

## 🌟 Method 3: Deploy to Render.com (Recommended for Persistent Python Web Services)

Render runs a **persistent Python server (Uvicorn)**, which has no serverless timeout limits and supports full Server-Sent Events (SSE) streaming.

### Step 1: Push code to GitHub
Ensure `render.yaml` and `requirements.txt` are committed.

### Step 2: Deploy on Render
1. Go to [https://render.com](https://render.com) and log in.
2. Click **"New +"** → **"Blueprint"**.
3. Connect your GitHub repository.
4. Render will read `render.yaml` and automatically configure:
   - A Python Web Service running FastAPI.
   - A free managed PostgreSQL database.
5. In the dashboard, enter your `GROQ_API_KEY`.
6. Click **Apply**.
7. Your app is live with a free URL: `https://dakshu-ai.onrender.com`!

---

## 🚂 Method 3: Deploy to Railway.app

1. Go to [https://railway.app](https://railway.app).
2. Click **"New Project"** → **"Deploy from GitHub repo"**.
3. Select your repository.
4. Railway will automatically detect the `Procfile` or `Dockerfile`.
5. Under **Variables**, add:
   - `AI_BACKEND=groq`
   - `GROQ_API_KEY=your_key`
   - `SECRET_KEY=your_secret`
6. (Optional) Click **New** → **Database** → **Add PostgreSQL**, and link `DATABASE_URL`.
7. Click **Deploy**.

---

## 🌐 Method 4: Deploy to Netlify

Netlify is optimized for static frontends.

### Architecture:
- Frontend on Netlify: `https://dakshu.netlify.app`
- Backend on Render / Railway: `https://dakshu-backend.onrender.com`

### Steps:
1. In `netlify.toml`, configure the proxy redirect:
   ```toml
   [[redirects]]
     from = "/api/*"
     to = "https://your-backend.onrender.com/api/:splat"
     status = 200
     force = true
   ```
2. Go to [https://netlify.com](https://netlify.com) → **"Add new site"** → **"Import from Git"**.
3. Set **Publish directory**: `frontend`.
4. Click **Deploy Site**.

---

## 🗄️ Free PostgreSQL Database (Neon.tech)

If you deploy to Vercel or Netlify and want your users' chat history and memories to persist permanently:

1. Go to [https://neon.tech](https://neon.tech) (Free tier: 0.5 GB, zero credit card required).
2. Click **"Create Project"** → name it `dakshu-db`.
3. Copy the **Connection String**:
   ```
   postgresql://user:password@ep-xyz.us-east-2.aws.neon.tech/neondb?sslmode=require
   ```
4. Paste it as `DATABASE_URL` in your Vercel or Render environment variables!
5. Dakshu AI will automatically create all tables (`users`, `conversations`, `messages`, `memories`, `user_preferences`) upon startup!

