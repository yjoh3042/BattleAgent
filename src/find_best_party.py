"""find_best_party.py
9개 캐릭터에서 5명 조합 전수탐색 (C(9,5) = 126가지)
+ 상위 10개 조합에 대해 얼티밋 순서 전수탐색 (5! = 120가지)
"""
import sys, os, itertools
sys.path.insert(0, os.path.dirname(__file__))

from battle.battle_engine import BattleEngine
from battle.battle_recorder import BattleRecorder
from fixtures.test_data import (
    make_hildred, make_arahan, make_dana, make_frey, make_citria,
    make_gumiho, make_kararatri, make_cain, make_lagaraja,
    get_enemies,
)

# ─── 캐릭터 풀 ────────────────────────────────────────────────
CHAR_POOL = {
    "hild":   make_hildred,
    "arahan": make_arahan,
    "dana":   make_dana,
    "frey":   make_frey,
    "citria": make_citria,
    "gumiho": make_gumiho,
    "kara":   make_kararatri,
    "cain":   make_cain,
    "laga":   make_lagaraja,
}
NAMES = {
    "hild": "힐드", "arahan": "아라한", "dana": "다나", "frey": "프레이",
    "citria": "시트리", "gumiho": "구미호", "kara": "카라라트리",
    "cain": "카인", "laga": "라가라자",
}

def run_battle(char_ids: list, mode: str = "auto", order: list = None) -> int:
    units = [CHAR_POOL[cid]() for cid in char_ids]
    rec = BattleRecorder()
    eng = BattleEngine(
        ally_units=units,
        enemy_units=get_enemies(),
        allow_active=True,
        allow_ultimate=True,
        ultimate_mode=mode,
        ultimate_order=order or [],
        recorder=rec,
        seed=42,
    )
    eng.run()
    return len(rec.records)

# ══════════════════════════════════════════════════════════════
# PHASE 1: 126가지 조합 × auto 모드
# ══════════════════════════════════════════════════════════════
print("=" * 64)
print("  PHASE 1 ─ C(9,5) = 126가지 조합 탐색 (auto 모드)")
print("=" * 64)

ALL_IDS = list(CHAR_POOL.keys())
combo_results = []

for i, combo in enumerate(itertools.combinations(ALL_IDS, 5), 1):
    turns = run_battle(list(combo))
    combo_results.append((turns, list(combo)))
    if i % 20 == 0 or i == 126:
        print(f"  진행: {i}/126 완료...")

combo_results.sort(key=lambda x: x[0])

print("\n── TOP 15 조합 (auto 모드) ───────────────────────────────")
for rank, (turns, combo) in enumerate(combo_results[:15], 1):
    names = " · ".join(NAMES[c] for c in combo)
    print(f"  {rank:>2}위  {turns:>3}턴   {names}")

print("\n── BOTTOM 5 조합 ─────────────────────────────────────────")
for rank, (turns, combo) in enumerate(combo_results[-5:], 1):
    names = " · ".join(NAMES[c] for c in combo)
    print(f"  {rank:>2}위  {turns:>3}턴   {names}")

# ══════════════════════════════════════════════════════════════
# PHASE 2: 상위 10개 조합 × 얼티밋 순서 전수탐색
# ══════════════════════════════════════════════════════════════
print("\n" + "=" * 64)
print("  PHASE 2 ─ 상위 10개 조합 × 5! 순서 전수탐색")
print("=" * 64)

TOP_COMBOS = combo_results[:10]
global_results = []  # (turns, combo, order, mode)

for rank, (auto_turns, combo) in enumerate(TOP_COMBOS, 1):
    names = " · ".join(NAMES[c] for c in combo)
    print(f"\n  [{rank:>2}] {names}  (auto {auto_turns}턴)")

    best_ord_turns = auto_turns
    best_ord = None

    for order in itertools.permutations(combo):
        t = run_battle(combo, mode="manual_ordered", order=list(order))
        if t < best_ord_turns:
            best_ord_turns = t
            best_ord = list(order)

    if best_ord:
        arrow = " → ".join(NAMES[o] for o in best_ord)
        print(f"       ✅ 최적 순서: {best_ord_turns}턴  [{arrow}]")
        global_results.append((best_ord_turns, combo, best_ord, "manual_ordered"))
    else:
        print(f"       ─ auto가 최선 ({auto_turns}턴)")
        global_results.append((auto_turns, combo, [], "auto"))

# ══════════════════════════════════════════════════════════════
# 최종 결과
# ══════════════════════════════════════════════════════════════
global_results.sort(key=lambda x: x[0])
print("\n" + "=" * 64)
print("  🏆 최종 최적 조합 TOP 5")
print("=" * 64)
for rank, (turns, combo, order, mode) in enumerate(global_results[:5], 1):
    names = " · ".join(NAMES[c] for c in combo)
    mode_str = "auto" if mode == "auto" else " → ".join(NAMES[o] for o in order)
    print(f"\n  {rank}위  {turns}턴")
    print(f"     파티: {names}")
    print(f"     모드: {mode_str}")

best_turns, best_combo, best_order, best_mode = global_results[0]
print("\n" + "─" * 64)
print(f"✅ 절대 최단: {best_turns}턴")
print(f"   파티: {' · '.join(NAMES[c] for c in best_combo)}")
if best_mode == "manual_ordered":
    print(f"   순서: {' → '.join(NAMES[o] for o in best_order)}")
else:
    print(f"   모드: auto")
