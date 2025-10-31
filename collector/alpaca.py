import alpaca_trade_api as tradeapi
import yaml
import pandas as pd
from pathlib import Path
import os
from dotenv import load_dotenv
import sys

# 프로젝트 루트 디렉토리를 sys.path에 추가
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from logger.data_saver import save_price_data

# --- Environment and Configuration ---
# .env 파일에서 환경 변수 로드
load_dotenv()

CONFIG_PATH = project_root / "config.yaml"
with open(CONFIG_PATH, 'r') as f:
    config = yaml.safe_load(f)

# 환경 변수에서 API 키 가져오기
API_KEY = os.getenv("ALPACA_API_KEY")
SECRET_KEY = os.getenv("ALPACA_SECRET_KEY")

# config.yaml에서 설정값 가져오기
PAPER = config['collectors']['alpaca']['paper']
ASSETS = config['assets']['tradfi']

# API 키 존재 여부 확인
if not API_KEY or not SECRET_KEY:
    raise ValueError("Alpaca API 키가 .env 파일에 설정되지 않았습니다. (ALPACA_API_KEY, ALPACA_SECRET_KEY)")

# --- API Initialization ---
api = tradeapi.REST(API_KEY, SECRET_KEY, base_url='https://paper-api.alpaca.markets' if PAPER else 'https://api.alpaca.markets', api_version='v2')

def get_tradfi_data(symbols, timeframe='1Day', start_date=None, end_date=None):
    """
    Alpaca API를 사용하여 주식/ETF 데이터를 가져옵니다.

    Args:
        symbols (list): 가져올 자산의 심볼 리스트 (e.g., ['SPY', 'AGG'])
        timeframe (str): 데이터의 시간 간격 (e.g., '1Day', '1Hour')
        start_date (str, optional): 시작 날짜 (YYYY-MM-DD). Defaults to None.
        end_date (str, optional): 종료 날짜 (YYYY-MM-DD). Defaults to None.

    Returns:
        dict: 각 심볼을 key로, 가격 데이터(DataFrame)를 value로 갖는 딕셔너리.
    """
    all_data = {}
    for symbol in symbols:
        try:
            bars = api.get_bars(symbol, timeframe, start=start_date, end=end_date).df
            bars = bars[['open', 'high', 'low', 'close', 'volume']]
            bars.index = bars.index.tz_convert('America/New_York').tz_localize(None) # 시간대 정보 제거
            all_data[symbol] = bars
            print(f"Successfully fetched {symbol} data from Alpaca.")
        except Exception as e:
            print(f"Error fetching {symbol} data from Alpaca: {e}")
    return all_data

def collect():
    """Alpaca 데이터 수집 및 저장을 위한 메인 함수"""
    print("--- Alpaca Data Collector ---")
    
    # 1. 데이터 가져오기
    # config.yaml에 정의된 TradFi 자산 목록으로 2023년 1분기 데이터 가져오기
    tradfi_data = get_tradfi_data(ASSETS, timeframe='1Hour', start_date="2025-09-01", end_date="2025-10-29")

    if tradfi_data:
        # 2. 가져온 데이터를 데이터베이스에 저장
        print("\n--- Saving data to database ---")
        save_price_data(tradfi_data)

        # 3. 저장 후 샘플 데이터 출력
        spy_data = tradfi_data.get("SPY")
        if spy_data is not None:
            print("\n--- SPY Data (last 5 rows) ---")
            print(spy_data.tail())

if __name__ == '__main__':
    collect()
