"""웹 배틀 시뮬레이터 실행
Usage: python run_simulator.py
-> http://localhost:8000 에서 시뮬레이터 접속
"""
import sys
import uvicorn

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    print("Battle Simulator starting at http://localhost:9000")
    uvicorn.run("src.api_server:app", host="0.0.0.0", port=9000)
