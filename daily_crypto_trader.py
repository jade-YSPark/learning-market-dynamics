
import sys
from pathlib import Path
import yaml
from datetime import datetime, timedelta

# 프로젝트 루트 디렉토리를 sys.path에 추가
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from collector.bybit import get_bybit_exchange, get_bybit_data
from logger.data_saver import save_price_data
from logger.data_loader import load_price_data
from strategy.sma import generate_signals
from executor.paper_bybit import execute_order

def run_daily_crypto_trader():
    """Bybit을 사용하여 암호화폐에 대한 일일 SMA 전략 거래를 실행합니다."""
    print(f"\n--- Daily Crypto (Bybit) SMA Trader --- ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})")

    # 1. Load configuration
    with open(project_root / "config.yaml", 'r') as f:
        config = yaml.safe_load(f)
    
    symbol = 'BTC/USDT' # 거래할 심볼
    timeframe = '1d'     # 일일 데이터 사용
    short_window = config['strategies']['sma']['short_window']
    long_window = config['strategies']['sma']['long_window']

    # 2. Initialize Bybit exchange
    exchange = get_bybit_exchange(testnet=True)

    # 3. Collect latest data
    print(f"\n1. Collecting latest data for {symbol}...")
    # SMA 계산에 필요한 충분한 데이터 수집 (long_window + 5일 버퍼)
    since = exchange.parse8601((datetime.now() - timedelta(days=long_window + 10)).isoformat())
    data = get_bybit_data(exchange, symbol, timeframe=timeframe, since=since)

    if data.empty:
        print(f"Could not collect data for {symbol}. Exiting.")
        return

    # 4. Save and reload data to ensure consistency
    save_price_data({symbol: data})
    start_date_load = (datetime.now() - timedelta(days=long_window + 10)).strftime('%Y-%m-%d')
    data_dict = load_price_data(symbols=[symbol], start_date=start_date_load)
    
    if not data_dict or symbol not in data_dict:
        print(f"Could not load data for {symbol} after saving. Exiting.")
        return
    
    loaded_data = data_dict[symbol]

    # 5. Generate signals
    print(f"\n2. Generating trading signals for {symbol}...")
    signals = generate_signals(loaded_data, short_window, long_window)
    
    # 6. Get the latest signal
    latest_signal = signals.iloc[-1]

    print(f"\n3. Latest signal for {symbol} on {latest_signal.name.strftime('%Y-%m-%d')}:")
    print(f"   - Short MA: {latest_signal['short_ma']:.2f}")
    print(f"   - Long MA:  {latest_signal['long_ma']:.2f}")
    print(f"   - Signal:   {'BUY' if latest_signal['signal'] == 1 else 'SELL' if latest_signal['signal'] == -1 else 'HOLD'}")
    print(f"   - Position: {'BUY/SELL Action' if latest_signal['position'] != 0 else 'No Action'}")

    # 7. Execute order based on the latest signal
    # position이 2.0이면 매수, -2.0이면 매도 신호
    if latest_signal['position'] == 2.0:
        print(f"\n4. Executing BUY order for {symbol}...")
        execute_order(symbol=symbol, qty=0.01, side='buy') # 예시로 0.01 BTC 매수
    elif latest_signal['position'] == -2.0:
        print(f"\n4. Executing SELL order for {symbol}...")
        execute_order(symbol=symbol, qty=0.01, side='sell') # 예시로 0.01 BTC 매도
    else:
        print("\n4. No new trade signal. Holding position.")

    print("\n--- Daily Crypto Trader Finished ---")

if __name__ == '__main__':
    run_daily_crypto_trader()
