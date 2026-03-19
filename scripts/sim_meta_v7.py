"""v7.0 메타 매치업 시뮬레이션 — 12개 메타 조합 전체 상성 매트릭스
Usage: py -X utf8 scripts/sim_meta_v7.py [seeds]
"""
import sys, os, pathlib, copy, random
from collections import defaultdict

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "src"))
sys.stdout.reconfigure(encoding="utf-8")

from battle.battle_engine import BattleEngine
from battle.enums import BattleResult
from fixtures import test_data as td

SEEDS = int(sys.argv[1]) if len(sys.argv) > 1 else 30

META_DEFS = {
    "M01_화상연소": td.get_meta_burn_inferno,
    "M02_빙결감옥": td.get_meta_freeze_prison,
    "M03_독정원":   td.get_meta_poison_garden,
    "M04_하이퍼캐리": td.get_meta_hyper_carry,
    "M05_철벽요새": td.get_meta_iron_fortress,
    "M06_반격요새": td.get_meta_counter_bruiser,
    "M07_속도처형": td.get_meta_speed_execute,
    "M08_암속강공": td.get_meta_dark_assault,
    "M09_전멸폭격": td.get_meta_aoe_cleave,
    "M10_광전사":   td.get_meta_berserker,
    "M11_광속성벽": td.get_meta_holy_bastion,
    "M12_CC킬체인": td.get_meta_cc_kill_chain,
}


def make_enemy_team(team_fn):
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
        # 트리거의 skill_id도 _e 접미사 추가
        for trigger in ec.triggers:
            if trigger.skill_id:
                trigger.skill_id = trigger.skill_id + "_e"
        enemy_chars.append(ec)
    return enemy_chars


def run_match(ally_fn, enemy_fn, seed):
    allies = ally_fn()
    enemies = make_enemy_team(enemy_fn)
    engine = BattleEngine(allies, enemies, seed=seed)
    result = engine.run()
    return result == BattleResult.ALLY_WIN


def main():
    names = list(META_DEFS.keys())
    n = len(names)
    wins = defaultdict(lambda: defaultdict(int))
    total_games = defaultdict(lambda: defaultdict(int))

    print(f"=== v7.0 메타 매치업 시뮬레이션 ({SEEDS} seeds x {n*(n-1)} matchups) ===\n")

    for i, atk_name in enumerate(names):
        for j, def_name in enumerate(names):
            if i == j:
                continue
            atk_fn = META_DEFS[atk_name]
            def_fn = META_DEFS[def_name]
            w = 0
            for s in range(SEEDS):
                try:
                    if run_match(atk_fn, def_fn, s * 1000 + i * 100 + j):
                        w += 1
                except Exception as e:
                    pass
            wins[atk_name][def_name] = w
            total_games[atk_name][def_name] = SEEDS
        pct = sum(wins[atk_name][d] for d in names if d != atk_name)
        tot = sum(total_games[atk_name][d] for d in names if d != atk_name)
        wr = pct / tot * 100 if tot else 0
        print(f"  [{i+1:2d}/12] {atk_name}: 종합 {wr:.1f}% ({pct}/{tot})")

    # ─── 매트릭스 출력 ───
    print("\n" + "=" * 120)
    print("📊 매치업 매트릭스 (공격덱 승률%)")
    print("=" * 120)

    short = [n.split("_")[0] for n in names]
    header = f"{'공격↓\\방어→':>16s}" + "".join(f"{s:>8s}" for s in short) + "  | 종합"
    print(header)
    print("-" * len(header))

    overall = {}
    for atk_name in names:
        row_wins = sum(wins[atk_name][d] for d in names if d != atk_name)
        row_total = sum(total_games[atk_name][d] for d in names if d != atk_name)
        wr = row_wins / row_total * 100 if row_total else 0
        overall[atk_name] = wr

        cells = []
        for def_name in names:
            if atk_name == def_name:
                cells.append(f"{'---':>8s}")
            else:
                t = total_games[atk_name][def_name]
                w = wins[atk_name][def_name]
                pct = w / t * 100 if t else 0
                cells.append(f"{pct:>7.0f}%")
        print(f"{atk_name:>16s}" + "".join(cells) + f"  | {wr:5.1f}%")

    # ─── 종합 랭킹 ───
    print("\n" + "=" * 60)
    print("🏆 종합 승률 랭킹 (공격덱 기준)")
    print("=" * 60)
    ranked = sorted(overall.items(), key=lambda x: -x[1])
    tiers = {"S": [], "A": [], "B": [], "C": []}
    for rank, (name, wr) in enumerate(ranked, 1):
        tier = "S" if wr >= 60 else "A" if wr >= 50 else "B" if wr >= 40 else "C"
        tiers[tier].append((name, wr))
        print(f"  {rank:2d}. {name:20s} {wr:5.1f}%  [{tier}]")

    print("\n" + "=" * 60)
    print("📋 티어 요약")
    print("=" * 60)
    for tier_name in ["S", "A", "B", "C"]:
        members = tiers[tier_name]
        if members:
            names_str = ", ".join(f"{n}({w:.0f}%)" for n, w in members)
            print(f"  {tier_name}티어: {names_str}")

    # ─── 메타별 최고/최악 상대 ───
    print("\n" + "=" * 80)
    print("📌 메타별 최고/최악 상대 (카운터 관계)")
    print("=" * 80)
    for atk_name in names:
        matchups = []
        for def_name in names:
            if atk_name == def_name:
                continue
            t = total_games[atk_name][def_name]
            w = wins[atk_name][def_name]
            pct = w / t * 100 if t else 0
            matchups.append((def_name, pct))
        matchups.sort(key=lambda x: -x[1])
        best = matchups[0]
        worst = matchups[-1]
        print(f"  {atk_name:18s} | 강점: {best[0]:18s}({best[1]:3.0f}%) | 약점: {worst[0]:18s}({worst[1]:3.0f}%)")

    # ─── 카운터 관계 ───
    print("\n" + "=" * 60)
    print("🔄 카운터 관계 (승률 70%+ = 강한 카운터)")
    print("=" * 60)
    counters = []
    for atk_name in names:
        for def_name in names:
            if atk_name == def_name:
                continue
            t = total_games[atk_name][def_name]
            w = wins[atk_name][def_name]
            pct = w / t * 100 if t else 0
            if pct >= 70:
                counters.append((atk_name, def_name, pct))
    counters.sort(key=lambda x: -x[2])
    if counters:
        for a, d, p in counters:
            print(f"  {a} >>> {d}: {p:.0f}%")
    else:
        print("  (70%+ 카운터 없음 — 밸런스 양호)")

    # ─── 속성 기믹 효과 분석 ───
    print("\n" + "=" * 60)
    print("🔥💧🌿✨🌙 속성 기믹별 평균 승률")
    print("=" * 60)
    gimmick_groups = {
        "🔥화상(burn)":   ["M01_화상연소"],
        "💧CC(freeze)":   ["M02_빙결감옥", "M07_속도처형"],
        "🌿독(poison)":   ["M03_독정원"],
        "✨보호(barrier)": ["M05_철벽요새", "M11_광속성벽"],
        "🌙관통(pen)":    ["M08_암속강공"],
        "혼합(hybrid)":   ["M04_하이퍼캐리", "M06_반격요새", "M09_전멸폭격", "M10_광전사", "M12_CC킬체인"],
    }
    for gname, gmetas in gimmick_groups.items():
        avg = sum(overall.get(m, 0) for m in gmetas) / len(gmetas) if gmetas else 0
        print(f"  {gname:20s}: {avg:5.1f}% (대표: {', '.join(m.split('_')[0] for m in gmetas)})")


if __name__ == "__main__":
    main()
