import sqlite3
import pandas as pd
import yaml
from pathlib import Path

# --- Configuration ---
CONFIG_PATH = Path(__file__).parent.parent / "config.yaml"
with open(CONFIG_PATH, 'r') as f:
    config = yaml.safe_load(f)

DB_PATH = config['database']['path'].replace('sqlite:///', '')

def get_db_connection():
    """SQLite 데이터베이스 연결을 생성하고 반환합니다."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def load_price_data(symbols, start_date=None, end_date=None):
    """
    데이터베이스에서 특정 기간 동안의 가격 데이터를 불러옵니다.

    Args:
        symbols (list): 불러올 자산의 심볼 리스트.
        start_date (str, optional): 조회 시작 날짜 (YYYY-MM-DD).
        end_date (str, optional): 조회 종료 날짜 (YYYY-MM-DD).

    Returns:
        dict: 각 심볼을 key로, 가격 데이터(DataFrame)를 value로 갖는 딕셔너리.
    """
    if not symbols:
        print("No symbols provided to load.")
        return {}

    conn = get_db_connection()
    
    query = "SELECT * FROM price_data WHERE symbol = ?"
    params = []

    if start_date:
        query += " AND timestamp >= ?"
        params.append(start_date)
    if end_date:
        if len(end_date) == 10: # YYYY-MM-DD
            end_date += ' 23:59:59'
        query += " AND timestamp <= ?"
        params.append(end_date)
    
    query += " ORDER BY timestamp ASC"

    all_data = {}
    for symbol in symbols:
        try:
            # 심볼을 포함한 전체 파라미터 리스트 생성
            full_params = [symbol] + params
            df = pd.read_sql_query(query, conn, params=full_params)
            
            if df.empty:
                print(f"No data found for symbol: {symbol}")
                continue

            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df.set_index('timestamp', inplace=True)
            all_data[symbol] = df
            print(f"Successfully loaded {len(df)} records for {symbol} from database.")

        except Exception as e:
            print(f"Error loading data for {symbol}: {e}")

    conn.close()
    return all_data

if __name__ == '__main__':
    # --- Example Usage ---
    print("--- Data Loader Module ---")
    
    # config.yaml에 정의된 TradFi 자산 목록으로 데이터 불러오기
    tradfi_assets = config.get('assets', {}).get('tradfi', [])
    if tradfi_assets:
        print(f"\nLoading data for TradFi assets: {tradfi_assets}")
        loaded_data = load_price_data(symbols=tradfi_assets, start_date="2023-03-01", end_date="2023-03-10")
        
        if loaded_data:
            spy_data = loaded_data.get("SPY")
            if spy_data is not None:
                print("\n--- SPY Data Sample ---")
                print(spy_data.head())
                print(spy_data.tail())
    else:
        print("No TradFi assets defined in config.yaml to load.")
