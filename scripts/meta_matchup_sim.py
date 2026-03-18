"""메타 조합 공격덱/방어덱 승률 시뮬레이션 v2.0

10개 메타 × 10개 메타 × 2 덱타입 × N 시드 전투 시뮬레이션.
결과를 테이블로 출력한다.

═══════════════════════════════════════════════════════════════
메타 설계 v2.0 — 다른 게임 기믹 참고
═══════════════════════════════════════════════════════════════
M01 🔥화상지옥   Epic Seven Burn팀     — 4 화상원 DoT 스택
M02 🧊빙결감옥   서머너즈워 CC Lock    — 3 CC메이지 행동봉쇄
M03 ⚡독살처형   붕괴:스타레일 Break    — 독 칩딜 → 이브 처형
M04 💎하이퍼캐리 붕괴:스타레일 Hyper    — 쿠바바 7.2× 원킬 버프
M05 🛡️철벽요새   방어덱 Stall          — 더블탱크+부활 생존전
M06 🗡️반격요새   Epic Seven Counter    — 반격탱크 자동딜
M07 🌀속도지배   서머너즈워 Speed       — CTB 턴 독점
M08 🎭혼돈의밤   원신 Reaction         — 공포+화상+디버프
M09 💥전멸폭격   Epic Seven Cleave     — 트리플 AoE 한방
M10 ⚔️광전사     킹스레이드 Burst      — 순수 고배율 폭딜

설계 원칙:
  - 모든 메타에 실제 힐러 1명 이상 필수 (M04 전패 방지)
  - 캐릭터 재사용 최대 2회 (48명 유니크 사용 / 56명 중)
  - 역할 반전 캐릭터 의도적 배치 (DPS 서포터는 DPS 슬롯)
  - 5속성 균등 분포
═══════════════════════════════════════════════════════════════
"""
import sys
sys.path.insert(0, "src")

from typing import List, Dict, Tuple
from battle.battle_engine import BattleEngine
from battle.enums import BattleResult
from battle.models import CharacterData
from fixtures.test_data import (
    # ── M01 화상지옥: 모건/다비/카라라트리/드미테르/지바 ──
    make_morgan, make_dabi, make_kararatri, make_demeter, make_jiva,
    # ── M02 빙결감옥: 마야우엘/마프데트/에르제베트/메티스/에우로스 ──
    make_mayahuel, make_mafdet, make_elizabeth, make_metis, make_euros,
    # ── M03 독살처형: 이브/바리/도계화/그릴라/브라우니 ──
    make_eve, make_bari, make_dogyehwa, make_grilla, make_brownie,
    # ── M04 하이퍼캐리: 쿠바바/루미나/시트리/티타니아/프레이야 ──
    make_kubaba, make_c600, make_sitri, make_titania, make_freya,
    # ── M05 철벽요새: 엘리시온/샤를/다누/네반/레다 ──
    make_elysion, make_charlotte, make_danu, make_nevan, make_leda,
    # ── M06 반격요새: 프레이/데레사/아누비스/유나/다나 ──
    make_frey, make_deresa, make_anubis, make_yuna, make_dana,
    # ── M07 속도지배: 니르티/모나/상아/티스베/아르테미스 ──
    make_nirrti, make_mona, make_sangah, make_thisbe, make_artemis,
    # ── M08 혼돈의밤: 미리암/세멜레/구미호/자청비/베르들레 ──
    make_miriam, make_semele, make_gumiho, make_jacheongbi, make_verdelet,
    # ── M09 전멸폭격: 에레보스/라가라자/두엣샤/아우로라/에우로스(재) ──
    make_c601, make_ragaraja, make_duetsha, make_aurora,
    # ── M10 광전사: 아슈토레스/카인/오네이로이/맘몬/다나(재) ──
    make_ashtoreth, make_cain, make_oneiroi, make_mammon,
)

# ═══════════════════════════════════════════════════════════
# 10개 메타 구성 (v2.0 — 게임 기믹 참고)
# ═══════════════════════════════════════════════════════════

def meta_m01() -> Tuple[str, List[CharacterData]]:
    """M01 화상지옥 (Epic Seven Burn팀)
    모건(MAG/self ATK+30%→AoE bleed) + 다비(MAG/burn spread)
    + 카라라트리(ATK/burn+DEF-20%) + 드미테르(SUP/burn 30% 3T)
    + 지바(HLR/heal+ATK buff)
    → 4개 화상원이 DoT 3스택 유지하여 지속 피해로 적 소모"""
    return "M01 🔥화상지옥", [
        make_morgan(), make_dabi(), make_kararatri(),
        make_demeter(), make_jiva(),
    ]

def meta_m02() -> Tuple[str, List[CharacterData]]:
    """M02 빙결감옥 (서머너즈워 CC Lock + 킬파워)
    마야우엘(MAG/Freeze 2T all) + 마프데트(MAG/Stun 2T all)
    + 에르제베트(ATK/4.43x normal + poison 30% AoE) + 메티스(DEF/DEF buff+cleanse)
    + 에우로스(HLR/heal+cleanse)
    → CC로 적 봉쇄하는 동안 에르제베트가 4.43x 노멀+독으로 처리"""
    return "M02 🧊빙결감옥", [
        make_mayahuel(), make_mafdet(), make_elizabeth(),
        make_metis(), make_euros(),
    ]

def meta_m03() -> Tuple[str, List[CharacterData]]:
    """M03 독살처형 (붕괴:스타레일 Break→Execute)
    이브(ATK/4.50x+3.00x execute) + 바리(MAG/매 스킬 poison)
    + 도계화(MAG/poison+stun) + 그릴라(SUP/ATK+CRI buff)
    + 브라우니(HLR/cleanse+SP)
    → 독으로 HP를 깎고 이브가 30% 이하에서 7.50x 처형"""
    return "M03 ⚡독살처형", [
        make_eve(), make_bari(), make_dogyehwa(),
        make_grilla(), make_brownie(),
    ]

def meta_m04() -> Tuple[str, List[CharacterData]]:
    """M04 하이퍼캐리 (붕괴:스타레일 Hypercarry)
    쿠바바(ATK/7.20x ult) + 루미나(MAG/ATK+35%+CRI_DMG+50%)
    + 시트리(SUP/ATK+25%+CRI_DMG+30%) + 티타니아(DEF/ATK+20%+heal)
    + 프레이야(HLR/heal+cleanse)
    → 트리플 버퍼가 쿠바바에 올인, 7.20x가 버프로 원킬 머신"""
    return "M04 💎하이퍼캐리", [
        make_kubaba(), make_c600(), make_sitri(),
        make_titania(), make_freya(),
    ]

def meta_m05() -> Tuple[str, List[CharacterData]]:
    """M05 철벽요새 (방어덱 Stall/Turtle)
    엘리시온(DEF/HEAL 50%+46%) + 샤를(DEF/BARRIER 30%+35%)
    + 다누(ATK→역할반전 healer/revive) + 네반(HLR/heal+barrier)
    + 레다(SUP/ATK+DEF buff)
    → 더블탱크 + 부활 + 배리어 중첩. 방어덱에서 생존만 하면 승리"""
    return "M05 🛡️철벽요새", [
        make_elysion(), make_charlotte(), make_danu(),
        make_nevan(), make_leda(),
    ]

def meta_m06() -> Tuple[str, List[CharacterData]]:
    """M06 반격요새 (Epic Seven Counter/Bruiser)
    프레이(DEF/Counter 3T+ATK+25%+CRI+40%) + 데레사(DEF/Counter+Row)
    + 아누비스(ATK/penetrate+execute) + 유나(SUP/DEF+20%+heal)
    + 다나(HLR/4.28x normal+heal)
    → 반격탱크가 피격시마다 자동 딜, 아누비스가 약해진 적 처형"""
    return "M06 🗡️반격요새", [
        make_frey(), make_deresa(), make_anubis(),
        make_yuna(), make_dana(),
    ]

def meta_m07() -> Tuple[str, List[CharacterData]]:
    """M07 속도지배 (서머너즈워 Speed Team)
    니르티(ATK/hybrid self-sustain) + 모나(DEF/SPD+15 buff)
    + 상아(SUP/SPD-20 debuff+ATK buff) + 티스베(HLR/SPD+15/+20 buff)
    + 아르테미스(MAG/multi-hit+DEF shred)
    → 아군 SPD+30 / 적 SPD-20 → CTB에서 1.5배 턴 우위"""
    return "M07 🌀속도지배", [
        make_nirrti(), make_mona(), make_sangah(),
        make_thisbe(), make_artemis(),
    ]

def meta_m08() -> Tuple[str, List[CharacterData]]:
    """M08 혼돈의밤 (원신 Reaction/Debuff)
    미리암(ATK/AoE PANIC 2T) + 세멜레(MAG/ATK-20%+burn)
    + 구미호(MAG/PANIC 1T) + 자청비(SUP/ATK+DEF buff)
    + 베르들레(HLR/heal+cleanse)
    → 공포(행동불가30%) + ATK디버프 + 화상으로 적 전투력 무력화"""
    return "M08 🎭혼돈의밤", [
        make_miriam(), make_semele(), make_gumiho(),
        make_jacheongbi(), make_verdelet(),
    ]

def meta_m09() -> Tuple[str, List[CharacterData]]:
    """M09 전멸폭격 (Epic Seven Cleave)
    에레보스(MAG/3.50x AoE+DEF-30%+bleed) + 라가라자(ATK/3.40x AoE)
    + 두엣샤(MAG/3.20x ROW) + 아우로라(SUP/ATK+20%+CRI buff)
    + 에우로스(HLR/heal+cleanse) [재사용 2회차]
    → 한 로테이션에 트리플 AoE로 적 전원 소멸"""
    return "M09 💥전멸폭격", [
        make_c601(), make_ragaraja(), make_duetsha(),
        make_aurora(), make_euros(),
    ]

def meta_m10() -> Tuple[str, List[CharacterData]]:
    """M10 광전사 (킹스레이드 Burst)
    아슈토레스(ATK/4.50x ult) + 카인(ATK/4.43x normal)
    + 오네이로이(SUP→역할반전 DPS/Sleep CC) + 맘몬(DEF/Stun+AoE)
    + 다나(HLR/4.28x normal+heal) [재사용 2회차]
    → 3명이 각각 4x+ 배율로 순수 폭딜, 탱크+힐러가 버틸 동안 처리"""
    return "M10 ⚔️광전사", [
        make_ashtoreth(), make_cain(), make_oneiroi(),
        make_mammon(), make_dana(),
    ]


ALL_METAS = [meta_m01, meta_m02, meta_m03, meta_m04, meta_m05,
             meta_m06, meta_m07, meta_m08, meta_m09, meta_m10]

# ═══════════════════════════════════════════════════════════
# 시뮬레이션
# ═══════════════════════════════════════════════════════════

NUM_SEEDS = 30  # 시드 수 (통계 안정성 개선: 20→30)

def _set_enemy_side(units: List[CharacterData]) -> List[CharacterData]:
    """적 유닛의 side를 'enemy'로 변경하고 타일 위치도 적측으로 배치."""
    for i, u in enumerate(units):
        u.side = "enemy"
        # 적은 3×3 그리드 반대편에 배치 (row 0~2, col 0~2)
        u.tile_pos = (i // 3, i % 3)
    return units


def run_matchup(ally_meta_fn, enemy_meta_fn, deck_type: str, seeds: int = NUM_SEEDS) -> Dict:
    """한 매치업을 여러 시드로 돌려 승률 계산."""
    wins = 0
    losses = 0
    timeouts = 0

    for seed in range(seeds):
        ally_name, ally_units = ally_meta_fn()
        enemy_name, enemy_units = enemy_meta_fn()

        # 아군/적군 side 및 타일 위치 설정
        for i, u in enumerate(ally_units):
            u.side = "ally"
            u.tile_pos = (i // 3, i % 3)
        _set_enemy_side(enemy_units)

        engine = BattleEngine(
            ally_units, enemy_units,
            deck_type=deck_type,
            seed=seed * 7 + 13,  # 다양한 시드
        )
        result = engine.run()

        if result == BattleResult.ALLY_WIN:
            wins += 1
        elif result == BattleResult.ENEMY_WIN:
            losses += 1
        else:
            timeouts += 1

    return {
        "wins": wins,
        "losses": losses,
        "timeouts": timeouts,
        "win_rate": wins / seeds * 100,
    }


def main():
    print("=" * 100)
    print("  메타 조합 공격덱/방어덱 승률 시뮬레이션 v2.0")
    print(f"  시드 수: {NUM_SEEDS}회 | 덱 타입: offense + defense")
    print("  설계: 다른 게임 기믹 참고 (Epic Seven/서머너즈워/붕스레/원신/킹스레이드)")
    print("=" * 100)

    meta_names = []
    for fn in ALL_METAS:
        name, _ = fn()
        meta_names.append(name)

    # ── 공격덱 승률 매트릭스 ──
    print("\n\n📊 [공격덱] 승률 매트릭스 (행=ally, 열=enemy, 타임오버=ally 패배)")
    print("-" * 100)

    offense_matrix = []
    header = f"{'':20s}"
    for i, name in enumerate(meta_names):
        short = name.split()[0]
        header += f" {short:>6s}"
    header += "   평균"
    print(header)

    for i, ally_fn in enumerate(ALL_METAS):
        row = []
        row_str = f"{meta_names[i]:20s}"
        for j, enemy_fn in enumerate(ALL_METAS):
            if i == j:
                row.append(None)
                row_str += "     - "
            else:
                result = run_matchup(ally_fn, enemy_fn, "offense")
                wr = result["win_rate"]
                row.append(wr)
                row_str += f" {wr:5.0f}%"
        offense_matrix.append(row)
        # 평균 (자기 자신 제외)
        valid = [x for x in row if x is not None]
        avg = sum(valid) / len(valid) if valid else 0
        row_str += f"  {avg:5.1f}%"
        print(row_str)

    # ── 방어덱 승률 매트릭스 ──
    print("\n\n📊 [방어덱] 승률 매트릭스 (행=ally, 열=enemy, 타임오버=ally 승리)")
    print("-" * 100)

    defense_matrix = []
    print(header)

    for i, ally_fn in enumerate(ALL_METAS):
        row = []
        row_str = f"{meta_names[i]:20s}"
        for j, enemy_fn in enumerate(ALL_METAS):
            if i == j:
                row.append(None)
                row_str += "     - "
            else:
                result = run_matchup(ally_fn, enemy_fn, "defense")
                wr = result["win_rate"]
                row.append(wr)
                row_str += f" {wr:5.0f}%"
        defense_matrix.append(row)
        valid = [x for x in row if x is not None]
        avg = sum(valid) / len(valid) if valid else 0
        row_str += f"  {avg:5.1f}%"
        print(row_str)

    # ── 종합 티어 ──
    print("\n\n📊 종합 티어 (평균 승률)")
    print("-" * 80)
    print(f"{'메타':20s} {'공격덱':>8s} {'방어덱':>8s} {'종합':>8s}  기믹")
    print("-" * 80)

    gimmick_tags = {
        "M01": "Burn DoT Stack",
        "M02": "CC Lock Chain",
        "M03": "Poison→Execute",
        "M04": "Hypercarry Buff",
        "M05": "Barrier Fortress",
        "M06": "Counter Bruiser",
        "M07": "Speed Control",
        "M08": "Debuff Chaos",
        "M09": "AoE Cleave",
        "M10": "Burst Rush",
    }

    tier_data = []
    for i, name in enumerate(meta_names):
        off_valid = [x for x in offense_matrix[i] if x is not None]
        def_valid = [x for x in defense_matrix[i] if x is not None]
        off_avg = sum(off_valid) / len(off_valid) if off_valid else 0
        def_avg = sum(def_valid) / len(def_valid) if def_valid else 0
        combined = (off_avg + def_avg) / 2
        tag = gimmick_tags.get(name.split()[0], "")
        tier_data.append((name, off_avg, def_avg, combined, tag))

    # 종합 순으로 정렬
    tier_data.sort(key=lambda x: x[3], reverse=True)
    for name, off, def_, comb, tag in tier_data:
        # 티어 레이블
        if comb >= 65:
            tier = "S"
        elif comb >= 50:
            tier = "A"
        elif comb >= 35:
            tier = "B"
        elif comb >= 20:
            tier = "C"
        else:
            tier = "F"
        print(f"[{tier}] {name:18s} {off:7.1f}% {def_:7.1f}% {comb:7.1f}%  {tag}")

    # ── 캐릭터 사용 통계 ──
    print("\n\n📊 캐릭터 사용 통계")
    print("-" * 50)
    char_count = {}
    for fn in ALL_METAS:
        _, units = fn()
        for u in units:
            char_count[u.name] = char_count.get(u.name, 0) + 1
    print(f"총 유니크 캐릭터: {len(char_count)}명")
    reused = {k: v for k, v in char_count.items() if v > 1}
    if reused:
        print(f"재사용 캐릭터: {', '.join(f'{k}({v}회)' for k, v in sorted(reused.items(), key=lambda x: -x[1]))}")

    print("\n" + "=" * 100)
    print("  시뮬레이션 완료")
    print("=" * 100)


if __name__ == "__main__":
    main()
