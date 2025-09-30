import pandas as pd
import sys
from pathlib import Path

# 프로젝트 루트 디렉토리를 sys.path에 추가
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from logger.data_loader import load_price_data

def generate_signals(data, short_window=20, long_window=50):
    """
    단순 이동 평균(SMA) 교차 전략에 따른 트레이딩 신호를 생성합니다.

    Args:
        data (pd.DataFrame): 'close' 컬럼을 포함하는 가격 데이터.
        short_window (int): 단기 이동 평균 기간.
        long_window (int): 장기 이동 평균 기간.

    Returns:
        pd.DataFrame: 'short_ma', 'long_ma', 'signal', 'position' 컬럼이 추가된 데이터프레임.
    """
    if 'close' not in data.columns:
        raise ValueError("Input DataFrame must contain a 'close' column.")

    signals = data.copy()
    signals['short_ma'] = signals['close'].rolling(window=short_window, min_periods=1).mean()
    signals['long_ma'] = signals['close'].rolling(window=long_window, min_periods=1).mean()

    # 신호 생성: 단기 MA가 장기 MA를 넘어설 때 매수(1), 반대일 때 매도(-1)
    signals['signal'] = 0
    signals.loc[signals['short_ma'] > signals['long_ma'], 'signal'] = 1
    signals.loc[signals['short_ma'] < signals['long_ma'], 'signal'] = -1

    # 포지션 결정: 신호의 변화가 있을 때만 포지션 변경
    signals['position'] = signals['signal'].diff()

    print(f"Generated signals for {len(signals)} data points using SMA({short_window}, {long_window}).")
    return signals

if __name__ == '__main__':
    # --- Example Usage ---
    print("--- SMA Strategy Signal Generation ---")
    
    # 1. 데이터베이스에서 SPY 데이터 로드
    spy_data_dict = load_price_data(symbols=['SPY'], start_date="2023-01-01", end_date="2023-03-31")
    
    if spy_data_dict:
        spy_data = spy_data_dict.get('SPY')
        
        # 2. SMA 전략 신호 생성 (20일, 50일)
        spy_signals = generate_signals(spy_data, short_window=20, long_window=50)
        
        # 3. 신호가 생성된 데이터 확인
        print("\n--- SPY Data with SMA Signals (last 10 rows) ---")
        print(spy_signals[['close', 'short_ma', 'long_ma', 'signal', 'position']].tail(10))

        # 4. 실제 매매가 일어나는 시점(포지션 변경)만 필터링하여 확인
        trade_points = spy_signals[spy_signals['position'] != 0]
        print("\n--- Trade Points (Buy/Sell signals) ---")
        print(trade_points[['close', 'short_ma', 'long_ma', 'signal', 'position']])
