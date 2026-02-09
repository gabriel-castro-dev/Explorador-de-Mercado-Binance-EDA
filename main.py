"""
Explorador de Mercado Binance - Sistema de Análise Exploratória de Dados

Extrai dados da API Binance e estrutura em DataFrames para análise.
"""

import logging
from config import setup_logging
from controllers.controllers_manager import ControllersManager

# Configurar logging global
setup_logging()
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("Iniciando Explorador de Mercado Binance")
    logger.info("=" * 60)
    
    try:
        # Inicializar managers com injeção de dependências
        controllers_manager = ControllersManager()
        market_data, account_history = controllers_manager.export_controllers()
        
        # Exemplos de uso
        symbol = 'BTCUSDT'
        interval = '1h'
        start_time = '2 days ago UTC'
        
        logger.info(f"Iniciando coleta de dados para {symbol}...")
        
        # Dados de mercado
        tickers_data = market_data.get_tickers()
        ticker24_data = market_data.get_ticker_24hr(symbol)
        orderbook_tickers_data = market_data.get_orderbook_tickers(symbol)
        klines_data = market_data.get_klines(symbol, interval)
        historical_klines_data = market_data.get_historical_klines(symbol, interval, start_time)
        average_price_data = market_data.get_avg_price(symbol)
        recent_trades_data = market_data.get_recent_trades(symbol)
        historical_trades_data = market_data.get_historical_trades(symbol)
        aggregate_trades_data = market_data.get_aggregate_trades(symbol)
        depth_data = market_data.get_depth(symbol)
        
        # Exibir amostra dos dados
        print("\n" + "="*60)
        print("AMOSTRA DOS DADOS COLETADOS (ticker 24h)")
        print("="*60)
        print(depth_data.head())
        print("="*60 + "\n")
        
        logger.info("Coleta de dados de mercado concluída com sucesso")
    
        
    except Exception as e:
        logger.error(f"Erro durante execução: {e}", exc_info=True)
        raise


