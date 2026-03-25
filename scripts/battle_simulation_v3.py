"""BattleAgent 메타팀 시뮬레이션 v3.0 — 3×3 그리드 배치 분석

v2.0 대비 추가:
- 3×3 그리드 포지셔닝 시스템 분석
  - 행(Row)별 피해 보정: 전열 +5%, 후열 -10%
  - 행(Row)별 DEF 보정: 전열 +15%, 후열 -5%
  - 전열 보호: ENEMY_NEAR 타격 시 전열 우선
  - 넉백(KNOCKBACK): 전열→후열 강제 이동 + 벽꿍 대미지
  - 위치 기반 대미지 스케일링(DAMAGE_POSITION_SCALE)
- 팀별 그리드 배치 시각화
- 포지션 효율 분석 (전열/중열/후열별 생존율·피해량)

실행: py -3 -X utf8 scripts/battle_simulation_v3.py
"""
import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from battle.battle_engine import BattleEngine
from battle.battle_unit import BattleUnit
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


def get_team_grid_layout(factory):
    """팀 팩토리에서 3×3 그리드 배치 정보 추출."""
    chars = factory()
    row_names = {0: "전열", 1: "중열", 2: "후열"}
    layout = []
    for c in chars:
        r, col = c.tile_pos
        layout.append({
            'name': c.name,
            'role': c.role.value,
            'row': r,
            'col': col,
            'row_name': row_names.get(r, "?"),
        })
    return layout


def analyze_position_distribution(factory):
    """팀의 행별 유닛 분포 분석."""
    chars = factory()
    row_count = {0: 0, 1: 0, 2: 0}
    row_roles = {0: [], 1: [], 2: []}
    for c in chars:
        r = c.tile_pos[0]
        row_count[r] = row_count.get(r, 0) + 1
        row_roles[r].append(f"{c.name}({c.role.value})")
    return row_count, row_roles


def main():
    n = len(TEAMS)
    # 승률 매트릭스 (row=아군팀, col=적팀)
    matrix = [[None] * n for _ in range(n)]
    detail = [[None] * n for _ in range(n)]

    total_battles = n * (n - 1) * RUNS_PER_MATCHUP
    print("=" * 80)
    print(f"  BattleAgent 메타팀 시뮬레이션 v3.0 (3×3 그리드 포지셔닝)")
    print(f"  {n}팀 × {n-1}상대 × {RUNS_PER_MATCHUP}회 = {total_battles}전투")
    print("=" * 80)

    # ════════════════════════════════════════════════════════════
    # [0] 팀별 3×3 그리드 배치 시각화
    # ════════════════════════════════════════════════════════════
    print()
    print("=" * 80)
    print("  [0] 팀별 3×3 그리드 배치")
    print("=" * 80)

    row_names_kr = {0: "전열", 1: "중열", 2: "후열"}
    for team_name, factory in TEAMS:
        print(f"\n  ▸ {team_name}")
        row_count, row_roles = analyze_position_distribution(factory)
        grid = [["  ·  " for _ in range(3)] for _ in range(3)]
        chars = factory()
        for c in chars:
            r, col = c.tile_pos
            short = c.name[:4]
            grid[r][col] = f" {short:^4s}"

        print(f"         좌       중       우     (인원)")
        for row in range(3):
            members = ", ".join(row_roles[row]) if row_roles[row] else "-"
            print(f"    {row_names_kr[row]}  [{grid[row][0]}] [{grid[row][1]}] [{grid[row][2]}]  ({row_count[row]}명) {members}")

    # ════════════════════════════════════════════════════════════
    # 매치업 시뮬레이션
    # ════════════════════════════════════════════════════════════
    print()
    print("=" * 80)
    print("  시뮬레이션 진행중...")
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
    # [4] 포지셔닝 분석 — 행별 배치와 승률 상관관계
    # ════════════════════════════════════════════════════════════
    print()
    print("=" * 80)
    print("  [4] 포지셔닝 분석 — 행별 배치와 성적")
    print("=" * 80)

    print(f"\n  {'팀명':14s} {'전열':>5s} {'중열':>5s} {'후열':>5s}  {'전열 역할':30s} {'평균승률':>8s}")
    print("-" * 80)

    # 팀별 행 분포와 승률 매핑
    team_avg_map = {name: avg for name, avg, w, l, d in team_stats}
    position_data = []

    for team_name, factory in TEAMS:
        row_count, row_roles = analyze_position_distribution(factory)
        avg = team_avg_map.get(team_name, 0)
        front_roles = ", ".join(row_roles[0]) if row_roles[0] else "-"
        print(f"  {team_name:14s} {row_count[0]:>5d} {row_count[1]:>5d} {row_count[2]:>5d}  "
              f"{front_roles:30s} {avg:>7.1f}%")
        position_data.append({
            'team': team_name,
            'front': row_count[0],
            'mid': row_count[1],
            'back': row_count[2],
            'avg_wr': avg,
            'front_roles': front_roles,
        })

    # 전열 유닛 수와 승률 상관관계
    print()
    print("  ── 전열 유닛 수별 평균 승률 ──")
    front_groups = {}
    for pd in position_data:
        fc = pd['front']
        if fc not in front_groups:
            front_groups[fc] = []
        front_groups[fc].append(pd['avg_wr'])

    for fc in sorted(front_groups.keys()):
        avg_wr = sum(front_groups[fc]) / len(front_groups[fc])
        count = len(front_groups[fc])
        print(f"    전열 {fc}명 배치: 평균 {avg_wr:.1f}% ({count}팀)")

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

    # ════════════════════════════════════════════════════════════
    # [6] v2 vs v3 비교 (포지셔닝 효과)
    # ════════════════════════════════════════════════════════════
    print()
    print("=" * 80)
    print("  [6] 3×3 포지셔닝 시스템 효과 요약")
    print("=" * 80)
    print()
    print("  적용된 포지셔닝 메커닉:")
    print("    ✅ 행별 피해 보정: 전열 +5%, 후열 -10%")
    print("    ✅ 행별 DEF 보정: 전열 DEF +15%, 후열 DEF -5%")
    print("    ✅ 전열 보호: 전열 생존 시 ENEMY_NEAR 타격 전열 우선")
    print("    ✅ 넉백(KNOCKBACK): 전열→후열 이동 + 벽꿍 대미지(maxHP 10%)")
    print("    ✅ 위치 기반 대미지(DAMAGE_POSITION_SCALE): 전열 대상 추가 배율")
    print("    ✅ 후열 우선 타겟(ENEMY_BACK_ROW_PRIORITY): 후열→중열→전열 순 선택")
    print()

    # 전열에 탱커 배치한 팀 vs 안 한 팀 비교
    print("  ── 전열 탱커 배치 효과 ──")
    tank_front = []
    no_tank_front = []
    for pd in position_data:
        if 'defender' in pd['front_roles'].lower() or '수호' in pd['front_roles']:
            tank_front.append(pd['avg_wr'])
        else:
            no_tank_front.append(pd['avg_wr'])

    # 역할명으로 다시 분석
    for team_name, factory in TEAMS:
        chars = factory()
        has_tank_front = False
        for c in chars:
            if c.role.value == "defender" and c.tile_pos[0] == 0:
                has_tank_front = True
                break
        avg = team_avg_map.get(team_name, 0)
        if has_tank_front:
            tank_front.append(avg)
        # 중복 방지를 위해 위의 단순 문자열 체크 결과는 버림

    # 깔끔한 재분석
    tank_front_teams = []
    no_tank_front_teams = []
    for team_name, factory in TEAMS:
        chars = factory()
        has_tank_front = any(c.role.value == "defender" and c.tile_pos[0] == 0 for c in chars)
        avg = team_avg_map.get(team_name, 0)
        if has_tank_front:
            tank_front_teams.append((team_name, avg))
        else:
            no_tank_front_teams.append((team_name, avg))

    if tank_front_teams:
        avg_tank = sum(a for _, a in tank_front_teams) / len(tank_front_teams)
        print(f"    전열 탱커 배치팀 ({len(tank_front_teams)}팀): 평균 {avg_tank:.1f}%")
        for tn, a in tank_front_teams:
            print(f"      - {tn}: {a:.1f}%")
    if no_tank_front_teams:
        avg_no = sum(a for _, a in no_tank_front_teams) / len(no_tank_front_teams)
        print(f"    전열 탱커 미배치팀 ({len(no_tank_front_teams)}팀): 평균 {avg_no:.1f}%")

    print()
    print("  ═══════════════════════════════════════════════════")
    print("  시뮬레이션 v3.0 완료")
    print("  ═══════════════════════════════════════════════════")


if __name__ == "__main__":
    main()
