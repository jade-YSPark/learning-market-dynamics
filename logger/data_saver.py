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

def save_price_data(data_dict):
    """
    가격 데이터 딕셔너리를 데이터베이스에 저장합니다.
    중복된 (timestamp, symbol)이 있을 경우, 새로운 데이터로 덮어씁니다(UPSERT).

    Args:
        data_dict (dict): 각 심볼을 key로, 가격 데이터(DataFrame)를 value로 갖는 딕셔너리.
    """
    if not data_dict:
        print("No data to save.")
        return

    conn = get_db_connection()
    cursor = conn.cursor()
    
    total_rows_affected = 0
    for symbol, df in data_dict.items():
        if df.empty:
            continue

        # 데이터프레임을 데이터베이스에 삽입할 튜플 리스트로 변환
        df_copy = df.copy()
        df_copy['symbol'] = symbol
        # 인덱스(timestamp)를 컬럼으로 변환
        df_copy.reset_index(inplace=True)
        
        # 다양한 시간 컬럼 이름(Datetime, time, index 등)을 'timestamp'로 통일
        df_copy.rename(columns={
            'Datetime': 'timestamp',
            'Date': 'timestamp',
            'time': 'timestamp',
            'index': 'timestamp'
        }, inplace=True)

        # 타임스탬프를 문자열로 변환 (YYYY-MM-DD HH:MM:SS 형식)
        if pd.api.types.is_datetime64_any_dtype(df_copy['timestamp']):
            df_copy['timestamp'] = df_copy['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')

        # 필요한 컬럼만 선택
        records_to_insert = df_copy[['timestamp', 'symbol', 'open', 'high', 'low', 'close', 'volume']].to_records(index=False).tolist()

        # UPSERT 쿼리 실행
        # ON CONFLICT(timestamp, symbol) DO UPDATE SET ...
        # -> (timestamp, symbol) 조합이 이미 존재하면, 나머지 컬럼들을 업데이트합니다.
        query = """
        INSERT INTO price_data (timestamp, symbol, open, high, low, close, volume)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(timestamp, symbol) DO UPDATE SET
            open=excluded.open,
            high=excluded.high,
            low=excluded.low,
            close=excluded.close,
            volume=excluded.volume;
        """
        
        try:
            cursor.executemany(query, records_to_insert)
            conn.commit()
            print(f"Successfully saved/updated {len(records_to_insert)} records for {symbol}.")
            total_rows_affected += len(records_to_insert)
        except sqlite3.Error as e:
            print(f"Database error for {symbol}: {e}")
            conn.rollback()

    conn.close()
    print(f"\nTotal rows affected: {total_rows_affected}")

if __name__ == '__main__':
    # --- Example Usage ---
    # 이 파일을 직접 실행하면 아무 일도 일어나지 않습니다.
    # 다른 collector 스크립트에서 이 파일의 save_price_data 함수를 임포트하여 사용합니다.
    print("This is a data saving utility module.")
    print("Import and use the 'save_price_data' function from other scripts.")
