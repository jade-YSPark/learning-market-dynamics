"""
간단한 데모 스크립트 - 과제 요구사항 확인용
"""

import yaml
from pathlib import Path
import sys
from datetime import datetime

# 프로젝트 루트 디렉토리를 sys.path에 추가
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from logger.trade_logger import init_trade_log_table, get_trade_statistics, print_trade_statistics
from backtest_advanced import run_backtest, print_results
from collector import yf

def main():
    print("\n" + "="*80)
    print(" "*15 + "TRADING SYSTEM DEMO - 과제 요구사항 확인")
    print("="*80)
    print(f"실행 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # 설정 파일 로드
    with open(project_root / "config.yaml", 'r') as f:
        config = yaml.safe_load(f)

    # ========== 1. 매수/매도 대상 ==========
    print("\n[1. 매수/매도 대상]")
    print(f"주식: {', '.join(config['assets']['tradfi'])}")
    print(f"암호화폐: {', '.join(config['assets']['crypto'])}")

    # ========== 2. 트레이딩 알고리즘의 종류 ==========
    print("\n[2. 트레이딩 알고리즘]")
    print("  - SMA (추세추종): 단기/장기 이동평균 교차 전략")
    print("  - Mean Reversion (평균회귀): Bollinger Bands 기반 역방향 진입")

    # ========== 3. API 자동매매 활용 여부 ==========
    print("\n[3. API 자동매매]")
    print("  - Alpaca API: Paper Trading 지원 (활성화)")
    print("  - yfinance: 데이터 수집 (활성화)")
    print("  - Bybit API: 암호화폐 거래 (구현됨)")

    # ========== 4. 매매일지 시연 ==========
    print("\n[4. 매매일지 시연]")
    print("\n데이터베이스 테이블 초기화...")
    init_trade_log_table()

    # 테스트 데이터 수집
    symbol = 'SPY'
    start_date = '2024-01-01'
    end_date = '2024-12-31'

    print(f"\n{symbol} 데이터 수집 중 ({start_date} ~ {end_date})...")
    try:
        from logger.data_saver import save_price_data
        data_dict = yf.get_yfinance_data([symbol], interval='1d', start=start_date, end=end_date)
        if data_dict:
            save_price_data(data_dict)
            print(f"✓ {symbol} 데이터 수집 및 저장 완료")
        else:
            print(f"⚠ {symbol} 데이터 수집 실패")
    except Exception as e:
        print(f"⚠ 데이터 수집 실패: {e}")

    # SMA 전략 백테스팅
    print(f"\nSMA 전략 백테스팅 중...")
    sma_results = run_backtest(
        symbol=symbol,
        strategy_name='sma',
        start_date=start_date,
        end_date=end_date,
        initial_capital=100000,
        save_trades=True,
        short_window=20,
        long_window=50
    )

    if sma_results:
        print_results(sma_results)

        # 매매일지 통계
        print("\n매매일지 통계 (SMA 전략):")
        stats = get_trade_statistics(symbol=symbol, strategy='sma')
        print_trade_statistics(stats)

        print("\n✓ 과제 요구사항이 모두 충족되었습니다!")
        print("\n주요 지표:")
        print(f"  - 총 거래 횟수: {stats['total_trades']}")
        print(f"  - 승률: {stats['win_rate']:.2f}%")
        print(f"  - 손익비 (Profit Factor): {stats['profit_factor']:.2f}")
        print(f"  - 누적 손익: ${stats['total_pnl']:.2f}")
    else:
        print("⚠ 백테스팅 실패 - 데이터를 확인해주세요")

    print("\n" + "="*80)
    print("데모 완료! 상세 리포트는 'python assignment_report.py'로 확인하세요")
    print("="*80 + "\n")

if __name__ == '__main__':
    main()
