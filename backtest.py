
import pandas as pd
import yaml
from pathlib import Path
import sys

# 프로젝트 루트 디렉토리를 sys.path에 추가
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from logger.data_loader import load_price_data
from strategy.sma import generate_signals

def run_backtest(symbol, start_date, end_date, initial_capital=100000):
    """
    지정된 기간 동안 SMA 전략의 백테스팅을 수행합니다.

    Args:
        symbol (str): 백테스팅할 자산의 심볼.
        start_date (str): 시작 날짜 (YYYY-MM-DD).
        end_date (str): 종료 날짜 (YYYY-MM-DD).
        initial_capital (float): 초기 자본금.

    Returns:
        dict: 백테스팅 결과.
    """
    # 1. Load strategy parameters from config
    with open(project_root / "config.yaml", 'r') as f:
        config = yaml.safe_load(f)
    
    short_window = config['strategies']['sma']['short_window']
    long_window = config['strategies']['sma']['long_window']

    # 2. Load data
    data_dict = load_price_data(symbols=[symbol], start_date=start_date, end_date=end_date)
    if not data_dict:
        print(f"백테스팅을 위한 데이터를 불러오지 못했습니다: {symbol}")
        return None
    
    data = data_dict[symbol]

    # 3. Generate signals
    signals = generate_signals(data, short_window, long_window)
    
    # 4. Simulate trading
    portfolio = pd.DataFrame(index=signals.index)
    portfolio['holdings'] = 0.0
    portfolio['cash'] = initial_capital
    portfolio['total'] = initial_capital

    position = 0  # 0: no position, 1: long
    num_trades = 0

    for i in range(len(signals)):
        # 이전 포트폴리오 상태를 현재로 복사
        if i > 0:
            portfolio.loc[signals.index[i], 'holdings'] = portfolio.loc[signals.index[i-1], 'holdings']
            portfolio.loc[signals.index[i], 'cash'] = portfolio.loc[signals.index[i-1], 'cash']

        # Buy signal
        if signals['position'].iloc[i] == 2.0 and position == 0:
            num_shares_to_buy = portfolio['cash'].iloc[i] // signals['close'].iloc[i]
            cost = num_shares_to_buy * signals['close'].iloc[i]
            
            portfolio.loc[signals.index[i], 'cash'] -= cost
            portfolio.loc[signals.index[i], 'holdings'] += num_shares_to_buy * signals['close'].iloc[i]
            position = 1
            num_trades += 1
            print(f"{signals.index[i].strftime('%Y-%m-%d')}: BUY {num_shares_to_buy} shares at {signals['close'].iloc[i]:.2f}")

        # Sell signal
        elif signals['position'].iloc[i] == -2.0 and position == 1:
            num_shares_to_sell = portfolio['holdings'].iloc[i-1] / signals['close'].iloc[i-1]
            proceeds = num_shares_to_sell * signals['close'].iloc[i]

            portfolio.loc[signals.index[i], 'cash'] += proceeds
            portfolio.loc[signals.index[i], 'holdings'] = 0
            position = 0
            num_trades += 1
            print(f"{signals.index[i].strftime('%Y-%m-%d')}: SELL at {signals['close'].iloc[i]:.2f}")

        # Update total portfolio value
        portfolio.loc[signals.index[i], 'total'] = portfolio['cash'].iloc[i] + portfolio['holdings'].iloc[i]

    final_value = portfolio['total'].iloc[-1]
    total_return = (final_value / initial_capital - 1) * 100
    
    # Buy & Hold 전략 계산
    buy_and_hold_return = (data['close'].iloc[-1] / data['close'].iloc[0] - 1) * 100

    results = {
        "start_date": start_date,
        "end_date": end_date,
        "symbol": symbol,
        "initial_capital": initial_capital,
        "final_portfolio_value": final_value,
        "total_return_pct": total_return,
        "buy_and_hold_return_pct": buy_and_hold_return,
        "num_trades": num_trades,
        "short_window": short_window,
        "long_window": long_window,
    }
    return results

def print_results(results):
    """백테스팅 결과를 보기 좋게 출력합니다."""
    if not results:
        return
        
    print("\n--- SMA Strategy Backtest Results ---")
    print(f"Period: {results['start_date']} to {results['end_date']}")
    print(f"Symbol: {results['symbol']}")
    print(f"SMA Windows: Short={results['short_window']}, Long={results['long_window']}")
    print("-----------------------------------------")
    print(f"Initial Capital:       ${results['initial_capital']:,.2f}")
    print(f"Final Portfolio Value: ${results['final_portfolio_value']:,.2f}")
    print(f"Total Return:          {results['total_return_pct']:.2f}%")
    print(f"Buy & Hold Return:     {results['buy_and_hold_return_pct']:.2f}%")
    print(f"Number of Trades:      {results['num_trades']}")
    print("-----------------------------------------")


if __name__ == '__main__':
    # 2025년 9월 1일부터 10월 29일까지 SPY에 대한 백테스팅 실행
    backtest_results = run_backtest(
        symbol='SPY', 
        start_date='2025-09-01', 
        end_date='2025-10-29',
        initial_capital=100000
    )
    print_results(backtest_results)
