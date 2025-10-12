from flask import Flask, request, jsonify
import subprocess
import threading
import sys
from pathlib import Path

app = Flask(__name__)

# 프로젝트 루트 디렉토리
project_root = Path(__file__).parent
# 현재 스크립트를 실행하고 있는 가상 환경의 Python 실행 파일 경로
python_executable = Path(sys.executable)

def run_main_script():
    """
    main.py를 별도의 프로세스로 실행합니다.
    가상 환경의 python을 사용하여 실행합니다.
    """
    script_path = project_root / "main.py"
    print(f"Attempting to run script: {script_path} with python: {python_executable}")
    try:
        # main.py가 프로젝트 루트에 있다고 가정
        result = subprocess.run(
            [str(python_executable), str(script_path)],
            capture_output=True,
            text=True,
            check=True,
            cwd=project_root # 작업 디렉토리를 프로젝트 루트로 설정
        )
        print("Script executed successfully.")
        print("STDOUT:", result.stdout)
        # STDERR은 에러가 없어도 출력될 수 있으므로 확인용으로 남겨둡니다.
        if result.stderr:
            print("STDERR:", result.stderr)
    except subprocess.CalledProcessError as e:
        print(f"Error executing script: {e}")
        print("STDOUT:", e.stdout)
        print("STDERR:", e.stderr)
    except FileNotFoundError:
        print(f"Error: The python executable or the script was not found.")
        print(f"  - Python: {python_executable}")
        print(f"  - Script: {script_path}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


@app.route('/run', methods=['POST'])
def run_script_endpoint():
    """
    /run 엔드포인트로 POST 요청을 받으면 백그라운드에서 main.py를 실행합니다.
    """
    print("Webhook received. Starting data collection in a background thread.")
    # 별도의 스레드에서 스크립트 실행을 시작
    thread = threading.Thread(target=run_main_script)
    thread.start()
    
    # 클라이언트에게 즉시 응답
    return jsonify({"status": "success", "message": "Data collection process started."}), 202

if __name__ == '__main__':
    # host='0.0.0.0'는 로컬 네트워크의 다른 장치에서도 접근 가능하게 합니다.
    # ngrok 사용 시에는 127.0.0.1로도 충분합니다.
    # debug=False로 설정하여 프로덕션 환경과 유사하게 실행합니다.
    app.run(host='127.0.0.1', port=5001, debug=False)
