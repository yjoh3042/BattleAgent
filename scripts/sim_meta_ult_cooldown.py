"""Meta Matchup Simulation — 얼티밋 쿨타임(SP+2) 룰 적용 버전
실행: py -X utf8 scripts/sim_meta_ult_cooldown.py
"""
import sys, os, dataclasses, math

SRC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
sys.path.insert(0, SRC_DIR)

from battle.battle_engine import BattleEngine
from battle.enums import BattleResult, Role
from battle.rules import ROLE_BASE_SP, ULT_COOLDOWN, ROLE_ULT_COOLDOWN

# ──────────────────────────────────────────
# 메타 정의 (12개)
# ──────────────────────────────────────────
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
    (meta1,  "화상연계"), (meta2,  "독정원  "), (meta3,  "출혈폭딜"),
    (meta4,  "CC잠금  "), (meta5,  "속도처형"), (meta6,  "크리폭딜"),
    (meta7,  "방어무력"), (meta8,  "철벽반격"), (meta9,  "풀암속성"),
    (meta10, "야성해방"), (meta11, "화상수면"), (meta12, "속도출혈"),
]

N_SEEDS = 50


def flip_to_enemy(chars):
    return [dataclasses.replace(c, side="enemy") for c in chars]


def wilson_interval(wins, n, z=1.96):
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


def run_matchup(ally_factory, enemy_factory, n_seeds=N_SEEDS, label=""):
    ally_wins = enemy_wins = timeouts = 0
    turn_counts = []
    ult_counts = {"ally": [], "enemy": []}

    for seed in range(n_seeds):
        ally_chars = ally_factory()
        enemy_chars = flip_to_enemy(enemy_factory())

        engine = BattleEngine(ally_units=ally_chars, enemy_units=enemy_chars, seed=seed)
        result = engine.run()
        turn_counts.append(engine.turn_count)

        # 얼티밋 사용 횟수 추적 (로그 기반)
        ally_ult = sum(1 for line in engine.get_log() if "💥" in line and "(ally)" in line)
        enemy_ult = sum(1 for line in engine.get_log() if "💥" in line and "(enemy)" in line)
        # 간이 추적: 로그에서 얼티밋 예약 수 카운트
        ally_ult_count = sum(1 for line in engine.get_log() if "얼티밋 예약" in line and "아군" not in line)

        if result == BattleResult.ALLY_WIN:
            ally_wins += 1
        elif result == BattleResult.ENEMY_WIN:
            enemy_wins += 1
        else:
            timeouts += 1

        bar = progress_bar(seed + 1, n_seeds)
        print(f"\r  {label} {bar} 완료", end="", flush=True)

    print()
    return ally_wins, enemy_wins, timeouts, turn_counts


def compute_meta_info(meta_factory):
    chars = meta_factory()
    spd_list = [(c.stats.spd, c.name) for c in chars]
    avg_spd = sum(s for s, _ in spd_list) / len(spd_list)

    # 역할별 SP 비용 및 쿨타임 정보
    ult_info = []
    for c in chars:
        sp = c.ultimate_skill.sp_cost
        cd = c.ultimate_skill.cooldown_turns
        if cd <= 0:
            cd = ULT_COOLDOWN  # 전 직업 공통 4턴
        ult_info.append((c.name, c.role.value, sp, cd))

    return avg_spd, spd_list, ult_info


def find_rps_cycles(win_matrix, n, threshold=0.55):
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

    # ══════════════════════════════════════════
    # 0. 얼티밋 쿨타임 룰 요약
    # ══════════════════════════════════════════
    print("=" * 80)
    print("  얼티밋 쿨타임 룰 적용 메타 시뮬레이션")
    print("  룰: 얼티밋 쿨타임 = 전 직업 공통 4턴 (자기 턴 기준 감소)")
    print("=" * 80)

    print(f"\n  {'역할':<12} {'SP비용':>6} {'쿨타임':>6}")
    print("  " + "-" * 28)
    for role in Role:
        sp = ROLE_BASE_SP[role]
        cd = ROLE_ULT_COOLDOWN[role]
        print(f"  {role.value:<12} {sp:>6} {cd:>5}턴")

    # ══════════════════════════════════════════
    # 0-1. 메타별 캐릭터 얼티밋 쿨타임 상세
    # ══════════════════════════════════════════
    print(f"\n{'=' * 80}")
    print("  메타별 캐릭터 얼티밋 쿨타임 (SP비용 + 2)")
    print("=" * 80)

    for i in range(n):
        factory, lbl = METAS[i]
        avg_spd, _, ult_info = compute_meta_info(factory)
        avg_cd = sum(cd for _, _, _, cd in ult_info) / len(ult_info)
        print(f"\n  M{i+1:02d} {lbl}  (평균SPD: {avg_spd:.0f}, 평균쿨타임: {avg_cd:.1f}턴)")
        for name, role, sp, cd in ult_info:
            print(f"    {name:<12} [{role:<10}] SP={sp}, 쿨타임={cd}턴")

    # ══════════════════════════════════════════
    # 1. 전면 대전
    # ══════════════════════════════════════════
    win_rate = [[-1.0] * n for _ in range(n)]
    avg_turns = [[-1.0] * n for _ in range(n)]
    raw = [[None] * n for _ in range(n)]
    raw_wins = [[-1] * n for _ in range(n)]

    total_matchups = n * (n - 1)
    print(f"\n{'=' * 80}")
    print(f"  전면 대전 시작 ({N_SEEDS} seeds × {total_matchups} 매치업 = {total_matchups * N_SEEDS:,}번 전투)")
    print("=" * 80)

    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            ally_f, ally_label = METAS[i]
            enemy_f, enemy_label = METAS[j]
            label = f"M{i+1:02d} vs M{j+1:02d}"
            w, l, t, turns = run_matchup(ally_f, enemy_f, N_SEEDS, label=label)
            raw[i][j] = (w, l, t)
            raw_wins[i][j] = w
            wr = (w + 0.5 * t) / N_SEEDS
            win_rate[i][j] = wr
            avg_turns[i][j] = sum(turns) / len(turns)
            print(f"  {label}: {w}W / {l}L / {t}T  → {wr*100:.1f}%  avg_turn={avg_turns[i][j]:.1f}")
        print()

    # ══════════════════════════════════════════
    # 2. 승률 매트릭스
    # ══════════════════════════════════════════
    col_w = 6
    row_label_w = 14
    header_labels = [f"M{j+1:02d}" for j in range(n)]

    print("\n" + "=" * 88)
    print("  WIN-RATE MATRIX  (row = ally, col = enemy)")
    print("  얼티밋 쿨타임 룰: 전 직업 공통 4턴 (자기 턴 기준 감소)")
    print("=" * 88)

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
                cell = f"{win_rate[i][j]*100:.1f}%"
            print(f"  {cell:>{col_w}}", end="")
        print()

    # ══════════════════════════════════════════
    # 3. 평균 승률 랭킹
    # ══════════════════════════════════════════
    avg_wr = []
    for i in range(n):
        vals = [win_rate[i][j] for j in range(n) if j != i]
        avg_wr.append(sum(vals) / len(vals))

    print("\n" + "=" * 88)
    print("  평균 승률 랭킹 (쿨타임 룰 적용)")
    print("=" * 88)
    ranked = sorted(range(n), key=lambda i: avg_wr[i], reverse=True)
    for rank, i in enumerate(ranked, 1):
        _, lbl = METAS[i]
        tier = "S" if avg_wr[i] >= 0.60 else "A" if avg_wr[i] >= 0.52 else "B" if avg_wr[i] >= 0.45 else "C"
        print(f"  {rank:>2}위  M{i+1:02d} {lbl}  {avg_wr[i]*100:.1f}%  [{tier}티어]")

    # ══════════════════════════════════════════
    # 4. 카운터 / 취약점
    # ══════════════════════════════════════════
    COUNTER_THRESH = 0.70
    WEAK_THRESH = 0.30

    counters = []
    weaknesses = []
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
    # 5. 평균 전투 턴 수
    # ══════════════════════════════════════════
    print("\n" + "=" * 88)
    print("  평균 전투 턴 수 매트릭스")
    print("=" * 88)

    print(f"  {'':>{row_label_w}}", end="")
    for lbl in header_labels:
        print(f"  {lbl:>{col_w-1}}", end="")
    print()

    for i in range(n):
        _, label = METAS[i]
        row_tag = f"M{i+1:02d} {label}"
        print(f"  {row_tag:>{row_label_w}}", end="")
        for j in range(n):
            if i == j:
                cell = "  -  "
            else:
                cell = f"{avg_turns[i][j]:.1f}"
            print(f"  {cell:>{col_w}}", end="")
        print()

    # ══════════════════════════════════════════
    # 6. 장기전 / 단기전 분류
    # ══════════════════════════════════════════
    print("\n" + "=" * 88)
    print("  장기전 / 단기전 분류 (쿨타임 영향)")
    print("  기준: 단기전 < 40턴 | 중기전 40~80턴 | 장기전 > 80턴")
    print("=" * 88)

    short_metas, mid_metas, long_metas = [], [], []
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

    for name, items in [("단기전 (< 40턴)", short_metas),
                        ("중기전 (40~80턴)", mid_metas),
                        ("장기전 (> 80턴)", long_metas)]:
        print(f"\n  [{name}]")
        if items:
            for avg, i, lbl in sorted(items):
                print(f"    M{i+1:02d} {lbl}  평균 {avg:.1f}턴")
        else:
            print("    없음")

    # ══════════════════════════════════════════
    # 7. 승률 표준편차
    # ══════════════════════════════════════════
    print("\n" + "=" * 88)
    print("  승률 표준편차 (매치업별)")
    print(f"  {'META':<16} {'평균 승률':>10} {'표준편차':>10} {'최고':>10} {'최저':>10}")
    print("  " + "-" * 55)
    print("=" * 88)

    for i in range(n):
        _, lbl = METAS[i]
        vals = [win_rate[i][j] for j in range(n) if j != i]
        mean = sum(vals) / len(vals)
        std = math.sqrt(sum((v - mean) ** 2 for v in vals) / len(vals))
        tag = f"M{i+1:02d} {lbl}"
        print(f"  {tag:<16} {mean*100:>9.1f}% {std*100:>9.1f}% {max(vals)*100:>9.1f}% {min(vals)*100:>9.1f}%")

    # ══════════════════════════════════════════
    # 8. RPS 순환 상성
    # ══════════════════════════════════════════
    print("\n" + "=" * 88)
    print("  순환 상성 관계 (RPS 구도)  [승률 >55% 기준]")
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
            print(f"  M{a+1:02d} {la.strip()} ({wa_b:.1f}%) → "
                  f"M{b+1:02d} {lb.strip()} ({wb_c:.1f}%) → "
                  f"M{c+1:02d} {lc.strip()} ({wc_a:.1f}%) → "
                  f"M{a+1:02d} {la.strip()}")
    else:
        print("  순환 상성 없음")

    # ══════════════════════════════════════════
    # 9. 쿨타임 영향 분석
    # ══════════════════════════════════════════
    print("\n" + "=" * 88)
    print("  쿨타임 룰 영향 분석")
    print("=" * 88)

    # 메타별 평균 쿨타임과 승률 상관관계
    meta_avg_cd = []
    for i in range(n):
        factory, lbl = METAS[i]
        _, _, ult_info = compute_meta_info(factory)
        avg_cd = sum(cd for _, _, _, cd in ult_info) / len(ult_info)
        meta_avg_cd.append(avg_cd)

    print(f"\n  {'META':<16} {'평균쿨타임':>10} {'평균승률':>10} {'티어':>6}")
    print("  " + "-" * 46)
    for i in ranked:
        _, lbl = METAS[i]
        tier = "S" if avg_wr[i] >= 0.60 else "A" if avg_wr[i] >= 0.52 else "B" if avg_wr[i] >= 0.45 else "C"
        tag = f"M{i+1:02d} {lbl}"
        print(f"  {tag:<16} {meta_avg_cd[i]:>9.1f}턴 {avg_wr[i]*100:>9.1f}% {tier:>6}")

    # 쿨타임별 승률 평균
    low_cd_wr = [avg_wr[i] for i in range(n) if meta_avg_cd[i] < 6.5]
    high_cd_wr = [avg_wr[i] for i in range(n) if meta_avg_cd[i] >= 6.5]

    print(f"\n  낮은 쿨타임 메타 (< 6.5턴 평균): "
          f"평균 승률 {sum(low_cd_wr)/len(low_cd_wr)*100:.1f}% ({len(low_cd_wr)}개)" if low_cd_wr else "")
    print(f"  높은 쿨타임 메타 (>= 6.5턴 평균): "
          f"평균 승률 {sum(high_cd_wr)/len(high_cd_wr)*100:.1f}% ({len(high_cd_wr)}개)" if high_cd_wr else "")

    print("\n  [분석]")
    print("  - 전 직업 공통 4턴 쿨타임 → 얼티밋 빈도 균등화")
    print("  - SPD가 높은 유닛일수록 실제 시간(타임라인) 기준 쿨타임 빨리 회복")
    print("  - 고속 SUPPORTER(SPD120): 4턴 = 타임라인 10.0")
    print("  - 저속 ATTACKER(SPD80):  4턴 = 타임라인 15.0")
    print("  - 공용 SP + 쿨타임 제약 → '누가 먼저 쓸지' 전략적 선택 더 중요")

    # ══════════════════════════════════════════
    # 10. 통계적 유의성
    # ══════════════════════════════════════════
    print("\n" + "=" * 88)
    print("  통계적 유의성 - 핵심 상성 95% 신뢰구간 (승률 >60% 또는 <40%)")
    print(f"  {'매치업':<30} {'승률':>7} {'95% CI':>20}")
    print("  " + "-" * 60)
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

    print("\n=== 시뮬레이션 완료 (얼티밋 쿨타임: 전 직업 공통 4턴) ===\n")


if __name__ == "__main__":
    main()
