"""BattleAgent 메타팀 시뮬레이션 v2.0 — 실제 CTB 엔진 기반

기존 간이 모델(v1, 33% 정확도)을 대체하여
실제 BattleEngine으로 10대 메타팀 간 매치업을 수행한다.

실행: py -3 -X utf8 scripts/battle_simulation_v2.py
"""
import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from battle.battle_engine import BattleEngine
from battle.enums import BattleResult
from fixtures.test_data import (
    as_enemy_party,
    get_meta_v82_m01, get_meta_v82_m02, get_meta_v82_m03,
    get_meta_v82_m04, get_meta_v82_m05, get_meta_v82_m06,
    get_meta_v82_m07, get_meta_v82_m08, get_meta_v82_m09,
    get_meta_v82_m10,
)

# ════════════════════════════════════════════════════════════
# 메타팀 정의
# ════════════════════════════════════════════════════════════

TEAMS = [
    ("M01 화상연소", get_meta_v82_m01),
    ("M02 빙결제어", get_meta_v82_m02),
    ("M03 수면폭발", get_meta_v82_m03),
    ("M04 치명타학살", get_meta_v82_m04),
    ("M05 속도압도", get_meta_v82_m05),
    ("M06 철벽수호", get_meta_v82_m06),
    ("M07 출혈암살", get_meta_v82_m07),
    ("M08 보호막연합", get_meta_v82_m08),
    ("M09 디버프착취", get_meta_v82_m09),
    ("M10 혼성엘리트", get_meta_v82_m10),
]

RUNS_PER_MATCHUP = 20  # 매치업당 반복 횟수 (시드 변경)

# 기존 예상 상성 (메타 분석에서 도출)
EXPECTED = {
    ("M01", "M02"): "불리", ("M01", "M03"): "유리", ("M01", "M06"): "불리", ("M01", "M08"): "불리",
    ("M02", "M01"): "유리", ("M02", "M03"): "불리", ("M02", "M05"): "호각", ("M02", "M08"): "유리",
    ("M03", "M01"): "불리", ("M03", "M02"): "유리", ("M03", "M04"): "불리", ("M03", "M09"): "불리",
    ("M04", "M03"): "유리", ("M04", "M06"): "불리", ("M04", "M07"): "호각", ("M04", "M08"): "불리",
    ("M05", "M01"): "유리", ("M05", "M03"): "호각", ("M05", "M04"): "호각", ("M05", "M06"): "불리",
    ("M06", "M01"): "유리", ("M06", "M04"): "유리", ("M06", "M05"): "유리", ("M06", "M09"): "불리",
    ("M07", "M03"): "유리", ("M07", "M06"): "호각", ("M07", "M01"): "호각", ("M07", "M08"): "불리",
    ("M08", "M04"): "유리", ("M08", "M07"): "유리", ("M08", "M02"): "불리", ("M08", "M09"): "불리",
    ("M09", "M06"): "유리", ("M09", "M08"): "유리", ("M09", "M02"): "불리", ("M09", "M05"): "불리",
}


def run_matchup(ally_factory, enemy_factory, runs=RUNS_PER_MATCHUP):
    """매치업 N회 실행 → (승, 패, 무) 반환."""
    wins, losses, draws = 0, 0, 0
    for seed in range(runs):
        try:
            allies = ally_factory()
            enemies = as_enemy_party(enemy_factory())
            engine = BattleEngine(
                ally_units=allies,
                enemy_units=enemies,
                seed=seed,
            )
            result = engine.run()
            if result == BattleResult.ALLY_WIN:
                wins += 1
            elif result == BattleResult.ENEMY_WIN:
                losses += 1
            else:
                draws += 1
        except Exception as e:
            print(f"    ⚠ seed={seed} 오류: {e}")
            draws += 1
    return wins, losses, draws


def main():
    n = len(TEAMS)
    # 승률 매트릭스 (row=아군팀, col=적팀)
    matrix = [[None] * n for _ in range(n)]
    detail = [[None] * n for _ in range(n)]

    total_battles = n * (n - 1) * RUNS_PER_MATCHUP
    print("=" * 80)
    print(f"  BattleAgent 메타팀 시뮬레이션 v2.0 (실제 CTB 엔진)")
    print(f"  {n}팀 × {n-1}상대 × {RUNS_PER_MATCHUP}회 = {total_battles}전투")
    print("=" * 80)

    start = time.time()
    battle_count = 0

    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            ally_name, ally_factory = TEAMS[i]
            enemy_name, enemy_factory = TEAMS[j]
            w, l, d = run_matchup(ally_factory, enemy_factory)
            win_rate = w / RUNS_PER_MATCHUP * 100
            matrix[i][j] = win_rate
            detail[i][j] = (w, l, d)
            battle_count += RUNS_PER_MATCHUP
            elapsed = time.time() - start
            pct = battle_count / total_battles * 100
            print(f"\r  진행: {battle_count}/{total_battles} ({pct:.0f}%) "
                  f"| {ally_name} vs {enemy_name}: {win_rate:.0f}% "
                  f"| 경과 {elapsed:.1f}s", end="", flush=True)

    elapsed = time.time() - start
    print(f"\n\n  완료: {total_battles}전투, {elapsed:.1f}초 소요\n")

    # ════════════════════════════════════════════════════════════
    # [1] 10×10 승률 매트릭스
    # ════════════════════════════════════════════════════════════
    print("=" * 80)
    print("  [1] 10×10 승률 매트릭스 (%)")
    print("=" * 80)

    short_names = [t[0][:7] for t in TEAMS]
    header = f"{'':14s}" + "".join(f"{s:>8s}" for s in short_names)
    print(header)
    print("-" * len(header))

    for i in range(n):
        row = f"{TEAMS[i][0]:14s}"
        for j in range(n):
            if i == j:
                row += f"{'---':>8s}"
            else:
                wr = matrix[i][j]
                row += f"{wr:>7.0f}%"
        print(row)

    # ════════════════════════════════════════════════════════════
    # [2] 팀별 종합 성적
    # ════════════════════════════════════════════════════════════
    print()
    print("=" * 80)
    print("  [2] 팀별 종합 성적")
    print("=" * 80)

    team_stats = []
    for i in range(n):
        total_w, total_l, total_d = 0, 0, 0
        rates = []
        for j in range(n):
            if i == j:
                continue
            w, l, d = detail[i][j]
            total_w += w
            total_l += l
            total_d += d
            rates.append(matrix[i][j])
        avg_rate = sum(rates) / len(rates) if rates else 0
        team_stats.append((TEAMS[i][0], avg_rate, total_w, total_l, total_d))

    team_stats.sort(key=lambda x: -x[1])

    print(f"  {'팀명':14s} {'평균승률':>8s} {'승':>5s} {'패':>5s} {'무':>5s}")
    print("-" * 50)
    for name, avg, w, l, d in team_stats:
        print(f"  {name:14s} {avg:>7.1f}% {w:>5d} {l:>5d} {d:>5d}")

    # ════════════════════════════════════════════════════════════
    # [3] 티어 판정
    # ════════════════════════════════════════════════════════════
    print()
    print("=" * 80)
    print("  [3] 티어 판정")
    print("=" * 80)

    for name, avg, w, l, d in team_stats:
        if avg >= 70:
            tier = "★ S"
        elif avg >= 55:
            tier = "☆ A"
        elif avg >= 40:
            tier = "  B"
        else:
            tier = "  C"
        bar = "█" * int(avg / 5)
        print(f"  [{tier}] {name:14s} {avg:5.1f}% {bar}")

    # ════════════════════════════════════════════════════════════
    # [4] 기존 예상 상성 비교
    # ════════════════════════════════════════════════════════════
    print()
    print("=" * 80)
    print("  [4] 기존 예상 상성 vs 실제 승률")
    print("=" * 80)

    match_count = 0
    correct = 0

    print(f"  {'매치업':34s} {'예상':>6s} {'실제':>7s} {'판정':>6s}")
    print("-" * 60)

    for (ak, dk), expected in sorted(EXPECTED.items()):
        # 팀 인덱스 찾기
        ai = next(i for i, t in enumerate(TEAMS) if t[0].startswith(ak))
        di = next(i for i, t in enumerate(TEAMS) if t[0].startswith(dk))
        wr = matrix[ai][di]

        if expected == "유리":
            actual_match = wr >= 55
        elif expected == "불리":
            actual_match = wr < 45
        else:  # 호각
            actual_match = 40 <= wr <= 60

        match_count += 1
        if actual_match:
            correct += 1
            mark = "✓"
        else:
            mark = "✗"

        print(f"  {TEAMS[ai][0]:14s} vs {TEAMS[di][0]:14s}  {expected:>4s}  {wr:>5.0f}%  {mark}")

    rate = correct / match_count * 100 if match_count else 0
    print(f"\n  일치율: {correct}/{match_count} ({rate:.1f}%)")

    # ════════════════════════════════════════════════════════════
    # [5] 밸런스 경고
    # ════════════════════════════════════════════════════════════
    print()
    print("=" * 80)
    print("  [5] 밸런스 경고")
    print("=" * 80)

    warnings = []
    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            wr = matrix[i][j]
            if wr >= 85:
                warnings.append(("🔴", TEAMS[i][0], TEAMS[j][0], wr, "압도적 유리 — 너프 필요"))
            elif wr <= 15:
                warnings.append(("🔴", TEAMS[i][0], TEAMS[j][0], wr, "압도적 불리 — 버프 필요"))
            elif wr >= 75:
                warnings.append(("🟡", TEAMS[i][0], TEAMS[j][0], wr, "유리 편향"))
            elif wr <= 25:
                warnings.append(("🟡", TEAMS[i][0], TEAMS[j][0], wr, "불리 편향"))

    if warnings:
        for icon, a, d, wr, msg in sorted(warnings, key=lambda x: -x[3]):
            print(f"  {icon} {a} vs {d}: {wr:.0f}% — {msg}")
    else:
        print("  ✅ 극단적 매치업 없음 (모든 승률 25-75% 범위)")

    # 팀 평균 승률 경고
    print()
    for name, avg, w, l, d in team_stats:
        if avg >= 75:
            print(f"  🔴 {name} 평균승률 {avg:.1f}% — 전체적 너프 필요")
        elif avg <= 25:
            print(f"  🔴 {name} 평균승률 {avg:.1f}% — 전체적 버프 필요")


if __name__ == "__main__":
    main()
