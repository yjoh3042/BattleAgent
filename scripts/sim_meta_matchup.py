"""Meta Matchup Simulation
12개 메타 조합끼리 전면 대전, 승률 매트릭스 + 추가 분석 출력.
실행: py -X utf8 scripts/sim_meta_matchup.py  (C:\\Ai\\BattleAgent\\ 에서)
"""
import sys
import os
import dataclasses
import math

# src 를 모듈 경로에 추가
SRC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
sys.path.insert(0, SRC_DIR)

from battle.battle_engine import BattleEngine
from battle.enums import BattleResult

# ──────────────────────────────────────────────
# 메타 정의 (각 배틀마다 새 인스턴스 생성)
# ──────────────────────────────────────────────

def meta1():
    from fixtures.test_data import make_dabi, make_kararatri, make_semele, make_jiva, make_salmakis
    return [make_dabi(), make_kararatri(), make_semele(), make_jiva(), make_salmakis()]

def meta2():
    from fixtures.test_data import make_bari, make_dogyehwa, make_sangah, make_thisbe, make_elysion
    return [make_bari(), make_dogyehwa(), make_sangah(), make_thisbe(), make_elysion()]

def meta3():
    from fixtures.test_data import make_batory, make_mircalla, make_morgan, make_aurora, make_danu
    return [make_batory(), make_mircalla(), make_morgan(), make_aurora(), make_danu()]

def meta4():
    from fixtures.test_data import make_pan, make_oneiroi, make_gumiho, make_brownie, make_metis
    return [make_pan(), make_oneiroi(), make_gumiho(), make_brownie(), make_metis()]

def meta5():
    from fixtures.test_data import make_eve, make_sangah, make_thisbe, make_salmakis, make_brownie
    return [make_eve(), make_sangah(), make_thisbe(), make_salmakis(), make_brownie()]

def meta6():
    from fixtures.test_data import make_ashtoreth, make_artemis, make_aurora, make_grilla, make_sitri
    return [make_ashtoreth(), make_artemis(), make_aurora(), make_grilla(), make_sitri()]

def meta7():
    from fixtures.test_data import make_kubaba, make_tiwaz, make_artemis, make_kararatri, make_yuna
    return [make_kubaba(), make_tiwaz(), make_artemis(), make_kararatri(), make_yuna()]

def meta8():
    from fixtures.test_data import make_deresa, make_frey, make_ragaraja, make_metis, make_jiva
    return [make_deresa(), make_frey(), make_ragaraja(), make_metis(), make_jiva()]

def meta9():
    from fixtures.test_data import make_kubaba, make_artemis, make_anubis, make_frey, make_yuna
    return [make_kubaba(), make_artemis(), make_anubis(), make_frey(), make_yuna()]

def meta10():
    from fixtures.test_data import make_grilla, make_miriam, make_batory, make_aurora, make_brownie
    return [make_grilla(), make_miriam(), make_batory(), make_aurora(), make_brownie()]

def meta11():
    from fixtures.test_data import make_pan, make_dabi, make_semele, make_aurora, make_jiva
    return [make_pan(), make_dabi(), make_semele(), make_aurora(), make_jiva()]

def meta12():
    from fixtures.test_data import make_morgan, make_mircalla, make_salmakis, make_sangah, make_elysion
    return [make_morgan(), make_mircalla(), make_salmakis(), make_sangah(), make_elysion()]


METAS = [
    (meta1,  "화상연계"),
    (meta2,  "독정원  "),
    (meta3,  "출혈폭딜"),
    (meta4,  "CC잠금  "),
    (meta5,  "속도처형"),
    (meta6,  "크리폭딜"),
    (meta7,  "방어무력"),
    (meta8,  "철벽반격"),
    (meta9,  "풀암속성"),
    (meta10, "야성해방"),
    (meta11, "화상수면"),
    (meta12, "속도출혈"),
]

N_SEEDS = 50   # 시드 수 (0 ~ N_SEEDS-1)


def flip_to_enemy(chars):
    """CharacterData 리스트를 side='enemy'로 복사."""
    return [dataclasses.replace(c, side="enemy") for c in chars]


def wilson_interval(wins, n, z=1.96):
    """Wilson score 95% 신뢰구간 반환 (lower, upper)."""
    if n == 0:
        return 0.0, 0.0
    p = wins / n
    center = (p + z**2 / (2 * n)) / (1 + z**2 / n)
    margin = z * math.sqrt(p * (1 - p) / n + z**2 / (4 * n**2)) / (1 + z**2 / n)
    return max(0.0, center - margin), min(1.0, center + margin)


def progress_bar(current, total, width=20):
    filled = int(width * current / total)
    bar = "=" * filled + " " * (width - filled)
    return f"[{bar}] {current}/{total}"


def run_matchup(ally_factory, enemy_factory, n_seeds=N_SEEDS, show_progress=False, label=""):
    """ally_factory vs enemy_factory 를 n_seeds 번 돌려
    (ally_wins, enemy_wins, timeouts, turn_counts) 반환."""
    ally_wins = 0
    enemy_wins = 0
    timeouts = 0
    turn_counts = []

    for seed in range(n_seeds):
        ally_chars  = ally_factory()
        enemy_chars = flip_to_enemy(enemy_factory())

        engine = BattleEngine(
            ally_units=ally_chars,
            enemy_units=enemy_chars,
            seed=seed,
        )
        result = engine.run()
        turn_counts.append(engine.turn_count)

        if result == BattleResult.ALLY_WIN:
            ally_wins += 1
        elif result == BattleResult.ENEMY_WIN:
            enemy_wins += 1
        else:
            timeouts += 1

        if show_progress:
            bar = progress_bar(seed + 1, n_seeds)
            print(f"\r  {label} {bar} 완료", end="", flush=True)

    if show_progress:
        print()  # 줄바꿈

    return ally_wins, enemy_wins, timeouts, turn_counts


def compute_avg_spd(meta_factory):
    """메타 팩토리에서 평균 SPD, 최고/최저 유닛을 반환."""
    chars = meta_factory()
    spd_list = [(c.stats.spd, c.name) for c in chars]
    avg = sum(s for s, _ in spd_list) / len(spd_list)
    max_unit = max(spd_list, key=lambda x: x[0])
    min_unit = min(spd_list, key=lambda x: x[0])
    return avg, max_unit, min_unit


def find_rps_cycles(win_matrix, n, threshold=0.55):
    """A→B 이기면 directed edge. 3-사이클 탐지."""
    # directed adjacency: edges[i] = set of j where i beats j (win_rate > threshold)
    edges = [set() for _ in range(n)]
    for i in range(n):
        for j in range(n):
            if i != j and win_matrix[i][j] > threshold:
                edges[i].add(j)

    cycles = []
    seen = set()
    for a in range(n):
        for b in edges[a]:
            for c in edges[b]:
                if a in edges[c] and len({a, b, c}) == 3:
                    key = tuple(sorted([a, b, c]))
                    if key not in seen:
                        seen.add(key)
                        cycles.append((a, b, c))
    return cycles


def main():
    n = len(METAS)

    # win_rate[i][j]  = META i (ally) vs META j (enemy) 의 아군 승률
    # avg_turns[i][j] = 평균 전투 턴 수
    # raw[i][j]       = (W, L, T)
    # raw_wins[i][j]  = 순수 ally_wins (신뢰구간용)
    win_rate  = [[-1.0] * n for _ in range(n)]
    avg_turns = [[-1.0] * n for _ in range(n)]
    raw       = [[None]   * n for _ in range(n)]
    raw_wins  = [[-1]     * n for _ in range(n)]

    total_matchups = n * (n - 1)
    done = 0

    print(f"=== Meta Matchup Simulation ({N_SEEDS} seeds per match) ===")
    print(f"    총 {total_matchups} 매치업 × {N_SEEDS} = {total_matchups * N_SEEDS:,}번 전투\n")

    for i in range(n):
        for j in range(n):
            if i == j:
                continue

            ally_f,  ally_label  = METAS[i]
            enemy_f, enemy_label = METAS[j]

            label = f"M{i+1:02d} vs M{j+1:02d}"
            w, l, t, turns = run_matchup(
                ally_f, enemy_f, N_SEEDS,
                show_progress=True,
                label=label,
            )
            raw[i][j]      = (w, l, t)
            raw_wins[i][j] = w

            wr = (w + 0.5 * t) / N_SEEDS
            win_rate[i][j]  = wr
            avg_turns[i][j] = sum(turns) / len(turns)

            done += 1
            print(f"  {label}: {w}W / {l}L / {t}T  → {wr*100:.1f}%  avg_turn={avg_turns[i][j]:.1f}")

        print()

    # ──────────────────────────────────────────
    # 승률 매트릭스
    # ──────────────────────────────────────────
    print("\n" + "=" * 88)
    print("  WIN-RATE MATRIX  (row = ally, col = enemy)")
    print("  값: row 메타가 col 메타를 상대할 때 row의 승률")
    print("=" * 88)

    header_labels = [f"M{j+1:02d}" for j in range(n)]
    col_w = 6
    row_label_w = 14

    print(f"  {'':>{row_label_w}}", end="")
    for lbl in header_labels:
        print(f"  {lbl:>{col_w-2}}", end="")
    print()
    print(f"  {'':>{row_label_w}}", end="")
    for _ in header_labels:
        print(f"  {'----':>{col_w-2}}", end="")
    print()

    for i in range(n):
        _, label = METAS[i]
        row_tag = f"M{i+1:02d} {label}"
        print(f"  {row_tag:>{row_label_w}}", end="")
        for j in range(n):
            if i == j:
                cell = "  -  "
            else:
                wr = win_rate[i][j]
                cell = f"{wr*100:.1f}%"
            print(f"  {cell:>{col_w}}", end="")
        print()

    # ──────────────────────────────────────────
    # 평균 승률 랭킹
    # ──────────────────────────────────────────
    avg_wr = []
    for i in range(n):
        vals = [win_rate[i][j] for j in range(n) if j != i]
        avg_wr.append(sum(vals) / len(vals))

    print("\n" + "=" * 88)
    print("  평균 승률 랭킹 (전체 matchup 기준)")
    print("=" * 88)
    ranked = sorted(range(n), key=lambda i: avg_wr[i], reverse=True)
    for rank, i in enumerate(ranked, 1):
        _, lbl = METAS[i]
        print(f"  {rank:>2}위  M{i+1:02d} {lbl}  {avg_wr[i]*100:.1f}%")

    # ──────────────────────────────────────────
    # 카운터 / 취약점
    # ──────────────────────────────────────────
    COUNTER_THRESH = 0.70
    WEAK_THRESH    = 0.30

    counters    = []
    weaknesses  = []
    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            wr = win_rate[i][j]
            _, li = METAS[i]
            _, lj = METAS[j]
            if wr >= COUNTER_THRESH:
                counters.append((wr, i, j, li, lj))
            if wr <= WEAK_THRESH:
                weaknesses.append((wr, i, j, li, lj))

    print("\n" + "=" * 88)
    print(f"  강한 카운터 (승률 >= {int(COUNTER_THRESH*100)}%)")
    print("=" * 88)
    if counters:
        for wr, i, j, li, lj in sorted(counters, reverse=True):
            print(f"  M{i+1:02d} {li.strip()} vs M{j+1:02d} {lj.strip()}: {wr*100:.1f}%")
    else:
        print("  없음")

    print("\n" + "=" * 88)
    print(f"  심각한 취약점 (승률 <= {int(WEAK_THRESH*100)}%)")
    print("=" * 88)
    if weaknesses:
        for wr, i, j, li, lj in sorted(weaknesses):
            print(f"  M{i+1:02d} {li.strip()} vs M{j+1:02d} {lj.strip()}: {wr*100:.1f}%")
    else:
        print("  없음")

    # ══════════════════════════════════════════
    # A. 평균 전투 턴 수 매트릭스
    # ══════════════════════════════════════════
    print("\n" + "=" * 88)
    print("  A. 평균 전투 턴 수 매트릭스  (row = ally, col = enemy)")
    print("=" * 88)

    print(f"  {'':>{row_label_w}}", end="")
    for lbl in header_labels:
        print(f"  {lbl:>{col_w-1}}", end="")
    print()
    print(f"  {'':>{row_label_w}}", end="")
    for _ in header_labels:
        print(f"  {'-----':>{col_w-1}}", end="")
    print()

    for i in range(n):
        _, label = METAS[i]
        row_tag = f"M{i+1:02d} {label}"
        print(f"  {row_tag:>{row_label_w}}", end="")
        for j in range(n):
            if i == j:
                cell = "  -  "
            else:
                t = avg_turns[i][j]
                cell = f"{t:.1f}"
            print(f"  {cell:>{col_w}}", end="")
        print()

    # ══════════════════════════════════════════
    # B. 승률 표준편차 (매치업별 신뢰도)
    # ══════════════════════════════════════════
    print("\n" + "=" * 88)
    print("  B. 승률 표준편차 (매치업별)")
    print("  표준편차가 낮을수록 예측 가능, 높을수록 시드 의존적(운빨)")
    print(f"  {'META':<16} {'평균 승률':>10} {'표준편차':>10} {'최고 승률':>10} {'최저 승률':>10}")
    print("  " + "-" * 60)
    print("=" * 88)

    for i in range(n):
        _, lbl = METAS[i]
        vals = [win_rate[i][j] for j in range(n) if j != i]
        mean = sum(vals) / len(vals)
        variance = sum((v - mean) ** 2 for v in vals) / len(vals)
        std = math.sqrt(variance)
        max_v = max(vals)
        min_v = min(vals)
        tag = f"M{i+1:02d} {lbl}"
        print(f"  {tag:<16} {mean*100:>9.1f}% {std*100:>9.1f}% {max_v*100:>9.1f}% {min_v*100:>9.1f}%")

    # ══════════════════════════════════════════
    # C. 메타별 평균 SPD
    # ══════════════════════════════════════════
    print("\n" + "=" * 88)
    print("  C. 메타별 평균 SPD")
    print(f"  {'META':<16} {'평균 SPD':>10} {'최고 SPD 유닛':>18} {'최저 SPD 유닛':>18}")
    print("  " + "-" * 65)
    print("=" * 88)

    for i in range(n):
        factory, lbl = METAS[i]
        avg_spd, max_unit, min_unit = compute_avg_spd(factory)
        tag = f"M{i+1:02d} {lbl}"
        max_str = f"{max_unit[1]}({max_unit[0]})"
        min_str = f"{min_unit[1]}({min_unit[0]})"
        print(f"  {tag:<16} {avg_spd:>10.1f} {max_str:>18} {min_str:>18}")

    # ══════════════════════════════════════════
    # D. 장기전 / 단기전 분류
    # ══════════════════════════════════════════
    print("\n" + "=" * 88)
    print("  D. 장기전 / 단기전 분류 (메타별 평균 전투 종료 턴)")
    print("  기준: 단기전 < 40턴 | 중기전 40~80턴 | 장기전 > 80턴")
    print("=" * 88)

    short_metas  = []
    mid_metas    = []
    long_metas   = []

    for i in range(n):
        _, lbl = METAS[i]
        all_turns = [avg_turns[i][j] for j in range(n) if j != i] + \
                    [avg_turns[j][i] for j in range(n) if j != i]
        meta_avg = sum(all_turns) / len(all_turns)
        entry = (meta_avg, i, lbl)
        if meta_avg < 40:
            short_metas.append(entry)
        elif meta_avg <= 80:
            mid_metas.append(entry)
        else:
            long_metas.append(entry)

    def print_category(name, items):
        print(f"\n  [{name}]")
        if items:
            for avg, i, lbl in sorted(items):
                print(f"    M{i+1:02d} {lbl}  평균 {avg:.1f}턴")
        else:
            print("    없음")

    print_category("단기전 (< 40턴)",   short_metas)
    print_category("중기전 (40~80턴)", mid_metas)
    print_category("장기전 (> 80턴)",   long_metas)

    # ══════════════════════════════════════════
    # E. 통계적 유의성 (Wilson score 95% CI)
    # ══════════════════════════════════════════
    print("\n" + "=" * 88)
    print("  E. 통계적 유의성 - 핵심 상성 95% 신뢰구간 (승률 >60% 또는 <40%)")
    print(f"  {'매치업':<30} {'승률':>7} {'95% CI 하한':>12} {'95% CI 상한':>12}")
    print("  " + "-" * 65)
    print("=" * 88)

    sig_entries = []
    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            wr = win_rate[i][j]
            if wr > 0.60 or wr < 0.40:
                w = raw_wins[i][j]
                lo, hi = wilson_interval(w, N_SEEDS)
                _, li = METAS[i]
                _, lj = METAS[j]
                sig_entries.append((wr, i, j, li, lj, lo, hi))

    for wr, i, j, li, lj, lo, hi in sorted(sig_entries, key=lambda x: -x[0]):
        label = f"M{i+1:02d} {li.strip()} vs M{j+1:02d} {lj.strip()}"
        print(f"  {label:<30} {wr*100:>6.1f}% [{lo*100:>5.1f}%, {hi*100:>5.1f}%]")

    if not sig_entries:
        print("  유의미한 상성 없음")

    # ══════════════════════════════════════════
    # F. Rock-Paper-Scissors 순환 상성
    # ══════════════════════════════════════════
    print("\n" + "=" * 88)
    print("  F. 순환 상성 관계 (RPS 구도)  [승률 >55% 기준 directed graph]")
    print("=" * 88)

    cycles = find_rps_cycles(win_rate, n, threshold=0.55)

    if cycles:
        for a, b, c in cycles:
            _, la = METAS[a]
            _, lb = METAS[b]
            _, lc = METAS[c]
            wa_b = win_rate[a][b] * 100
            wb_c = win_rate[b][c] * 100
            wc_a = win_rate[c][a] * 100
            print(
                f"  M{a+1:02d} {la.strip()} ({wa_b:.1f}%) → "
                f"M{b+1:02d} {lb.strip()} ({wb_c:.1f}%) → "
                f"M{c+1:02d} {lc.strip()} ({wc_a:.1f}%) → "
                f"M{a+1:02d} {la.strip()}"
            )
    else:
        print("  순환 상성 없음")

    print("\n=== 시뮬레이션 완료 ===\n")


if __name__ == "__main__":
    main()
