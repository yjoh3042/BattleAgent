"""run_visual.py - 9개 시나리오 배틀 리플레이 HTML 생성 및 브라우저 오픈
엑셀 기준 시나리오: NormalOnly / AddActive / RandomUltimate / SettingUltimate / ChangePartyRandom / ChangePartySetting / OptimizedOrder / BestOrder / AbsoluteBest
실행: python -X utf8 src/run_visual.py
"""
import sys
import os
import webbrowser

sys.path.insert(0, os.path.dirname(__file__))

from battle.battle_engine import BattleEngine
from battle.battle_recorder import BattleRecorder
from fixtures.test_data import (
    get_party1, get_party2, get_enemies, get_enemies_5,
    make_hildred, make_arahan, make_gumiho, make_kararatri, make_cain,
)

def get_best_party():
    """전수탐색 1위 조합: 힐드·아라한·구미호·카라라트리·카인"""
    return [make_hildred(), make_arahan(), make_gumiho(), make_kararatri(), make_cain()]
from html_visualizer import generate_multi_html

OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "..", "battle_replay.html")

# ─── 시나리오 정의 (엑셀 기준 6개) ──────────────────────────────
SCENARIOS = [
    {
        "label": "Scenario 1: NormalOnly",
        "ally_factory": get_party1,
        "allow_active": False,
        "allow_ultimate": False,
        "ultimate_mode": "auto",
        "ultimate_order": [],
    },
    {
        "label": "Scenario 2: AddActive",
        "ally_factory": get_party1,
        "allow_active": True,
        "allow_ultimate": False,
        "ultimate_mode": "auto",
        "ultimate_order": [],
    },
    {
        "label": "Scenario 3: RandomUltimate",
        "ally_factory": get_party1,
        "allow_active": True,
        "allow_ultimate": True,
        "ultimate_mode": "auto",
        "ultimate_order": [],
    },
    {
        "label": "Scenario 4: SettingUltimate",
        "ally_factory": get_party1,
        "allow_active": True,
        "allow_ultimate": True,
        "ultimate_mode": "manual_ordered",
        "ultimate_order": ["citria", "hild", "arahan", "frey", "dana"],
    },
    {
        "label": "Scenario 5: ChangePartyRandom",
        "ally_factory": get_party2,
        "allow_active": True,
        "allow_ultimate": True,
        "ultimate_mode": "auto",
        "ultimate_order": [],
    },
    {
        "label": "Scenario 6: ChangePartySetting",
        "ally_factory": get_party2,
        "allow_active": True,
        "allow_ultimate": True,
        "ultimate_mode": "manual_ordered",
        "ultimate_order": ["citria", "laga", "gumiho", "kara", "cain"],
    },
    {
        "label": "Scenario 7: OptimizedOrder",
        "ally_factory": get_party2,
        "allow_active": True,
        "allow_ultimate": True,
        "ultimate_mode": "manual_ordered",
        # 화상 시너지 우선: 구미호(전체화상) → 카인(화상×200%) → 시트리(속도버프) → 카라(기절) → 라가(반격버프)
        "ultimate_order": ["gumiho", "cain", "citria", "kara", "laga"],
    },
    {
        "label": "Scenario 8: BestOrder",
        "ally_factory": get_party2,
        "allow_active": True,
        "allow_ultimate": True,
        "ultimate_mode": "manual_ordered",
        # 전수탐색 1위 (120가지 중 최단 36턴)
        # 카인 먼저(전체딜) → 시트리(속도버프 조기발동) → 구미호(전체화상) → 카라(기절) → 라가(반격)
        "ultimate_order": ["cain", "citria", "gumiho", "kara", "laga"],
    },
    {
        "label": "Scenario 9: AbsoluteBest",
        "ally_factory": get_best_party,
        "allow_active": True,
        "allow_ultimate": True,
        "ultimate_mode": "manual_ordered",
        # 전수탐색 절대 최단 (126조합×120순서 중 1위, 27턴)
        # 파티: 힐드·아라한·구미호·카라라트리·카인
        # 카인(전체딜선제) → 힐드(ATK버프) → 카라라트리(기절) → 아라한(지원) → 구미호(전체화상)
        "ultimate_order": ["cain", "hild", "kara", "arahan", "gumiho"],
    },
    {
        "label": "Scenario 10: 5Monster_NormalParty",
        "ally_factory": get_party1,
        "enemy_factory": get_enemies_5,
        "allow_active": True,
        "allow_ultimate": True,
        "ultimate_mode": "manual_ordered",
        "ultimate_order": ["citria", "hild", "arahan", "frey", "dana"],
    },
    {
        "label": "Scenario 11: 5Monster_BurnParty",
        "ally_factory": get_party2,
        "enemy_factory": get_enemies_5,
        "allow_active": True,
        "allow_ultimate": True,
        "ultimate_mode": "manual_ordered",
        "ultimate_order": ["cain", "citria", "gumiho", "kara", "laga"],
    },
]


def run_all():
    print("=" * 60)
    print("  ⚔️  CTB 배틀 리플레이 - 11개 시나리오 실행")
    print("=" * 60)

    all_battle_data = []
    all_labels = []

    for scen in SCENARIOS:
        print(f"\n{'─'*60}")
        print(f"▶ {scen['label']} 실행 중...")
        print(f"{'─'*60}")

        recorder = BattleRecorder()
        recorder.scenario_label = scen["label"]

        engine = BattleEngine(
            ally_units=scen["ally_factory"](),
            enemy_units=scen.get("enemy_factory", get_enemies)(),
            allow_active=scen["allow_active"],
            allow_ultimate=scen["allow_ultimate"],
            ultimate_mode=scen["ultimate_mode"],
            ultimate_order=scen["ultimate_order"],
            recorder=recorder,
            seed=42,
        )
        result = engine.run()
        engine.print_summary()

        print(f"  → {len(recorder.records)}턴 기록됨")
        all_battle_data.append(recorder.to_dict())
        all_labels.append(scen["label"])

    # ─── HTML 생성 ────────────────────────────────────────────────
    print(f"\n{'='*60}")
    print(f"총 {len(all_battle_data)}개 시나리오 완료.")
    print("HTML 파일 생성 중...")

    html_content = generate_multi_html(all_battle_data, all_labels)

    out_path = os.path.abspath(OUTPUT_FILE)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    size_kb = os.path.getsize(out_path) / 1024
    print(f"저장 완료: {out_path}  ({size_kb:.1f} KB)")

    # ─── 브라우저 오픈 ────────────────────────────────────────────
    print("브라우저에서 열기...")
    webbrowser.open(f"file:///{out_path.replace(os.sep, '/')}")
    print("Done! 브라우저에서 battle_replay.html을 확인하세요.")
    print("\n[조작법]")
    print("  시나리오 탭 클릭    : 시나리오 전환")
    print("  ◀ / ▶ 또는 방향키  : 이전/다음 턴")
    print("  Home / End         : 처음/마지막 턴")
    print("  Space              : 자동재생 토글")
    print("  슬라이더            : 임의 턴 이동")


if __name__ == "__main__":
    run_all()
