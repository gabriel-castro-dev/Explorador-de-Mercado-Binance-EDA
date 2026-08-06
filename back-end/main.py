"""Standalone script that verifies connectivity with the Binance API."""

from app.services.binance_market_data_service import BinanceMarketService

service = BinanceMarketService()

print(service.ping())