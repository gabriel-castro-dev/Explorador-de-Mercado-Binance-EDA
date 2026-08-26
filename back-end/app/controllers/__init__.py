from app.controllers import (
    auth,
    features,
    forecasts,
    insights,
    klines,
    preferences,
    symbols,
    tickers,
)

routers = [
    symbols.router,
    klines.router,
    features.router,
    tickers.router,
    forecasts.router,
    preferences.router,
    insights.router,
    auth.router,
]

__all__ = ["routers"]
