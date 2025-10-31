
import sys
from pathlib import Path
import yaml
from datetime import datetime, timedelta

# 프로젝트 루트 디렉토리를 sys.path에 추가
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from collector import yfinance
from logger.data_loader import load_price_data
from strategy.sma import generate_signals
from executor.paper_alpaca import execute_order

def run_daily_trader():
    """SMA 전략에 따라 일일 거래를 실행합니다."""
    print(f"\n--- Daily SMA Trader --- ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})")

    # 1. Load configuration
    with open(project_root / "config.yaml", 'r') as f:
        config = yaml.safe_load(f)
    
    symbol = 'SPY'
    short_window = config['strategies']['sma']['short_window']
    long_window = config['strategies']['sma']['long_window']

    # 2. Collect latest data
    # 전략 계산에 필요한 최소한의 기간(long_window + 5일 버퍼)만큼 데이터 수집
    print(f"\n1. Collecting latest data for {symbol}...")
    start_date_collect = (datetime.now() - timedelta(days=long_window + 5)).strftime('%Y-%m-%d')
    yfinance.get_yfinance_data([symbol], interval='1d', start=start_date_collect)

    # 3. Load data for signal generation
    print(f"\n2. Loading data for signal generation...")
    # 데이터 로딩 시에도 동일한 기간으로 로드
    data_dict = load_price_data(symbols=[symbol], start_date=start_date_collect)
    if not data_dict or symbol not in data_dict:
        print(f"Could not load data for {symbol}. Exiting.")
        return

    data = data_dict[symbol]

    # 4. Generate signals
    print(f"\n3. Generating trading signals...")
    signals = generate_signals(data, short_window, long_window)
    
    # 5. Get the latest signal
    latest_signal = signals.iloc[-1]

    print(f"\n4. Latest signal for {symbol} on {latest_signal.name.strftime('%Y-%m-%d')}:")
    print(f"   - Short MA: {latest_signal['short_ma']:.2f}")
    print(f"   - Long MA:  {latest_signal['long_ma']:.2f}")
    print(f"   - Signal:   {'BUY' if latest_signal['signal'] == 1 else 'SELL' if latest_signal['signal'] == -1 else 'HOLD'}")
    print(f"   - Position: {'BUY/SELL Action' if latest_signal['position'] != 0 else 'No Action'}")

    # 6. Execute order based on the latest signal
    # position이 2.0이면 매수, -2.0이면 매도 신호
    if latest_signal['position'] == 2.0:
        print(f"\n5. Executing BUY order for {symbol}...")
        execute_order(symbol=symbol, qty=10, side='buy') # 예시로 10주 매수
    elif latest_signal['position'] == -2.0:
        print(f"\n5. Executing SELL order for {symbol}...")
        execute_order(symbol=symbol, qty=10, side='sell') # 예시로 10주 매도
    else:
        print("\n5. No new trade signal. Holding position.")

    print("\n--- Daily SMA Trader Finished ---")

if __name__ == '__main__':
    run_daily_trader()
