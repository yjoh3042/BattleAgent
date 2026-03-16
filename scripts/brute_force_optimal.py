"""brute_force_optimal.py — 전수 탐색: 9명 풀 × C(9,5)=126 조합 × 5!=120 얼티밋 순서

CRI 15% / PEN 0% 룰 통일 이후 최적 파티 + 얼티밋 순서 재탐색.

캐릭터 풀 (상위 2개 메타 구성원 합집합 9명):
  루미나(c600), 에레보스(c601), 시트리, 아르테미스, 다누,
  이브, 쿠바바, 엘리시온, 아우로라

적군: 5마리 봉제인형 (get_enemies_5)

Phase 1: 126 조합 × 10 시드 → auto 모드 승률+평균턴 기준 상위 추출
Phase 2: 상위 조합 × 5!=120 얼티밋 순서 × 10 시드 → 최적 순서 탐색

실행: py -3 -X utf8 scripts/brute_force_optimal.py
"""
import sys, os, itertools, time, json
from collections import defaultdict

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from battle.battle_engine import BattleEngine
from battle.enums import BattleResult
from fixtures.test_data import (
    make_c600, make_c601, make_sitri, make_artemis, make_danu,
    make_eve, make_kubaba, make_elysion, make_aurora,
    get_enemies_5,
)

# ── 캐릭터 풀 (9명) ──────────────────────────────────────────────────────
CHAR_POOL = [
    ("루미나",     make_c600),
    ("에레보스",   make_c601),
    ("시트리",     make_sitri),
    ("아르테미스", make_artemis),
    ("다누",       make_danu),
    ("이브",       make_eve),
    ("쿠바바",     make_kubaba),
    ("엘리시온",   make_elysion),
    ("아우로라",   make_aurora),
]

SEEDS_PHASE1 = 10      # Phase 1: 조합 탐색 시드 수
SEEDS_PHASE2 = 10      # Phase 2: 순서 탐색 시드 수
TOP_N = 20              # Phase 2로 넘길 상위 조합 수
PARTY_SIZE = 5


def run_battle(ally_factories, enemy_factory, seed, ultimate_mode="auto", ultimate_order=None):
    """한 전투 실행, (result, turn_count) 반환"""
    allies = [f() for f in ally_factories]
    enemies = enemy_factory()
    kwargs = dict(
        ally_units=allies,
        enemy_units=enemies,
        allow_active=True,
        allow_ultimate=True,
        ultimate_mode=ultimate_mode,
        seed=seed,
    )
    if ultimate_order:
        kwargs["ultimate_order"] = ultimate_order
    engine = BattleEngine(**kwargs)
    result = engine.run()
    return result, engine.turn_count


def evaluate_combo(factories, seeds, ultimate_mode="auto", ultimate_order=None):
    """여러 시드로 평가 → (승수, 평균턴, 턴리스트)"""
    wins = 0
    turns = []
    for s in range(seeds):
        r, t = run_battle(factories, get_enemies_5, s, ultimate_mode, ultimate_order)
        if r == BattleResult.ALLY_WIN:
            wins += 1
            turns.append(t)
    avg_turn = sum(turns) / len(turns) if turns else 999
    return wins, avg_turn, turns


def phase1_combo_search():
    """Phase 1: C(9,5)=126 조합 전수 탐색 (auto 모드)"""
    print("=" * 80)
    print(f"  Phase 1: 파티 조합 전수 탐색  C({len(CHAR_POOL)},{PARTY_SIZE}) = "
          f"{len(list(itertools.combinations(range(len(CHAR_POOL)), PARTY_SIZE)))} 조합")
    print(f"  시드: {SEEDS_PHASE1}개, 적군: 봉제인형 5마리, 모드: auto")
    print("=" * 80)

    results = []
    combos = list(itertools.combinations(range(len(CHAR_POOL)), PARTY_SIZE))
    total = len(combos)
    t0 = time.time()

    for idx, combo_idx in enumerate(combos):
        names = [CHAR_POOL[i][0] for i in combo_idx]
        factories = [CHAR_POOL[i][1] for i in combo_idx]

        wins, avg_turn, turn_list = evaluate_combo(factories, SEEDS_PHASE1)
        wr = wins / SEEDS_PHASE1
        min_turn = min(turn_list) if turn_list else 999
        max_turn = max(turn_list) if turn_list else 999

        results.append({
            "idx": combo_idx,
            "names": names,
            "factories": factories,
            "wins": wins,
            "wr": wr,
            "avg_turn": avg_turn,
            "min_turn": min_turn,
            "max_turn": max_turn,
            "turns": turn_list,
        })

        if (idx + 1) % 20 == 0 or idx == total - 1:
            elapsed = time.time() - t0
            print(f"  [{idx+1:3d}/{total}] {elapsed:.1f}s  "
                  f"현재: {'/'.join(names)}  승률={wr*100:.0f}% 평균={avg_turn:.1f}턴")

    # 정렬: 승률 내림 → 평균턴 오름 → 최소턴 오름
    results.sort(key=lambda x: (-x["wr"], x["avg_turn"], x["min_turn"]))

    # 결과 출력
    print()
    print("─" * 80)
    print(f"  Phase 1 결과: 전체 {total} 조합")
    print("─" * 80)
    print(f"  {'순위':<4} {'조합':<40} {'승률':>6} {'평균턴':>7} {'최소':>5} {'최대':>5}")
    print("  " + "-" * 76)

    for rank, r in enumerate(results[:30], 1):
        combo_str = ", ".join(r["names"])
        print(f"  {rank:>2}위  {combo_str:<38} {r['wr']*100:>5.0f}%  {r['avg_turn']:>6.1f}  "
              f"{r['min_turn']:>4}  {r['max_turn']:>4}")

    # 승리 0인 조합 수
    zero_win = sum(1 for r in results if r["wins"] == 0)
    full_win = sum(1 for r in results if r["wins"] == SEEDS_PHASE1)
    print(f"\n  전승({SEEDS_PHASE1}/{SEEDS_PHASE1}): {full_win}개 | 전패(0승): {zero_win}개")
    print(f"  소요시간: {time.time()-t0:.1f}s")

    return results


def phase2_order_search(top_combos):
    """Phase 2: 상위 조합 × 5!=120 얼티밋 순서 전수 탐색"""
    print()
    print("=" * 80)
    print(f"  Phase 2: 얼티밋 순서 전수 탐색  상위 {len(top_combos)} 조합 × 5!={120} 순서")
    print(f"  시드: {SEEDS_PHASE2}개, 모드: manual_ordered (setting)")
    print("=" * 80)

    all_results = []
    t0 = time.time()

    for ci, combo in enumerate(top_combos):
        names = combo["names"]
        factories = combo["factories"]

        # 캐릭터 ID 추출
        sample_units = [f() for f in factories]
        char_ids = [u.id for u in sample_units]

        best_order = None
        best_avg = 999
        best_min = 999
        order_results = []

        for perm in itertools.permutations(char_ids):
            wins, avg_turn, turn_list = evaluate_combo(
                factories, SEEDS_PHASE2,
                ultimate_mode="setting", ultimate_order=list(perm)
            )
            min_t = min(turn_list) if turn_list else 999
            order_results.append({
                "order": list(perm),
                "wins": wins,
                "avg_turn": avg_turn,
                "min_turn": min_t,
            })

            if wins > 0 and avg_turn < best_avg:
                best_avg = avg_turn
                best_min = min_t
                best_order = list(perm)

        # 순서 결과 정렬
        order_results.sort(key=lambda x: (-x["wins"], x["avg_turn"]))

        # ID → 이름 매핑
        id_to_name = {u.id: n for u, n in zip(sample_units, names)}
        best_order_names = [id_to_name.get(oid, oid) for oid in best_order] if best_order else []

        entry = {
            "names": names,
            "combo_wr": combo["wr"],
            "combo_avg": combo["avg_turn"],
            "best_order": best_order,
            "best_order_names": best_order_names,
            "best_avg": best_avg,
            "best_min": best_min,
            "top3_orders": order_results[:3],
            "worst3_orders": order_results[-3:],
            "total_orders": len(order_results),
            "id_to_name": id_to_name,
        }
        all_results.append(entry)

        elapsed = time.time() - t0
        print(f"  [{ci+1:2d}/{len(top_combos)}] {elapsed:.1f}s  "
              f"{'/'.join(names)}  최적순서={'/'.join(best_order_names)} "
              f"평균={best_avg:.1f}턴 최소={best_min}턴")

    # 최종 결과 정렬
    all_results.sort(key=lambda x: (x["best_avg"], x["best_min"]))

    print()
    print("─" * 90)
    print(f"  Phase 2 최종 결과: 최적 파티 + 얼티밋 순서 TOP {min(10, len(all_results))}")
    print("─" * 90)
    print(f"  {'순위':<4} {'조합':<32} {'최적 얼티밋 순서':<32} {'평균턴':>7} {'최소':>5}")
    print("  " + "-" * 86)

    for rank, r in enumerate(all_results[:10], 1):
        combo_str = ", ".join(r["names"])
        order_str = " → ".join(r["best_order_names"])
        print(f"  {rank:>2}위  {combo_str:<30} {order_str:<30} {r['best_avg']:>6.1f}  {r['best_min']:>4}")

    print(f"\n  소요시간: {time.time()-t0:.1f}s")

    return all_results


def save_results(phase1, phase2):
    """결과를 JSON으로 저장"""
    output = {
        "config": {
            "pool_size": len(CHAR_POOL),
            "party_size": PARTY_SIZE,
            "seeds_phase1": SEEDS_PHASE1,
            "seeds_phase2": SEEDS_PHASE2,
            "pool": [name for name, _ in CHAR_POOL],
            "rules": "cri_ratio=0.15, penetration=0.0 (2026-03-13 통일)",
        },
        "phase1_top10": [
            {
                "rank": i + 1,
                "names": r["names"],
                "win_rate": r["wr"],
                "avg_turn": r["avg_turn"],
                "min_turn": r["min_turn"],
                "max_turn": r["max_turn"],
            }
            for i, r in enumerate(phase1[:10])
        ],
        "phase2_top10": [
            {
                "rank": i + 1,
                "names": r["names"],
                "best_order": r["best_order_names"],
                "best_avg_turn": r["best_avg"],
                "best_min_turn": r["best_min"],
            }
            for i, r in enumerate(phase2[:10])
        ],
    }
    path = os.path.join(os.path.dirname(__file__), "..", "data", "brute_force_result.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"\n  결과 저장: {path}")


def main():
    print()
    print("╔══════════════════════════════════════════════════════════════════════╗")
    print("║  BattleAgent 브루트포스 최적 파티 탐색                                ║")
    print("║  풀: 9명 (OP듀오+극딜버스트 합집합)                                   ║")
    print("║  룰: CRI 15% / PEN 0% 통일 (2026-03-13)                            ║")
    print("╚══════════════════════════════════════════════════════════════════════╝")

    total_t0 = time.time()

    # Phase 1
    phase1 = phase1_combo_search()

    # Phase 2: 상위 TOP_N 조합 (승리 있는 것만)
    top = [r for r in phase1 if r["wins"] > 0][:TOP_N]
    phase2 = phase2_order_search(top)

    # 최종 요약
    print()
    print("═" * 90)
    print("  ★ 최종 결과: 최적 파티 조합 + 얼티밋 발동 순서")
    print("═" * 90)

    if phase2:
        best = phase2[0]
        print(f"  파티:     {' / '.join(best['names'])}")
        print(f"  얼티순서: {' → '.join(best['best_order_names'])}")
        print(f"  평균턴:   {best['best_avg']:.1f}")
        print(f"  최소턴:   {best['best_min']}")
        print()

        # 상위 5개 비교
        print(f"  {'순위':<4} {'평균턴':>7} {'최소':>5}  {'조합':>30}   {'얼티밋 순서'}")
        print("  " + "-" * 86)
        for rank, r in enumerate(phase2[:5], 1):
            combo = " / ".join(r["names"])
            order = " → ".join(r["best_order_names"])
            print(f"  {rank:>2}위  {r['best_avg']:>6.1f}  {r['best_min']:>4}  {combo}   {order}")

    save_results(phase1, phase2)

    total_elapsed = time.time() - total_t0
    print(f"\n  총 소요시간: {total_elapsed:.1f}s")


if __name__ == "__main__":
    main()
