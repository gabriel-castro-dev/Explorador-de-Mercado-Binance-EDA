"""FastAPI application entrypoint (uvicorn app.main:app)."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.controllers import routers
from app.schemas.market import HealthOut
from config import get_settings, setup_logging


def create_app() -> FastAPI:
    """Build the API application with CORS, routers and the public health check."""
    setup_logging()
    settings = get_settings()
    if not settings.SUPABASE_PUBLISHABLE_KEY:
        raise RuntimeError("SUPABASE_PUBLISHABLE_KEY is required to run the API")
    application = FastAPI(title="Crypto Forecasting API", version=settings.API_VERSION)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=[
            origin.strip() for origin in settings.API_CORS_ORIGINS.split(",") if origin.strip()
        ],
        allow_credentials=True,
        allow_methods=["GET"],
        allow_headers=["Authorization", "Content-Type"],
    )
    for router in routers:
        application.include_router(router)

    @application.get("/health", tags=["health"])
    def health() -> HealthOut:  # público: sem auth e sem banco (monitoramento da VM)
        return HealthOut(status="ok", version=settings.API_VERSION)

    return application


app = create_app()
