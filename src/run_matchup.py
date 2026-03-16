"""run_matchup.py – 메타 덱 상성 매트릭스 시뮬레이션
캐릭터 데이터를 fixtures/test_data.py 에 추가한 뒤 META_DECKS 를 채우세요.
실행: py -X utf8 src/run_matchup.py
"""
import sys
import os
import copy

sys.path.insert(0, os.path.dirname(__file__))

from battle.battle_engine import BattleEngine
from battle.enums import BattleResult

# ─── 메타 덱 정의 ────────────────────────────────────────────────
# 예시:
# from fixtures.test_data import get_my_party_a, get_my_party_b
# META_DECKS = [
#     ("DeckA", "설명", get_my_party_a),
#     ("DeckB", "설명", get_my_party_b),
# ]
META_DECKS = []


def run_matrix(decks, n_seeds=5):
    names = [d[0] for d in decks]
    wins = {n: {m: 0 for m in names} for n in names}

    for i, (name_a, _, factory_a) in enumerate(decks):
        for j, (name_b, _, factory_b) in enumerate(decks):
            if i == j:
                continue
            for seed in range(n_seeds):
                engine = BattleEngine(
                    ally_units=factory_a(),
                    enemy_units=factory_b(),
                    allow_active=True, allow_ultimate=True,
                    ultimate_mode="auto", seed=seed,
                )
                result = engine.run()
                if result == BattleResult.ALLY_WIN:
                    wins[name_a][name_b] += 1

    # 출력
    col_w = 14
    header = f"{'':14}" + "".join(f"{n:>{col_w}}" for n in names)
    print(header)
    for na in names:
        row = f"{na:14}"
        for nb in names:
            row += f"{'—':>{col_w}}" if na == nb else f"{wins[na][nb]:>{col_w}}"
        print(row)


def main():
    if not META_DECKS:
        print("META_DECKS 가 비어 있습니다. 캐릭터 추가 후 덱을 정의하세요.")
        return
    run_matrix(META_DECKS)


if __name__ == "__main__":
    main()
