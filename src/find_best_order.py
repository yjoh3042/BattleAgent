"""find_best_order.py – 얼티밋 발동 순서 전수 탐색 (5! = 120가지)
캐릭터 데이터를 fixtures/test_data.py 에 추가한 뒤 설정을 채우세요.
실행: py -X utf8 src/find_best_order.py
"""
import sys, os, itertools
sys.path.insert(0, os.path.dirname(__file__))

from battle.battle_engine import BattleEngine
from battle.enums import BattleResult

# ─── 설정 ────────────────────────────────────────────────────────
# from fixtures.test_data import get_my_party, get_enemies
# ALLY_FACTORY   = get_my_party
# ENEMY_FACTORY  = get_enemies

ALLY_FACTORY  = None
ENEMY_FACTORY = None


def main():
    if not ALLY_FACTORY or not ENEMY_FACTORY:
        print("ALLY_FACTORY / ENEMY_FACTORY 가 설정되지 않았습니다.")
        return

    ally_units = ALLY_FACTORY()
    order_ids  = [u.id for u in ally_units]
    best, best_turns = None, 10**9

    for perm in itertools.permutations(order_ids):
        engine = BattleEngine(
            ally_units=ALLY_FACTORY(),
            enemy_units=ENEMY_FACTORY(),
            allow_active=True, allow_ultimate=True,
            ultimate_mode="setting", ultimate_order=list(perm),
            seed=42,
        )
        result = engine.run()
        if result == BattleResult.ALLY_WIN and engine.turn_count < best_turns:
            best_turns = engine.turn_count
            best = perm

    if best:
        print(f"최적 순서 ({best_turns}턴): {best}")
    else:
        print("승리 조합 없음.")


if __name__ == "__main__":
    main()
