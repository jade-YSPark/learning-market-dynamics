import requests
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
load_dotenv()

CONFIG_PATH = project_root / "config.yaml"
with open(CONFIG_PATH, 'r') as f:
    config = yaml.safe_load(f)

# Coinbase API는 키가 없어도 공개 데이터(가격) 조회는 가능합니다.
# 하지만 인증된 요청을 위해 키를 로드합니다.
API_KEY = os.getenv("COINBASE_API_KEY")
API_SECRET = os.getenv("COINBASE_API_SECRET")

API_URL = "https://api.pro.coinbase.com"
ASSETS = config['assets']['crypto']

def get_crypto_data(product_ids, granularity=86400, start=None, end=None):
    """
    Coinbase Pro (Advanced Trade) API를 사용하여 암호화폐 데이터를 가져옵니다.

    Args:
        product_ids (list): 가져올 자산의 페어 ID 리스트 (e.g., ['BTC-USD', 'ETH-USD'])
        granularity (int): 캔들 간격 (초 단위). 기본값 86400 (1일).
        start (str, optional): 시작 시간 (ISO 8601). Defaults to None.
        end (str, optional): 종료 시간 (ISO 8601). Defaults to None.

    Returns:
        dict: 각 페어 ID를 key로, 가격 데이터(DataFrame)를 value로 갖는 딕셔너리.
    """
    all_data = {}
    for product_id in product_ids:
        params = {'granularity': granularity}
        if start:
            params['start'] = start
        if end:
            params['end'] = end
        
        try:
            # Coinbase의 공개 데이터는 API 키 없이도 접근 가능합니다.
            # 인증이 필요한 요청의 경우, 헤더에 API 키 정보를 추가해야 합니다.
            response = requests.get(f"{API_URL}/products/{product_id}/candles", params=params)
            response.raise_for_status()
            
            data = response.json()
            if not data:
                print(f"No data found for {product_id} with the given parameters.")
                continue

            df = pd.DataFrame(data, columns=['time', 'low', 'high', 'open', 'close', 'volume'])
            df['time'] = pd.to_datetime(df['time'], unit='s')
            # data_saver가 인덱스 및 컬럼명('time')을 처리하므로 여기서는 인덱스를 설정하지 않습니다.
            
            all_data[product_id] = df
            print(f"Successfully fetched {product_id} data from Coinbase.")
        except requests.exceptions.RequestException as e:
            print(f"Error fetching {product_id} data from Coinbase: {e}")
        except Exception as e:
            print(f"An unexpected error occurred for {product_id}: {e}")
            
    return all_data

def collect():
    """Coinbase 데이터 수집 및 저장을 위한 메인 함수"""
    print("--- Coinbase Data Collector ---")
    if not config['collectors']['coinbase']['enabled']:
        print("Coinbase collector is disabled in config.yaml. Skipping.")
        return

    if not API_KEY or not API_SECRET:
        print("Warning: Coinbase API keys not found in .env file. Proceeding with public access.")
        
    # 1. 데이터 가져오기 (2023년 1분기 데이터)
    crypto_data = get_crypto_data(ASSETS, granularity=3600, start="2023-01-01T00:00:00Z", end="2023-03-31T23:59:59Z")

    if crypto_data:
        # 2. 데이터베이스에 저장
        print("\n--- Saving data to database ---")
        save_price_data(crypto_data)

        # 3. 샘플 데이터 출력
        btc_data = crypto_data.get("BTC-USD")
        if btc_data is not None:
            print("\n--- BTC-USD Data (last 5 rows) ---")
            print(btc_data.tail())

if __name__ == '__main__':
    collect()
