"""커스텀 조합 분석기 - 5명 선택 → 12메타 대전 → 티어 판정
사용: py -X utf8 scripts/analyze_comp.py char1 char2 char3 char4 char5
웹 API: py -X utf8 scripts/analyze_comp.py --serve
"""
import sys, os, json, dataclasses, math

SRC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
sys.path.insert(0, SRC_DIR)

from battle.battle_engine import BattleEngine
from battle.enums import BattleResult, Role, Element
from battle.rules import ROLE_BASE_SP, ULT_COOLDOWN, ROLE_ULT_COOLDOWN

# ─── 캐릭터 레지스트리 ───────────────────────────────────────
def _build_registry():
    import fixtures.test_data as td
    registry = {}
    for name in dir(td):
        if name.startswith("make_") and not name.startswith("make_teddy"):
            fn = getattr(td, name)
            if callable(fn):
                try:
                    char = fn()
                    key = name.replace("make_", "")
                    registry[key] = {
                        "factory": fn,
                        "name": char.name,
                        "element": char.element.value,
                        "role": char.role.value,
                        "sp": char.ultimate_skill.sp_cost,
                        "spd": char.stats.spd,
                        "atk": char.stats.atk,
                        "def": char.stats.def_,
                        "hp": char.stats.hp,
                    }
                except Exception:
                    pass
    return registry

REGISTRY = _build_registry()

# ─── 메타 정의 ───────────────────────────────────────────────
def _meta_factories():
    from fixtures.test_data import (
        make_dabi, make_kararatri, make_semele, make_jiva, make_salmakis,
        make_bari, make_dogyehwa, make_sangah, make_thisbe, make_elysion,
        make_batory, make_mircalla, make_morgan, make_aurora, make_danu,
        make_pan, make_oneiroi, make_gumiho, make_brownie, make_metis,
        make_eve, make_ashtoreth, make_artemis, make_grilla, make_sitri,
        make_kubaba, make_tiwaz, make_yuna, make_deresa, make_frey,
        make_ragaraja, make_anubis, make_miriam,
    )
    return [
        ("M01", "화상연계", lambda: [make_dabi(), make_kararatri(), make_semele(), make_jiva(), make_salmakis()]),
        ("M02", "독정원",   lambda: [make_bari(), make_dogyehwa(), make_sangah(), make_thisbe(), make_elysion()]),
        ("M03", "출혈폭딜", lambda: [make_batory(), make_mircalla(), make_morgan(), make_aurora(), make_danu()]),
        ("M04", "CC잠금",   lambda: [make_pan(), make_oneiroi(), make_gumiho(), make_brownie(), make_metis()]),
        ("M05", "속도처형", lambda: [make_eve(), make_sangah(), make_thisbe(), make_salmakis(), make_brownie()]),
        ("M06", "크리폭딜", lambda: [make_ashtoreth(), make_artemis(), make_aurora(), make_grilla(), make_sitri()]),
        ("M07", "방어무력", lambda: [make_kubaba(), make_tiwaz(), make_artemis(), make_kararatri(), make_yuna()]),
        ("M08", "철벽반격", lambda: [make_deresa(), make_frey(), make_ragaraja(), make_metis(), make_jiva()]),
        ("M09", "풀암속성", lambda: [make_kubaba(), make_artemis(), make_anubis(), make_frey(), make_yuna()]),
        ("M10", "야성해방", lambda: [make_grilla(), make_miriam(), make_batory(), make_aurora(), make_brownie()]),
        ("M11", "화상수면", lambda: [make_pan(), make_dabi(), make_semele(), make_aurora(), make_jiva()]),
        ("M12", "속도출혈", lambda: [make_morgan(), make_mircalla(), make_salmakis(), make_sangah(), make_elysion()]),
    ]

METAS = _meta_factories()
N_SEEDS = 5  # 웹 API 응답 속도를 위해 최소화 (CLI에서는 --seeds N 으로 조절)

def flip_to_enemy(chars):
    return [dataclasses.replace(c, side="enemy") for c in chars]

def run_matchup(ally_factory, enemy_factory, n_seeds=N_SEEDS):
    ally_wins = enemy_wins = timeouts = 0
    turn_counts = []
    for seed in range(n_seeds):
        ally_chars = ally_factory()
        enemy_chars = flip_to_enemy(enemy_factory())
        engine = BattleEngine(ally_units=ally_chars, enemy_units=enemy_chars, seed=seed)
        result = engine.run()
        turn_counts.append(engine.turn_count)
        if result == BattleResult.ALLY_WIN:
            ally_wins += 1
        elif result == BattleResult.ENEMY_WIN:
            enemy_wins += 1
        else:
            timeouts += 1
    wr = (ally_wins + 0.5 * timeouts) / n_seeds
    avg_turn = sum(turn_counts) / len(turn_counts)
    return {"wins": ally_wins, "losses": enemy_wins, "timeouts": timeouts,
            "win_rate": round(wr * 100, 1), "avg_turns": round(avg_turn, 1)}

def analyze_comp(char_keys):
    """5명 캐릭터로 조합 분석."""
    factories = []
    comp_info = []
    for key in char_keys:
        if key not in REGISTRY:
            return {"error": f"캐릭터 '{key}' 없음. 사용 가능: {sorted(REGISTRY.keys())}"}
        info = REGISTRY[key]
        factories.append(info["factory"])
        comp_info.append({
            "key": key, "name": info["name"], "element": info["element"],
            "role": info["role"], "sp": info["sp"], "spd": info["spd"],
            "atk": info["atk"], "def": info["def"], "hp": info["hp"],
        })

    def user_team():
        return [f() for f in factories]

    # 12 메타 대전
    results = []
    total_wr = 0
    for mid, mname, mfactory in METAS:
        r = run_matchup(user_team, mfactory, N_SEEDS)
        r["meta_id"] = mid
        r["meta_name"] = mname
        results.append(r)
        total_wr += r["win_rate"]

    avg_wr = round(total_wr / len(METAS), 1)

    # 티어 판정
    if avg_wr >= 60:
        tier = "S"
    elif avg_wr >= 52:
        tier = "A"
    elif avg_wr >= 45:
        tier = "B"
    elif avg_wr >= 35:
        tier = "C"
    else:
        tier = "D"

    # 상성 분석
    counters = [r for r in results if r["win_rate"] >= 70]
    weaknesses = [r for r in results if r["win_rate"] <= 30]

    # 조합 분석
    roles = [c["role"] for c in comp_info]
    elements = [c["element"] for c in comp_info]
    avg_spd = round(sum(c["spd"] for c in comp_info) / len(comp_info), 1)

    return {
        "composition": comp_info,
        "avg_winrate": avg_wr,
        "tier": tier,
        "avg_spd": avg_spd,
        "roles": roles,
        "elements": elements,
        "matchups": sorted(results, key=lambda x: -x["win_rate"]),
        "counters": len(counters),
        "weaknesses": len(weaknesses),
    }

def get_char_list():
    """캐릭터 목록 반환."""
    chars = []
    for key, info in sorted(REGISTRY.items(), key=lambda x: (x[1]["element"], x[1]["role"], x[1]["name"])):
        chars.append({
            "key": key, "name": info["name"], "element": info["element"],
            "role": info["role"], "sp": info["sp"], "spd": info["spd"],
            "atk": info["atk"], "def": info["def"], "hp": info["hp"],
        })
    return chars

# ─── HTTP 서버 (웹 UI 연동) ──────────────────────────────────
def serve():
    from http.server import HTTPServer, SimpleHTTPRequestHandler
    import urllib.parse

    class Handler(SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=os.path.join(
                os.path.dirname(os.path.abspath(__file__)), "..", "web"), **kwargs)

        def do_GET(self):
            parsed = urllib.parse.urlparse(self.path)
            if parsed.path == "/api/chars":
                self._json_response(get_char_list())
            elif parsed.path == "/api/analyze":
                qs = urllib.parse.parse_qs(parsed.query)
                chars = qs.get("chars", [""])[0].split(",")
                chars = [c.strip() for c in chars if c.strip()]
                if len(chars) != 5:
                    self._json_response({"error": "5명의 캐릭터를 선택해주세요."})
                else:
                    print(f"  분석 시작: {chars}")
                    result = analyze_comp(chars)
                    print(f"  분석 완료: 평균 승률 {result.get('avg_winrate', '?')}%")
                    self._json_response(result)
            elif parsed.path == "/api/test":
                # 즉시 응답 테스트
                self._json_response({
                    "tier": "B", "avg_winrate": 48.5, "avg_spd": 90,
                    "counters": 2, "weaknesses": 3,
                    "composition": [],
                    "matchups": [
                        {"meta_id": "M01", "meta_name": "테스트", "win_rate": 60.0,
                         "wins": 3, "losses": 2, "timeouts": 0, "avg_turns": 80}
                    ]
                })
            elif parsed.path == "/view/result":
                qs = urllib.parse.parse_qs(parsed.query)
                chars = qs.get("chars", [""])[0].split(",")
                chars = [c.strip() for c in chars if c.strip()]
                if len(chars) != 5:
                    self._html_response("<p style='color:red'>5명의 캐릭터를 선택해주세요.</p>")
                else:
                    print(f"  분석 시작: {chars}")
                    result = analyze_comp(chars)
                    print(f"  분석 완료: 평균 승률 {result.get('avg_winrate', '?')}%")
                    self._html_response(self._render_result_html(result))
            else:
                super().do_GET()

        def _render_result_html(self, d):
            tier = d["tier"]
            tc = {"S":"#ff4a6a","A":"#ff8c4a","B":"#ffd84a","C":"#4a9eff","D":"#8b8fa8"}[tier]
            rows = ""
            for m in d["matchups"]:
                w = m["win_rate"]
                wc = "#4aff8b" if w >= 50 else "#ff4a6a"
                bc = "#4aff8b" if w >= 60 else "#ffd84a" if w >= 40 else "#ff4a6a"
                v = "유리" if w >= 70 else "소폭유리" if w >= 55 else "호각" if w >= 45 else "소폭불리" if w >= 30 else "불리"
                vc = "#4aff8b" if w >= 55 else "#ffd84a" if w >= 45 else "#ff4a6a"
                rows += f"""<tr>
                  <td><b>{m['meta_id']}</b> {m['meta_name']}</td>
                  <td style="font-weight:700;color:{wc}">{w}%</td>
                  <td><div style="width:50px;height:4px;background:#242836;border-radius:2px;display:inline-block;overflow:hidden">
                    <div style="height:100%;width:{w}%;background:{bc};border-radius:2px"></div></div></td>
                  <td>{m['wins']}/{m['losses']}/{m['timeouts']}</td>
                  <td>{m['avg_turns']}</td>
                  <td style="color:{vc};font-weight:600">{v}</td>
                </tr>"""
            return f"""<!DOCTYPE html><html><head><meta charset="UTF-8"><style>
              *{{box-sizing:border-box;margin:0;padding:0}}
              body{{font-family:'Segoe UI',sans-serif;background:#0f1117;color:#e4e6f0;padding:10px;font-size:12px}}
              .rh{{display:flex;align-items:center;padding:12px;background:#1a1d27;border:1px solid #2d3348;border-radius:10px;margin-bottom:10px}}
              .tb{{display:inline-flex;align-items:center;justify-content:center;width:44px;height:44px;border-radius:10px;
                font-size:24px;font-weight:800;margin-right:10px;border:2px solid {tc};color:{tc};background:rgba(0,0,0,.2)}}
              table{{width:100%;border-collapse:collapse;background:#1a1d27;border:1px solid #2d3348;border-radius:10px;overflow:hidden}}
              th{{text-align:left;padding:5px 8px;font-size:10px;color:#8b8fa8;border-bottom:1px solid #2d3348}}
              td{{padding:4px 8px;font-size:11px;border-bottom:1px solid #2d3348}}
              tr:hover{{background:#242836}}
            </style></head><body>
            <div class="rh"><div class="tb">{tier}</div><div>
              <div style="font-size:15px;font-weight:700">평균 승률 {d['avg_winrate']}%</div>
              <div style="font-size:10px;color:#8b8fa8;margin-top:3px">
                카운터 <b style="color:#4aff8b">{d['counters']}개</b> ·
                취약 <b style="color:#ff4a6a">{d['weaknesses']}개</b> ·
                SPD <b style="color:#e4e6f0">{d['avg_spd']}</b></div>
            </div></div>
            <table><thead><tr><th>메타</th><th>승률</th><th></th><th>W/L/T</th><th>턴</th><th>판정</th></tr></thead>
            <tbody>{rows}</tbody></table></body></html>"""

        def _json_response(self, data):
            body = json.dumps(data, ensure_ascii=False).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(body)

        def _html_response(self, html_str):
            body = html_str.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format, *args):
            if "/api/" in str(args[0]):
                super().log_message(format, *args)

    port = 8765
    print(f"  서버 시작: http://localhost:{port}")
    print(f"  캐릭터 수: {len(REGISTRY)}명")
    print(f"  메타 수: {len(METAS)}개")
    print(f"  시뮬레이션: {N_SEEDS} seeds/매치업")
    HTTPServer(("", port), Handler).serve_forever()


if __name__ == "__main__":
    if "--serve" in sys.argv:
        serve()
    elif "--list" in sys.argv:
        for c in get_char_list():
            print(f"  {c['key']:<16} {c['name']:<10} [{c['element']:<7}] {c['role']:<10} SPD={c['spd']}")
    elif len(sys.argv) >= 6:
        chars = sys.argv[1:6]
        result = analyze_comp(chars)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("사용법:")
        print("  py -X utf8 scripts/analyze_comp.py char1 char2 char3 char4 char5")
        print("  py -X utf8 scripts/analyze_comp.py --list")
        print("  py -X utf8 scripts/analyze_comp.py --serve")
