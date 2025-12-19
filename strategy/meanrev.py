"""
평균회귀 전략 (Mean Reversion Strategy)
Bollinger Bands를 사용하여 과매수/과매도 구간에서 역방향 진입
"""

import pandas as pd
import sys
from pathlib import Path

# 프로젝트 루트 디렉토리를 sys.path에 추가
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from logger.data_loader import load_price_data

def generate_signals(data, window=20, num_std=2.0):
    """
    Bollinger Bands 기반 평균회귀 전략 신호를 생성합니다.

    Args:
        data (pd.DataFrame): 'close' 컬럼을 포함하는 가격 데이터.
        window (int): 이동 평균 및 표준편차 계산 기간 (기본값: 20)
        num_std (float): 표준편차 승수 (기본값: 2.0)

    Returns:
        pd.DataFrame: 'bb_middle', 'bb_upper', 'bb_lower', 'signal', 'position' 컬럼이 추가된 데이터프레임.

    전략 로직:
        - 가격이 하단 밴드(bb_lower) 아래로 떨어지면 매수 신호 (과매도 -> 반등 기대)
        - 가격이 상단 밴드(bb_upper) 위로 올라가면 매도 신호 (과매수 -> 하락 기대)
        - 가격이 중간 밴드(bb_middle)로 회귀하면 청산
    """
    if 'close' not in data.columns:
        raise ValueError("Input DataFrame must contain a 'close' column.")

    signals = data.copy()

    # Bollinger Bands 계산
    signals['bb_middle'] = signals['close'].rolling(window=window, min_periods=1).mean()
    rolling_std = signals['close'].rolling(window=window, min_periods=1).std()
    signals['bb_upper'] = signals['bb_middle'] + (rolling_std * num_std)
    signals['bb_lower'] = signals['bb_middle'] - (rolling_std * num_std)

    # 신호 생성
    signals['signal'] = 0

    # 매수 신호: 가격이 하단 밴드 아래
    signals.loc[signals['close'] < signals['bb_lower'], 'signal'] = 1

    # 매도 신호: 가격이 상단 밴드 위
    signals.loc[signals['close'] > signals['bb_upper'], 'signal'] = -1

    # 중립 (청산) 신호: 가격이 중간 밴드 근처
    # 중간 밴드 ± 0.5 표준편차 이내면 청산
    signals.loc[
        (signals['close'] >= signals['bb_middle'] - (rolling_std * 0.5)) &
        (signals['close'] <= signals['bb_middle'] + (rolling_std * 0.5)),
        'signal'
    ] = 0

    # 포지션 변화 감지
    signals['position'] = signals['signal'].diff()

    print(f"Generated mean reversion signals for {len(signals)} data points using BB({window}, {num_std}).")
    return signals

if __name__ == '__main__':
    # --- Example Usage ---
    print("--- Mean Reversion Strategy Signal Generation ---")

    # 1. 데이터베이스에서 SPY 데이터 로드
    spy_data_dict = load_price_data(symbols=['SPY'], start_date="2024-01-01", end_date="2024-12-31")

    if spy_data_dict:
        spy_data = spy_data_dict.get('SPY')

        # 2. 평균회귀 전략 신호 생성
        spy_signals = generate_signals(spy_data, window=20, num_std=2.0)

        # 3. 신호가 생성된 데이터 확인
        print("\n--- SPY Data with Mean Reversion Signals (last 10 rows) ---")
        print(spy_signals[['close', 'bb_middle', 'bb_upper', 'bb_lower', 'signal', 'position']].tail(10))

        # 4. 실제 매매가 일어나는 시점(포지션 변경)만 필터링하여 확인
        trade_points = spy_signals[spy_signals['position'] != 0]
        print("\n--- Trade Points (Entry/Exit signals) ---")
        if not trade_points.empty:
            print(trade_points[['close', 'bb_middle', 'bb_upper', 'bb_lower', 'signal', 'position']])
        else:
            print("No trade signals generated in this period.")
