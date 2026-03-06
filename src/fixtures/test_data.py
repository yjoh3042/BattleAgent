"""하드코딩 테스트 파티 데이터 - 배틀 시나리오.xlsx 기준 파티1/2 + 몬스터 3종
Excel 스탯: HP/Atk/Def/Spd/SP/CriRatio/CriDmg 모두 기획서 수치 반영
"""
from __future__ import annotations
from typing import List

from battle.enums import (
    Element, Role, SkillType, LogicType, CCType, TargetType, TriggerEvent, StatType
)
from battle.models import (
    StatBlock, BuffData, SkillEffect, SkillData, CharacterData, TriggerData
)


# ════════════════════════════════════════════════════════════════
# ─── 헬퍼 함수 ───────────────────────────────────────────────────
# ════════════════════════════════════════════════════════════════

def _dmg(target: TargetType, mult: float, burn_bonus: float = 0.0) -> SkillEffect:
    cond = {'burn_bonus_per_stack': burn_bonus} if burn_bonus > 0 else None
    return SkillEffect(logic_type=LogicType.DAMAGE, target_type=target,
                       multiplier=mult, condition=cond)


def _heal_full(target: TargetType) -> SkillEffect:
    """최대 HP 100% 즉시 회복 (완전 치유)"""
    return SkillEffect(logic_type=LogicType.HEAL_HP_RATIO, target_type=target, value=1.0)


def _heal_ratio(target: TargetType, ratio: float) -> SkillEffect:
    return SkillEffect(logic_type=LogicType.HEAL_HP_RATIO, target_type=target, value=ratio)


def _stat_buff(stat: str, value: float, duration: int,
               skill_id: str, name: str, is_debuff: bool = False) -> BuffData:
    return BuffData(
        id=f"buff_{skill_id}_{stat}",
        name=name,
        source_skill_id=skill_id,
        logic_type=LogicType.STAT_CHANGE,
        stat=stat,
        value=value,
        duration=duration,
        is_debuff=is_debuff,
    )


def _burn(skill_id: str, dot_ratio: float = 0.05, duration: int = 2) -> BuffData:
    return BuffData(
        id=f"buff_{skill_id}_burn",
        name="화상",
        source_skill_id=skill_id,
        logic_type=LogicType.DOT,
        dot_type="burn",
        value=dot_ratio,
        duration=duration,
        is_debuff=True,
        max_stacks=5,
        buff_turn_reduce_timing="CharacterTurnStart",  # 틱 발동 후 턴 시작에 감소
    )


def _cc(cc_type: CCType, duration: int, skill_id: str,
        condition: dict = None) -> SkillEffect:
    bd = BuffData(
        id=f"buff_{skill_id}_{cc_type.value}",
        name=cc_type.value,
        source_skill_id=skill_id,
        logic_type=LogicType.CC,
        cc_type=cc_type,
        duration=duration,
        is_debuff=True,
    )
    return SkillEffect(logic_type=LogicType.CC, target_type=TargetType.ENEMY_LOWEST_HP,
                       buff_data=bd, condition=condition)


def _stat_eff(target: TargetType, buff: BuffData) -> SkillEffect:
    return SkillEffect(logic_type=LogicType.STAT_CHANGE, target_type=target, buff_data=buff)


def _dot_eff(target: TargetType, buff: BuffData) -> SkillEffect:
    return SkillEffect(logic_type=LogicType.DOT, target_type=target, buff_data=buff)


def _taunt(duration: int) -> SkillEffect:
    return SkillEffect(logic_type=LogicType.TAUNT,
                       target_type=TargetType.ALL_ENEMY, value=duration)


def _counter(duration: int) -> SkillEffect:
    return SkillEffect(logic_type=LogicType.COUNTER,
                       target_type=TargetType.SELF, value=duration)


def _revive(ratio: float) -> SkillEffect:
    return SkillEffect(logic_type=LogicType.REVIVE,
                       target_type=TargetType.ALLY_DEAD_RANDOM, value=ratio)


def _normal(sid: str, name: str, effects: list) -> SkillData:
    return SkillData(id=sid, name=name, skill_type=SkillType.NORMAL,
                     effects=effects, cooldown_turns=0)


def _active(sid: str, name: str, effects: list, cd: int = 2) -> SkillData:
    return SkillData(id=sid, name=name, skill_type=SkillType.ACTIVE,
                     effects=effects, cooldown_turns=cd)


def _ult(sid: str, name: str, effects: list, sp: int) -> SkillData:
    return SkillData(id=sid, name=name, skill_type=SkillType.ULTIMATE,
                     effects=effects, sp_cost=sp)


# ════════════════════════════════════════════════════════════════
# ─── 파티1: 밸런스 파티 ────────────────────────────────────────
# ════════════════════════════════════════════════════════════════

def make_hildred() -> CharacterData:
    """힐드 - Light/Attacker: 강타 딜러, 공격력 자버프
    Normal: 라이트닝 불릿 - 적1명 100%
    Active: 크랙 샷     - 적1명 200%+자신 공격력30% 증가(2턴)  [atk+108]
    Ultimate: 루나틱 스나이퍼 - 적1명 300%  [SP6]
    """
    atk_buff = _stat_buff("atk", 108, 2, "hild_a", "공격강화(힐드)")   # 359*0.3≈108

    normal   = _normal("hild_n", "라이트닝 불릿", [_dmg(TargetType.ENEMY_RANDOM, 1.0)])
    active   = _active("hild_a", "크랙 샷", [
        _dmg(TargetType.ENEMY_RANDOM, 2.0),
        _stat_eff(TargetType.SELF, atk_buff),
    ])
    ultimate = _ult("hild_u", "루나틱 스나이퍼", [
        _dmg(TargetType.ENEMY_RANDOM, 3.0),
    ], sp=6)

    return CharacterData(
        id="hild", name="힐드", element=Element.LIGHT, role=Role.ATTACKER, side="ally",
        stats=StatBlock(atk=359, def_=187, hp=3570, spd=80,
                        cri_ratio=0.05, cri_dmg_ratio=1.5),
        normal_skill=normal, active_skill=active, ultimate_skill=ultimate, sp_cost=6,
    )


def make_arahan() -> CharacterData:
    """아라한 - Water/Supporter: 공격형 크리버퍼
    Normal: 적1명 100%
    Active: 적1명 150%+공격형 아군 치명타확률 증가(2턴)  [cri+0.10]
    Ultimate: 아군 전체 치명타 대미지 증가(2턴)  [cri_dmg+0.30, SP5]
    """
    cri_buff     = _stat_buff("cri_ratio",    0.10, 2, "arahan_a", "예리한 감각(아라한)")
    cri_dmg_buff = _stat_buff("cri_dmg_ratio", 0.30, 2, "arahan_u", "치명각성(아라한)")

    normal   = _normal("arahan_n", "출", [_dmg(TargetType.ENEMY_RANDOM, 1.0)])
    active   = _active("arahan_a", "초감", [
        _dmg(TargetType.ENEMY_RANDOM, 1.5),
        _stat_eff(TargetType.ALLY_ROLE_ATTACKER, cri_buff),
    ])
    ultimate = _ult("arahan_u", "멸도", [
        _stat_eff(TargetType.ALL_ALLY, cri_dmg_buff),
    ], sp=5)

    return CharacterData(
        id="arahan", name="아라한", element=Element.WATER, role=Role.SUPPORTER, side="ally",
        stats=StatBlock(atk=287, def_=187, hp=3213, spd=120,
                        cri_ratio=0.05, cri_dmg_ratio=1.5),
        normal_skill=normal, active_skill=active, ultimate_skill=ultimate, sp_cost=5,
    )


def make_dana() -> CharacterData:
    """다나 - Light/Healer: 전투힐러/부활기
    Normal: 적1명 100%
    Active: 체력 낮은 아군 2명 최대HP 100% 즉시 회복
    Ultimate: 사망 아군 1명 최대HP 10%로 부활  [SP4]
    """
    normal   = _normal("dana_n", "라이트 리플렉팅", [_dmg(TargetType.ENEMY_RANDOM, 1.0)])
    active   = _active("dana_a", "성자의 축복", [
        _heal_full(TargetType.ALLY_LOWEST_HP_2),
    ])
    ultimate = _ult("dana_u", "여신의 세례", [
        _revive(0.10),
    ], sp=4)

    return CharacterData(
        id="dana", name="다나", element=Element.LIGHT, role=Role.HEALER, side="ally",
        stats=StatBlock(atk=287, def_=187, hp=2856, spd=90,
                        cri_ratio=0.05, cri_dmg_ratio=1.5),
        normal_skill=normal, active_skill=active, ultimate_skill=ultimate, sp_cost=4,
    )


def make_frey() -> CharacterData:
    """프레이 - Dark/Defender: 방어 탱커/도발기
    Normal: 적1명 100%
    Active: 적1명 100%+자신 방어력30% 증가(2턴)  [def+70]
    Ultimate: 적 전체 2턴 도발  [SP4]
    """
    def_buff = _stat_buff("def_", 70, 2, "frey_a", "철벽방어(프레이)")   # 234*0.3≈70

    normal   = _normal("frey_n", "그림 리퍼", [_dmg(TargetType.ENEMY_RANDOM, 1.0)])
    active   = _active("frey_a", "사신의 잔상", [
        _dmg(TargetType.ENEMY_RANDOM, 1.0),
        _stat_eff(TargetType.SELF, def_buff),
    ])
    ultimate = _ult("frey_u", "트릭스터", [
        _taunt(2),
    ], sp=4)

    return CharacterData(
        id="frey", name="프레이", element=Element.DARK, role=Role.DEFENDER, side="ally",
        stats=StatBlock(atk=287, def_=234, hp=4284, spd=110,
                        cri_ratio=0.05, cri_dmg_ratio=1.5),
        normal_skill=normal, active_skill=active, ultimate_skill=ultimate, sp_cost=4,
    )


def make_citria() -> CharacterData:
    """시트리 - Light/Supporter: 속도 버퍼
    Normal: 적1명 100%
    Active: 적1명 150%+공격형 아군 속도50 증가(2턴)
    Ultimate: 아군 전체 속도15 증가(2턴)  [SP5]
    """
    spd_buff_a = _stat_buff("spd", 50, 2, "citria_a", "질풍가도(시트리)")
    spd_buff_u = _stat_buff("spd", 15, 2, "citria_u", "폭풍의 질주(시트리)")

    normal   = _normal("citria_n", "폴 인 러브", [_dmg(TargetType.ENEMY_RANDOM, 1.0)])
    active   = _active("citria_a", "크런치 캔디", [
        _dmg(TargetType.ENEMY_RANDOM, 1.5),
        _stat_eff(TargetType.ALLY_ROLE_ATTACKER, spd_buff_a),
    ])
    ultimate = _ult("citria_u", "라 돌체 비타", [
        _stat_eff(TargetType.ALL_ALLY, spd_buff_u),
    ], sp=5)

    return CharacterData(
        id="citria", name="시트리", element=Element.LIGHT, role=Role.SUPPORTER, side="ally",
        stats=StatBlock(atk=287, def_=187, hp=3213, spd=120,
                        cri_ratio=0.05, cri_dmg_ratio=1.5),
        normal_skill=normal, active_skill=active, ultimate_skill=ultimate, sp_cost=5,
    )


def get_party1() -> List[CharacterData]:
    """파티1: 힐드/아라한/다나/프레이/시트리"""
    return [make_hildred(), make_arahan(), make_dana(), make_frey(), make_citria()]


# ════════════════════════════════════════════════════════════════
# ─── 파티2: 화상 연계 파티 ─────────────────────────────────────
# ════════════════════════════════════════════════════════════════

def make_gumiho() -> CharacterData:
    """구미호 - Fire/Magician: 화상 부여기
    Normal: 적1명 100%
    Active: 적2명 80%+2턴 화상 부여
    Ultimate: 적 전체 2턴 화상 부여  [SP6]
    """
    burn_a = _burn("gumiho_a")
    burn_u = _burn("gumiho_u")

    normal   = _normal("gumiho_n", "꼬리의 매질", [_dmg(TargetType.ENEMY_RANDOM, 1.0)])
    active   = _active("gumiho_a", "원혼의 아홉 꼬리", [
        _dmg(TargetType.ENEMY_RANDOM_2, 0.8),
        _dot_eff(TargetType.ENEMY_RANDOM_2, burn_a),
    ])
    ultimate = _ult("gumiho_u", "붉은 원망의 폭풍", [
        _dot_eff(TargetType.ALL_ENEMY, burn_u),
    ], sp=6)

    return CharacterData(
        id="gumiho", name="구미호", element=Element.FIRE, role=Role.MAGICIAN, side="ally",
        stats=StatBlock(atk=287, def_=187, hp=3213, spd=100,
                        cri_ratio=0.05, cri_dmg_ratio=1.5),
        normal_skill=normal, active_skill=active, ultimate_skill=ultimate, sp_cost=6,
    )


def make_kararatri() -> CharacterData:
    """카라라트리 - Fire/Magician: 방깎/기절 딜러
    Normal: 적1명 100%
    Active: 적2명 80%+2턴 방어력30% 감소  [def-60]
    Ultimate: 적1명 100%+화상3스택 이상시 2턴 기절  [SP6]
    """
    def_debuff = _stat_buff("def_", -60, 2, "kara_a", "방어붕괴(카라)", is_debuff=True)  # 200*0.3=60

    stun_bd = BuffData(
        id="buff_kara_u_stun",
        name=CCType.STUN.value,
        source_skill_id="kara_u",
        logic_type=LogicType.CC,
        cc_type=CCType.STUN,
        duration=2,
        is_debuff=True,
    )
    stun_eff = SkillEffect(
        logic_type=LogicType.CC,
        target_type=TargetType.ENEMY_LOWEST_HP,
        buff_data=stun_bd,
        condition={'target_burn_min': 3},   # 화상 3스택 이상 시 발동
    )

    normal   = _normal("kara_n", "무기법", [_dmg(TargetType.ENEMY_RANDOM, 1.0)])
    active   = _active("kara_a", "무루의 고통", [
        _dmg(TargetType.ENEMY_RANDOM_2, 0.8),
        _stat_eff(TargetType.ENEMY_RANDOM_2, def_debuff),
    ])
    ultimate = _ult("kara_u", "출세간의 선법", [
        _dmg(TargetType.ENEMY_LOWEST_HP, 1.0),
        stun_eff,
    ], sp=6)

    return CharacterData(
        id="kara", name="카라라트리", element=Element.FIRE, role=Role.MAGICIAN, side="ally",
        stats=StatBlock(atk=287, def_=187, hp=3213, spd=100,
                        cri_ratio=0.05, cri_dmg_ratio=1.5),
        normal_skill=normal, active_skill=active, ultimate_skill=ultimate, sp_cost=6,
    )


def make_cain() -> CharacterData:
    """카인 - Fire/Attacker: 화상 시너지 폭딜러
    Normal: 적1명 100%
    Active: 적1명 100%(화상시 스택당 +150%)
    Ultimate: 전 적체 100%(화상시 스택당 +200%)  [SP6]
    """
    normal   = _normal("cain_n", "오레무스", [_dmg(TargetType.ENEMY_LOWEST_HP, 1.0)])
    active   = _active("cain_a", "베르붐 도미니", [
        _dmg(TargetType.ENEMY_LOWEST_HP, 1.0, burn_bonus=1.5),
    ])
    ultimate = _ult("cain_u", "십자가의 피", [
        _dmg(TargetType.ALL_ENEMY, 1.0, burn_bonus=2.0),
    ], sp=6)

    return CharacterData(
        id="cain", name="카인", element=Element.FIRE, role=Role.ATTACKER, side="ally",
        stats=StatBlock(atk=359, def_=187, hp=3570, spd=80,
                        cri_ratio=0.05, cri_dmg_ratio=1.5),
        normal_skill=normal, active_skill=active, ultimate_skill=ultimate, sp_cost=6,
    )


def make_lagaraja() -> CharacterData:
    """라가라자 - Fire/Defender: 화상반격 탱커
    Normal: 적1명 100%
    Active: 적1명 100%+자신 방어력30% 증가(2턴)  [def+70]
    Ultimate: 자신에게 2턴 화상반격 부여  [SP4]
    """
    def_buff = _stat_buff("def_", 70, 2, "laga_a", "불꽃갑옷(라가)")   # 234*0.3≈70

    normal   = _normal("laga_n", "지장", [_dmg(TargetType.ENEMY_RANDOM, 1.0)])
    active   = _active("laga_a", "관음", [
        _dmg(TargetType.ENEMY_LOWEST_HP, 1.0),
        _stat_eff(TargetType.SELF, def_buff),
    ])
    ultimate = _ult("laga_u", "맹화", [
        _counter(2),
    ], sp=4)

    return CharacterData(
        id="laga", name="라가라자", element=Element.FIRE, role=Role.DEFENDER, side="ally",
        stats=StatBlock(atk=287, def_=234, hp=4284, spd=110,
                        cri_ratio=0.05, cri_dmg_ratio=1.5),
        normal_skill=normal, active_skill=active, ultimate_skill=ultimate, sp_cost=4,
    )


def get_party2() -> List[CharacterData]:
    """파티2: 구미호/카라라트리/카인/라가라자/시트리"""
    return [make_gumiho(), make_kararatri(), make_cain(), make_lagaraja(), make_citria()]


# ════════════════════════════════════════════════════════════════
# ─── 적군: 봉제인형 3체 (Data/Character.xlsx - Detail<Monster>)
# ────────────────────────────────────────────────────────────────
# ID 20130101 (A형) Spd=110 / ID 20130201 (B형) Spd=84 / C형 Spd=100
# Element=Fire, Role=Defender, Skill: 뿌로롱(Normal·Active)
# ════════════════════════════════════════════════════════════════

def make_teddy_a() -> CharacterData:
    """봉제인형 (A형) - Fire/Defender  [Spd=110, ID 20130101]
    Normal : 뿌로롱        - 적1명 100%
    Active : 뿌로롱(꽉)    - 무작위 적3명 150%+2턴 방어력30% 감소 [def-60]
    Ultimate: 없음 (SP=99)
    Passive : HP 50% 이하 시 방어력 증가 (배틀 엔진 미구현 → 생략)
    """
    def_debuff = _stat_buff("def_", -60, 2, "teddy_a_a", "방어붕괴(봉제인형)", is_debuff=True)

    normal   = _normal("teddy_a_n", "뿌로롱", [_dmg(TargetType.ENEMY_RANDOM, 1.0)])
    active   = _active("teddy_a_a", "뿌로롱(꽉)", [
        _dmg(TargetType.ENEMY_RANDOM_3, 1.5),
        _stat_eff(TargetType.ENEMY_RANDOM_3, def_debuff),
    ])
    ultimate = _ult("teddy_a_u", "뿌로롱(없음)", [_dmg(TargetType.ENEMY_RANDOM, 1.0)], sp=99)

    return CharacterData(
        id="teddy_a", name="봉제인형", element=Element.FIRE, role=Role.DEFENDER, side="enemy",
        stats=StatBlock(atk=300, def_=200, hp=3000, spd=110,
                        cri_ratio=0.0, cri_dmg_ratio=1.5),
        normal_skill=normal, active_skill=active, ultimate_skill=ultimate, sp_cost=99,
    )


def make_teddy_b() -> CharacterData:
    """봉제인형 (B형) - Fire/Defender  [Spd=84, ID 20130201]
    Normal : 뿌로롱        - 적1명 100%
    Active : 뿌로롱(탁)    - 무작위 적3명 150%+2턴 공격력30% 감소 [atk-90]
    Ultimate: 없음 (SP=99)
    """
    atk_debuff = _stat_buff("atk", -90, 2, "teddy_b_a", "공격약화(봉제인형)", is_debuff=True)

    normal   = _normal("teddy_b_n", "뿌로롱", [_dmg(TargetType.ENEMY_RANDOM, 1.0)])
    active   = _active("teddy_b_a", "뿌로롱(탁)", [
        _dmg(TargetType.ENEMY_RANDOM_3, 1.5),
        _stat_eff(TargetType.ENEMY_RANDOM_3, atk_debuff),
    ])
    ultimate = _ult("teddy_b_u", "뿌로롱(없음)", [_dmg(TargetType.ENEMY_RANDOM, 1.0)], sp=99)

    return CharacterData(
        id="teddy_b", name="봉제인형", element=Element.FIRE, role=Role.DEFENDER, side="enemy",
        stats=StatBlock(atk=300, def_=200, hp=3000, spd=84,
                        cri_ratio=0.0, cri_dmg_ratio=1.5),
        normal_skill=normal, active_skill=active, ultimate_skill=ultimate, sp_cost=99,
    )


def make_teddy_c() -> CharacterData:
    """봉제인형 (C형) - Fire/Defender  [Spd=100, 중간 속도 변형]
    Normal : 뿌로롱        - 적1명 100%
    Active : 뿌로롱(빵)    - 무작위 적3명 150%+아군(봉제인형) 전체 공격력30% 증가 [atk+90]
    Ultimate: 없음 (SP=99)
    """
    atk_buff = _stat_buff("atk", 90, 2, "teddy_c_a", "전투기합(봉제인형)")

    normal   = _normal("teddy_c_n", "뿌로롱", [_dmg(TargetType.ENEMY_RANDOM, 1.0)])
    active   = _active("teddy_c_a", "뿌로롱(빵)", [
        _dmg(TargetType.ENEMY_RANDOM_3, 1.5),
        _stat_eff(TargetType.ALL_ALLY, atk_buff),   # ALL_ALLY = 봉제인형 전체
    ])
    ultimate = _ult("teddy_c_u", "뿌로롱(없음)", [_dmg(TargetType.ENEMY_RANDOM, 1.0)], sp=99)

    return CharacterData(
        id="teddy_c", name="봉제인형", element=Element.FIRE, role=Role.DEFENDER, side="enemy",
        stats=StatBlock(atk=300, def_=200, hp=3000, spd=100,
                        cri_ratio=0.0, cri_dmg_ratio=1.5),
        normal_skill=normal, active_skill=active, ultimate_skill=ultimate, sp_cost=99,
    )


def make_teddy_d() -> CharacterData:
    """봉제인형 (D형) - Fire/Defender  [Spd=90, 속도감소형]
    Normal : 뿌로롱        - 적1명 100%
    Active : 뿌로롱(슝)    - 무작위 적3명 150%+2턴 속도20 감소
    Ultimate: 없음 (SP=99)
    """
    spd_debuff = _stat_buff("spd", -20, 2, "teddy_d_a", "속도약화(봉제인형)", is_debuff=True)

    normal   = _normal("teddy_d_n", "뿌로롱", [_dmg(TargetType.ENEMY_RANDOM, 1.0)])
    active   = _active("teddy_d_a", "뿌로롱(슝)", [
        _dmg(TargetType.ENEMY_RANDOM_3, 1.5),
        _stat_eff(TargetType.ENEMY_RANDOM_3, spd_debuff),
    ])
    ultimate = _ult("teddy_d_u", "뿌로롱(없음)", [_dmg(TargetType.ENEMY_RANDOM, 1.0)], sp=99)

    return CharacterData(
        id="teddy_d", name="봉제인형", element=Element.FIRE, role=Role.DEFENDER, side="enemy",
        stats=StatBlock(atk=300, def_=200, hp=3000, spd=90,
                        cri_ratio=0.0, cri_dmg_ratio=1.5),
        normal_skill=normal, active_skill=active, ultimate_skill=ultimate, sp_cost=99,
    )


def make_teddy_e() -> CharacterData:
    """봉제인형 (E형) - Fire/Defender  [Spd=95, 힐러형]
    Normal : 뿌로롱        - 적1명 100%
    Active : 뿌로롱(뿅)    - 무작위 적3명 120%+아군(몬스터) 전체 HP 15% 회복
    Ultimate: 없음 (SP=99)
    """
    normal   = _normal("teddy_e_n", "뿌로롱", [_dmg(TargetType.ENEMY_RANDOM, 1.0)])
    active   = _active("teddy_e_a", "뿌로롱(뿅)", [
        _dmg(TargetType.ENEMY_RANDOM_3, 1.2),
        _heal_ratio(TargetType.ALL_ALLY, 0.15),
    ])
    ultimate = _ult("teddy_e_u", "뿌로롱(없음)", [_dmg(TargetType.ENEMY_RANDOM, 1.0)], sp=99)

    return CharacterData(
        id="teddy_e", name="봉제인형", element=Element.FIRE, role=Role.DEFENDER, side="enemy",
        stats=StatBlock(atk=300, def_=200, hp=3000, spd=95,
                        cri_ratio=0.0, cri_dmg_ratio=1.5),
        normal_skill=normal, active_skill=active, ultimate_skill=ultimate, sp_cost=99,
    )


def get_enemies() -> List[CharacterData]:
    """적군: 봉제인형 A형(Spd110) / B형(Spd84) / C형(Spd100)"""
    return [make_teddy_a(), make_teddy_b(), make_teddy_c()]


def get_enemies_5() -> List[CharacterData]:
    """적군 5마리: 봉제인형 A~E형"""
    return [make_teddy_a(), make_teddy_b(), make_teddy_c(), make_teddy_d(), make_teddy_e()]
