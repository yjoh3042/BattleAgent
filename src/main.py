"""전투 시스템 진입점 - 엑셀 기준 6개 시나리오 실행 및 검증"""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from battle.battle_engine import BattleEngine
from battle.enums import BattleResult
from fixtures.test_data import get_party1, get_party2, get_enemies, get_enemies_5


def run_scenario(
    label: str,
    ally_factory,
    enemy_factory,
    allow_active: bool = True,
    allow_ultimate: bool = True,
    ultimate_mode: str = "auto",
    ultimate_order: list = None,
    verbose: bool = False,
):
    """시나리오 실행 헬퍼"""
    print(f"\n{'='*60}")
    print(f"  {label}")
    print(f"{'='*60}")

    engine = BattleEngine(
        ally_units=ally_factory(),
        enemy_units=enemy_factory(),
        allow_active=allow_active,
        allow_ultimate=allow_ultimate,
        ultimate_mode=ultimate_mode,
        ultimate_order=ultimate_order or [],
        seed=42,
    )
    result = engine.run()

    if verbose:
        engine.print_log()

    engine.print_summary()
    return result, engine.turn_manager.current_time, engine.turn_count


def main():
    print("⚔️  턴제 RPG 전투 시스템 시뮬레이션")
    print("기획 스펙: CTB (300/SPD), 공용 SP, 얼티밋 끼어들기")
    print("엑셀 시나리오: NormalOnly / AddActive / RandomUltimate / SettingUltimate / ChangePartyRandom / ChangePartySetting")

    results = []

    # ─── Scenario 1: NormalOnly ──────────────────────────────────
    # 파티1 × 노멀 스킬만. 힐/버프/얼티밋 없음 → 가장 오래 걸림
    r, t, turns = run_scenario(
        "Scenario 1: NormalOnly (파티1 × 노멀 스킬만)",
        get_party1, get_enemies,
        allow_active=False,
        allow_ultimate=False,
        verbose=False,
    )
    results.append(("Scenario 1 (NormalOnly)", r, t, turns))

    # ─── Scenario 2: AddActive ───────────────────────────────────
    # 파티1 × 노멀+액티브. 광역기/버프 추가 → 조금 빠름
    r, t, turns = run_scenario(
        "Scenario 2: AddActive (파티1 × 노멀+액티브)",
        get_party1, get_enemies,
        allow_active=True,
        allow_ultimate=False,
        verbose=False,
    )
    results.append(("Scenario 2 (AddActive)", r, t, turns))

    # ─── Scenario 3: RandomUltimate ─────────────────────────────
    # 파티1 × 전부 허용, 얼티밋 자동. SP 쌓이면 랜덤 발동
    r, t, turns = run_scenario(
        "Scenario 3: RandomUltimate (파티1 × 얼티밋 자동)",
        get_party1, get_enemies,
        allow_active=True,
        allow_ultimate=True,
        ultimate_mode="auto",
        verbose=False,
    )
    results.append(("Scenario 3 (RandomUltimate)", r, t, turns))

    # ─── Scenario 4: SettingUltimate ────────────────────────────
    # 파티1 × 지정 얼티밋. 시트리→힐드→아라한→프레이→다나 순
    # 예상: 시트리 속도버프 먼저 → 힐드 광역딜 강화 → 프레이 도발
    party1_ult_order = ["citria", "hild", "arahan", "frey", "dana"]
    r, t, turns = run_scenario(
        "Scenario 4: SettingUltimate (파티1 × 지정 얼티밋)",
        get_party1, get_enemies,
        allow_active=True,
        allow_ultimate=True,
        ultimate_mode="manual_ordered",
        ultimate_order=party1_ult_order,
        verbose=True,
    )
    results.append(("Scenario 4 (SettingUltimate)", r, t, turns))

    # ─── Scenario 5: ChangePartyRandom ──────────────────────────
    # 파티2 × 얼티밋 자동. 화상 시너지 파티 + 랜덤 얼티밋
    r, t, turns = run_scenario(
        "Scenario 5: ChangePartyRandom (파티2 × 얼티밋 자동)",
        get_party2, get_enemies,
        allow_active=True,
        allow_ultimate=True,
        ultimate_mode="auto",
        verbose=False,
    )
    results.append(("Scenario 5 (ChangePartyRandom)", r, t, turns))

    # ─── Scenario 6: ChangePartySetting ─────────────────────────
    # 파티2 × 지정 얼티밋. 시트리→라가→구미호→카라→카인 순
    # 예상: 구미호 화상전체 → 카인 핵폭탄 → 최단 클리어
    party2_ult_order = ["citria", "laga", "gumiho", "kara", "cain"]
    r, t, turns = run_scenario(
        "Scenario 6: ChangePartySetting (파티2 × 지정 얼티밋)",
        get_party2, get_enemies,
        allow_active=True,
        allow_ultimate=True,
        ultimate_mode="manual_ordered",
        ultimate_order=party2_ult_order,
        verbose=True,
    )
    results.append(("Scenario 6 (ChangePartySetting)", r, t, turns))

    # ─── Scenario 7: 5Monster_NormalParty ─────────────────────────
    # 파티1(밸런스) × 몬스터 5마리 (D형: 속도감소, E형: 힐러 추가)
    r, t, turns = run_scenario(
        "Scenario 7: 5Monster_NormalParty (파티1 × 5마리)",
        get_party1, get_enemies_5,
        allow_active=True,
        allow_ultimate=True,
        ultimate_mode="manual_ordered",
        ultimate_order=["citria", "hild", "arahan", "frey", "dana"],
        verbose=False,
    )
    results.append(("Scenario 7 (5Monster_Normal)", r, t, turns))

    # ─── Scenario 8: 5Monster_BurnParty ────────────────────────
    # 파티2(화상연계) × 몬스터 5마리, 최적 얼티밋 순서
    r, t, turns = run_scenario(
        "Scenario 8: 5Monster_BurnParty (파티2 × 5마리)",
        get_party2, get_enemies_5,
        allow_active=True,
        allow_ultimate=True,
        ultimate_mode="manual_ordered",
        ultimate_order=["cain", "citria", "gumiho", "kara", "laga"],
        verbose=False,
    )
    results.append(("Scenario 8 (5Monster_Burn)", r, t, turns))

    # ─── 결과 요약 ────────────────────────────────────────────────
    print("\n" + "=" * 68)
    print("📊 전체 시뮬레이션 결과 요약 (8개 시나리오)")
    print("=" * 68)
    print(f"{'시나리오':<38} {'결과':<10} {'타임라인':>10} {'턴수':>6}")
    print("-" * 68)
    for label, result, timeline, turn_count in results:
        r_str = "🏆 아군 승리" if result == BattleResult.ALLY_WIN else \
                "💀 적군 승리" if result == BattleResult.ENEMY_WIN else "⏰ 타임오버"
        print(f"{label:<38} {r_str:<10} {timeline:>10.3f} {turn_count:>6}")

    print("\n✅ 검증 기준:")
    print("  - Scenario 4 (SettingUltimate): 파티1 지정 얼티밋 → 아군 승리")
    print("  - Scenario 6 (ChangePartySetting): 파티2 화상연계 → 아군 승리 (빠름)")
    print("  - SPD 120(시트리/아라한) > SPD 80(힐드/카인) 행동 빈도 차이")
    print("  - 얼티밋 끼어들기: 발동 직후 Extra Turn 2연속 행동 확인")
    print("  - 화상 스택 × 카인 핵폭탄 대미지 상승 확인")


if __name__ == "__main__":
    main()
