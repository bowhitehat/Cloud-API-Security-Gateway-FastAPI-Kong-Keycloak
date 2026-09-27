from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.core.config import get_settings
from app.core.logging_config import request_logging_middleware, setup_logging
from app.core.database import Base, engine
from app.models import Order, User  # noqa: F401 - import de SQLAlchemy nhan model
from app.routers import orders, users, fetch, webhooks
settings = get_settings()
setup_logging()

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.app_name,
    description="FastAPI + JWT + RBAC + BOLA demo + web UI + Docker/Kong Gateway/Rate Limiting/Logging/TLS",
    version="2.0.0",
    swagger_ui_init_oauth={
        "clientId": "frontend-app",
        "appName": "Swagger UI",
        "usePkceWithAuthorizationCodeGrant": True,
        "scopes": "openid profile email"
    }
)

app.middleware("http")(request_logging_middleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

frontend_dir = Path(__file__).resolve().parent / "frontend"
static_dir = frontend_dir / "static"

app.mount("/static", StaticFiles(directory=static_dir), name="static")

app.include_router(users.router)
app.include_router(orders.router)
app.include_router(fetch.router)
app.include_router(webhooks.router)
@app.get("/", include_in_schema=False)
def web_home():
    return FileResponse(frontend_dir / "index.html")


@app.get("/web", include_in_schema=False)
def web_alias():
    return FileResponse(frontend_dir / "index.html")


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok"}
