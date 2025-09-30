import requests
import yaml
import pandas as pd
from pathlib import Path
from datetime import datetime
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

# .env 파일에서 FRED API 키 가져오기 (선택 사항)
API_KEY = os.getenv("FRED_API_KEY", '') # 키가 없으면 빈 문자열로 기본값 설정
SERIES_IDS = config['assets']['macro']
API_URL = "https://api.stlouisfed.org/fred/series/observations"

def get_fred_data(series_ids, start_date=None, end_date=None):
    """
    FRED API를 사용하여 거시경제 데이터를 가져옵니다.
    데이터를 OHLCV 형식에 맞춰 변환하여 반환합니다.

    Args:
        series_ids (list): 가져올 데이터의 시리즈 ID 리스트.
        start_date (str, optional): 시작 날짜 (YYYY-MM-DD). Defaults to None.
        end_date (str, optional): 종료 날짜 (YYYY-MM-DD). Defaults to None.

    Returns:
        dict: 각 시리즈 ID를 key로, OHLCV 형식의 DataFrame을 value로 갖는 딕셔너리.
    """
    all_series_data = {}
    for series_id in series_ids:
        params = {
            'series_id': series_id,
            'api_key': API_KEY,
            'file_type': 'json',
            'observation_start': start_date if start_date else '1776-07-04',
            'observation_end': end_date if end_date else datetime.today().strftime('%Y-%m-%d'),
        }
        try:
            response = requests.get(API_URL, params=params)
            response.raise_for_status()
            data = response.json()['observations']
            
            if not data:
                print(f"No data returned for series {series_id}.")
                continue

            df = pd.DataFrame(data)
            df = df[['date', 'value']]
            df['date'] = pd.to_datetime(df['date'])
            df['value'] = pd.to_numeric(df['value'], errors='coerce')
            
            # 누락된 값을 이전 값으로 채우기
            df['value'].fillna(method='ffill', inplace=True)
            df.dropna(inplace=True) # ffill 후에도 남은 NaN 제거

            # OHLCV 형식으로 변환
            df.rename(columns={'date': 'timestamp', 'value': 'close'}, inplace=True)
            df['open'] = df['close']
            df['high'] = df['close']
            df['low'] = df['close']
            df['volume'] = 0

            all_series_data[series_id] = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
            print(f"Successfully fetched and formatted {series_id} data from FRED.")
        except requests.exceptions.RequestException as e:
            print(f"Error fetching {series_id} data from FRED: {e}")
        except Exception as e:
            print(f"An unexpected error occurred for {series_id}: {e}")

    return all_series_data

def collect():
    """FRED 데이터 수집 및 저장을 위한 메인 함수"""
    print("--- FRED Data Collector ---")
    if not API_KEY:
        print("Warning: FRED_API_KEY not found in .env file. Using public access (rate limits may apply).")

    # 1. 데이터 가져오기
    macro_data_dict = get_fred_data(SERIES_IDS, start_date="2022-01-01")

    if macro_data_dict:
        # 2. 데이터베이스에 저장
        print("\n--- Saving data to database ---")
        save_price_data(macro_data_dict)

        # 3. 샘플 데이터 출력
        dff_data = macro_data_dict.get("DFF")
        if dff_data is not None:
            print("\n--- DFF Data (last 5 rows) ---")
            print(dff_data.tail())

if __name__ == '__main__':
    collect()
