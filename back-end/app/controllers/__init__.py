from app.controllers import features, klines, preferences, symbols, tickers

routers = [
    symbols.router,
    klines.router,
    features.router,
    tickers.router,
    preferences.router,
]

__all__ = ["routers"]
