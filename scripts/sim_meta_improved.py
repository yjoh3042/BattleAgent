"""메타 개선안 검증 시뮬레이션
개선된 M05'/M06'/M07' vs 기존 상위 메타 비교
실행: py -X utf8 scripts/sim_meta_improved.py  (C:\\Ai\\BattleAgent\\ 에서)
"""
from __future__ import annotations
import sys, os, dataclasses

SRC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
sys.path.insert(0, SRC_DIR)

from battle.battle_engine import BattleEngine
from battle.enums import BattleResult

# ──────────────────────────────────────────────────────────────────────
# 기존 상위 메타 (M01~M04, M08, M10, M11)
# ──────────────────────────────────────────────────────────────────────

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

def meta8():
    from fixtures.test_data import make_deresa, make_frey, make_ragaraja, make_metis, make_jiva
    return [make_deresa(), make_frey(), make_ragaraja(), make_metis(), make_jiva()]

def meta10():
    from fixtures.test_data import make_grilla, make_miriam, make_batory, make_aurora, make_brownie
    return [make_grilla(), make_miriam(), make_batory(), make_aurora(), make_brownie()]

def meta11():
    from fixtures.test_data import make_pan, make_dabi, make_semele, make_aurora, make_jiva
    return [make_pan(), make_dabi(), make_semele(), make_aurora(), make_jiva()]

# ──────────────────────────────────────────────────────────────────────
# 기존 하위 메타 (M05, M06, M07)
# ──────────────────────────────────────────────────────────────────────

def meta5_old():
    """M05 속도처형(기존): 이브+상아+티스베+살마키스+브라우니"""
    from fixtures.test_data import make_eve, make_sangah, make_thisbe, make_salmakis, make_brownie
    return [make_eve(), make_sangah(), make_thisbe(), make_salmakis(), make_brownie()]

def meta6_old():
    """M06 크리폭딜(기존): 아슈토레스+아르테미스+아우로라+그릴라+시트리"""
    from fixtures.test_data import make_ashtoreth, make_artemis, make_aurora, make_grilla, make_sitri
    return [make_ashtoreth(), make_artemis(), make_aurora(), make_grilla(), make_sitri()]

def meta7_old():
    """M07 방어무력(기존): 쿠바바+티와즈+아르테미스+카라라트리+유나"""
    from fixtures.test_data import make_kubaba, make_tiwaz, make_artemis, make_kararatri, make_yuna
    return [make_kubaba(), make_tiwaz(), make_artemis(), make_kararatri(), make_yuna()]

# ──────────────────────────────────────────────────────────────────────
# 개선 메타 (M05', M06', M07')
# ──────────────────────────────────────────────────────────────────────

def meta5_new():
    """M05' 속도처형(개선): 이브+쿠바바+살마키스+티스베+아우로라"""
    from fixtures.test_data import make_eve, make_kubaba, make_salmakis, make_thisbe, make_aurora
    return [make_eve(), make_kubaba(), make_salmakis(), make_thisbe(), make_aurora()]

def meta6_new():
    """M06' 크리폭딜(개선): 아슈토레스+미리암+아우로라+시트리+지바"""
    from fixtures.test_data import make_ashtoreth, make_miriam, make_aurora, make_sitri, make_jiva
    return [make_ashtoreth(), make_miriam(), make_aurora(), make_sitri(), make_jiva()]

def meta7_new():
    """M07' 방어무력(개선): 쿠바바+아르테미스+카라라트리+지바+유나"""
    from fixtures.test_data import make_kubaba, make_artemis, make_kararatri, make_jiva, make_yuna
    return [make_kubaba(), make_artemis(), make_kararatri(), make_jiva(), make_yuna()]

# ──────────────────────────────────────────────────────────────────────
# 설정
# ──────────────────────────────────────────────────────────────────────

N_SEEDS = 50

EXISTING = [
    (meta1,  "M01 화상연계"),
    (meta2,  "M02 독정원 "),
    (meta3,  "M03 출혈폭딜"),
    (meta4,  "M04 CC잠금 "),
    (meta8,  "M08 철벽반격"),
    (meta10, "M10 야성해방"),
    (meta11, "M11 화상수면"),
]

COMPARE = [
    (meta5_old, "M05  속도처형(기존)", meta5_new, "M05' 속도처형(개선)"),
    (meta6_old, "M06  크리폭딜(기존)", meta6_new, "M06' 크리폭딜(개선)"),
    (meta7_old, "M07  방어무력(기존)", meta7_new, "M07' 방어무력(개선)"),
]

# ──────────────────────────────────────────────────────────────────────
# 유틸
# ──────────────────────────────────────────────────────────────────────

def flip_to_enemy(chars):
    return [dataclasses.replace(c, side="enemy") for c in chars]


def run_matchup(ally_factory, enemy_factory, n_seeds=N_SEEDS):
    ally_wins = enemy_wins = timeouts = 0
    for seed in range(n_seeds):
        engine = BattleEngine(
            ally_units=ally_factory(),
            enemy_units=flip_to_enemy(enemy_factory()),
            seed=seed,
        )
        result = engine.run()
        if result == BattleResult.ALLY_WIN:
            ally_wins += 1
        elif result == BattleResult.ENEMY_WIN:
            enemy_wins += 1
        else:
            timeouts += 1
    return ally_wins, enemy_wins, timeouts


def winrate(w, t, n=N_SEEDS):
    return (w + 0.5 * t) / n * 100


# ──────────────────────────────────────────────────────────────────────
# 메인
# ──────────────────────────────────────────────────────────────────────

def main():
    print("=== 메타 개선안 검증 시뮬레이션 ===")
    print(f"    시드 수: {N_SEEDS}  |  비교 상위 메타: {len(EXISTING)}개\n")

    summary = []  # (old_name, new_name, old_avg, new_avg)

    for old_f, old_name, new_f, new_name in COMPARE:
        print(f"\n{'='*72}")
        print(f"  {old_name}  →  {new_name}")
        print(f"{'='*72}")
        print(f"  {'상대 메타':<18}  {'기존':>7}    {'개선':>7}   {'변화':>7}")
        print(f"  {'-'*56}")

        old_total = 0.0
        new_total = 0.0

        for exist_f, exist_name in EXISTING:
            w_old, _, t_old = run_matchup(old_f, exist_f)
            w_new, _, t_new = run_matchup(new_f, exist_f)

            wr_old = winrate(w_old, t_old)
            wr_new = winrate(w_new, t_new)
            delta  = wr_new - wr_old

            old_total += wr_old
            new_total += wr_new

            if delta > 0.5:
                arrow = "▲"
            elif delta < -0.5:
                arrow = "▼"
            else:
                arrow = "─"

            sign = "+" if delta >= 0 else ""
            print(f"  vs {exist_name:<16}  {wr_old:>6.1f}%  →  {wr_new:>6.1f}%   {arrow}{sign}{delta:.1f}%p")

        n_exist = len(EXISTING)
        old_avg = old_total / n_exist
        new_avg = new_total / n_exist
        avg_delta = new_avg - old_avg

        print(f"  {'-'*56}")
        sign = "+" if avg_delta >= 0 else ""
        print(f"  {'평균':<18}  {old_avg:>6.1f}%  →  {new_avg:>6.1f}%   {sign}{avg_delta:.1f}%p")

        summary.append((old_name.strip(), new_name.strip(), old_avg, new_avg))

    # ── 최종 요약 ──────────────────────────────────────────────────────
    print(f"\n\n{'='*72}")
    print("  최종 요약")
    print(f"{'='*72}")
    print(f"  {'메타':<22}  {'기존 평균':>10}  {'개선 평균':>10}  {'변화':>8}")
    print(f"  {'-'*58}")
    for old_name, new_name, old_avg, new_avg in summary:
        delta = new_avg - old_avg
        sign = "+" if delta >= 0 else ""
        arrow = "▲" if delta > 0.5 else "▼" if delta < -0.5 else "─"
        print(f"  {new_name:<22}  {old_avg:>9.1f}%  {new_avg:>9.1f}%  {arrow}{sign}{delta:.1f}%p")

    print(f"\n=== 검증 완료 ===\n")


if __name__ == "__main__":
    main()
