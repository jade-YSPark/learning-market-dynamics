"""
고급 백테스팅 시스템
- 매매일지 통합
- 승률, 손익비, MDD, Sharpe Ratio 등 상세 지표 계산
- 다중 전략 지원
"""

import pandas as pd
import numpy as np
import yaml
from pathlib import Path
import sys

# 프로젝트 루트 디렉토리를 sys.path에 추가
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from logger.data_loader import load_price_data
from logger.trade_logger import init_trade_log_table, complete_trade, get_trade_statistics, print_trade_statistics
from strategy import sma, meanrev

def calculate_max_drawdown(equity_curve):
    """최대 낙폭(MDD)을 계산합니다."""
    cumulative_max = equity_curve.cummax()
    drawdown = (equity_curve - cumulative_max) / cumulative_max
    max_drawdown = drawdown.min() * 100
    return max_drawdown

def calculate_sharpe_ratio(returns, risk_free_rate=0.02):
    """
    샤프 비율을 계산합니다.

    Args:
        returns (pd.Series): 일별 수익률
        risk_free_rate (float): 연간 무위험 이자율 (기본값: 2%)

    Returns:
        float: 샤프 비율
    """
    if len(returns) == 0 or returns.std() == 0:
        return 0

    # 연율화된 수익률과 변동성
    annual_return = returns.mean() * 252
    annual_volatility = returns.std() * np.sqrt(252)

    sharpe = (annual_return - risk_free_rate) / annual_volatility
    return sharpe

def run_backtest(symbol, strategy_name, start_date, end_date, initial_capital=100000,
                 save_trades=False, **strategy_params):
    """
    고급 백테스팅을 수행합니다.

    Args:
        symbol (str): 백테스팅할 자산의 심볼.
        strategy_name (str): 전략 이름 ('sma' 또는 'meanrev')
        start_date (str): 시작 날짜 (YYYY-MM-DD).
        end_date (str): 종료 날짜 (YYYY-MM-DD).
        initial_capital (float): 초기 자본금.
        save_trades (bool): 거래 내역을 DB에 저장할지 여부
        **strategy_params: 전략별 파라미터

    Returns:
        dict: 백테스팅 결과.
    """
    # 1. Load strategy configuration
    with open(project_root / "config.yaml", 'r') as f:
        config = yaml.safe_load(f)

    # 2. Load data
    data_dict = load_price_data(symbols=[symbol], start_date=start_date, end_date=end_date)
    if not data_dict or symbol not in data_dict:
        print(f"백테스팅을 위한 데이터를 불러오지 못했습니다: {symbol}")
        return None

    data = data_dict[symbol]

    # 3. Generate signals based on strategy
    if strategy_name == 'sma':
        short_window = strategy_params.get('short_window', config['strategies']['sma']['short_window'])
        long_window = strategy_params.get('long_window', config['strategies']['sma']['long_window'])
        signals = sma.generate_signals(data, short_window, long_window)
    elif strategy_name == 'meanrev':
        window = strategy_params.get('window', config['strategies']['mean_reversion']['window'])
        entry_threshold = strategy_params.get('entry_threshold', config['strategies']['mean_reversion']['entry_threshold'])
        signals = meanrev.generate_signals(data, window, entry_threshold)
    else:
        print(f"Unknown strategy: {strategy_name}")
        return None

    # 4. Simulate trading
    portfolio = pd.DataFrame(index=signals.index)
    portfolio['holdings'] = 0.0
    portfolio['cash'] = initial_capital
    portfolio['total'] = initial_capital

    position = 0  # 0: no position, 1: long, -1: short
    num_trades = 0
    trades = []  # 거래 내역 저장

    entry_price = None
    entry_time = None
    entry_qty = 0

    for i in range(len(signals)):
        # 이전 포트폴리오 상태를 현재로 복사
        if i > 0:
            portfolio.loc[signals.index[i], 'holdings'] = portfolio.loc[signals.index[i-1], 'holdings']
            portfolio.loc[signals.index[i], 'cash'] = portfolio.loc[signals.index[i-1], 'cash']

        current_price = signals['close'].iloc[i]
        current_signal = signals['position'].iloc[i]

        # Buy signal (진입)
        if current_signal > 0 and position == 0:
            num_shares_to_buy = portfolio['cash'].iloc[i] // current_price
            cost = num_shares_to_buy * current_price

            if num_shares_to_buy > 0:
                portfolio.loc[signals.index[i], 'cash'] -= cost
                portfolio.loc[signals.index[i], 'holdings'] += num_shares_to_buy * current_price
                position = 1
                entry_price = current_price
                entry_time = signals.index[i].strftime('%Y-%m-%d %H:%M:%S')
                entry_qty = num_shares_to_buy
                num_trades += 1
                print(f"{signals.index[i].strftime('%Y-%m-%d')}: BUY {num_shares_to_buy} shares at ${current_price:.2f}")

        # Sell signal (청산)
        elif current_signal < 0 and position == 1:
            num_shares_to_sell = portfolio['holdings'].iloc[i-1] / signals['close'].iloc[i-1]
            proceeds = num_shares_to_sell * current_price

            portfolio.loc[signals.index[i], 'cash'] += proceeds
            portfolio.loc[signals.index[i], 'holdings'] = 0
            position = 0

            exit_price = current_price
            exit_time = signals.index[i].strftime('%Y-%m-%d %H:%M:%S')

            # 거래 기록
            trade_record = {
                'symbol': symbol,
                'strategy': strategy_name,
                'entry_time': entry_time,
                'exit_time': exit_time,
                'entry_price': entry_price,
                'exit_price': exit_price,
                'quantity': entry_qty,
                'position_side': 'long'
            }
            trades.append(trade_record)

            # DB에 저장
            if save_trades:
                complete_trade(**trade_record)

            print(f"{signals.index[i].strftime('%Y-%m-%d')}: SELL at ${current_price:.2f} | P&L: ${(exit_price - entry_price) * entry_qty:.2f}")

            num_trades += 1

        # Update total portfolio value
        portfolio.loc[signals.index[i], 'total'] = portfolio['cash'].iloc[i] + portfolio['holdings'].iloc[i]

    # 5. Calculate performance metrics
    final_value = portfolio['total'].iloc[-1]
    total_return = (final_value / initial_capital - 1) * 100

    # Buy & Hold 전략 계산
    buy_and_hold_return = (data['close'].iloc[-1] / data['close'].iloc[0] - 1) * 100

    # 일별 수익률 계산
    daily_returns = portfolio['total'].pct_change().dropna()

    # 최대 낙폭(MDD) 계산
    mdd = calculate_max_drawdown(portfolio['total'])

    # 샤프 비율 계산
    sharpe = calculate_sharpe_ratio(daily_returns)

    # 거래별 통계
    if trades:
        trades_df = pd.DataFrame(trades)
        trades_df['pnl'] = (trades_df['exit_price'] - trades_df['entry_price']) * trades_df['quantity']
        trades_df['pnl_pct'] = ((trades_df['exit_price'] / trades_df['entry_price']) - 1) * 100

        winning_trades = trades_df[trades_df['pnl'] > 0]
        losing_trades = trades_df[trades_df['pnl'] <= 0]

        win_rate = len(winning_trades) / len(trades_df) * 100 if len(trades_df) > 0 else 0
        avg_win = winning_trades['pnl'].mean() if not winning_trades.empty else 0
        avg_loss = losing_trades['pnl'].mean() if not losing_trades.empty else 0
        profit_factor = abs(winning_trades['pnl'].sum() / losing_trades['pnl'].sum()) if not losing_trades.empty and losing_trades['pnl'].sum() != 0 else float('inf')
    else:
        win_rate = 0
        avg_win = 0
        avg_loss = 0
        profit_factor = 0

    results = {
        "start_date": start_date,
        "end_date": end_date,
        "symbol": symbol,
        "strategy": strategy_name,
        "initial_capital": initial_capital,
        "final_portfolio_value": final_value,
        "total_return_pct": total_return,
        "buy_and_hold_return_pct": buy_and_hold_return,
        "num_trades": len(trades),
        "win_rate": win_rate,
        "avg_win": avg_win,
        "avg_loss": avg_loss,
        "profit_factor": profit_factor,
        "max_drawdown_pct": mdd,
        "sharpe_ratio": sharpe,
        "strategy_params": strategy_params,
        "equity_curve": portfolio['total'],
        "trades": trades
    }

    return results

def print_results(results):
    """백테스팅 결과를 보기 좋게 출력합니다."""
    if not results:
        return

    print("\n" + "="*70)
    print(f"        BACKTEST RESULTS - {results['strategy'].upper()} STRATEGY")
    print("="*70)
    print(f"Period:                {results['start_date']} to {results['end_date']}")
    print(f"Symbol:                {results['symbol']}")
    print(f"Strategy:              {results['strategy']}")
    print(f"Strategy Params:       {results['strategy_params']}")
    print("-"*70)
    print(f"Initial Capital:       ${results['initial_capital']:,.2f}")
    print(f"Final Portfolio Value: ${results['final_portfolio_value']:,.2f}")
    print(f"Total Return:          {results['total_return_pct']:.2f}%")
    print(f"Buy & Hold Return:     {results['buy_and_hold_return_pct']:.2f}%")
    print("-"*70)
    print(f"Number of Trades:      {results['num_trades']}")
    print(f"Win Rate:              {results['win_rate']:.2f}%")
    print(f"Average Win:           ${results['avg_win']:.2f}")
    print(f"Average Loss:          ${results['avg_loss']:.2f}")
    print(f"Profit Factor:         {results['profit_factor']:.2f}")
    print("-"*70)
    print(f"Max Drawdown:          {results['max_drawdown_pct']:.2f}%")
    print(f"Sharpe Ratio:          {results['sharpe_ratio']:.2f}")
    print("="*70 + "\n")

def compare_strategies(symbol, strategies, start_date, end_date, initial_capital=100000):
    """
    여러 전략을 비교합니다.

    Args:
        symbol (str): 백테스팅할 자산
        strategies (list): 전략 리스트 [{'name': 'sma', 'params': {...}}, ...]
        start_date (str): 시작 날짜
        end_date (str): 종료 날짜
        initial_capital (float): 초기 자본
    """
    results_list = []

    for strategy in strategies:
        print(f"\n{'='*70}")
        print(f"Running backtest for {strategy['name']} strategy...")
        print(f"{'='*70}")

        result = run_backtest(
            symbol=symbol,
            strategy_name=strategy['name'],
            start_date=start_date,
            end_date=end_date,
            initial_capital=initial_capital,
            save_trades=False,
            **strategy.get('params', {})
        )

        if result:
            print_results(result)
            results_list.append(result)

    # 비교 테이블 출력
    if results_list:
        print("\n" + "="*70)
        print("                    STRATEGY COMPARISON")
        print("="*70)
        comparison_df = pd.DataFrame([
            {
                'Strategy': r['strategy'],
                'Return (%)': f"{r['total_return_pct']:.2f}",
                'Win Rate (%)': f"{r['win_rate']:.2f}",
                'Profit Factor': f"{r['profit_factor']:.2f}",
                'Max DD (%)': f"{r['max_drawdown_pct']:.2f}",
                'Sharpe': f"{r['sharpe_ratio']:.2f}",
                'Trades': r['num_trades']
            }
            for r in results_list
        ])
        print(comparison_df.to_string(index=False))
        print("="*70 + "\n")

if __name__ == '__main__':
    # 테이블 초기화
    init_trade_log_table()

    print("\n" + "="*70)
    print("           ADVANCED BACKTESTING SYSTEM")
    print("="*70)

    # 예시 1: 단일 전략 백테스팅 (SMA)
    print("\n1. Testing SMA Strategy...")
    sma_results = run_backtest(
        symbol='SPY',
        strategy_name='sma',
        start_date='2024-01-01',
        end_date='2024-12-31',
        initial_capital=100000,
        save_trades=True,  # DB에 거래 저장
        short_window=20,
        long_window=50
    )
    print_results(sma_results)

    # 예시 2: 전략 비교
    print("\n2. Comparing Multiple Strategies...")
    compare_strategies(
        symbol='SPY',
        strategies=[
            {'name': 'sma', 'params': {'short_window': 20, 'long_window': 50}},
            {'name': 'sma', 'params': {'short_window': 10, 'long_window': 30}},
            {'name': 'meanrev', 'params': {'window': 20, 'entry_threshold': 2.0}},
        ],
        start_date='2024-01-01',
        end_date='2024-12-31',
        initial_capital=100000
    )

    # 예시 3: 매매일지 통계 확인
    print("\n3. Trade Log Statistics (from saved trades)...")
    stats = get_trade_statistics(symbol='SPY', strategy='sma')
    print_trade_statistics(stats)
