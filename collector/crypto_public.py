import ccxt
import pandas as pd
import yaml
from pathlib import Path
from datetime import datetime
import sys

# 프로젝트 루트 디렉토리를 sys.path에 추가
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from logger.data_saver import save_price_data

# --- Configuration ---
CONFIG_PATH = project_root / "config.yaml"
with open(CONFIG_PATH, 'r') as f:
    config = yaml.safe_load(f)

EXCHANGE = config['crypto_public']['exchange']
SYMBOLS = config['crypto_public']['symbols']
INTERVAL = config['crypto_public']['interval']

def get_public_crypto_data(exchange_name, symbols, timeframe='1h', since=None, limit=100):
    """
    ccxt를 사용하여 API 키 없이 공개된 암호화폐 데이터를 가져옵니다.

    Args:
        exchange_name (str): 거래소 이름 (e.g., 'binance', 'bybit').
        symbols (list): 가져올 자산의 심볼 리스트 (e.g., ['BTC/USDT', 'ETH/USDT']).
        timeframe (str): 데이터의 시간 간격 (e.g., '1m', '5m', '1h', '1d').
        since (int, optional): 데이터를 가져올 시작 시간 (milliseconds timestamp).
        limit (int): 가져올 데이터 포인트의 수.

    Returns:
        dict: 각 심볼을 key로, 가격 데이터(DataFrame)를 value로 갖는 딕셔너리.
    """
    try:
        exchange_class = getattr(ccxt, exchange_name)
        exchange = exchange_class()
    except (AttributeError, ccxt.ExchangeNotFound):
        print(f"Error: The exchange '{exchange_name}' is not supported by ccxt or not found.")
        return {}

    if not exchange.has['fetchOHLCV']:
        print(f"Error: The exchange '{exchange_name}' does not support fetching OHLCV data.")
        return {}

    all_data = {}
    for symbol in symbols:
        try:
            print(f"Fetching {symbol} from {exchange_name}...")
            ohlcv = exchange.fetch_ohlcv(symbol, timeframe, since, limit)
            
            if not ohlcv:
                print(f"No data returned for {symbol}.")
                continue

            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            # data_saver가 인덱스를 처리하므로 여기서는 인덱스를 설정하지 않습니다.
            all_data[symbol] = df
            print(f"Successfully fetched {len(df)} data points for {symbol}.")

        except ccxt.BadSymbol as e:
            print(f"Error fetching {symbol}: The symbol is not supported by {exchange_name}. Details: {e}")
        except Exception as e:
            print(f"An unexpected error occurred for {symbol}: {e}")
            
    return all_data

def collect():
    """공개 암호화폐 데이터 수집 및 저장을 위한 메인 함수"""
    print(f"--- Public Crypto Data Collector (using {EXCHANGE}) ---")
    
    # 1. 데이터 가져오기
    # 예시: 최근 1000개의 1시간 봉 데이터 가져오기
    crypto_data = get_public_crypto_data(EXCHANGE, SYMBOLS, timeframe=INTERVAL, limit=1000)

    if crypto_data:
        # 2. 가져온 데이터를 데이터베이스에 저장
        print("\n--- Saving data to database ---")
        save_price_data(crypto_data)

        # 3. 저장 후 샘플 데이터 출력
        btc_data = crypto_data.get("BTC/USDT")
        if btc_data is not None:
            print("\n--- BTC/USDT Data (last 5 rows) ---")
            # 인덱스가 아닌 'timestamp' 컬럼을 기준으로 tail을 확인합니다.
            print(btc_data.tail())

if __name__ == '__main__':
    collect()
