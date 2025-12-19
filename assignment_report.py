"""
과제 요구사항 통합 실행 스크립트

과제 요구사항:
1. 매수/매도 하는 대상 (코인, 주식 등)
2. 트레이딩 알고리즘의 종류 (추세추종, 평균회귀, 차익거래, 아비트라지, 기본적분석 등)
3. API 등 자동매매 활용 여부
4. 매매일지 (진입 횟수, 승률, 손익비, 누적수익률 등)
"""

import yaml
from pathlib import Path
import sys
from datetime import datetime, timedelta

# 프로젝트 루트 디렉토리를 sys.path에 추가
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from logger.trade_logger import init_trade_log_table, get_trade_statistics, print_trade_statistics, get_all_trades
from backtest_advanced import run_backtest, print_results, compare_strategies
from collector import yf
from logger.data_loader import load_price_data

def print_header():
    """과제 리포트 헤더 출력"""
    print("\n" + "="*80)
    print(" "*20 + "TRADING SYSTEM ASSIGNMENT REPORT")
    print("="*80)
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80 + "\n")

def section_1_trading_targets():
    """섹션 1: 매수/매도 대상"""
    print("\n" + "="*80)
    print("1. 매수/매도 대상 (TRADING TARGETS)")
    print("="*80)

    with open(project_root / "config.yaml", 'r') as f:
        config = yaml.safe_load(f)

    print("\n[주식 (Stocks)]")
    tradfi = config['assets']['tradfi']
    for i, symbol in enumerate(tradfi, 1):
        print(f"  {i}. {symbol}")

    print("\n[암호화폐 (Cryptocurrency)]")
    crypto = config['assets']['crypto']
    for i, symbol in enumerate(crypto, 1):
        print(f"  {i}. {symbol}")

    print("\n[거시경제 지표 (Macro Indicators)]")
    macro = config['assets']['macro']
    for i, symbol in enumerate(macro, 1):
        print(f"  {i}. {symbol}")

    print("\n" + "-"*80)
    print(f"총 거래 대상: {len(tradfi) + len(crypto)} 자산")
    print("="*80 + "\n")

def section_2_trading_algorithms():
    """섹션 2: 트레이딩 알고리즘의 종류"""
    print("\n" + "="*80)
    print("2. 트레이딩 알고리즘의 종류 (TRADING ALGORITHMS)")
    print("="*80)

    algorithms = [
        {
            "name": "SMA (Simple Moving Average)",
            "type": "추세추종 (Trend Following)",
            "description": "단기 이동평균과 장기 이동평균의 교차를 이용한 추세 추종 전략",
            "file": "strategy/sma.py",
            "parameters": "short_window=20, long_window=50"
        },
        {
            "name": "Mean Reversion (Bollinger Bands)",
            "type": "평균회귀 (Mean Reversion)",
            "description": "볼린저 밴드를 이용한 과매수/과매도 구간에서의 역방향 진입 전략",
            "file": "strategy/meanrev.py",
            "parameters": "window=20, num_std=2.0"
        }
    ]

    for i, algo in enumerate(algorithms, 1):
        print(f"\n[알고리즘 {i}]")
        print(f"  이름:         {algo['name']}")
        print(f"  분류:         {algo['type']}")
        print(f"  설명:         {algo['description']}")
        print(f"  구현 파일:    {algo['file']}")
        print(f"  파라미터:     {algo['parameters']}")

    print("\n" + "-"*80)
    print("추가 구현 가능 알고리즘:")
    print("  - 통계적 차익거래 (Statistical Arbitrage): 상관관계 기반 페어 트레이딩")
    print("  - 변동성 브레이크아웃 (Volatility Breakout): ATR, Donchian Channel")
    print("  - 모멘텀 전략 (Momentum): MACD, RSI, ADX 활용")
    print("="*80 + "\n")

def section_3_api_automation():
    """섹션 3: API 등 자동매매 활용 여부"""
    print("\n" + "="*80)
    print("3. API 등 자동매매 활용 여부 (API & AUTOMATION)")
    print("="*80)

    print("\n[데이터 수집 API]")
    apis = [
        {
            "name": "Alpaca Markets API",
            "purpose": "미국 주식 데이터 수집 및 Paper Trading",
            "file": "collector/alpaca.py, executor/paper_alpaca.py",
            "status": "활성화"
        },
        {
            "name": "yfinance",
            "purpose": "주식 및 암호화폐 가격 데이터 수집",
            "file": "collector/yf.py",
            "status": "활성화"
        },
        {
            "name": "Bybit API",
            "purpose": "암호화폐 데이터 수집 및 거래",
            "file": "collector/bybit.py, executor/paper_bybit.py",
            "status": "구현됨"
        },
        {
            "name": "FRED API",
            "purpose": "거시경제 지표 데이터 수집",
            "file": "collector/fred.py",
            "status": "구현됨"
        }
    ]

    for i, api in enumerate(apis, 1):
        print(f"\n  {i}. {api['name']}")
        print(f"     용도:       {api['purpose']}")
        print(f"     구현 파일:  {api['file']}")
        print(f"     상태:       {api['status']}")

    print("\n[자동화 시스템]")
    print("\n  1. 데이터 수집 자동화")
    print("     - main.py: config.yaml 설정에 따라 활성화된 수집기 실행")
    print("     - 일일 자동 실행 가능 (cron, 스케줄러)")

    print("\n  2. 트레이딩 자동화")
    print("     - daily_trader.py: 일일 주식 트레이딩")
    print("     - daily_crypto_trader.py: 일일 암호화폐 트레이딩")
    print("     - webhook_server.py: 웹훅 기반 백그라운드 실행")

    print("\n  3. Paper Trading 지원")
    print("     - Alpaca Paper Trading 계정 연동")
    print("     - Bybit Paper Trading 계정 연동")
    print("     - 실거래 전환 가능 (config.yaml에서 설정)")

    print("\n" + "="*80 + "\n")

def section_4_trading_journal_demo(symbol='SPY', start_date='2024-01-01', end_date='2024-12-31'):
    """섹션 4: 매매일지 시연"""
    print("\n" + "="*80)
    print("4. 매매일지 (TRADING JOURNAL)")
    print("="*80)

    print(f"\n백테스팅 기간: {start_date} ~ {end_date}")
    print(f"대상 자산: {symbol}")

    # 테이블 초기화
    init_trade_log_table()

    # 데이터 수집
    print(f"\n[Step 1] 데이터 수집 중...")
    try:
        # yfinance로 최신 데이터 수집
        yf.get_yfinance_data([symbol], interval='1d', start=start_date, end=end_date)
        print(f"✓ {symbol} 데이터 수집 완료")
    except Exception as e:
        print(f"⚠ 데이터 수집 중 오류 발생: {e}")
        print("  기존 DB 데이터로 진행합니다.")

    # 전략 1: SMA 백테스팅
    print(f"\n[Step 2] SMA 전략 백테스팅...")
    sma_results = run_backtest(
        symbol=symbol,
        strategy_name='sma',
        start_date=start_date,
        end_date=end_date,
        initial_capital=100000,
        save_trades=True,  # DB에 거래 저장
        short_window=20,
        long_window=50
    )

    if sma_results:
        print_results(sma_results)
    else:
        print("⚠ SMA 백테스팅 실패")

    # 전략 2: Mean Reversion 백테스팅
    print(f"\n[Step 3] Mean Reversion 전략 백테스팅...")
    meanrev_results = run_backtest(
        symbol=symbol,
        strategy_name='meanrev',
        start_date=start_date,
        end_date=end_date,
        initial_capital=100000,
        save_trades=True,
        window=20,
        entry_threshold=2.0
    )

    if meanrev_results:
        print_results(meanrev_results)
    else:
        print("⚠ Mean Reversion 백테스팅 실패")

    # 매매일지 통계 출력
    print(f"\n[Step 4] 통합 매매일지 통계...")

    print("\n--- SMA 전략 통계 ---")
    sma_stats = get_trade_statistics(symbol=symbol, strategy='sma')
    print_trade_statistics(sma_stats)

    print("\n--- Mean Reversion 전략 통계 ---")
    meanrev_stats = get_trade_statistics(symbol=symbol, strategy='meanrev')
    print_trade_statistics(meanrev_stats)

    # 최근 거래 내역
    print("\n[Step 5] 최근 거래 내역 (SMA 전략)")
    sma_trades = get_all_trades(symbol=symbol, strategy='sma', limit=10)
    if not sma_trades.empty:
        print(sma_trades[['symbol', 'entry_time', 'exit_time', 'entry_price', 'exit_price', 'pnl', 'pnl_pct']].to_string(index=False))
    else:
        print("거래 내역이 없습니다.")

    print("\n" + "="*80 + "\n")

def section_5_strategy_comparison(symbol='SPY', start_date='2024-01-01', end_date='2024-12-31'):
    """섹션 5: 전략 비교"""
    print("\n" + "="*80)
    print("5. 전략 성과 비교 (STRATEGY COMPARISON)")
    print("="*80)

    compare_strategies(
        symbol=symbol,
        strategies=[
            {'name': 'sma', 'params': {'short_window': 20, 'long_window': 50}},
            {'name': 'sma', 'params': {'short_window': 10, 'long_window': 30}},
            {'name': 'meanrev', 'params': {'window': 20, 'entry_threshold': 2.0}},
            {'name': 'meanrev', 'params': {'window': 15, 'entry_threshold': 1.5}},
        ],
        start_date=start_date,
        end_date=end_date,
        initial_capital=100000
    )

def print_footer():
    """과제 리포트 푸터 출력"""
    print("\n" + "="*80)
    print("                          REPORT END")
    print("="*80)
    print("\n주요 파일:")
    print("  - logger/trade_logger.py        : 매매일지 시스템")
    print("  - strategy/sma.py               : SMA 추세추종 전략")
    print("  - strategy/meanrev.py           : Bollinger Bands 평균회귀 전략")
    print("  - backtest_advanced.py          : 고급 백테스팅 시스템")
    print("  - assignment_report.py          : 과제 요구사항 통합 리포트")
    print("  - executor/paper_alpaca.py      : Alpaca Paper Trading 실행기")
    print("  - collector/                    : 데이터 수집기 모음")
    print("\n" + "="*80 + "\n")

def main():
    """메인 실행 함수"""
    # 리포트 헤더
    print_header()

    # 1. 매수/매도 대상
    section_1_trading_targets()

    # 2. 트레이딩 알고리즘의 종류
    section_2_trading_algorithms()

    # 3. API 등 자동매매 활용 여부
    section_3_api_automation()

    # 4. 매매일지 (백테스팅 시연)
    section_4_trading_journal_demo(
        symbol='SPY',
        start_date='2024-01-01',
        end_date='2024-12-31'
    )

    # 5. 전략 비교
    section_5_strategy_comparison(
        symbol='SPY',
        start_date='2024-01-01',
        end_date='2024-12-31'
    )

    # 리포트 푸터
    print_footer()

if __name__ == '__main__':
    main()
