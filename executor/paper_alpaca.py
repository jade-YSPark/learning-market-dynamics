import yaml
from pathlib import Path
import alpaca_trade_api as tradeapi
import os
from dotenv import load_dotenv

# --- Environment and Configuration ---
load_dotenv()

CONFIG_PATH = Path(__file__).parent.parent / "config.yaml"
with open(CONFIG_PATH, 'r') as f:
    config = yaml.safe_load(f)

API_KEY = os.getenv("ALPACA_API_KEY")
SECRET_KEY = os.getenv("ALPACA_SECRET_KEY")
PAPER = config['alpaca']['paper']

if not API_KEY or not SECRET_KEY:
    raise ValueError("Alpaca API 키가 .env 파일에 설정되지 않았습니다. (ALPACA_API_KEY, ALPACA_SECRET_KEY)")

# --- API Initialization ---
api = tradeapi.REST(API_KEY, SECRET_KEY, base_url='https://paper-api.alpaca.markets' if PAPER else 'https://api.alpaca.markets', api_version='v2')

def execute_order(symbol, qty, side):
    """
    Alpaca 페이퍼 트레이딩 계정으로 주문을 실행합니다.

    Args:
        symbol (str): 주문할 자산의 심볼 (e.g., "SPY")
        qty (float): 주문 수량
        side (str): 'buy' 또는 'sell'
    """
    if not PAPER:
        print("WARNING: This is a live trading environment. Orders will be executed with real money.")
        confirm = input("Type 'confirm' to proceed: ")
        if confirm != 'confirm':
            print("Order cancelled.")
            return

    try:
        try:
            position = api.get_position(symbol)
            current_qty = float(position.qty)
        except tradeapi.rest.APIError as e:
            if e.status_code == 404:
                current_qty = 0
            else:
                raise e

        if side == 'buy' and current_qty <= 0:
            if current_qty < 0:
                api.close_position(symbol)
                print(f"Closed existing short position for {symbol}.")
            
            api.submit_order(
                symbol=symbol,
                qty=qty,
                side='buy',
                type='market',
                time_in_force='gtc'
            )
            print(f"Submitted market BUY order for {qty} of {symbol}.")

        elif side == 'sell' and current_qty >= 0:
            if current_qty > 0:
                api.close_position(symbol)
                print(f"Closed existing long position for {symbol}.")

            api.submit_order(
                symbol=symbol,
                qty=qty,
                side='sell',
                type='market',
                time_in_force='gtc'
            )
            print(f"Submitted market SELL order for {qty} of {symbol}.")
        
        elif side == 'close':
            if current_qty != 0:
                api.close_position(symbol)
                print(f"Submitted order to CLOSE position for {symbol}.")
            else:
                print(f"No open position to close for {symbol}.")

        else:
            print(f"Order for {symbol} skipped. Side: {side}, Current Qty: {current_qty}")

    except Exception as e:
        print(f"Error executing order for {symbol}: {e}")


if __name__ == '__main__':
    print("--- Alpaca Order Executor ---")
    print(f"Environment: {'Paper Trading' if PAPER else 'Live Trading'}")

    # 예시: SPY 10주 매수
    execute_order('SPY', 10, 'buy')

    try:
        portfolio = api.list_positions()
        if portfolio:
            print("\n--- Current Positions ---")
            for position in portfolio:
                print(f"{position.symbol}: Qty={position.qty}, Market Value={position.market_value}")
        else:
            print("\nNo open positions.")
    except Exception as e:
        print(f"Could not retrieve positions: {e}")
