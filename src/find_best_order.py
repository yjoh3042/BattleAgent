"""find_best_order.py - 파티2 얼티밋 순서 전수 탐색 (5! = 120가지)
데이터 변경 없이 순서만 바꿔 최단 턴 조합을 찾는다.
"""
import sys, os, itertools
sys.path.insert(0, os.path.dirname(__file__))

from battle.battle_engine import BattleEngine
from battle.battle_recorder import BattleRecorder
from fixtures.test_data import get_party2, get_enemies

CHARS = ["gumiho", "cain", "citria", "kara", "laga"]
ALL_ORDERS = list(itertools.permutations(CHARS))

results = []

for order in ALL_ORDERS:
    rec = BattleRecorder()
    eng = BattleEngine(
        ally_units=get_party2(),
        enemy_units=get_enemies(),
        allow_active=True,
        allow_ultimate=True,
        ultimate_mode="manual_ordered",
        ultimate_order=list(order),
        recorder=rec,
        seed=42,
    )
    res = eng.run()
    turns = len(rec.records)
    results.append((turns, list(order)))

# 턴수 기준 정렬
results.sort(key=lambda x: x[0])

print("=" * 60)
print(f"  🔍 파티2 얼티밋 순서 전수 탐색  (총 {len(results)}가지)")
print("=" * 60)

print("\n── TOP 10 최단 순서 ──────────────────────────────────────")
for rank, (turns, order) in enumerate(results[:10], 1):
    arrow = " → ".join(order)
    print(f"  {rank:>2}위  {turns:>3}턴   {arrow}")

print("\n── BOTTOM 5 최장 순서 ────────────────────────────────────")
for rank, (turns, order) in enumerate(results[-5:], 1):
    arrow = " → ".join(order)
    print(f"  {rank:>2}위  {turns:>3}턴   {arrow}")

best_turns, best_order = results[0]
worst_turns, worst_order = results[-1]
print(f"\n✅ 최단: {best_turns}턴  →  {' → '.join(best_order)}")
print(f"❌ 최장: {worst_turns}턴  →  {' → '.join(worst_order)}")
print(f"   차이: {worst_turns - best_turns}턴")

# 현재 시나리오 6 순서 위치 확인
sc6 = ["citria", "laga", "gumiho", "kara", "cain"]
sc6_rank = next((i+1 for i, (_, o) in enumerate(results) if o == sc6), None)
sc6_turns = next((t for t, o in results if o == sc6), None)
sc7 = ["gumiho", "cain", "citria", "kara", "laga"]
sc7_rank = next((i+1 for i, (_, o) in enumerate(results) if o == sc7), None)
sc7_turns = next((t for t, o in results if o == sc7), None)
print(f"\n   시나리오 6 순서: {sc6_turns}턴  (전체 {sc6_rank}위 / 120)")
print(f"   시나리오 7 순서: {sc7_turns}턴  (전체 {sc7_rank}위 / 120)")
