import yaml
from pathlib import Path

# collector 모듈들을 동적으로 임포트하기 위한 설정
from collector import alpaca, coinbase, crypto_public, defillama, fred, yf

# --- Configuration ---
CONFIG_PATH = Path(__file__).parent / "config.yaml"
with open(CONFIG_PATH, 'r') as f:
    config = yaml.safe_load(f)

# 실행할 collector들을 매핑
ENABLED_COLLECTORS = {
    "alpaca": alpaca,
    "coinbase": coinbase,
    "crypto_public": crypto_public,
    "defillama": defillama,
    "fred": fred,
    "yfinance": yf,
}

def main():
    """
    config.yaml 설정에 따라 활성화된 모든 데이터 수집기를 실행합니다.
    """
    print("========================================")
    print("   Starting Market Data Collection      ")
    print("========================================")

    for name, module in ENABLED_COLLECTORS.items():
        # config 파일에서 해당 collector가 활성화되어 있는지 확인
        if config.get('collectors', {}).get(name, {}).get('enabled', False):
            try:
                print(f"\n----- Running {name} collector -----")
                module.collect()
                print(f"----- Finished {name} collector -----")
            except Exception as e:
                print(f"!!!!!! An error occurred while running the {name} collector: {e} !!!!!!")
        else:
            print(f"\n----- Skipping {name} collector (disabled in config.yaml) -----")

    print("\n========================================")
    print("   All collection tasks finished.       ")
    print("========================================")


if __name__ == "__main__":
    main()
