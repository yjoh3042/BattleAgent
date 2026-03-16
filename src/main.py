"""전투 시스템 진입점
실행: py -X utf8 src/main.py
"""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from battle.battle_engine import BattleEngine
from battle.enums import BattleResult
from fixtures.test_data import (
    get_party_fire, get_party_water, get_party_forest,
    get_party_light, get_party_dark, get_party_mixed,
    get_enemies_3, get_enemies_5,
)


def run_scenario(label, ally_factory, enemy_factory,
                 allow_active=True, allow_ultimate=True,
                 ultimate_mode="auto", ultimate_order=None, verbose=False):
    """시나리오 실행 헬퍼"""
    print(f"\n{'='*60}\n  {label}\n{'='*60}")
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
    scenarios = [
        ("화속성 파티 vs 3마리 몬스터", get_party_fire,  get_enemies_3),
        ("암속성 파티 vs 3마리 몬스터", get_party_dark,  get_enemies_3),
        ("혼합 파티 vs 5마리 몬스터",   get_party_mixed, get_enemies_5),
        ("광속성 파티 vs 5마리 몬스터", get_party_light, get_enemies_5),
    ]

    wins = 0
    losses = 0
    time_overs = 0
    rows = []

    for label, ally_f, enemy_f in scenarios:
        result, elapsed, turns = run_scenario(label, ally_f, enemy_f)
        if result == BattleResult.ALLY_WIN:
            outcome = "승리"
            wins += 1
        elif result == BattleResult.ENEMY_WIN:
            outcome = "패배"
            losses += 1
        else:
            outcome = "시간초과"
            time_overs += 1
        rows.append((label, outcome, turns, f"{elapsed:.1f}"))

    # 요약 테이블
    print(f"\n{'='*60}")
    print("  결과 요약")
    print(f"{'='*60}")
    col_w = 26
    print(f"  {'시나리오':<{col_w}} {'결과':<8} {'턴수':>5} {'시간':>8}")
    print(f"  {'-'*col_w} {'-'*7} {'-'*5} {'-'*8}")
    for label, outcome, turns, elapsed in rows:
        print(f"  {label:<{col_w}} {outcome:<8} {turns:>5} {elapsed:>8}")
    print(f"  {'-'*col_w} {'-'*7} {'-'*5} {'-'*8}")
    print(f"  승리: {wins}  패배: {losses}  시간초과: {time_overs}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
