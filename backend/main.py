import os
import sys
from datetime import datetime
from pathlib import Path

# Ensure both project root and backend directory are in sys.path
root_dir = Path(__file__).resolve().parent.parent
backend_dir = Path(__file__).resolve().parent
for p in [str(root_dir), str(backend_dir)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from sqlalchemy.orm import Session

from backend.config import settings
from backend.database import engine, Base, get_db
from backend.routers import auth, chat, memories, profile
from backend.schemas import HealthResponse

# Create database tables if they do not exist
try:
    Base.metadata.create_all(bind=engine)
except Exception as e:
    import logging
    logging.getLogger("dakshu").warning(f"Database table initialization warning: {e}")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Dakshu AI - Friendly Personal AI Companion Backend API"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins for flexible local development & container setups
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(memories.router)
app.include_router(profile.router)

@app.get(f"{settings.API_PREFIX}/health", response_model=HealthResponse, tags=["System Health"])
def health_check(db: Session = Depends(get_db)):
    """Health check endpoint verifying API, database, and configured AI backend."""
    db_status = "healthy"
    try:
        from sqlalchemy import text
        db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    if settings.AI_BACKEND == "ollama":
        model_name = f"Ollama ({settings.OLLAMA_MODEL})"
    elif settings.AI_BACKEND in ("transformers", "local"):
        model_name = f"Transformers ({settings.LOCAL_MODEL_PATH})"
    else:
        model_name = "Builtin Gemma-4-E4B Companion Engine"

    return HealthResponse(
        status="operational",
        version=settings.VERSION,
        ai_backend=settings.AI_BACKEND,
        ai_model=model_name,
        database=db_status,
        timestamp=datetime.utcnow().isoformat() + "Z"
    )

# Static Files & Frontend SPA serving
frontend_dir = Path(__file__).resolve().parent.parent / "frontend"
if frontend_dir.exists():
    # Mount css, js, assets if directories exist
    for sub in ["css", "js", "assets"]:
        sub_path = frontend_dir / sub
        if sub_path.exists():
            app.mount(f"/{sub}", StaticFiles(directory=str(sub_path)), name=sub)

    def safe_html(file_path: Path):
        try:
            if file_path.exists():
                return HTMLResponse(content=file_path.read_text(encoding="utf-8"))
        except Exception:
            pass
        return FileResponse(file_path)

    # Route for landing page
    @app.get("/", include_in_schema=False)
    async def serve_index():
        return safe_html(frontend_dir / "index.html")

    # Route for chat page
    @app.get("/chat", include_in_schema=False)
    @app.get("/chat.html", include_in_schema=False)
    async def serve_chat():
        return safe_html(frontend_dir / "chat.html")

    # Route for login page
    @app.get("/login", include_in_schema=False)
    @app.get("/login.html", include_in_schema=False)
    async def serve_login():
        return safe_html(frontend_dir / "login.html")

    # Route for register page
    @app.get("/register", include_in_schema=False)
    @app.get("/register.html", include_in_schema=False)
    async def serve_register():
        return safe_html(frontend_dir / "register.html")

    # Route for profile page
    @app.get("/profile", include_in_schema=False)
    @app.get("/profile.html", include_in_schema=False)
    async def serve_profile():
        return safe_html(frontend_dir / "profile.html")

