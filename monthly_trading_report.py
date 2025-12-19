"""
최근 1달 매매일지 생성 스크립트
더 많은 거래를 생성하기 위해 단기 전략 파라미터 사용
"""

import yaml
from pathlib import Path
import sys
from datetime import datetime, timedelta

# 프로젝트 루트 디렉토리를 sys.path에 추가
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from logger.trade_logger import init_trade_log_table, get_trade_statistics, print_trade_statistics, get_all_trades
from logger.data_saver import save_price_data
from backtest_advanced import run_backtest, print_results
from collector import yf

def main():
    print("\n" + "="*80)
    print(" "*20 + "최근 1달 매매일지")
    print("="*80)
    print(f"생성 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # 최근 1달 기간 계산
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)

    start_date_str = start_date.strftime('%Y-%m-%d')
    end_date_str = end_date.strftime('%Y-%m-%d')

    print(f"백테스팅 기간: {start_date_str} ~ {end_date_str} (최근 1달)")

    # 테이블 초기화
    print("\n데이터베이스 테이블 초기화...")
    init_trade_log_table()

    # 거래 대상 자산
    symbols = ['SPY', 'QQQ']  # 주식 2개

    for symbol in symbols:
        print(f"\n{'='*80}")
        print(f"  {symbol} 분석 시작")
        print(f"{'='*80}")

        # 데이터 수집
        print(f"\n[1단계] {symbol} 데이터 수집 중...")
        try:
            data_dict = yf.get_yfinance_data([symbol], interval='1d', start=start_date_str, end=end_date_str)
            if data_dict:
                save_price_data(data_dict)
                print(f"✓ {symbol} 데이터 수집 및 저장 완료")
            else:
                print(f"⚠ {symbol} 데이터 수집 실패")
                continue
        except Exception as e:
            print(f"⚠ 데이터 수집 실패: {e}")
            continue

        # 전략 1: 단기 SMA (더 많은 거래 발생)
        print(f"\n[2단계] {symbol} - 단기 SMA 전략 백테스팅...")
        print("  파라미터: 단기=5일, 장기=15일 (빠른 반응)")

        sma_short_results = run_backtest(
            symbol=symbol,
            strategy_name='sma',
            start_date=start_date_str,
            end_date=end_date_str,
            initial_capital=100000,
            save_trades=True,
            short_window=5,
            long_window=15
        )

        if sma_short_results:
            print_results(sma_short_results)
        else:
            print(f"⚠ {symbol} SMA 백테스팅 실패")

        # 전략 2: Mean Reversion (더 공격적인 진입)
        print(f"\n[3단계] {symbol} - Mean Reversion 전략 백테스팅...")
        print("  파라미터: 윈도우=10일, 표준편차=1.5 (더 빈번한 진입)")

        meanrev_results = run_backtest(
            symbol=symbol,
            strategy_name='meanrev',
            start_date=start_date_str,
            end_date=end_date_str,
            initial_capital=100000,
            save_trades=True,
            window=10,
            entry_threshold=1.5
        )

        if meanrev_results:
            print_results(meanrev_results)
        else:
            print(f"⚠ {symbol} Mean Reversion 백테스팅 실패")

    # 전체 통합 매매일지
    print("\n" + "="*80)
    print("                    전체 매매일지 통합 리포트")
    print("="*80)

    # 전략별 통계
    print("\n[전략 1] 단기 SMA 전략 (5일/15일)")
    print("-" * 80)
    sma_stats = get_trade_statistics(strategy='sma', start_date=start_date_str, end_date=end_date_str)
    print_trade_statistics(sma_stats)

    print("\n[전략 2] Mean Reversion 전략 (10일, 1.5σ)")
    print("-" * 80)
    meanrev_stats = get_trade_statistics(strategy='meanrev', start_date=start_date_str, end_date=end_date_str)
    print_trade_statistics(meanrev_stats)

    # 자산별 통계
    print("\n" + "="*80)
    print("                      자산별 거래 내역")
    print("="*80)

    for symbol in symbols:
        print(f"\n[{symbol}] 최근 거래 내역 (최대 20건)")
        print("-" * 80)

        trades = get_all_trades(symbol=symbol, limit=20)
        if not trades.empty:
            print(trades[['strategy', 'entry_time', 'exit_time', 'entry_price', 'exit_price', 'pnl', 'pnl_pct']].to_string(index=False))

            # 자산별 통계
            symbol_stats = get_trade_statistics(symbol=symbol, start_date=start_date_str, end_date=end_date_str)
            print(f"\n{symbol} 통계:")
            print(f"  총 거래: {symbol_stats['total_trades']}건")
            print(f"  승률: {symbol_stats['win_rate']:.2f}%")
            print(f"  누적 손익: ${symbol_stats['total_pnl']:.2f}")
        else:
            print(f"  거래 내역이 없습니다.")

    # 전체 요약
    print("\n" + "="*80)
    print("                         종합 요약")
    print("="*80)

    all_stats = get_trade_statistics(start_date=start_date_str, end_date=end_date_str)

    print(f"\n기간: {start_date_str} ~ {end_date_str} (최근 1달)")
    print(f"거래 자산: {', '.join(symbols)}")
    print(f"사용 전략: 단기 SMA (5/15), Mean Reversion (10일, 1.5σ)")
    print("\n주요 성과:")
    print(f"  ├─ 총 거래 횟수: {all_stats['total_trades']}건")
    print(f"  ├─ 승리 거래: {all_stats['winning_trades']}건")
    print(f"  ├─ 패배 거래: {all_stats['losing_trades']}건")
    print(f"  ├─ 승률: {all_stats['win_rate']:.2f}%")
    print(f"  ├─ 손익비: {all_stats['profit_factor']:.2f}")
    print(f"  ├─ 누적 손익: ${all_stats['total_pnl']:.2f}")
    print(f"  ├─ 평균 손익: ${all_stats['avg_pnl']:.2f}")
    print(f"  └─ 평균 보유 기간: {all_stats['avg_holding_hours']:.1f}시간")

    print("\n" + "="*80)
    print("매매일지 생성 완료!")
    print("="*80 + "\n")

if __name__ == '__main__':
    main()
