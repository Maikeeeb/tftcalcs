# Quick Start: Deploying to Production

## Recommended: Render (Simplest for Portfolios)

### Step 1: Prepare Code (Optional - for unified deployment)

If you want to serve the frontend from FastAPI (simplest option), add static file serving. See `docs/deployment_example_static_serving.py` for example code.

**OR** use separate deployments (backend + frontend) - no code changes needed.

### Step 2: Deploy Backend to Render

1. Go to [render.com](https://render.com) and sign up/login
2. Click "New +" → "Web Service"
3. Connect your GitHub repository
4. Configure:
   - **Name**: `tftcalcs-backend` (or your choice)
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn ui_api.main:app --host 0.0.0.0 --port $PORT`
   - **Environment Variables**:
     - `CORS_ORIGINS`: `https://your-frontend-url.onrender.com` (we'll set this after frontend deploys)
     - `LOG_LEVEL`: `INFO`
5. Click "Create Web Service"
6. Copy the service URL (e.g., `https://tftcalcs-backend.onrender.com`)

### Step 3: Deploy Frontend to Render (or Vercel)

**Option A: Render (Static Site)**
1. Click "New +" → "Static Site"
2. Connect same GitHub repository
3. Configure:
   - **Name**: `tftcalcs-frontend`
   - **Build Command**: `cd frontend && npm install && npm run build`
   - **Publish Directory**: `frontend/dist`
   - **Environment Variables**:
     - `VITE_API_BASE_URL`: `https://tftcalcs-backend.onrender.com` (use your backend URL)
4. Click "Create Static Site"
5. Copy the frontend URL

**Option B: Vercel (Recommended for React apps)**
1. Go to [vercel.com](https://vercel.com) and sign up/login
2. Click "Add New" → "Project"
3. Import your GitHub repository
4. Configure:
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
   - **Environment Variables**:
     - `VITE_API_BASE_URL`: `https://tftcalcs-backend.onrender.com`
5. Click "Deploy"
6. Copy the deployment URL

### Step 4: Update CORS

Go back to Render backend service:
1. Go to Environment tab
2. Update `CORS_ORIGINS` to include your frontend URL: `https://your-frontend-url.vercel.app` (or `.onrender.com`)
3. Redeploy (Render auto-redeploys on env var changes)

### Step 5: Test

1. Visit your frontend URL
2. Try running a solver
3. Check browser console for errors
4. Check Render logs if issues occur

---

## Alternative: Railway (Similar to Render)

1. Go to [railway.app](https://railway.app)
2. Click "New Project" → "Deploy from GitHub repo"
3. Railway auto-detects Python
4. Add environment variable: `CORS_ORIGINS` (set after frontend deploys)
5. For frontend: Create separate service or deploy separately to Vercel/Netlify

---

## Alternative: Unified Deployment (One Service)

If you modify FastAPI to serve static files (see `docs/deployment_example_static_serving.py`):

**Render:**
1. New Web Service
2. Build Command: `pip install -r requirements.txt && cd frontend && npm install && npm run build`
3. Start Command: `uvicorn ui_api.main:app --host 0.0.0.0 --port $PORT`
4. No CORS needed (same origin)

**Note:** Render free tier may have limits on build time. Separate deployments are more reliable.

---

## Cost

All options above use **free tiers** suitable for portfolio sites:
- **Render**: 750 hours/month free (enough for 24/7)
- **Vercel**: Free for hobby projects
- **Railway**: $5/month credit (usually enough)

---

## Next Steps

- See `docs/DEPLOYMENT.md` for detailed options and troubleshooting
- Test locally with production build: `cd frontend && npm run build && npm run preview`
- Add custom domain (optional) in platform settings
- Monitor logs and errors in platform dashboards
