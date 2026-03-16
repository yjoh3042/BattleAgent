"""find_best_party.py – 파티 조합 전수 탐색
캐릭터 데이터를 fixtures/test_data.py 에 추가한 뒤 CHARACTER_POOL 을 채우세요.
실행: py -X utf8 src/find_best_party.py
"""
import sys, os, itertools
sys.path.insert(0, os.path.dirname(__file__))

from battle.battle_engine import BattleEngine
from battle.enums import BattleResult

# ─── 설정 ────────────────────────────────────────────────────────
# from fixtures.test_data import make_a, make_b, ..., get_enemies
# CHARACTER_POOL = [make_a, make_b, ...]  # 후보 캐릭터 팩토리 목록
# ENEMY_FACTORY  = get_enemies
# PARTY_SIZE     = 5

CHARACTER_POOL = []
ENEMY_FACTORY  = None
PARTY_SIZE     = 5


def main():
    if not CHARACTER_POOL or not ENEMY_FACTORY:
        print("CHARACTER_POOL / ENEMY_FACTORY 가 설정되지 않았습니다.")
        return

    results = []
    for combo in itertools.combinations(CHARACTER_POOL, PARTY_SIZE):
        engine = BattleEngine(
            ally_units=[f() for f in combo],
            enemy_units=ENEMY_FACTORY(),
            allow_active=True, allow_ultimate=True,
            ultimate_mode="auto", seed=42,
        )
        result = engine.run()
        results.append((result, engine.turn_count, [f.__name__ for f in combo]))

    wins = [(t, names) for r, t, names in results if r == BattleResult.ALLY_WIN]
    wins.sort()
    print(f"승리 조합 {len(wins)}개 (최단 순):")
    for t, names in wins[:10]:
        print(f"  {t}턴: {names}")


if __name__ == "__main__":
    main()
