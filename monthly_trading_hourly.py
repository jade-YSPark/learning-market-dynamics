"""
최근 1달 매매일지 생성 (시간봉 데이터)
더 많은 거래 기회를 위해 1시간봉 데이터 사용
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
    print(" "*15 + "최근 1달 매매일지 (시간봉 - 고빈도 거래)")
    print("="*80)
    print(f"생성 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # 최근 1달 기간 계산
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)

    start_date_str = start_date.strftime('%Y-%m-%d')
    end_date_str = end_date.strftime('%Y-%m-%d')

    print(f"백테스팅 기간: {start_date_str} ~ {end_date_str} (최근 1달)")
    print(f"데이터 간격: 1시간봉 (더 많은 거래 기회)")

    # 테이블 초기화
    print("\n데이터베이스 테이블 초기화...")
    init_trade_log_table()

    # 거래 대상 자산
    symbols = ['SPY', 'QQQ', 'BTC-USD']  # 주식 2개 + 암호화폐 1개

    for symbol in symbols:
        print(f"\n{'='*80}")
        print(f"  {symbol} 분석 시작")
        print(f"{'='*80}")

        # 데이터 수집 (1시간봉)
        print(f"\n[1단계] {symbol} 시간봉 데이터 수집 중...")
        try:
            data_dict = yf.get_yfinance_data([symbol], interval='1h', start=start_date_str, end=end_date_str)
            if data_dict:
                save_price_data(data_dict)
                data_points = len(data_dict[symbol])
                print(f"✓ {symbol} 데이터 수집 완료 ({data_points}개 시간봉)")
            else:
                print(f"⚠ {symbol} 데이터 수집 실패")
                continue
        except Exception as e:
            print(f"⚠ 데이터 수집 실패: {e}")
            continue

        # 전략 1: 초단기 SMA (시간봉용)
        print(f"\n[2단계] {symbol} - 초단기 SMA 전략 (시간봉)")
        print("  파라미터: 단기=10시간, 장기=30시간")

        sma_results = run_backtest(
            symbol=symbol,
            strategy_name='sma',
            start_date=start_date_str,
            end_date=end_date_str,
            initial_capital=100000,
            save_trades=True,
            short_window=10,
            long_window=30
        )

        if sma_results:
            print_results(sma_results)
        else:
            print(f"⚠ {symbol} SMA 백테스팅 실패")

        # 전략 2: Mean Reversion (시간봉용)
        print(f"\n[3단계] {symbol} - Mean Reversion 전략 (시간봉)")
        print("  파라미터: 윈도우=20시간, 표준편차=1.5")

        meanrev_results = run_backtest(
            symbol=symbol,
            strategy_name='meanrev',
            start_date=start_date_str,
            end_date=end_date_str,
            initial_capital=100000,
            save_trades=True,
            window=20,
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
    print("\n[전략 1] 초단기 SMA 전략 (10h/30h)")
    print("-" * 80)
    sma_stats = get_trade_statistics(strategy='sma', start_date=start_date_str, end_date=end_date_str)
    print_trade_statistics(sma_stats)

    print("\n[전략 2] Mean Reversion 전략 (20h, 1.5σ)")
    print("-" * 80)
    meanrev_stats = get_trade_statistics(strategy='meanrev', start_date=start_date_str, end_date=end_date_str)
    print_trade_statistics(meanrev_stats)

    # 자산별 상세 거래 내역
    print("\n" + "="*80)
    print("                      자산별 거래 내역 상세")
    print("="*80)

    for symbol in symbols:
        print(f"\n[{symbol}] 최근 거래 내역 (최대 30건)")
        print("-" * 80)

        trades = get_all_trades(symbol=symbol, limit=30)
        if not trades.empty:
            # 거래 시간을 보기 좋게 포맷팅
            print(f"총 {len(trades)}건의 거래 발생\n")

            # 상위 10건만 상세 출력
            display_trades = trades.head(10)
            for idx, trade in display_trades.iterrows():
                entry_time = trade['entry_time']
                exit_time = trade['exit_time']
                pnl_sign = "💰" if trade['pnl'] > 0 else "📉"

                print(f"{pnl_sign} [{trade['strategy'].upper()}] {entry_time[:16]} → {exit_time[:16]}")
                print(f"   진입: ${trade['entry_price']:.2f} | 청산: ${trade['exit_price']:.2f}")
                print(f"   손익: ${trade['pnl']:.2f} ({trade['pnl_pct']:.2f}%)")
                print()

            # 자산별 통계
            symbol_stats = get_trade_statistics(symbol=symbol, start_date=start_date_str, end_date=end_date_str)
            print(f"\n{symbol} 종합 통계:")
            print(f"  ├─ 총 거래: {symbol_stats['total_trades']}건")
            print(f"  ├─ 승률: {symbol_stats['win_rate']:.2f}%")
            print(f"  ├─ 손익비: {symbol_stats['profit_factor']:.2f}")
            print(f"  ├─ 누적 손익: ${symbol_stats['total_pnl']:.2f}")
            print(f"  └─ 평균 보유: {symbol_stats['avg_holding_hours']:.1f}시간")
        else:
            print(f"  거래 내역이 없습니다.")

    # 전체 요약
    print("\n" + "="*80)
    print("                         종합 요약")
    print("="*80)

    all_stats = get_trade_statistics(start_date=start_date_str, end_date=end_date_str)

    print(f"\n📊 백테스팅 기본 정보")
    print(f"  ├─ 기간: {start_date_str} ~ {end_date_str} (최근 1달)")
    print(f"  ├─ 데이터: 1시간봉")
    print(f"  ├─ 거래 자산: {', '.join(symbols)}")
    print(f"  └─ 사용 전략: 초단기 SMA (10h/30h), Mean Reversion (20h, 1.5σ)")

    print(f"\n💼 거래 성과")
    print(f"  ├─ 총 거래 횟수: {all_stats['total_trades']}건")
    print(f"  ├─ 승리 거래: {all_stats['winning_trades']}건 ({all_stats['win_rate']:.1f}%)")
    print(f"  ├─ 패배 거래: {all_stats['losing_trades']}건")
    print(f"  └─ 손익비 (Profit Factor): {all_stats['profit_factor']:.2f}")

    print(f"\n💰 손익 분석")
    print(f"  ├─ 누적 손익: ${all_stats['total_pnl']:.2f}")
    print(f"  ├─ 평균 손익: ${all_stats['avg_pnl']:.2f}")
    print(f"  ├─ 평균 수익: ${all_stats['avg_win']:.2f}")
    print(f"  ├─ 평균 손실: ${all_stats['avg_loss']:.2f}")
    print(f"  ├─ 최대 수익: ${all_stats['max_win']:.2f}")
    print(f"  └─ 최대 손실: ${all_stats['max_loss']:.2f}")

    print(f"\n⏱️  보유 기간")
    print(f"  └─ 평균 보유 기간: {all_stats['avg_holding_hours']:.1f}시간 ({all_stats['avg_holding_hours']/24:.1f}일)")

    # 전략별 비교
    print(f"\n📈 전략별 비교")
    print(f"  SMA 전략:")
    print(f"    ├─ 거래 횟수: {sma_stats['total_trades']}건")
    print(f"    ├─ 승률: {sma_stats['win_rate']:.1f}%")
    print(f"    └─ 누적 손익: ${sma_stats['total_pnl']:.2f}")

    print(f"  Mean Reversion 전략:")
    print(f"    ├─ 거래 횟수: {meanrev_stats['total_trades']}건")
    print(f"    ├─ 승률: {meanrev_stats['win_rate']:.1f}%")
    print(f"    └─ 누적 손익: ${meanrev_stats['total_pnl']:.2f}")

    print("\n" + "="*80)
    print("✅ 매매일지 생성 완료!")
    print("="*80 + "\n")

if __name__ == '__main__':
    main()
