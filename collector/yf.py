import yfinance as yf
import pandas as pd
import yaml
from pathlib import Path
import sys

# 프로젝트 루트 디렉토리를 sys.path에 추가
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from logger.data_saver import save_price_data

# --- Configuration ---
CONFIG_PATH = project_root / "config.yaml"
with open(CONFIG_PATH, 'r') as f:
    config = yaml.safe_load(f)

SYMBOLS = config['collectors']['yfinance']['symbols']
INTERVAL = config['collectors']['yfinance']['interval']

def get_yfinance_data(symbols, interval='1h', start=None, end=None, period='1mo'):
    """
    yfinance를 사용하여 주식, 암호화폐 등의 데이터를 가져옵니다.

    Args:
        symbols (list): 가져올 자산의 티커 리스트 (e.g., ['SPY', 'BTC-USD']).
        interval (str): 데이터 간격 (e.g., '1m', '1h', '1d').
        start (str, optional): 시작 날짜 (YYYY-MM-DD).
        end (str, optional): 종료 날짜 (YYYY-MM-DD).
        period (str): start/end가 지정되지 않은 경우 가져올 기간.

    Returns:
        dict: 각 심볼을 key로, 가격 데이터(DataFrame)를 value로 갖는 딕셔너리.
    """
    all_data = {}
    for symbol in symbols:
        try:
            print(f"Fetching {symbol} from Yahoo Finance...")
            ticker = yf.Ticker(symbol)
            
            # yfinance는 interval에 따라 다운로드 기간 제약이 있음
            if start and end:
                df = ticker.history(interval=interval, start=start, end=end)
            else:
                df = ticker.history(period=period, interval=interval)

            if df.empty:
                print(f"No data returned for {symbol}.")
                continue
            
            # 컬럼 이름 표준화 (yfinance는 대문자로 시작)
            df.rename(columns={
                'Open': 'open',
                'High': 'high',
                'Low': 'low',
                'Close': 'close',
                'Volume': 'volume'
            }, inplace=True)

            # 시간대 정보 제거
            df.index = df.index.tz_localize(None)
            
            all_data[symbol] = df[['open', 'high', 'low', 'close', 'volume']]
            print(f"Successfully fetched {len(df)} data points for {symbol}.")

        except Exception as e:
            print(f"An unexpected error occurred for {symbol}: {e}")
            
    return all_data

def collect():
    """yfinance 데이터 수집 및 저장을 위한 메인 함수"""
    print("--- Yahoo Finance Data Collector ---")
    
    # 1. 데이터 가져오기
    # config.yaml에 정의된 자산 목록으로 데이터 가져오기
    data_dict = get_yfinance_data(SYMBOLS, interval=INTERVAL, start="2025-09-01", end="2025-10-29")

    if data_dict:
        # 2. 가져온 데이터를 데이터베이스에 저장
        print("\n--- Saving data to database ---")
        save_price_data(data_dict)

        # 3. 저장 후 샘플 데이터 출력
        spy_data = data_dict.get("SPY")
        if spy_data is not None:
            print("\n--- SPY Data (last 5 rows) ---")
            print(spy_data.tail())

if __name__ == '__main__':
    collect()
