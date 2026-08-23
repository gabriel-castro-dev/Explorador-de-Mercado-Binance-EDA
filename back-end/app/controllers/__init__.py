from app.controllers import auth, features, insights, klines, preferences, symbols, tickers

routers = [
    symbols.router,
    klines.router,
    features.router,
    tickers.router,
    preferences.router,
    insights.router,
    auth.router,
]

__all__ = ["routers"]
