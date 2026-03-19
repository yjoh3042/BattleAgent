"""8-meta round robin simulation — 매치업당 10회 반복 (총 280경기)"""
import sys, os, copy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from battle.battle_engine import BattleEngine
from battle.enums import BattleResult
from fixtures.test_data import (
    get_meta_burst, get_meta_op_duo, get_meta_fire_burn, get_meta_cc_control,
    get_meta_water_tempo, get_meta_dark_assault, get_meta_light_holy, get_meta_forest_rush,
)

TRIALS = 10  # 매치업당 반복 횟수

META_TEAMS = {
    "1.극딜버스트":    get_meta_burst,
    "2.OP듀오":       get_meta_op_duo,
    "3.화상시너지":    get_meta_fire_burn,
    "4.CC컨트롤":     get_meta_cc_control,
    "5.수속템포":      get_meta_water_tempo,
    "6.암속강공":      get_meta_dark_assault,
    "7.광속순수":      get_meta_light_holy,
    "8.목속돌격":      get_meta_forest_rush,
}


def make_enemy_team(team_fn):
    """팀 생성 후 side='enemy' + ID에 '_e' 접미사로 충돌 방지"""
    chars = team_fn()
    enemy_chars = []
    for c in chars:
        ec = copy.deepcopy(c)
        ec.id = ec.id + "_e"
        ec.side = "enemy"
        skills = [ec.normal_skill, ec.active_skill, ec.ultimate_skill]
        if ec.passive_skill:
            skills.append(ec.passive_skill)
        for skill in skills:
            skill.id = skill.id + "_e"
            for eff in skill.effects:
                if eff.buff_data:
                    eff.buff_data.id = eff.buff_data.id + "_e"
                    eff.buff_data.source_skill_id = eff.buff_data.source_skill_id + "_e"
        for trigger in ec.triggers:
            if trigger.skill_id:
                trigger.skill_id = trigger.skill_id + "_e"
        enemy_chars.append(ec)
    return enemy_chars


def run_match(ally_fn, enemy_fn, seed=42):
    allies = ally_fn()
    enemies = make_enemy_team(enemy_fn)
    engine = BattleEngine(allies, enemies, seed=seed)
    result = engine.run()
    return result, engine.turn_count


team_names = list(META_TEAMS.keys())
n = len(team_names)

# 매치업별 상세 기록
matchup_detail = {}
wins = {name: 0 for name in team_names}
losses = {name: 0 for name in team_names}
draws = {name: 0 for name in team_names}

print("=" * 76)
print(f"  8 META ROUND ROBIN -- {TRIALS}trial x 28matchup = {28 * TRIALS} games")
print("=" * 76)
print()

matchup_idx = 0
for i in range(n):
    for j in range(i + 1, n):
        matchup_idx += 1
        name_a = team_names[i]
        name_b = team_names[j]
        fn_a = META_TEAMS[name_a]
        fn_b = META_TEAMS[name_b]

        a_wins = 0
        b_wins = 0
        d_count = 0
        turns_list = []

        for trial in range(TRIALS):
            seed = matchup_idx * 1000 + trial
            result, turns = run_match(fn_a, fn_b, seed=seed)
            turns_list.append(turns)
            if result == BattleResult.ALLY_WIN:
                a_wins += 1
            elif result == BattleResult.ENEMY_WIN:
                b_wins += 1
            else:
                d_count += 1

        matchup_detail[(name_a, name_b)] = {
            'a_wins': a_wins, 'b_wins': b_wins, 'draws': d_count,
            'avg_turns': sum(turns_list) / len(turns_list),
        }

        wins[name_a] += a_wins
        losses[name_a] += b_wins
        draws[name_a] += d_count
        wins[name_b] += b_wins
        losses[name_b] += a_wins
        draws[name_b] += d_count

        # 매치업 결과 출력
        if a_wins > b_wins:
            winner_str = f"{name_a} {a_wins}-{b_wins}"
        elif b_wins > a_wins:
            winner_str = f"{name_b} {b_wins}-{a_wins}"
        else:
            winner_str = f"EVEN {a_wins}-{b_wins}"
        draw_str = f" (draw {d_count})" if d_count > 0 else ""
        avg_t = sum(turns_list) / len(turns_list)
        print(f"  [{matchup_idx:2d}] {name_a:10s} vs {name_b:10s}  =>  {winner_str}{draw_str}  (avg {avg_t:.0f}t)")

# ── 종합 성적표 ──
print()
print("=" * 76)
print(f"  STANDINGS  (total {28 * TRIALS} games)")
print("=" * 76)
print(f"{'team':<14s} {'W':>4s} {'L':>4s} {'D':>4s} {'total':>6s} {'WR':>7s}")
print("-" * 45)

rankings = sorted(team_names, key=lambda nm: (wins[nm], -losses[nm]), reverse=True)
for name in rankings:
    total = wins[name] + losses[name] + draws[name]
    wr = wins[name] / total * 100 if total > 0 else 0
    print(f"{name:<14s} {wins[name]:>4d} {losses[name]:>4d} {draws[name]:>4d} {total:>6d} {wr:>6.1f}%")

# ── 상성표 (승수 표기) ──
print()
print("=" * 76)
print(f"  MATCHUP TABLE  (row=A, col=B, cell=A_win-B_win out of {TRIALS})")
print("=" * 76)

short = {nm: nm.split('.')[1] for nm in team_names}

header = f"{'':>12s}"
for name in team_names:
    header += f" {short[name]:>8s}"
print(header)
print("-" * (12 + 9 * n))

for i, name_a in enumerate(team_names):
    row = f"{short[name_a]:>12s}"
    for j, name_b in enumerate(team_names):
        if i == j:
            row += f" {'---':>8s}"
        elif i < j:
            d = matchup_detail[(name_a, name_b)]
            cell = f"{d['a_wins']}-{d['b_wins']}"
            if d['draws'] > 0:
                cell += f"d{d['draws']}"
            row += f" {cell:>8s}"
        else:
            d = matchup_detail[(name_b, name_a)]
            cell = f"{d['b_wins']}-{d['a_wins']}"
            if d['draws'] > 0:
                cell += f"d{d['draws']}"
            row += f" {cell:>8s}"
    print(row)

# ── 최종 순위 ──
print()
print("=" * 76)
print("  FINAL RANKING")
print("=" * 76)
for rank, name in enumerate(rankings, 1):
    total = wins[name] + losses[name] + draws[name]
    wr = wins[name] / total * 100 if total > 0 else 0
    print(f"  {rank}. {name}  --  {wins[name]}W {losses[name]}L {draws[name]}D ({wr:.1f}%)")
