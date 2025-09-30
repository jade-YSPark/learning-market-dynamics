import requests
import pandas as pd
from datetime import datetime
import os
from dotenv import load_dotenv
import sys
from pathlib import Path

# 프로젝트 루트 디렉토리를 sys.path에 추가
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from logger.data_saver import save_price_data

# --- Environment and Configuration ---
load_dotenv()

# The Graph API 키 (현재 이 스크립트에서는 사용하지 않음)
THE_GRAPH_AAVE_KEY = os.getenv("THE_GRAPH_AAVE_V3_ETHEREUM")

# DefiLlama API base URL
API_URL = "https://api.llama.fi"

def get_stablecoin_total_supply(chain="Ethereum"):
    """
    지정된 체인의 전체 스테이블코인 발행량 시계열 데이터를 가져옵니다.
    (현재는 시계열이 아닌 현재 스냅샷만 제공)
    """
    # 이 함수는 현재 시점의 데이터만 반환하므로, 시계열 저장은 부적합합니다.
    # 향후 시계열 데이터 API가 생기면 구현합니다.
    print("get_stablecoin_total_supply is not a time-series function and will not be saved to the database.")
    return pd.DataFrame()


def get_protocol_tvl_history(protocol_slug):
    """
    특정 프로토콜의 과거 TVL(Total Value Locked) 데이터를 가져옵니다.
    """
    try:
        response = requests.get(f"{API_URL}/protocol/{protocol_slug}")
        response.raise_for_status()
        data = response.json()

        tvl_history = data.get('tvl', [])
        if not tvl_history:
            print(f"No TVL history found for protocol: {protocol_slug}")
            return pd.DataFrame()

        df = pd.DataFrame(tvl_history)
        df['date'] = pd.to_datetime(df['date'], unit='s')
        
        # OHLCV 형식에 맞추기
        df.rename(columns={'totalLiquidityUSD': 'close', 'date': 'timestamp'}, inplace=True)
        df['open'] = df['close']
        df['high'] = df['close']
        df['low'] = df['close']
        df['volume'] = 0 # TVL 데이터에는 거래량 정보가 없음
        
        print(f"Successfully fetched and formatted TVL history for {protocol_slug}.")
        return df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]

    except requests.exceptions.RequestException as e:
        print(f"Error fetching TVL history for {protocol_slug}: {e}")
        return pd.DataFrame()


def collect():
    """DefiLlama 데이터 수집 및 저장을 위한 메인 함수"""
    print("--- DefiLlama Data Collector ---")
    
    # --- Aave TVL 데이터 가져오기 및 저장 ---
    protocol_slug = "aave"
    print(f"\n--- Fetching {protocol_slug.upper()} TVL History ---")
    aave_tvl_df = get_protocol_tvl_history(protocol_slug)
    
    if not aave_tvl_df.empty:
        # 데이터베이스 저장을 위해 딕셔너리 형태로 변환
        # 심볼 이름을 'tvl-aave' 와 같이 접두사를 붙여 구분
        data_to_save = {f"tvl-{protocol_slug}": aave_tvl_df}
        
        print("\n--- Saving data to database ---")
        save_price_data(data_to_save)
        
        print(f"\n--- {protocol_slug.upper()} TVL Data (last 5 rows) ---")
        print(aave_tvl_df.tail())

if __name__ == '__main__':
    collect()
