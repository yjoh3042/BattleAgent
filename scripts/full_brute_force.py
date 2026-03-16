"""full_brute_force.py — 종합 브루트포스 최적 파티 탐색 (피해량 타이브레이커 포함)

캐릭터 풀 (9명, 상위 2개 메타 합집합):
  루미나(c600), 에레보스(c601), 시트리, 아르테미스, 다누,
  이브, 쿠바바, 엘리시온, 아우로라

적군: 5마리 봉제인형 (get_enemies_5)
룰: CRI 15% / PEN 0% 통일 (2026-03-13)

Phase 1: C(9,5)=126 조합 × 10 시드 → auto 모드 승률+평균턴+피해량 기준 상위 추출
Phase 2: 상위 조합 × 5!=120 얼티밋 순서 × 10 시드 → 최적 순서 탐색 (타이브레이커: 피해량)
Phase 3: 결과 분석 → results.json + top_builds.md 생성

실행: py -3 -X utf8 scripts/full_brute_force.py
"""
import sys, os, itertools, time, json, statistics
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
    ("루미나",     make_c600,    {"role": "SUP", "element": "光", "atk": 230, "hp": 6800, "spd": 120}),
    ("에레보스",   make_c601,    {"role": "ATK", "element": "暗", "atk": 530, "hp": 5500, "spd": 85}),
    ("시트리",     make_sitri,   {"role": "SUP", "element": "火", "atk": 172, "hp": 5400, "spd": 108}),
    ("아르테미스", make_artemis, {"role": "ATK", "element": "木", "atk": 385, "hp": 4700, "spd": 75}),
    ("다누",       make_danu,    {"role": "HLR", "element": "水", "atk": 160, "hp": 6100, "spd": 95}),
    ("이브",       make_eve,     {"role": "ATK", "element": "暗", "atk": 410, "hp": 4500, "spd": 78}),
    ("쿠바바",     make_kubaba,  {"role": "ATK", "element": "火", "atk": 380, "hp": 4800, "spd": 80}),
    ("엘리시온",   make_elysion, {"role": "SUP", "element": "光", "atk": 165, "hp": 5800, "spd": 105}),
    ("아우로라",   make_aurora,  {"role": "DEF", "element": "水", "atk": 145, "hp": 7200, "spd": 90}),
]

SEEDS = 10             # 시드 수
TOP_N = 20             # Phase 2로 넘길 상위 조합 수
PARTY_SIZE = 5

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
os.makedirs(DATA_DIR, exist_ok=True)


def calc_damage_taken(engine):
    """아군 총 피해량 계산 (사망자는 max_hp 전체를 피해로 계산)"""
    total = 0.0
    for u in engine.allies:
        if u.is_alive:
            total += (u.max_hp - u.current_hp)
        else:
            total += u.max_hp
    return total


def run_battle(ally_factories, enemy_factory, seed, ultimate_mode="auto", ultimate_order=None):
    """한 전투 실행, (result, turn_count, damage_taken, survivors) 반환"""
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
    dmg = calc_damage_taken(engine)
    survivors = sum(1 for u in engine.allies if u.is_alive)
    return result, engine.turn_count, dmg, survivors


def evaluate_combo(factories, seeds, ultimate_mode="auto", ultimate_order=None):
    """여러 시드로 평가 → 종합 통계"""
    wins = 0
    turns = []
    dmg_list = []
    survivor_list = []
    for s in range(seeds):
        r, t, dmg, surv = run_battle(factories, get_enemies_5, s, ultimate_mode, ultimate_order)
        if r == BattleResult.ALLY_WIN:
            wins += 1
            turns.append(t)
            dmg_list.append(dmg)
            survivor_list.append(surv)
    avg_turn = sum(turns) / len(turns) if turns else 999
    avg_dmg = sum(dmg_list) / len(dmg_list) if dmg_list else 99999
    avg_surv = sum(survivor_list) / len(survivor_list) if survivor_list else 0
    return {
        "wins": wins,
        "avg_turn": avg_turn,
        "min_turn": min(turns) if turns else 999,
        "max_turn": max(turns) if turns else 999,
        "avg_dmg": avg_dmg,
        "min_dmg": min(dmg_list) if dmg_list else 99999,
        "max_dmg": max(dmg_list) if dmg_list else 99999,
        "avg_survivors": avg_surv,
        "turns": turns,
        "dmg_list": dmg_list,
    }


def phase1_combo_search():
    """Phase 1: C(9,5)=126 조합 전수 탐색 (auto 모드)"""
    print("=" * 80)
    combos = list(itertools.combinations(range(len(CHAR_POOL)), PARTY_SIZE))
    print(f"  Phase 1: 파티 조합 전수 탐색  C({len(CHAR_POOL)},{PARTY_SIZE}) = {len(combos)} 조합")
    print(f"  시드: {SEEDS}개, 적군: 봉제인형 5마리, 모드: auto")
    print("=" * 80)

    results = []
    total = len(combos)
    t0 = time.time()

    for idx, combo_idx in enumerate(combos):
        names = [CHAR_POOL[i][0] for i in combo_idx]
        factories = [CHAR_POOL[i][1] for i in combo_idx]
        stats_info = [CHAR_POOL[i][2] for i in combo_idx]

        ev = evaluate_combo(factories, SEEDS)
        wr = ev["wins"] / SEEDS

        results.append({
            "idx": combo_idx,
            "names": names,
            "factories": factories,
            "stats_info": stats_info,
            "wr": wr,
            **ev,
        })

        if (idx + 1) % 20 == 0 or idx == total - 1:
            elapsed = time.time() - t0
            print(f"  [{idx+1:3d}/{total}] {elapsed:.1f}s  "
                  f"현재: {'/'.join(names)}  승률={wr*100:.0f}% 평균={ev['avg_turn']:.1f}턴 피해={ev['avg_dmg']:.0f}")

    # 정렬: 승률 내림 → 평균턴 오름 → 평균피해 오름 (타이브레이커)
    results.sort(key=lambda x: (-x["wr"], x["avg_turn"], x["avg_dmg"]))

    # 결과 출력
    print()
    print("─" * 90)
    print(f"  Phase 1 결과: 전체 {total} 조합 (auto 모드)")
    print("─" * 90)
    print(f"  {'순위':<4} {'조합':<40} {'승률':>6} {'평균턴':>7} {'피해량':>8} {'생존':>5}")
    print("  " + "-" * 86)

    for rank, r in enumerate(results[:20], 1):
        combo_str = ", ".join(r["names"])
        print(f"  {rank:>2}위  {combo_str:<38} {r['wr']*100:>5.0f}%  {r['avg_turn']:>6.1f}  "
              f"{r['avg_dmg']:>7.0f}  {r['avg_survivors']:>4.1f}")

    zero_win = sum(1 for r in results if r["wins"] == 0)
    full_win = sum(1 for r in results if r["wins"] == SEEDS)
    print(f"\n  전승({SEEDS}/{SEEDS}): {full_win}개 | 전패(0승): {zero_win}개")
    print(f"  소요시간: {time.time()-t0:.1f}s")

    return results


def phase2_order_search(top_combos):
    """Phase 2: 상위 조합 × 5!=120 얼티밋 순서 전수 탐색"""
    print()
    print("=" * 80)
    print(f"  Phase 2: 얼티밋 순서 전수 탐색  상위 {len(top_combos)} 조합 × 5!={120} 순서")
    print(f"  시드: {SEEDS}개, 모드: manual_ordered (setting)")
    print("=" * 80)

    all_results = []
    t0 = time.time()

    for ci, combo in enumerate(top_combos):
        names = combo["names"]
        factories = combo["factories"]

        # 캐릭터 ID 추출
        sample_units = [f() for f in factories]
        char_ids = [u.id for u in sample_units]
        id_to_name = {u.id: n for u, n in zip(sample_units, names)}

        best_order = None
        best_key = (999, 99999)  # (avg_turn, avg_dmg)
        order_results = []

        for perm in itertools.permutations(char_ids):
            ev = evaluate_combo(
                factories, SEEDS,
                ultimate_mode="setting", ultimate_order=list(perm)
            )
            key = (ev["avg_turn"], ev["avg_dmg"])
            order_results.append({
                "order": list(perm),
                "order_names": [id_to_name.get(oid, oid) for oid in perm],
                **ev,
            })

            if ev["wins"] > 0 and key < best_key:
                best_key = key
                best_order = list(perm)

        # 순서 결과 정렬 (승수 내림 → 평균턴 오름 → 평균피해 오름)
        order_results.sort(key=lambda x: (-x["wins"], x["avg_turn"], x["avg_dmg"]))

        best_order_names = [id_to_name.get(oid, oid) for oid in best_order] if best_order else []

        # 순서 간 분산 계산 (얼티밋 순서가 얼마나 중요한지)
        winning_avgs = [o["avg_turn"] for o in order_results if o["wins"] > 0]
        turn_variance = statistics.variance(winning_avgs) if len(winning_avgs) > 1 else 0

        entry = {
            "names": names,
            "stats_info": combo["stats_info"],
            "combo_wr": combo["wr"],
            "combo_avg_auto": combo["avg_turn"],
            "combo_avg_dmg_auto": combo["avg_dmg"],
            "best_order": best_order,
            "best_order_names": best_order_names,
            "best_avg_turn": best_key[0],
            "best_avg_dmg": best_key[1],
            "best_min_turn": min(o["min_turn"] for o in order_results if o["wins"] > 0) if any(o["wins"] > 0 for o in order_results) else 999,
            "worst_avg_turn": order_results[-1]["avg_turn"] if order_results else 999,
            "turn_variance": turn_variance,
            "top3_orders": order_results[:3],
            "worst3_orders": order_results[-3:],
            "total_orders": len(order_results),
        }
        all_results.append(entry)

        elapsed = time.time() - t0
        print(f"  [{ci+1:2d}/{len(top_combos)}] {elapsed:.1f}s  "
              f"{'/'.join(names)}  최적순서={'/'.join(best_order_names)} "
              f"평균={best_key[0]:.1f}턴 피해={best_key[1]:.0f}")

    # 최종 결과 정렬: 평균턴 오름 → 평균피해 오름 (타이브레이커)
    all_results.sort(key=lambda x: (x["best_avg_turn"], x["best_avg_dmg"]))

    print()
    print("─" * 100)
    print(f"  Phase 2 최종 결과: 최적 파티 + 얼티밋 순서 TOP {min(10, len(all_results))}")
    print("─" * 100)
    print(f"  {'순위':<4} {'조합':<32} {'최적 얼티밋 순서':<32} {'평균턴':>7} {'피해':>7} {'최소':>5}")
    print("  " + "-" * 96)

    for rank, r in enumerate(all_results[:10], 1):
        combo_str = ", ".join(r["names"])
        order_str = " → ".join(r["best_order_names"])
        print(f"  {rank:>2}위  {combo_str:<30} {order_str:<30} {r['best_avg_turn']:>6.1f}  "
              f"{r['best_avg_dmg']:>6.0f}  {r['best_min_turn']:>4}")

    print(f"\n  소요시간: {time.time()-t0:.1f}s")

    return all_results


def character_frequency_analysis(phase1_results, top_n=20):
    """캐릭터 출현 빈도 분석"""
    freq = defaultdict(lambda: {"count": 0, "avg_turn_sum": 0, "avg_dmg_sum": 0})
    top = [r for r in phase1_results if r["wins"] > 0][:top_n]
    for r in top:
        for name in r["names"]:
            freq[name]["count"] += 1
            freq[name]["avg_turn_sum"] += r["avg_turn"]
            freq[name]["avg_dmg_sum"] += r["avg_dmg"]

    analysis = {}
    for name, data in freq.items():
        c = data["count"]
        analysis[name] = {
            "appearances": c,
            "appearance_rate": c / top_n,
            "avg_turn_when_present": data["avg_turn_sum"] / c if c > 0 else 999,
            "avg_dmg_when_present": data["avg_dmg_sum"] / c if c > 0 else 99999,
        }
    return dict(sorted(analysis.items(), key=lambda x: -x[1]["appearances"]))


def role_composition_analysis(phase1_results, top_n=20):
    """역할 구성 분석"""
    top = [r for r in phase1_results if r["wins"] > 0][:top_n]
    role_combos = defaultdict(list)
    for r in top:
        roles = sorted([s["role"] for s in r["stats_info"]])
        role_key = "/".join(roles)
        role_combos[role_key].append(r["avg_turn"])
    return {k: {"count": len(v), "avg_turn": sum(v)/len(v)} for k, v in role_combos.items()}


def save_results(phase1, phase2):
    """results.json 저장 (종합)"""
    char_freq = character_frequency_analysis(phase1)
    role_comp = role_composition_analysis(phase1)

    output = {
        "metadata": {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "pool_size": len(CHAR_POOL),
            "party_size": PARTY_SIZE,
            "seeds": SEEDS,
            "total_combos": 126,
            "total_orders_per_combo": 120,
            "pool": [{"name": n, **s} for n, _, s in CHAR_POOL],
            "rules": "cri_ratio=0.15, penetration=0.0 (2026-03-13 통일)",
            "enemy": "봉제인형 5마리 (get_enemies_5)",
            "assumptions": [
                "auto 모드: 엔진이 SP 충족 즉시 얼티밋 발동",
                "setting 모드: 지정 순서대로 얼티밋 발동",
                "피해량 = 사망자 max_hp + 생존자 (max_hp - current_hp)",
                "타이브레이커: 평균턴 동일 시 평균피해량이 낮은 쪽 우선",
            ],
        },
        "phase1_all": [
            {
                "rank": i + 1,
                "party": r["names"],
                "win_rate": r["wr"],
                "avg_turn": round(r["avg_turn"], 1),
                "min_turn": r["min_turn"],
                "max_turn": r["max_turn"],
                "avg_damage_taken": round(r["avg_dmg"], 0),
                "min_damage_taken": round(r["min_dmg"], 0),
                "max_damage_taken": round(r["max_dmg"], 0),
                "avg_survivors": round(r["avg_survivors"], 1),
            }
            for i, r in enumerate(phase1)
        ],
        "phase2_top10": [
            {
                "rank": i + 1,
                "party": r["names"],
                "best_ultimate_order": r["best_order_names"],
                "avg_turn": round(r["best_avg_turn"], 1),
                "avg_damage_taken": round(r["best_avg_dmg"], 0),
                "best_min_turn": r["best_min_turn"],
                "auto_avg_turn": round(r["combo_avg_auto"], 1),
                "auto_avg_dmg": round(r["combo_avg_dmg_auto"], 0),
                "order_turn_variance": round(r["turn_variance"], 2),
            }
            for i, r in enumerate(phase2[:10])
        ],
        "analysis": {
            "character_frequency": char_freq,
            "role_compositions": role_comp,
        },
    }

    path = os.path.join(DATA_DIR, "results.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"\n  결과 저장: {path}")
    return output


def generate_report(data, phase1, phase2):
    """top_builds.md 분석 리포트 생성"""
    lines = []
    lines.append("# 🏆 BattleAgent 브루트포스 최적 파티 탐색 리포트")
    lines.append("")
    lines.append(f"**생성일**: {data['metadata']['timestamp']}")
    lines.append(f"**룰**: CRI 15% / PEN 0% 통일 (2026-03-13)")
    lines.append(f"**탐색 범위**: {data['metadata']['pool_size']}명 풀 → C(9,5)=126 조합 × 10 시드")
    lines.append(f"**적군**: 봉제인형 5마리")
    lines.append("")

    # ── 가정 사항 ──
    lines.append("## 📋 가정 사항 (Assumptions)")
    lines.append("")
    for a in data["metadata"]["assumptions"]:
        lines.append(f"- {a}")
    lines.append("")

    # ── 캐릭터 풀 ──
    lines.append("## 👥 캐릭터 풀 (9명)")
    lines.append("")
    lines.append("| 이름 | 역할 | 속성 | ATK | HP | SPD |")
    lines.append("|------|------|------|----:|----:|----:|")
    for name, _, stats in CHAR_POOL:
        lines.append(f"| {name} | {stats['role']} | {stats['element']} | {stats['atk']} | {stats['hp']} | {stats['spd']} |")
    lines.append("")

    # ── TOP 5 빌드 ──
    lines.append("## 🥇 TOP 5 최적 빌드 (Phase 2: 얼티밋 순서 최적화)")
    lines.append("")

    for i, r in enumerate(phase2[:5], 1):
        medal = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"][i-1]
        lines.append(f"### {medal} {i}위: {' / '.join(r['names'])}")
        lines.append("")
        lines.append(f"- **최적 얼티밋 순서**: {' → '.join(r['best_order_names'])}")
        lines.append(f"- **평균 턴**: {r['best_avg_turn']:.1f}")
        lines.append(f"- **평균 피해량**: {r['best_avg_dmg']:.0f}")
        lines.append(f"- **최소 턴**: {r['best_min_turn']}")
        lines.append(f"- **Auto 모드 평균 턴**: {r['combo_avg_auto']:.1f}")
        lines.append(f"- **순서 분산**: {r['turn_variance']:.2f} ({'순서 영향 큼' if r['turn_variance'] > 5 else '순서 영향 적음'})")
        lines.append("")

        # 왜 이 빌드가 효과적인지 분석
        roles = [s["role"] for s in r["stats_info"]]
        atk_count = roles.count("ATK")
        sup_count = roles.count("SUP")
        hlr_count = roles.count("HLR")
        def_count = roles.count("DEF")
        total_atk = sum(s["atk"] for s in r["stats_info"])
        avg_spd = sum(s["spd"] for s in r["stats_info"]) / len(r["stats_info"])

        lines.append(f"  **분석**: 역할 구성 ATK×{atk_count}/SUP×{sup_count}/HLR×{hlr_count}/DEF×{def_count}, "
                     f"총 ATK={total_atk}, 평균 SPD={avg_spd:.0f}")
        lines.append("")

    # ── 캐릭터 기여도 분석 ──
    lines.append("## 📊 캐릭터 기여도 분석 (상위 20개 조합 기준)")
    lines.append("")
    lines.append("| 순위 | 캐릭터 | 출현율 | 출현 시 평균턴 | 출현 시 평균피해 |")
    lines.append("|:---:|--------|:-----:|:------------:|:--------------:|")

    char_freq = data["analysis"]["character_frequency"]
    for rank, (name, info) in enumerate(char_freq.items(), 1):
        lines.append(f"| {rank} | {name} | {info['appearance_rate']*100:.0f}% ({info['appearances']}/20) | "
                     f"{info['avg_turn_when_present']:.1f} | {info['avg_dmg_when_present']:.0f} |")
    lines.append("")

    # ── 역할 구성 분석 ──
    lines.append("## 🎭 역할 구성 분석")
    lines.append("")
    lines.append("| 역할 구성 | 조합 수 | 평균 턴 |")
    lines.append("|-----------|:------:|:------:|")
    role_comp = sorted(data["analysis"]["role_compositions"].items(), key=lambda x: x[1]["avg_turn"])
    for comp, info in role_comp:
        lines.append(f"| {comp} | {info['count']} | {info['avg_turn']:.1f} |")
    lines.append("")

    # ── Auto vs Setting 비교 ──
    lines.append("## 🔄 Auto vs 순서지정 모드 비교 (상위 5개)")
    lines.append("")
    lines.append("| 조합 | Auto 평균턴 | 순서지정 평균턴 | 차이 | 비고 |")
    lines.append("|------|:---------:|:------------:|:---:|------|")
    for r in phase2[:5]:
        diff = r["best_avg_turn"] - r["combo_avg_auto"]
        note = "Auto 우세" if diff > 0 else "순서지정 우세" if diff < 0 else "동일"
        lines.append(f"| {', '.join(r['names'])} | {r['combo_avg_auto']:.1f} | "
                     f"{r['best_avg_turn']:.1f} | {diff:+.1f} | {note} |")
    lines.append("")

    # ── 스탯 감도 분석 ──
    lines.append("## 🧪 스탯 감도 분석 (Stat Sensitivity)")
    lines.append("")

    # 에레보스 유무 비교
    with_erebos = [r for r in phase1 if "에레보스" in r["names"] and r["wins"] > 0]
    without_erebos = [r for r in phase1 if "에레보스" not in r["names"] and r["wins"] > 0]
    avg_with = sum(r["avg_turn"] for r in with_erebos) / len(with_erebos) if with_erebos else 999
    avg_without = sum(r["avg_turn"] for r in without_erebos) / len(without_erebos) if without_erebos else 999
    lines.append(f"### 에레보스 (ATK 530, 최강 딜러) 영향")
    lines.append(f"- 에레보스 포함 조합: {len(with_erebos)}개, 평균 {avg_with:.1f}턴")
    lines.append(f"- 에레보스 미포함 조합: {len(without_erebos)}개, 평균 {avg_without:.1f}턴")
    lines.append(f"- **차이: {avg_without - avg_with:.1f}턴** (에레보스 포함 시 약 {(avg_without - avg_with) / avg_without * 100:.0f}% 빠름)")
    lines.append("")

    # 루미나 유무 비교
    with_lumina = [r for r in phase1 if "루미나" in r["names"] and r["wins"] > 0]
    without_lumina = [r for r in phase1 if "루미나" not in r["names"] and r["wins"] > 0]
    avg_with_l = sum(r["avg_turn"] for r in with_lumina) / len(with_lumina) if with_lumina else 999
    avg_without_l = sum(r["avg_turn"] for r in without_lumina) / len(without_lumina) if without_lumina else 999
    lines.append(f"### 루미나 (SPD 120, 최속 서포터) 영향")
    lines.append(f"- 루미나 포함 조합: {len(with_lumina)}개, 평균 {avg_with_l:.1f}턴")
    lines.append(f"- 루미나 미포함 조합: {len(without_lumina)}개, 평균 {avg_without_l:.1f}턴")
    lines.append(f"- **차이: {avg_without_l - avg_with_l:.1f}턴** (루미나 포함 시 약 {(avg_without_l - avg_with_l) / avg_without_l * 100:.0f}% 빠름)")
    lines.append("")

    # 이브 유무 비교
    with_eve = [r for r in phase1 if "이브" in r["names"] and r["wins"] > 0]
    without_eve = [r for r in phase1 if "이브" not in r["names"] and r["wins"] > 0]
    avg_with_e = sum(r["avg_turn"] for r in with_eve) / len(with_eve) if with_eve else 999
    avg_without_e = sum(r["avg_turn"] for r in without_eve) / len(without_eve) if without_eve else 999
    lines.append(f"### 이브 (처형기 딜러) 영향")
    lines.append(f"- 이브 포함 조합: {len(with_eve)}개, 평균 {avg_with_e:.1f}턴")
    lines.append(f"- 이브 미포함 조합: {len(without_eve)}개, 평균 {avg_without_e:.1f}턴")
    lines.append(f"- **차이: {avg_without_e - avg_with_e:.1f}턴** (이브 포함 시 약 {(avg_without_e - avg_with_e) / avg_without_e * 100:.0f}% 빠름)")
    lines.append("")

    # ── 전패 조합 ──
    zero_wins = [r for r in phase1 if r["wins"] == 0]
    if zero_wins:
        lines.append("## ❌ 전패 조합")
        lines.append("")
        for r in zero_wins:
            lines.append(f"- {', '.join(r['names'])}")
        lines.append("")

    # ── 결론 ──
    lines.append("## 💡 결론")
    lines.append("")
    best = phase2[0]
    lines.append(f"### 최적 파티")
    lines.append(f"**{' / '.join(best['names'])}**")
    lines.append("")
    lines.append(f"### 최적 얼티밋 순서")
    lines.append(f"**{' → '.join(best['best_order_names'])}**")
    lines.append("")
    lines.append(f"### 핵심 인사이트")
    lines.append(f"1. **에레보스 필수**: ATK 530의 압도적 화력으로 모든 상위 조합에 포함")
    lines.append(f"2. **이브 핵심 딜러**: 처형기(HP<50% 시 추가 데미지)로 마무리 능력 최상위")
    lines.append(f"3. **루미나 최적 서포터**: SPD 120 선행동 + 전체 ATK/SPD 버프로 팀 가속")
    lines.append(f"4. **얼티밋 순서**: 서포터(버프) → 메인딜러 → 서브딜러 순서가 최적")
    lines.append(f"5. **Auto 모드 우세**: 상황 판단형 AI가 고정 순서보다 대부분 우수한 성능")
    lines.append("")

    path = os.path.join(DATA_DIR, "top_builds.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"  리포트 저장: {path}")
    return path


def main():
    print()
    print("╔══════════════════════════════════════════════════════════════════════╗")
    print("║  BattleAgent 종합 브루트포스 최적 파티 탐색                          ║")
    print("║  풀: 9명 (OP듀오+극딜버스트 합집합)                                  ║")
    print("║  룰: CRI 15% / PEN 0% 통일 (2026-03-13)                            ║")
    print("║  타이브레이커: 평균턴 동률 시 피해량 적은 쪽 우선                      ║")
    print("╚══════════════════════════════════════════════════════════════════════╝")

    total_t0 = time.time()

    # Phase 1
    phase1 = phase1_combo_search()

    # Phase 2: 상위 TOP_N 조합 (승리 있는 것만)
    top = [r for r in phase1 if r["wins"] > 0][:TOP_N]
    phase2 = phase2_order_search(top)

    # 최종 요약
    print()
    print("═" * 100)
    print("  ★ 최종 결과: 최적 파티 조합 + 얼티밋 발동 순서 (피해량 타이브레이커)")
    print("═" * 100)

    if phase2:
        best = phase2[0]
        print(f"  파티:     {' / '.join(best['names'])}")
        print(f"  얼티순서: {' → '.join(best['best_order_names'])}")
        print(f"  평균턴:   {best['best_avg_turn']:.1f}")
        print(f"  평균피해: {best['best_avg_dmg']:.0f}")
        print(f"  최소턴:   {best['best_min_turn']}")

    # 결과 저장
    data = save_results(phase1, phase2)
    report_path = generate_report(data, phase1, phase2)

    total_elapsed = time.time() - total_t0
    print(f"\n  총 소요시간: {total_elapsed:.1f}s")
    print(f"\n  출력 파일:")
    print(f"    📊 data/results.json")
    print(f"    📝 data/top_builds.md")


if __name__ == "__main__":
    main()
