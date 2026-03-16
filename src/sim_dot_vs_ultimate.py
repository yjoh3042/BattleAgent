"""sim_dot_vs_ultimate.py – 두 파티 N회 대전 승률 비교
캐릭터 데이터를 fixtures/test_data.py 에 추가한 뒤 설정을 채우세요.
실행: py -X utf8 src/sim_dot_vs_ultimate.py
"""
from __future__ import annotations
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from battle.battle_engine import BattleEngine
from battle.enums import BattleResult

# ─── 설정 ────────────────────────────────────────────────────────
# from fixtures.test_data import get_party_a, get_party_b
# PARTY_A_FACTORY = get_party_a   # 아군
# PARTY_B_FACTORY = get_party_b   # 적군
# N_SIMS = 100

PARTY_A_FACTORY = None
PARTY_B_FACTORY = None
N_SIMS = 100


def simulate(ally_f, enemy_f, n, label_a="A", label_b="B"):
    wins_a = wins_b = draws = 0
    for seed in range(n):
        engine = BattleEngine(
            ally_units=ally_f(), enemy_units=enemy_f(),
            allow_active=True, allow_ultimate=True,
            ultimate_mode="auto", seed=seed,
        )
        r = engine.run()
        if r == BattleResult.ALLY_WIN:
            wins_a += 1
        elif r == BattleResult.ENEMY_WIN:
            wins_b += 1
        else:
            draws += 1
    print(f"{label_a} 승: {wins_a}/{n} ({wins_a/n*100:.1f}%) | "
          f"{label_b} 승: {wins_b}/{n} | 무: {draws}")


def main():
    if not PARTY_A_FACTORY or not PARTY_B_FACTORY:
        print("PARTY_A_FACTORY / PARTY_B_FACTORY 가 설정되지 않았습니다.")
        return
    simulate(PARTY_A_FACTORY, PARTY_B_FACTORY, N_SIMS, "PartyA", "PartyB")


if __name__ == "__main__":
    main()
