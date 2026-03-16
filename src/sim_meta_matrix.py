"""sim_meta_matrix.py – 메타 덱 전체 상성 매트릭스 (각 조합 N전)
캐릭터 데이터를 fixtures/test_data.py 에 추가한 뒤 META_DECKS 를 채우세요.
실행: py -X utf8 src/sim_meta_matrix.py
"""
from __future__ import annotations
import sys, os, time
sys.path.insert(0, os.path.dirname(__file__))

from battle.battle_engine import BattleEngine
from battle.enums import BattleResult

# ─── 설정 ────────────────────────────────────────────────────────
# from fixtures.test_data import get_deck_a, get_deck_b
# META_DECKS = [
#     ("DeckA", get_deck_a),
#     ("DeckB", get_deck_b),
# ]
META_DECKS = []
N_SIMS = 100


def main():
    if not META_DECKS:
        print("META_DECKS 가 비어 있습니다. 캐릭터 추가 후 덱을 정의하세요.")
        return

    names = [d[0] for d in META_DECKS]
    wins = {a: {b: 0 for b in names} for a in names}
    t0 = time.time()

    for na, fa in META_DECKS:
        for nb, fb in META_DECKS:
            if na == nb:
                continue
            for seed in range(N_SIMS):
                engine = BattleEngine(
                    ally_units=fa(), enemy_units=fb(),
                    allow_active=True, allow_ultimate=True,
                    ultimate_mode="auto", seed=seed,
                )
                if engine.run() == BattleResult.ALLY_WIN:
                    wins[na][nb] += 1

    col_w = 14
    print(f"{'':14}" + "".join(f"{n:>{col_w}}" for n in names))
    for na in names:
        row = f"{na:14}"
        for nb in names:
            row += f"{'—':>{col_w}}" if na == nb else f"{wins[na][nb]:>{col_w}}"
        print(row)
    print(f"\n소요 시간: {time.time()-t0:.1f}s")


if __name__ == "__main__":
    main()
