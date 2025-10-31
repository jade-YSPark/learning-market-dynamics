
import ccxt
import os
from dotenv import load_dotenv

# --- Environment and Configuration ---
load_dotenv()

API_KEY = os.getenv("BYBIT_API_KEY")
SECRET_KEY = os.getenv("BYBIT_API_SECRET")

if not API_KEY or not SECRET_KEY:
    raise ValueError("Bybit API 키가 .env 파일에 설정되지 않았습니다. (BYBIT_API_KEY, BYBIT_API_SECRET)")

# --- API Initialization ---
def get_bybit_exchange(testnet=True):
    """ccxt를 사용하여 Bybit 거래소 객체를 생성합니다."""
    exchange = ccxt.bybit({
        'apiKey': API_KEY,
        'secret': SECRET_KEY,
    })
    if testnet:
        exchange.set_sandbox_mode(True)
    return exchange

def execute_order(symbol, qty, side):
    """
    Bybit 테스트넷 계정으로 주문을 실행합니다.

    Args:
        symbol (str): 주문할 자산의 심볼 (e.g., "BTC/USDT")
        qty (float): 주문 수량
        side (str): 'buy' 또는 'sell'
    """
    print(f"--- Bybit Order Executor (Testnet) ---")
    exchange = get_bybit_exchange(testnet=True)

    try:
        print(f"Attempting to place a {side} order for {qty} of {symbol}")
        
        # ccxt는 시장가 주문(market order)을 지원합니다.
        order = exchange.create_market_order(symbol, side, qty)
        
        print("\n--- Order Result ---")
        print(order)
        print(f"Successfully placed a {side} order for {qty} of {symbol}.")
        return order

    except ccxt.InsufficientFunds as e:
        print(f"Error: Insufficient funds to place order. Details: {e}")
    except ccxt.NetworkError as e:
        print(f"Error: Network issue. Please check your connection. Details: {e}")
    except ccxt.ExchangeError as e:
        print(f"Error: The exchange returned an error. Details: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == '__main__':
    # --- Example Usage ---
    # BTC/USDT 0.01개 매수 주문 예시
    # 실제 테스트를 위해서는 .env 파일에 유효한 Bybit 테스트넷 API 키가 필요합니다.
    print("Executing example order...")
    example_order = execute_order('BTC/USDT', 0.01, 'buy')

    # 현재 잔고 확인 (예시)
    if example_order:
        try:
            exchange = get_bybit_exchange(testnet=True)
            balance = exchange.fetch_balance()
            print("\n--- Current Balance (Testnet) ---")
            if 'USDT' in balance['total']:
                print(f"USDT Balance: {balance['total']['USDT']}")
            if 'BTC' in balance['total']:
                print(f"BTC Balance: {balance['total']['BTC']}")
        except Exception as e:
            print(f"Could not retrieve balance: {e}")
