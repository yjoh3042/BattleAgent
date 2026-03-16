"""run_visual.py – 배틀 리플레이 HTML 생성 + HTTP 서버
캐릭터 데이터를 fixtures/test_data.py 에 추가한 뒤 SCENARIOS 를 채우세요.
실행: py -X utf8 src/run_visual.py
"""
import sys
import os
import http.server
import threading

sys.path.insert(0, os.path.dirname(__file__))

PORT = 8000
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUTPUT_FILE = os.path.join(PROJECT_ROOT, "battle_replay.html")

# ─── 시나리오 정의 ────────────────────────────────────────────────
# 예시:
# from fixtures.test_data import get_my_party, get_enemies
# SCENARIOS = [
#     {
#         "label": "Scenario 1",
#         "ally_factory": get_my_party,
#         "enemy_factory": get_enemies,
#         "allow_active": True,
#         "allow_ultimate": True,
#         "ultimate_mode": "auto",
#     },
# ]
SCENARIOS = []


def generate_html():
    if not SCENARIOS:
        html = """<!DOCTYPE html>
<html lang="ko">
<head><meta charset="UTF-8"><title>Battle Visual</title>
<style>
  body { font-family: sans-serif; display: flex; align-items: center;
         justify-content: center; height: 100vh; margin: 0; background: #1a1a2e; color: #eee; }
  .box { text-align: center; padding: 2rem; border: 1px solid #444; border-radius: 8px; }
  code { background: #333; padding: 2px 6px; border-radius: 4px; }
</style>
</head>
<body>
<div class="box">
  <h2>⚔️ Battle Visual</h2>
  <p>SCENARIOS 가 비어 있습니다.</p>
  <p><code>src/run_visual.py</code> 에서 SCENARIOS 를 정의한 뒤 서버를 재시작하세요.</p>
</div>
</body>
</html>"""
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write(html)
        print("placeholder HTML 생성 완료 (SCENARIOS 없음)")
        return

    from battle.battle_engine import BattleEngine
    from html_visualizer import generate_multi_html

    all_logs = []
    for s in SCENARIOS:
        engine = BattleEngine(
            ally_units=s["ally_factory"](),
            enemy_units=s["enemy_factory"](),
            allow_active=s.get("allow_active", True),
            allow_ultimate=s.get("allow_ultimate", True),
            ultimate_mode=s.get("ultimate_mode", "auto"),
            ultimate_order=s.get("ultimate_order", []),
            seed=42,
        )
        engine.run()
        all_logs.append((s["label"], engine.recorder))

    html = generate_multi_html(all_logs)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"HTML 저장 완료: {OUTPUT_FILE}")


def main():
    generate_html()

    os.chdir(PROJECT_ROOT)

    handler = http.server.SimpleHTTPRequestHandler

    class QuietHandler(handler):
        def log_message(self, fmt, *args):
            pass  # suppress per-request noise

    server = http.server.HTTPServer(("", PORT), QuietHandler)
    print(f"서버 시작: http://localhost:{PORT}/battle_replay.html")
    sys.stdout.flush()
    server.serve_forever()


if __name__ == "__main__":
    main()
