from app.controllers import auth, features, klines, preferences, symbols, tickers

routers = [
    symbols.router,
    klines.router,
    features.router,
    tickers.router,
    preferences.router,
    auth.router,
]

__all__ = ["routers"]
