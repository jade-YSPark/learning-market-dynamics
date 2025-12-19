"""
매매 일지 시스템
거래 내역을 기록하고 성과 지표를 계산합니다.
"""

import sqlite3
import pandas as pd
from pathlib import Path
from datetime import datetime
import yaml

# --- Configuration ---
CONFIG_PATH = Path(__file__).parent.parent / "config.yaml"
with open(CONFIG_PATH, 'r') as f:
    config = yaml.safe_load(f)

DB_PATH = config['database']['path'].replace('sqlite:///', '')

def init_trade_log_table():
    """매매 일지 테이블을 초기화합니다."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 거래 로그 테이블 생성
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS trade_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        symbol TEXT NOT NULL,
        strategy TEXT NOT NULL,
        action TEXT NOT NULL,
        price REAL NOT NULL,
        quantity REAL NOT NULL,
        position_side TEXT,
        trade_id INTEGER,
        notes TEXT
    )
    """)

    # 완료된 거래 (진입-청산 쌍) 테이블
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS completed_trades (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        symbol TEXT NOT NULL,
        strategy TEXT NOT NULL,
        entry_time TEXT NOT NULL,
        exit_time TEXT NOT NULL,
        entry_price REAL NOT NULL,
        exit_price REAL NOT NULL,
        quantity REAL NOT NULL,
        position_side TEXT NOT NULL,
        pnl REAL NOT NULL,
        pnl_pct REAL NOT NULL,
        holding_period_hours REAL,
        notes TEXT
    )
    """)

    conn.commit()
    conn.close()
    print("Trade log tables initialized.")

def log_trade(symbol, strategy, action, price, quantity, position_side='long', trade_id=None, notes=''):
    """
    거래를 기록합니다.

    Args:
        symbol (str): 거래 심볼 (예: 'SPY', 'BTC-USD')
        strategy (str): 전략 이름 (예: 'sma', 'meanrev')
        action (str): 'entry' 또는 'exit'
        price (float): 거래 가격
        quantity (float): 거래 수량
        position_side (str): 'long' 또는 'short'
        trade_id (int): 거래 ID (진입과 청산을 매칭하기 위해 사용)
        notes (str): 추가 메모
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    cursor.execute("""
    INSERT INTO trade_log (timestamp, symbol, strategy, action, price, quantity, position_side, trade_id, notes)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (timestamp, symbol, strategy, action, price, quantity, position_side, trade_id, notes))

    conn.commit()
    conn.close()

    print(f"[{timestamp}] {action.upper()} {symbol} @ {price:.2f} (qty: {quantity}, strategy: {strategy})")

def complete_trade(symbol, strategy, entry_time, exit_time, entry_price, exit_price,
                   quantity, position_side='long', notes=''):
    """
    완료된 거래를 기록하고 손익을 계산합니다.

    Args:
        symbol (str): 거래 심볼
        strategy (str): 전략 이름
        entry_time (str): 진입 시간
        exit_time (str): 청산 시간
        entry_price (float): 진입 가격
        exit_price (float): 청산 가격
        quantity (float): 거래 수량
        position_side (str): 'long' 또는 'short'
        notes (str): 추가 메모
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 손익 계산
    if position_side == 'long':
        pnl = (exit_price - entry_price) * quantity
        pnl_pct = ((exit_price / entry_price) - 1) * 100
    else:  # short
        pnl = (entry_price - exit_price) * quantity
        pnl_pct = ((entry_price / exit_price) - 1) * 100

    # 보유 기간 계산 (시간 단위)
    try:
        entry_dt = datetime.strptime(entry_time, '%Y-%m-%d %H:%M:%S')
        exit_dt = datetime.strptime(exit_time, '%Y-%m-%d %H:%M:%S')
        holding_period = (exit_dt - entry_dt).total_seconds() / 3600
    except:
        holding_period = None

    cursor.execute("""
    INSERT INTO completed_trades (symbol, strategy, entry_time, exit_time, entry_price, exit_price,
                                   quantity, position_side, pnl, pnl_pct, holding_period_hours, notes)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (symbol, strategy, entry_time, exit_time, entry_price, exit_price, quantity,
          position_side, pnl, pnl_pct, holding_period, notes))

    conn.commit()
    conn.close()

    print(f"Trade completed: {symbol} | PnL: ${pnl:.2f} ({pnl_pct:.2f}%)")

def get_trade_statistics(symbol=None, strategy=None, start_date=None, end_date=None):
    """
    매매 통계를 계산합니다.

    Args:
        symbol (str): 특정 심볼로 필터링 (None이면 전체)
        strategy (str): 특정 전략으로 필터링 (None이면 전체)
        start_date (str): 시작 날짜 (YYYY-MM-DD)
        end_date (str): 종료 날짜 (YYYY-MM-DD)

    Returns:
        dict: 통계 결과
    """
    conn = sqlite3.connect(DB_PATH)

    query = "SELECT * FROM completed_trades WHERE 1=1"
    params = []

    if symbol:
        query += " AND symbol = ?"
        params.append(symbol)
    if strategy:
        query += " AND strategy = ?"
        params.append(strategy)
    if start_date:
        query += " AND entry_time >= ?"
        params.append(start_date)
    if end_date:
        query += " AND exit_time <= ?"
        params.append(end_date)

    df = pd.read_sql_query(query, conn, params=params)
    conn.close()

    if df.empty:
        return {
            "total_trades": 0,
            "winning_trades": 0,
            "losing_trades": 0,
            "win_rate": 0,
            "total_pnl": 0,
            "avg_pnl": 0,
            "avg_win": 0,
            "avg_loss": 0,
            "profit_factor": 0,
            "max_win": 0,
            "max_loss": 0,
            "avg_holding_hours": 0
        }

    winning_trades = df[df['pnl'] > 0]
    losing_trades = df[df['pnl'] <= 0]

    total_wins = winning_trades['pnl'].sum() if not winning_trades.empty else 0
    total_losses = abs(losing_trades['pnl'].sum()) if not losing_trades.empty else 0

    stats = {
        "total_trades": len(df),
        "winning_trades": len(winning_trades),
        "losing_trades": len(losing_trades),
        "win_rate": len(winning_trades) / len(df) * 100 if len(df) > 0 else 0,
        "total_pnl": df['pnl'].sum(),
        "total_pnl_pct": df['pnl_pct'].sum(),
        "avg_pnl": df['pnl'].mean(),
        "avg_pnl_pct": df['pnl_pct'].mean(),
        "avg_win": winning_trades['pnl'].mean() if not winning_trades.empty else 0,
        "avg_loss": losing_trades['pnl'].mean() if not losing_trades.empty else 0,
        "profit_factor": total_wins / total_losses if total_losses > 0 else float('inf'),
        "max_win": df['pnl'].max(),
        "max_loss": df['pnl'].min(),
        "avg_holding_hours": df['holding_period_hours'].mean() if 'holding_period_hours' in df else 0
    }

    return stats

def print_trade_statistics(stats):
    """매매 통계를 보기 좋게 출력합니다."""
    print("\n" + "="*60)
    print("                   TRADING STATISTICS")
    print("="*60)
    print(f"Total Trades:          {stats['total_trades']}")
    print(f"Winning Trades:        {stats['winning_trades']}")
    print(f"Losing Trades:         {stats['losing_trades']}")
    print(f"Win Rate:              {stats['win_rate']:.2f}%")
    print("-"*60)
    pnl_pct = stats.get('total_pnl_pct', 0)
    avg_pnl_pct = stats.get('avg_pnl_pct', 0)
    print(f"Total P&L:             ${stats['total_pnl']:.2f} ({pnl_pct:.2f}%)")
    print(f"Average P&L:           ${stats['avg_pnl']:.2f} ({avg_pnl_pct:.2f}%)")
    print(f"Average Win:           ${stats['avg_win']:.2f}")
    print(f"Average Loss:          ${stats['avg_loss']:.2f}")
    print(f"Profit Factor:         {stats['profit_factor']:.2f}")
    print("-"*60)
    print(f"Max Win:               ${stats['max_win']:.2f}")
    print(f"Max Loss:              ${stats['max_loss']:.2f}")
    print(f"Avg Holding Period:    {stats['avg_holding_hours']:.2f} hours")
    print("="*60 + "\n")

def get_all_trades(symbol=None, strategy=None, limit=50):
    """
    모든 거래 내역을 조회합니다.

    Args:
        symbol (str): 특정 심볼로 필터링
        strategy (str): 특정 전략으로 필터링
        limit (int): 최대 조회 건수

    Returns:
        pd.DataFrame: 거래 내역
    """
    conn = sqlite3.connect(DB_PATH)

    query = "SELECT * FROM completed_trades WHERE 1=1"
    params = []

    if symbol:
        query += " AND symbol = ?"
        params.append(symbol)
    if strategy:
        query += " AND strategy = ?"
        params.append(strategy)

    query += f" ORDER BY exit_time DESC LIMIT {limit}"

    df = pd.read_sql_query(query, conn, params=params)
    conn.close()

    return df

if __name__ == '__main__':
    # 테이블 초기화
    init_trade_log_table()

    # 예시: 테스트 데이터 입력
    print("\n--- Testing Trade Logger ---")

    # 거래 1: Long SPY
    complete_trade(
        symbol='SPY',
        strategy='sma',
        entry_time='2025-01-01 10:00:00',
        exit_time='2025-01-05 15:00:00',
        entry_price=450.00,
        exit_price=455.00,
        quantity=10,
        position_side='long',
        notes='Test trade 1'
    )

    # 거래 2: Long SPY (손실)
    complete_trade(
        symbol='SPY',
        strategy='sma',
        entry_time='2025-01-10 10:00:00',
        exit_time='2025-01-12 15:00:00',
        entry_price=455.00,
        exit_price=450.00,
        quantity=10,
        position_side='long',
        notes='Test trade 2'
    )

    # 통계 조회
    stats = get_trade_statistics()
    print_trade_statistics(stats)

    # 모든 거래 조회
    print("\n--- Recent Trades ---")
    trades = get_all_trades(limit=10)
    if not trades.empty:
        print(trades[['symbol', 'strategy', 'entry_time', 'exit_time', 'entry_price', 'exit_price', 'pnl', 'pnl_pct']].to_string(index=False))
