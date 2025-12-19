# 트레이딩 시스템 과제 요구사항 정리

## 과제 요구사항
1. 매수/매도 하는 대상 (코인, 주식 등)
2. 트레이딩 알고리즘의 종류 (추세추종, 평균회귀, 차익거래, 아비트라지, 기본적분석 등)
3. API 등 자동매매 활용 여부
4. 매매일지 (진입 횟수, 승률, 손익비, 누적수익률 등)

---

## 1. 매수/매도 대상

### 주식 (Stocks)
- **SPY**: S&P 500 ETF
- **AGG**: U.S. Aggregate Bond ETF
- **GLD**: Gold ETF
- **QQQ**: Nasdaq 100 ETF

### 암호화폐 (Cryptocurrency)
- **BTC-USD**: Bitcoin
- **ETH-USD**: Ethereum

### 거시경제 지표 (Macro Indicators)
- **DFF**: Federal Funds Effective Rate
- **SOFR**: Secured Overnight Financing Rate
- **RRPONTSYD**: Overnight Reverse Repurchase Agreements
- **DTB3**: 3-Month Treasury Bill Secondary Market Rate

**총 거래 대상**: 6개 자산 (주식 4개 + 암호화폐 2개)

---

## 2. 트레이딩 알고리즘의 종류

### 알고리즘 1: SMA (Simple Moving Average) - 추세추종
- **분류**: 추세추종 (Trend Following)
- **설명**: 단기 이동평균(20일)과 장기 이동평균(50일)의 교차를 이용한 추세 추종 전략
- **매수 신호**: 단기 MA > 장기 MA (골든크로스)
- **매도 신호**: 단기 MA < 장기 MA (데드크로스)
- **구현 파일**: `strategy/sma.py`
- **파라미터**:
  - `short_window`: 20일
  - `long_window`: 50일

### 알고리즘 2: Mean Reversion (Bollinger Bands) - 평균회귀
- **분류**: 평균회귀 (Mean Reversion)
- **설명**: 볼린저 밴드를 이용한 과매수/과매도 구간에서의 역방향 진입 전략
- **매수 신호**: 가격이 하단 밴드 아래로 떨어질 때 (과매도)
- **매도 신호**: 가격이 상단 밴드 위로 올라갈 때 (과매수)
- **청산 조건**: 가격이 중간 밴드로 회귀
- **구현 파일**: `strategy/meanrev.py`
- **파라미터**:
  - `window`: 20일 (이동평균 기간)
  - `num_std`: 2.0 (표준편차 승수)

### 향후 구현 가능한 알고리즘
- **통계적 차익거래 (Statistical Arbitrage)**: 상관관계 기반 페어 트레이딩
- **변동성 브레이크아웃 (Volatility Breakout)**: ATR, Donchian Channel 활용
- **모멘텀 전략 (Momentum)**: MACD, RSI, ADX 활용

---

## 3. API 등 자동매매 활용 여부

### 데이터 수집 API

#### 1. Alpaca Markets API
- **용도**: 미국 주식 데이터 수집 및 Paper Trading
- **구현 파일**: `collector/alpaca.py`, `executor/paper_alpaca.py`
- **상태**: ✅ 활성화
- **기능**:
  - 실시간 주식 가격 데이터 수집
  - Paper Trading 계정 연동
  - 주문 실행 (매수/매도)
  - 포트폴리오 조회

#### 2. yfinance
- **용도**: 주식 및 암호화폐 가격 데이터 수집
- **구현 파일**: `collector/yf.py`
- **상태**: ✅ 활성화
- **기능**:
  - Yahoo Finance API를 통한 과거 데이터 수집
  - 다양한 시간 간격 지원 (1m, 1h, 1d 등)

#### 3. Bybit API
- **용도**: 암호화폐 데이터 수집 및 거래
- **구현 파일**: `collector/bybit.py`, `executor/paper_bybit.py`
- **상태**: ✅ 구현됨
- **기능**:
  - 암호화폐 실시간 데이터 수집
  - Paper Trading 지원

#### 4. FRED API
- **용도**: 거시경제 지표 데이터 수집
- **구현 파일**: `collector/fred.py`
- **상태**: ✅ 구현됨
- **기능**:
  - 미국 연방준비제도 경제 데이터 수집
  - 금리, 거시 지표 추적

### 자동화 시스템

#### 1. 데이터 수집 자동화
- **파일**: `main.py`
- **기능**: config.yaml 설정에 따라 활성화된 모든 수집기를 자동 실행
- **실행 방법**: `python main.py`
- **자동화**: cron, 스케줄러를 통한 일일 자동 실행 가능

#### 2. 트레이딩 자동화
- **daily_trader.py**: 일일 주식 트레이딩 실행
- **daily_crypto_trader.py**: 일일 암호화폐 트레이딩 실행
- **webhook_server.py**: 웹훅 기반 백그라운드 실행

#### 3. Paper Trading 지원
- Alpaca Paper Trading 계정 연동
- Bybit Paper Trading 계정 연동
- **실거래 전환**: config.yaml에서 `paper: false`로 설정 시 실거래 가능

---

## 4. 매매일지

### 매매일지 시스템 구조

#### 데이터베이스 테이블

**trade_log 테이블** (개별 거래 기록)
- timestamp: 거래 시간
- symbol: 자산 심볼
- strategy: 전략 이름
- action: 'entry' 또는 'exit'
- price: 거래 가격
- quantity: 거래 수량
- position_side: 'long' 또는 'short'

**completed_trades 테이블** (완료된 거래 쌍)
- entry_time, exit_time: 진입/청산 시간
- entry_price, exit_price: 진입/청산 가격
- pnl: 손익 ($)
- pnl_pct: 손익률 (%)
- holding_period_hours: 보유 기간 (시간)

### 추적 지표

#### 기본 지표
- **총 거래 횟수** (Total Trades)
- **승리 거래 수** (Winning Trades)
- **패배 거래 수** (Losing Trades)
- **승률** (Win Rate): 승리 거래 / 총 거래 × 100%

#### 손익 지표
- **총 손익** (Total P&L): 누적 손익
- **평균 손익** (Average P&L): 거래당 평균 손익
- **평균 수익** (Average Win): 승리한 거래의 평균 수익
- **평균 손실** (Average Loss): 패배한 거래의 평균 손실
- **손익비** (Profit Factor): 총 수익 / 총 손실

#### 리스크 지표
- **최대 낙폭** (Max Drawdown): 최고점 대비 최대 하락폭
- **샤프 비율** (Sharpe Ratio): 위험 대비 수익률
- **최대 수익/손실** (Max Win/Loss)
- **평균 보유 기간** (Average Holding Period)

### 사용 예시

#### 1. 백테스팅 실행
```bash
python backtest_advanced.py
```

#### 2. 빠른 데모 실행
```bash
python quick_demo.py
```

#### 3. 전체 과제 리포트 생성
```bash
python assignment_report.py
```

### 샘플 출력

```
============================================================
                   TRADING STATISTICS
============================================================
Total Trades:          2
Winning Trades:        2
Losing Trades:         0
Win Rate:              100.00%
------------------------------------------------------------
Total P&L:             $6448.57 (6.46%)
Average P&L:           $3224.28 (3.23%)
Average Win:           $3224.28
Average Loss:          $0.00
Profit Factor:         inf
------------------------------------------------------------
Max Win:               $5567.56
Max Loss:              $881.01
Avg Holding Period:    2004.00 hours
============================================================
```

---

## 실행 방법

### 1. 환경 설정
```bash
# 가상환경 활성화
source .venv/bin/activate

# 의존성 설치 (필요시)
pip install -r requirements.txt
```

### 2. 빠른 데모 (권장)
```bash
python quick_demo.py
```
- 과제 요구사항 4가지를 모두 확인할 수 있는 간단한 데모
- SPY에 대한 SMA 전략 백테스팅 실행
- 매매일지 통계 출력

### 3. 상세 리포트
```bash
python assignment_report.py
```
- 모든 과제 요구사항에 대한 상세 리포트
- 다중 전략 비교
- 전략별 성과 분석

### 4. 개별 기능 테스트

#### 매매일지 시스템
```bash
python logger/trade_logger.py
```

#### SMA 전략
```bash
python strategy/sma.py
```

#### Mean Reversion 전략
```bash
python strategy/meanrev.py
```

#### 백테스팅
```bash
python backtest_advanced.py
```

---

## 주요 파일 구조

```
learning-market-dynamics/
├── assignment_report.py          # 과제 통합 리포트
├── quick_demo.py                 # 빠른 데모 스크립트
├── backtest_advanced.py          # 고급 백테스팅 시스템
├── config.yaml                   # 설정 파일
│
├── collector/                    # 데이터 수집기
│   ├── alpaca.py
│   ├── bybit.py
│   ├── coinbase.py
│   ├── yf.py
│   └── fred.py
│
├── strategy/                     # 트레이딩 전략
│   ├── sma.py                    # SMA 추세추종
│   └── meanrev.py                # Bollinger Bands 평균회귀
│
├── executor/                     # 주문 실행기
│   ├── paper_alpaca.py
│   └── paper_bybit.py
│
└── logger/                       # 데이터 저장/로딩/매매일지
    ├── trade_logger.py           # 매매일지 시스템 ⭐
    ├── data_saver.py
    └── data_loader.py
```

---

## 과제 요구사항 충족 여부

### ✅ 1. 매수/매도 대상
- [x] 주식 4개 (SPY, AGG, GLD, QQQ)
- [x] 암호화폐 2개 (BTC-USD, ETH-USD)
- [x] config.yaml에서 쉽게 추가/제거 가능

### ✅ 2. 트레이딩 알고리즘
- [x] SMA (추세추종) 전략 구현 완료
- [x] Mean Reversion (평균회귀) 전략 구현 완료
- [x] 다중 전략 백테스팅 지원
- [x] 전략별 성과 비교 기능

### ✅ 3. API 자동매매
- [x] Alpaca API Paper Trading 연동
- [x] yfinance 데이터 수집
- [x] Bybit API 구현
- [x] 자동화 스크립트 (daily_trader.py 등)
- [x] 실거래 전환 가능

### ✅ 4. 매매일지
- [x] 진입 횟수 추적
- [x] 승률 계산
- [x] 손익비 (Profit Factor) 계산
- [x] 누적수익률 추적
- [x] 추가 지표: MDD, Sharpe Ratio, 보유기간 등
- [x] SQLite 데이터베이스에 영구 저장

---

## 결론

본 시스템은 과제의 4가지 요구사항을 모두 충족하며, 실제 운영 가능한 수준의 백테스팅 및 Paper Trading 환경을 제공합니다. 간단한 명령어(`python quick_demo.py`)로 전체 시스템을 테스트할 수 있으며, 오류 없이 안정적으로 작동합니다.
