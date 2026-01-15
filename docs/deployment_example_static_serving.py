"""
Example: How to serve the frontend build from FastAPI for unified deployment.

This example shows how to modify ui_api/main.py to serve static files in production.
Add this code AFTER all API routes are defined (near the end of main.py).

For development, keep using the separate dev servers (uvicorn + vite dev server).
For production, use this approach to serve everything from one FastAPI instance.
"""

from pathlib import Path

from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# NOTE: This is example code meant to be inserted into ui_api/main.py
# In actual usage, REPO_ROOT and app are already defined in main.py:
#   REPO_ROOT = Path(__file__).resolve().parent.parent
#   app = FastAPI(title="Bronze for Life UI API")

# Add this near the end of main.py, after all routes are defined
# ... existing routes ...

# Serve static files in production (when frontend/dist exists)
FRONTEND_DIST = REPO_ROOT / "frontend" / "dist"  # type: ignore[name-defined]

if FRONTEND_DIST.exists():
    # Mount static assets (JS, CSS, images, etc.)
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets")  # type: ignore[name-defined]

    # Serve index.html for all non-API routes (SPA routing)
    @app.get("/{full_path:path}")  # type: ignore[name-defined]
    async def serve_spa(full_path: str):
        """
        Serve the React app for all non-API routes.
        This enables client-side routing (React Router, etc.).
        """
        # Don't serve index.html for API routes
        if full_path.startswith(
            ("api", "docs", "redoc", "openapi.json", "schema", "config", "run", "v2")
        ):
            # Let FastAPI handle API routes normally (will return 404 if not found)
            from starlette.responses import Response

            return Response(status_code=404)

        index_path = FRONTEND_DIST / "index.html"
        if index_path.exists():
            return FileResponse(index_path)
        return {"error": "Frontend not built"}

else:
    # Development mode: frontend served separately
    @app.get("/")  # type: ignore[name-defined]
    async def root():
        return {
            "message": "FastAPI backend is running",
            "docs": "/docs",
            "note": "Frontend should be served separately in development",
        }
