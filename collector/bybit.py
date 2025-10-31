
import ccxt
import pandas as pd
import yaml
from pathlib import Path
import os
from dotenv import load_dotenv
import sys

# 프로젝트 루트 디렉토리를 sys.path에 추가
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from logger.data_saver import save_price_data

# --- Environment and Configuration ---
load_dotenv()

CONFIG_PATH = project_root / "config.yaml"
with open(CONFIG_PATH, 'r') as f:
    config = yaml.safe_load(f)

# 환경 변수에서 API 키 가져오기
API_KEY = os.getenv("BYBIT_API_KEY")
SECRET_KEY = os.getenv("BYBIT_API_SECRET")

# --- API Initialization ---
def get_bybit_exchange(testnet=True):
    """ccxt를 사용하여 Bybit 거래소 객체를 생성합니다."""
    exchange = ccxt.bybit({
        'apiKey': API_KEY,
        'secret': SECRET_KEY,
    })
    if testnet:
        exchange.set_sandbox_mode(True)
    return exchange

def get_bybit_data(exchange, symbol, timeframe='1d', since=None, limit=100):
    """
    Bybit API를 사용하여 암호화폐 데이터를 가져옵니다.

    Args:
        exchange: ccxt 거래소 객체.
        symbol (str): 가져올 자산의 심볼 (e.g., 'BTC/USDT').
        timeframe (str): 데이터의 시간 간격 (e.g., '1h', '1d').
        since (int, optional): 데이터를 가져올 시작 시간 (milliseconds timestamp).
        limit (int): 가져올 데이터 포인트의 수.

    Returns:
        pd.DataFrame: 가격 데이터.
    """
    try:
        print(f"Fetching {symbol} from Bybit...")
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe, since, limit)
        
        if not ohlcv:
            print(f"No data returned for {symbol}.")
            return pd.DataFrame()

        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)
        print(f"Successfully fetched {len(df)} data points for {symbol}.")
        return df

    except ccxt.BadSymbol as e:
        print(f"Error fetching {symbol}: The symbol is not supported by Bybit. Details: {e}")
    except Exception as e:
        print(f"An unexpected error occurred for {symbol}: {e}")
    return pd.DataFrame()

def collect():
    """Bybit 데이터 수집 및 저장을 위한 메인 함수"""
    print("--- Bybit Data Collector ---")
    
    if not API_KEY or not SECRET_KEY:
        print("Bybit API 키가 .env 파일에 설정되지 않았습니다. 수집을 건너뜁니다.")
        return

    exchange = get_bybit_exchange(testnet=True)
    
    # 예시: BTC/USDT 데이터를 최근 100일치 가져오기
    btc_data = get_bybit_data(exchange, 'BTC/USDT', timeframe='1d', limit=100)

    if not btc_data.empty:
        data_to_save = {'BTC/USDT': btc_data}
        print("\n--- Saving data to database ---")
        save_price_data(data_to_save)
        
        print("\n--- BTC/USDT Data (last 5 rows) ---")
        print(btc_data.tail())

if __name__ == '__main__':
    collect()
