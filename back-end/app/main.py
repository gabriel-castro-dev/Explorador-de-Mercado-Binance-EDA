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
    application = FastAPI(
        title="Crypto Forecasting API",
        version=settings.API_VERSION,
        description=(
            "API de dados de mercado cripto: candles OHLCV, indicadores técnicos "
            "calculados e snapshots 24h dos top 20 ativos por volume da Binance. "
            "**Auth**: envie `Authorization: Bearer <access_token>` do Supabase Auth "
            "em todas as rotas `/api/v1/*`. O token é validado localmente (JWKS) e as "
            "consultas rodam sob o RLS do usuário. Obtenha um token autenticando no "
            "Supabase Auth (`POST {SUPABASE_URL}/auth/v1/token?grant_type=password`)."
        ),
        openapi_tags=[
            {"name": "health", "description": "Liveness da API (público)."},
            {"name": "symbols", "description": "Ativos rastreados pela plataforma."},
            {"name": "klines", "description": "Candles OHLCV por timeframe (15m, 1h, 1d)."},
            {
                "name": "features",
                "description": "Indicadores técnicos calculados (SMA, EMA, RSI, MACD, "
                "Bollinger, ATR...). `24h` é sinônimo de `1d`.",
            },
            {"name": "tickers", "description": "Snapshot 24h mais recente por ativo."},
            {
                "name": "auth",
                "description": "Ponte de identidade: emite custom token do Firebase "
                "para o usuario autenticado no Supabase.",
            },
            {
                "name": "preferences",
                "description": "Preferencias do usuario autenticado (Firestore): dados "
                "pessoais, notificacoes e acessibilidade.",
            },
        ],
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=[
            origin.strip() for origin in settings.API_CORS_ORIGINS.split(",") if origin.strip()
        ],
        allow_credentials=True,
        allow_methods=["GET", "PUT", "POST"],  # PUT: preferencias | POST: token Firebase
        allow_headers=["Authorization", "Content-Type"],
    )
    for router in routers:
        application.include_router(router)

    @application.get("/health", tags=["health"])
    def health() -> HealthOut:  # público: sem auth e sem banco (monitoramento da VM)
        return HealthOut(status="ok", version=settings.API_VERSION)

    return application


app = create_app()
