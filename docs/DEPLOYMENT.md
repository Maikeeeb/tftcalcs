# Production Deployment Guide

This guide covers multiple approaches to deploying the TFT Calculator for portfolio use.

## Quick Decision Matrix

| Option | Complexity | Cost | Best For |
|--------|-----------|------|----------|
| **Unified (FastAPI serves frontend)** | Low | Free/Cheap | Portfolio sites, simple deployments |
| **Platform-as-a-Service (Render/Railway)** | Low-Medium | Free tier available | Quick deployment, managed infrastructure |
| **Separate deployments** | Medium | Free tier available | Scalable architecture, independent scaling |
| **Docker** | Medium-High | Varies | Maximum portability, custom hosting |

---

## Option 1: Unified Deployment (Recommended for Portfolios)

Serve the frontend build directly from FastAPI. This is the simplest approach for portfolio sites.

### Pros
- Single deployment target
- No CORS issues
- Simple configuration
- Works well for portfolio sites

### Cons
- Tighter coupling between frontend and backend
- Less flexible scaling

### Implementation Steps

1. **Modify FastAPI to serve static files** (see `ui_api/main.py` changes below)
2. **Build the frontend**: `cd frontend && npm run build`
3. **Deploy to any Python hosting platform** (Render, Railway, Fly.io, Heroku, etc.)

### Code Changes Required

The FastAPI app needs to serve static files from `frontend/dist`. See the code changes in the section below.

### Deployment Platforms

**Render** (Recommended - free tier available):
- Create a new Web Service
- Connect your GitHub repository
- Build command: `cd frontend && npm install && npm run build`
- Start command: `uvicorn ui_api.main:app --host 0.0.0.0 --port $PORT`
- Environment: Python 3
- Add Python version file: `.python-version` or use runtime.txt

**Railway**:
- Connect GitHub repository
- Auto-detects Python project
- Add build step: `cd frontend && npm install && npm run build`
- Start command: `uvicorn ui_api.main:app --host 0.0.0.0 --port $PORT`

**Fly.io**:
- Install flyctl CLI
- Run `fly launch` in project root
- Configure `fly.toml` for Python app
- Add build step for frontend

---

## Option 2: Platform-as-a-Service (Render/Railway/Fly.io)

Deploy backend and frontend separately but manage them on the same platform.

### Render Configuration

**Backend Service:**
- Type: Web Service
- Environment: Python 3
- Build Command: `pip install -r requirements.txt`
- Start Command: `uvicorn ui_api.main:app --host 0.0.0.0 --port $PORT`
- Environment Variables:
  - `CORS_ORIGINS`: Your frontend URL (e.g., `https://your-app.onrender.com`)

**Frontend Service:**
- Type: Static Site
- Build Command: `cd frontend && npm install && npm run build`
- Publish Directory: `frontend/dist`
- Environment Variables:
  - `VITE_API_BASE_URL`: Your backend URL (e.g., `https://your-backend.onrender.com`)

### Railway Configuration

**Backend:**
- Connect repository
- Add build command: `pip install -r requirements.txt`
- Start command: `uvicorn ui_api.main:app --host 0.0.0.0 --port $PORT`
- Add environment variable: `CORS_ORIGINS` with frontend URL

**Frontend:**
- Connect repository
- Root directory: `frontend`
- Build command: `npm install && npm run build`
- Start command: `npx serve dist -s`
- Add environment variable: `VITE_API_BASE_URL` with backend URL

---

## Option 3: Separate Deployments (Backend + Frontend)

Deploy backend to a Python host and frontend to a static hosting service.

### Backend Deployment Options

- **Render**: Free tier, Python support, automatic HTTPS
- **Railway**: Free tier (limited hours), easy setup
- **Fly.io**: Generous free tier, global deployment
- **PythonAnywhere**: Free tier, simple for Python apps
- **Heroku**: Paid (no free tier), but widely used

### Frontend Deployment Options

- **Vercel**: Free tier, excellent React support, automatic deployments
- **Netlify**: Free tier, great for static sites
- **GitHub Pages**: Free, simple for static sites
- **Cloudflare Pages**: Free, fast CDN

### Example: Backend on Render + Frontend on Vercel

**Backend (Render):**
1. Create Web Service on Render
2. Connect GitHub repo
3. Build: `pip install -r requirements.txt`
4. Start: `uvicorn ui_api.main:app --host 0.0.0.0 --port $PORT`
5. Environment: `CORS_ORIGINS=https://your-app.vercel.app`

**Frontend (Vercel):**
1. Import project on Vercel
2. Root directory: `frontend`
3. Build command: `npm run build`
4. Output directory: `dist`
5. Environment: `VITE_API_BASE_URL=https://your-backend.onrender.com`
6. Deploy

---

## Option 4: Docker Deployment

For maximum portability and control.

### Dockerfile Example

See `Dockerfile` in repository root (if created) for a multi-stage build:
- Stage 1: Build frontend
- Stage 2: Python runtime with built frontend

### Docker Compose (for local testing)

Useful for testing production-like setup locally.

### Deployment

- **Docker Hub + Any VPS**: Build image, push to Docker Hub, deploy to VPS
- **Fly.io**: Supports Dockerfiles natively
- **Railway**: Supports Dockerfiles
- **AWS ECS/Fargate**: For AWS deployments
- **DigitalOcean App Platform**: Supports Dockerfiles

---

## Environment Variables for Production

### Backend (.env or platform config)

```env
# CORS - Set to your frontend URL(s)
CORS_ORIGINS=https://your-app.vercel.app,https://your-app.netlify.app

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# Rate Limiting (adjust based on expected traffic)
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60
```

### Frontend (.env.production)

```env
# API Base URL - Set to your backend URL
VITE_API_BASE_URL=https://your-backend.onrender.com
```

**Note:** Vite requires `VITE_` prefix for environment variables to be exposed to the frontend.

---

## Build Process

### Local Build (for testing)

```bash
# 1. Build frontend
cd frontend
npm install
npm run build

# 2. Test production build locally
# Option A: Serve from FastAPI (if using unified deployment)
# (See code changes below)

# Option B: Test frontend separately
npm run preview  # Vite preview server
# Set VITE_API_BASE_URL to your backend URL
```

### Production Build

Most platforms handle this automatically, but manual steps:

```bash
# Install dependencies
pip install -r requirements.txt
cd frontend && npm install

# Build frontend
cd frontend && npm run build

# Start backend (serves frontend if using unified deployment)
uvicorn ui_api.main:app --host 0.0.0.0 --port $PORT
```

---

## Pre-Deployment Checklist

- [ ] Test production build locally
- [ ] Verify environment variables are set correctly
- [ ] Check CORS configuration matches frontend URL
- [ ] Ensure API_BASE_URL in frontend points to backend
- [ ] Test all major features (Bronze mode, Standard mode, Itemization)
- [ ] Verify static assets (images) load correctly
- [ ] Check console for errors in production build
- [ ] Test on mobile devices (responsive design)
- [ ] Verify rate limiting is appropriate for portfolio traffic
- [ ] Check HTTPS is enabled (required for modern browsers)

---

## Monitoring & Maintenance

### Logs
- Most platforms provide log access in their dashboards
- FastAPI logging is configured to output structured logs
- Set `LOG_FORMAT=json` for easier parsing in log aggregation tools

### Performance
- Monitor response times for `/run` endpoint (solver execution)
- Consider caching if traffic increases
- Monitor rate limit hit rate

### Updates
- Push to main branch triggers automatic deployments on most platforms
- Test changes locally first
- Consider staging environment for larger changes

---

## Troubleshooting

### CORS Errors
- Verify `CORS_ORIGINS` includes your frontend URL (exact match, including protocol)
- Check browser console for CORS error details
- Ensure backend URL in frontend matches deployed backend

### Frontend Can't Connect to Backend
- Verify `VITE_API_BASE_URL` is set correctly
- Check backend is running and accessible
- Verify CORS configuration
- Check browser network tab for failed requests

### Static Files Not Loading
- Ensure frontend build completed successfully
- Verify file paths are correct (case-sensitive on some platforms)
- Check browser network tab for 404s
- Verify build output directory matches configuration

### Build Failures
- Check platform logs for specific errors
- Verify Node.js version compatibility (check `frontend/package.json` engines if specified)
- Verify Python version compatibility
- Check for missing dependencies in `requirements.txt` or `package.json`

---

## Cost Estimates (Free Tiers)

- **Render**: Free tier includes 750 hours/month (enough for 24/7 on one service)
- **Railway**: $5/month free credit (enough for small projects)
- **Vercel**: Free tier for hobby projects
- **Netlify**: Free tier (100GB bandwidth/month)
- **Fly.io**: Generous free tier (3 shared-cpu VMs)

For portfolio sites, the free tiers should be sufficient unless you expect significant traffic.
