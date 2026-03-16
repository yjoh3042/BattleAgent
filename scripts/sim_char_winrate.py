"""캐릭터별 개인 승률 분석 (개선판)

기준팀: 데레사 + 라가라자 + c600 (3명, 의도적 약체)
+ 테스트 캐릭터 1명 = 총 4명

적군1: 중간난이도A - 봉제인형ABC + 아우로라(enemy) + 미리암(enemy)
       → 강딜러 ~100%, 서포터 10~90%, 방어형 ~17% 의 의미있는 분산
적군2: 중간난이도B - 봉제인형ABC + 아우로라(enemy) + 브라우니(enemy)
       → 강딜러 ~100%, 서포터 0~50%, 방어형 ~0% 의 다른 패턴 분산
시드: N=100

실행: py -X utf8 scripts/sim_char_winrate.py
"""
import sys
import os
import dataclasses

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from battle.battle_engine import BattleEngine
from battle.enums import BattleResult, Element, Role
from fixtures.test_data import (
    make_aurora, make_elysion, make_tiwaz, make_sangah,
    make_morgan, make_dabi, make_gumiho,
    make_jiva, make_kararatri, make_deresa,
    make_ragaraja, make_salmakis,
    make_eve, make_thisbe, make_bari,
    make_dogyehwa,
    make_brownie, make_batory, make_pan,
    make_miriam, make_metis, make_grilla,
    make_danu,
    make_ashtoreth, make_sitri, make_mona,
    make_semele, make_tiwaz, make_titania, make_oneiroi,
    make_c600,
    make_frey, make_banshee, make_artemis,
    make_mircalla, make_yuna, make_kubaba,
    make_anubis, make_c601,
    make_teddy_a, make_teddy_b, make_teddy_c,
)

# ── 기준팀 (약체 3인) ──────────────────────────────────────────────────────
def make_control_team():
    return [make_deresa(), make_ragaraja(), make_c600()]

# ── 적군 빌더 ──────────────────────────────────────────────────────────────
def _to_enemy(c):
    """CharacterData 를 enemy side 로 전환"""
    return dataclasses.replace(c, side="enemy")

def make_enemy_mid_a():
    """중간난이도A: 봉제인형ABC + 아우로라(enemy) + 미리암(enemy)
    강딜러~100%, 서포터10~90%, 방어형~17% 분산 확인됨"""
    return [make_teddy_a(), make_teddy_b(), make_teddy_c(),
            _to_enemy(make_aurora()), _to_enemy(make_miriam())]

def make_enemy_mid_b():
    """중간난이도B: 봉제인형ABC + 아우로라(enemy) + 브라우니(enemy)
    강딜러~100%, 서포터0~53%, 방어형~0% 분산 확인됨"""
    return [make_teddy_a(), make_teddy_b(), make_teddy_c(),
            _to_enemy(make_aurora()), _to_enemy(make_brownie())]

# ── 테스트 대상 (기준팀 3인 제외) ──────────────────────────────────────────
CHARS = {
    "모건":      make_morgan,
    "다비":      make_dabi,
    "구미호":    make_gumiho,
    "지바":      make_jiva,
    "카라라트리": make_kararatri,
    "살마키스":  make_salmakis,
    "이브":      make_eve,
    "상아":      make_sangah,
    "티스베":    make_thisbe,
    "바리":      make_bari,
    "도계화":    make_dogyehwa,
    "엘리시온":  make_elysion,
    "브라우니":  make_brownie,
    "바토리":    make_batory,
    "판":        make_pan,
    "미리암":    make_miriam,
    "아우로라":  make_aurora,
    "메티스":    make_metis,
    "그릴라":    make_grilla,
    "다누":      make_danu,
    "아슈토레스": make_ashtoreth,
    "시트리":    make_sitri,
    "모나":      make_mona,
    "세멜레":    make_semele,
    "티와즈":    make_tiwaz,
    "티타니아":  make_titania,
    "오네이로이": make_oneiroi,
    "프레이":    make_frey,
    "반시":      make_banshee,
    "아르테미스": make_artemis,
    "미르칼라":  make_mircalla,
    "유나":      make_yuna,
    "쿠바바":    make_kubaba,
    "아누비스":  make_anubis,
    "c601":     make_c601,
}

SEEDS = 100

ELEMENT_KR = {
    Element.FIRE:   "화",
    Element.WATER:  "수",
    Element.FOREST: "목",
    Element.LIGHT:  "광",
    Element.DARK:   "암",
}

ROLE_KR = {
    Role.ATTACKER:  "공격형",
    Role.DEFENDER:  "방어형",
    Role.MAGICIAN:  "마법형",
    Role.SUPPORTER: "보조형",
    Role.HEALER:    "회복형",
}

# 스킬 패턴 설명 (역할 기반)
SKILL_PATTERN = {
    Role.ATTACKER:  "단일/광역 딜",
    Role.DEFENDER:  "도발/방어 버프",
    Role.MAGICIAN:  "마법 광역 딜",
    Role.SUPPORTER: "버프/디버프",
    Role.HEALER:    "힐/회복",
}


def run_char_vs(make_fn, make_enemies_fn):
    """SEEDS 시드 전투 실행, 승리 수 반환"""
    wins = 0
    for seed in range(SEEDS):
        allies = make_control_team() + [make_fn()]
        enemies = make_enemies_fn()
        engine = BattleEngine(ally_units=allies, enemy_units=enemies, seed=seed)
        result = engine.run()
        if result == BattleResult.ALLY_WIN:
            wins += 1
    return wins


def main():
    # results: (name, element, role, spd, wr_m10, wr_m03, wr_avg)
    results = []

    total = len(CHARS)
    for idx, (name, make_fn) in enumerate(CHARS.items(), 1):
        wins_m10 = run_char_vs(make_fn, make_enemy_mid_a)
        wins_m03 = run_char_vs(make_fn, make_enemy_mid_b)

        wr_m10 = wins_m10 / SEEDS
        wr_m03 = wins_m03 / SEEDS
        wr_avg = (wr_m10 + wr_m03) / 2

        char_data = make_fn()
        elem = char_data.element
        role = char_data.role
        spd = char_data.stats.spd

        results.append((name, elem, role, spd, wr_m10, wr_m03, wr_avg))
        print(f"[{idx:2d}/{total}] {name:<10}  vsM10={wr_m10*100:5.1f}%  vsM03={wr_m03*100:5.1f}%  avg={wr_avg*100:5.1f}%")

    # 평균 승률 내림차순 정렬
    results.sort(key=lambda x: x[6], reverse=True)

    # ── 1. 전체 순위 ───────────────────────────────────────────────────────
    print()
    print("=" * 78)
    print("  캐릭터별 개인 승률 분석")
    print("  기준팀: 데레사+라가라자+c600 + 테스트캐릭터 (총 4명)")
    print("  적군A: 봉제ABC+아우로라+미리암 / 적군B: 봉제ABC+아우로라+브라우니   N=100시드")
    print("=" * 78)
    header = (f"  {'순위':<4} {'캐릭터':<10} {'속성':<4} {'역할':<8}"
              f" {'vs적A':>7} {'vs적B':>7} {'평균승률':>8}  {'SPD':>5}")
    print(header)
    print("  " + "-" * 74)

    for rank, (name, elem, role, spd, wr_m10, wr_m03, wr_avg) in enumerate(results, 1):
        elem_str = ELEMENT_KR.get(elem, str(elem))
        role_str = ROLE_KR.get(role, str(role))
        print(f"  {rank:>2}위  {name:<10} {elem_str:<4} {role_str:<8}"
              f" {wr_m10*100:>6.1f}%  {wr_m03*100:>6.1f}%  {wr_avg*100:>7.1f}%  {int(spd):>5}")

    # 최하위 강조
    print()
    print("  최하위 5명:")
    for rank, (name, elem, role, spd, wr_m10, wr_m03, wr_avg) in \
            enumerate(results[-5:][::-1], len(results) - 4):
        elem_str = ELEMENT_KR.get(elem, str(elem))
        role_str = ROLE_KR.get(role, str(role))
        print(f"  {rank:>2}위  {name:<10} {elem_str:<4} {role_str:<8}"
              f" {wr_m10*100:>6.1f}%  {wr_m03*100:>6.1f}%  {wr_avg*100:>7.1f}%  {int(spd):>5}")

    # ── 2. 역할별 평균 승률 ───────────────────────────────────────────────
    print()
    print("=" * 50)
    print("  역할별 평균 승률")
    print("=" * 50)
    for role in [Role.ATTACKER, Role.MAGICIAN, Role.SUPPORTER, Role.DEFENDER, Role.HEALER]:
        group = [wr_avg for _, _, r, _, _, _, wr_avg in results if r == role]
        if group:
            avg = sum(group) / len(group) * 100
            label = ROLE_KR[role]
            print(f"  {label}: {avg:.1f}%  (n={len(group)})")
        else:
            print(f"  {ROLE_KR[role]}: 해당 없음")

    # ── 3. 속성별 평균 승률 ───────────────────────────────────────────────
    print()
    print("=" * 50)
    print("  속성별 평균 승률")
    print("=" * 50)
    for elem in [Element.FIRE, Element.WATER, Element.FOREST, Element.LIGHT, Element.DARK]:
        group = [wr_avg for _, e, _, _, _, _, wr_avg in results if e == elem]
        if group:
            avg = sum(group) / len(group) * 100
            label = ELEMENT_KR[elem]
            print(f"  {label}: {avg:.1f}%  (n={len(group)})")
        else:
            print(f"  {ELEMENT_KR[elem]}: 해당 없음")

    # ── 4. 최하위 5캐릭터 심층 분석 ───────────────────────────────────────
    print()
    print("=" * 80)
    print("  최하위 5 캐릭터 심층 분석")
    print("=" * 80)
    print(f"  {'순위':<4} {'캐릭터':<10} {'평균승률':>8} {'vs적A':>7} {'vs적B':>7}  약점 분석")
    print("  " + "-" * 78)

    bottom5 = results[-5:][::-1]
    for rank, (name, elem, role, spd, wr_m10, wr_m03, wr_avg) in \
            enumerate(bottom5, len(results) - 4):
        # 약점 분석 자동 추론
        issues = []
        if role == Role.DEFENDER:
            issues.append("도발/방어형 → 4인팀에서 딜 기여 없음")
        if role == Role.HEALER:
            issues.append("힐러 → 봉제인형 강팀 상대 힐만으로 역부족")
        if role == Role.SUPPORTER and spd < 110:
            issues.append("서포터지만 SPD 낮아 선행 버프 어려움")
        if role == Role.SUPPORTER and spd >= 110:
            issues.append("서포터 → 버프효과가 기준팀 딜러 부재로 시너지 미발휘")
        if role == Role.ATTACKER and spd < 100:
            issues.append("공격형이지만 SPD 낮아 선제 불가")
        if wr_m10 < wr_m03 - 0.1:
            issues.append("vs야성해방 특히 취약(M10 피해 큼)")
        if wr_m03 < wr_m10 - 0.1:
            issues.append("vs출혈폭딜 특히 취약(M03 피해 큼)")
        if not issues:
            if wr_avg < 0.25:
                issues.append("극저승률 → 전체적 전투 기여 부족")
            elif wr_avg < 0.40:
                issues.append("낮은 기여도 → 기준팀과 시너지 부재")
            else:
                issues.append("기준팀 딜 부족으로 역전 어려움")
        issue_str = "; ".join(issues)
        print(f"  {rank:>2}위  {name:<10} {wr_avg*100:>7.1f}%  {wr_m10*100:>6.1f}%  {wr_m03*100:>6.1f}%  {issue_str}")

    # ── 5. 약한 이유 종합 코멘트 ───────────────────────────────────────────
    print()
    print("=" * 80)
    print("  [종합 분석] 최하위 캐릭터들이 약한 이유")
    print("=" * 80)
    print("""
  기준팀 구성: 데레사(방어형/도발), 라가라자(자버프형 공격), c600(기본 서포터)
  이 팀은 의도적으로 딜 출력이 낮고, 시너지가 없는 조합입니다.

  [공통 약점 패턴]
  1. 방어형(Defender): 데레사가 이미 도발/방어를 담당하므로, 추가 방어형은
     기여가 겹치고 딜을 보완하지 못해 4인 팀의 화력이 극도로 낮아집니다.

  2. 힐러(Healer): 강한 메타팀 상대로는 힐만으로는 역부족.
     적의 5인 딜이 힐 회복량을 압도하면 장기전에서도 패배합니다.

  3. 자버프 전용 공격형: 라가라자처럼 자기 자신에게만 버프를 거는 캐릭터는
     기준팀의 다른 딜러가 없으면 '1인 딜' 구조가 되어 효율이 낮습니다.

  4. 서포터 중 SPD 낮은 캐릭터: 버프를 거는 타이밍이 늦으면 딜러가 이미
     죽거나 행동 기회를 잃어 시너지가 발동하지 않습니다.

  5. CC 전용 마법형(구미호, 오네이로이, 판): 적을 마비시켜도 기준팀이
     그 기회에 충분한 딜을 넣지 못하면 승리로 이어지지 않습니다.
     CC는 딜러 팀과의 조합이 전제되어야 빛납니다.

  [적군 세트 비교]
  - vs 적군A(봉제ABC+아우로라+미리암): 아우로라의 전체 ATK버프와 미리암의
    광역딜이 조합되어 중간 난이도를 형성합니다. 서포터/방어형은 딜 부재로
    아우로라 버프를 활용하지 못해 낮은 승률을 기록합니다.
  - vs 적군B(봉제ABC+아우로라+브라우니): 브라우니의 전체힐이 추가되어
    장기전이 될수록 아군에게 불리합니다. 강딜러는 빠른 처치로 힐 전에
    승부를 내지만, 힐러나 서포터 위주 팀은 지속딜 부족으로 패배합니다.
""")


if __name__ == "__main__":
    main()
