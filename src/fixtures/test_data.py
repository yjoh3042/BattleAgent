"""캐릭터 빌더 헬퍼 – 스킬 이펙트 / 버프 / 스킬 생성 유틸

사용법:
    from fixtures.test_data import _dmg, _stat_buff, _burn, _normal, _active, _ult
    # → CharacterData / SkillData 를 조립해 사용

═══════════════════════════════════════════════════════════════
밸런싱 정책 v2.0 — 스탯 고정 + 스킬 밸런싱
═══════════════════════════════════════════════════════════════
스탯(ATK/DEF/HP)은 역할×등급으로 완전 고정 (ROLE_STAT_STANDARD).
캐릭터 개성화는 스킬(배율/타겟/부가효과)로만 수행한다.
→ battle.rules.ROLE_SKILL_TEMPLATE : 역할별 기본 스킬 설정
→ battle.rules.SKILL_MULTIPLIER_RANGE : 역할별 허용 배율 범위

전투 룰 요약 (엔진 불변):
  - CTB 큐: 300 / SPD 기반 heapq
  - 타일 배치: 3×3 그리드, row 0=전열·2=후열
  - ENEMY_NEAR 거리 = caster.row + target.row + |caster.col - target.col|
  - SP 공유 (파티 전원 합산), 얼티밋 끼어들기
  - 도발(Taunt) → 단일 타겟 강제, 다중 타겟 포함 강제

스탯 규약 (역할×등급 고정, 개별 조정 금지):
  역할        1★               2★               3★               3.5★
  ATTACKER   ATK480/DEF240   ATK640/DEF320   ATK800/DEF400   ATK920/DEF460
             HP2400           HP3200           HP4000           HP4600
  MAGICIAN   ATK360/DEF240   ATK480/DEF320   ATK600/DEF400   ATK690/DEF460
             HP3000           HP4000           HP5000           HP5750
  DEFENDER   ATK300/DEF360   ATK400/DEF480   ATK500/DEF600   ATK574/DEF690
             HP3600           HP4800           HP6000           HP6900
  HEALER     ATK240/DEF240   ATK320/DEF320   ATK400/DEF400   ATK460/DEF460
             HP2400           HP3200           HP4000           HP4600
  SUPPORTER  ATK300/DEF240   ATK400/DEF320   ATK500/DEF400   ATK574/DEF460
             HP3000           HP4000           HP5000           HP5750

역할별 고정값 (등급 무관):
  속도(SPD): Attacker=80 / Healer=90 / Magician=100 / Defender=110 / Supporter=120
  SP 비용:   Attacker=6  / Healer=3  / Magician=4   / Defender=3   / Supporter=4

스킬 배율 허용 범위 (battle.rules.SKILL_MULTIPLIER_RANGE):
  역할        일반공격        액티브           궁극기
  ATTACKER   2.00~5.00×     2.40~5.60×      4.00~8.00×
  MAGICIAN   1.60~4.40×     0.80~3.60×      1.60~5.00×
  DEFENDER   0.60~2.00×     0.40~1.60×      0.00~1.00×
  HEALER     0.40~1.60×     1.60~4.00×      0.40~0.80×
  SUPPORTER  0.80~2.40×     1.00~3.00×      1.20~3.60×

검증: py -3 -X utf8 scripts/validate_role_stats.py
"""
from __future__ import annotations
from typing import List, Optional

from battle.enums import (
    Element, Role, SkillType, LogicType, CCType, TargetType, TriggerEvent, StatType
)
from battle.models import (
    StatBlock, BuffData, SkillEffect, SkillData, CharacterData, TriggerData
)


# ════════════════════════════════════════════════════════════════
# ─── 데미지 / 힐 이펙트 ──────────────────────────────────────────
# ════════════════════════════════════════════════════════════════

def _dmg(target: TargetType, mult: float, burn_bonus: float = 0.0,
         hit_count: int = 1) -> SkillEffect:
    """데미지 이펙트. hit_count > 1 이면 다단 히트."""
    cond = {'burn_bonus_per_stack': burn_bonus} if burn_bonus > 0 else None
    return SkillEffect(logic_type=LogicType.DAMAGE, target_type=target,
                       multiplier=mult, condition=cond, hit_count=hit_count)


def _heal_full(target: TargetType) -> SkillEffect:
    """최대 HP 100% 즉시 회복"""
    return SkillEffect(logic_type=LogicType.HEAL_HP_RATIO, target_type=target, value=1.0)


def _heal_ratio(target: TargetType, ratio: float) -> SkillEffect:
    """최대 HP 비율 회복"""
    return SkillEffect(logic_type=LogicType.HEAL_HP_RATIO, target_type=target, value=ratio)


# ════════════════════════════════════════════════════════════════
# ─── 버프 / 디버프 데이터 빌더 ──────────────────────────────────
# ════════════════════════════════════════════════════════════════

def _stat_buff(stat: str, value: float, duration: int,
               skill_id: str, name: str, is_debuff: bool = False) -> BuffData:
    """스탯 버프/디버프 BuffData 생성."""
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


def _burn(skill_id: str, dot_ratio: float = 0.15, duration: int = 2) -> BuffData:
    """화상 DoT BuffData (max_stacks=3, TurnStart 틱)"""
    return BuffData(
        id=f"buff_{skill_id}_burn",
        name="화상",
        source_skill_id=skill_id,
        logic_type=LogicType.DOT,
        dot_type="burn",
        value=dot_ratio,
        duration=duration,
        is_debuff=True,
        max_stacks=3,
        buff_turn_reduce_timing="CharacterTurnStart",
    )


def _poison(skill_id: str, dot_ratio: float = 0.20, duration: int = 2) -> BuffData:
    """중독 DoT BuffData (max_stacks=3, TurnStart 틱)"""
    return BuffData(
        id=f"buff_{skill_id}_poison",
        name="중독",
        source_skill_id=skill_id,
        logic_type=LogicType.DOT,
        dot_type="poison",
        value=dot_ratio,
        duration=duration,
        is_debuff=True,
        max_stacks=3,
        buff_turn_reduce_timing="CharacterTurnStart",
    )


def _bleed(skill_id: str, dot_ratio: float = 0.15, duration: int = 2) -> BuffData:
    """출혈 DoT BuffData (max_stacks=3, TurnStart 틱)"""
    return BuffData(
        id=f"buff_{skill_id}_bleed",
        name="출혈",
        source_skill_id=skill_id,
        logic_type=LogicType.DOT,
        dot_type="bleed",
        value=dot_ratio,
        duration=duration,
        is_debuff=True,
        max_stacks=3,
        buff_turn_reduce_timing="CharacterTurnStart",
    )


# ════════════════════════════════════════════════════════════════
# ─── SkillEffect 빌더 ───────────────────────────────────────────
# ════════════════════════════════════════════════════════════════

def _cc(cc_type: CCType, duration: int, skill_id: str,
        target: TargetType = TargetType.ENEMY_NEAR,
        condition: Optional[dict] = None) -> SkillEffect:
    """CC 이펙트 생성. 기본 타겟 = ENEMY_NEAR."""
    bd = BuffData(
        id=f"buff_{skill_id}_{cc_type.value}",
        name=cc_type.value,
        source_skill_id=skill_id,
        logic_type=LogicType.CC,
        cc_type=cc_type,
        duration=duration,
        is_debuff=True,
    )
    return SkillEffect(logic_type=LogicType.CC, target_type=target,
                       buff_data=bd, condition=condition)


def _stat_eff(target: TargetType, buff: BuffData) -> SkillEffect:
    """스탯 변경 이펙트"""
    return SkillEffect(logic_type=LogicType.STAT_CHANGE, target_type=target, buff_data=buff)


def _dot_eff(target: TargetType, buff: BuffData) -> SkillEffect:
    """DoT 부여 이펙트"""
    return SkillEffect(logic_type=LogicType.DOT, target_type=target, buff_data=buff)


def _taunt(duration: int) -> SkillEffect:
    """전체 적 도발"""
    return SkillEffect(logic_type=LogicType.TAUNT,
                       target_type=TargetType.ALL_ENEMY, value=duration)


def _counter(duration: int, target: TargetType = TargetType.SELF) -> SkillEffect:
    """반격 준비 상태 부여"""
    return SkillEffect(logic_type=LogicType.COUNTER, target_type=target, value=duration)


def _revive(ratio: float) -> SkillEffect:
    """사망 아군 1명 부활 (HP ratio)"""
    return SkillEffect(logic_type=LogicType.REVIVE,
                       target_type=TargetType.ALLY_DEAD_RANDOM, value=ratio)


def _sp_gain(amount: float, target: TargetType = TargetType.SELF) -> SkillEffect:
    """SP 증가"""
    return SkillEffect(logic_type=LogicType.SP_INCREASE, target_type=target, value=amount)


def _shield(target: TargetType, ratio: float, duration: int = 2) -> SkillEffect:
    """보호막 (최대 HP 비율)"""
    return SkillEffect(logic_type=LogicType.BARRIER, target_type=target, value=ratio)


# ════════════════════════════════════════════════════════════════
# ─── SkillData 빌더 ─────────────────────────────────────────────
# ════════════════════════════════════════════════════════════════

def _normal(sid: str, name: str, effects: list) -> SkillData:
    """일반 공격 스킬 (쿨타임 없음, ENEMY_NEAR 기준)."""
    return SkillData(id=sid, name=name, skill_type=SkillType.NORMAL,
                     effects=effects, cooldown_turns=0)


def _active(sid: str, name: str, effects: list, cd: int = 3) -> SkillData:
    """액티브 스킬 (기본 CD=3)."""
    return SkillData(id=sid, name=name, skill_type=SkillType.ACTIVE,
                     effects=effects, cooldown_turns=cd)


def _ult(sid: str, name: str, effects: list, sp: int) -> SkillData:
    """얼티밋 스킬."""
    return SkillData(id=sid, name=name, skill_type=SkillType.ULTIMATE,
                     effects=effects, sp_cost=sp)


# ════════════════════════════════════════════════════════════════
# ─── 캐릭터 팩토리 ───────────────────────────────────────────────
# ════════════════════════════════════════════════════════════════

# ── 내부 헬퍼: is_ratio 지원 스탯 버프 ───────────────────────────

def _sb(stat: str, value: float, duration: int, skill_id: str,
        name: str, is_debuff: bool = False, is_ratio: bool = False) -> BuffData:
    """_stat_buff 에 is_ratio 를 더한 래퍼."""
    bd = _stat_buff(stat, value, duration, skill_id, name, is_debuff)
    bd.is_ratio = is_ratio
    return bd


def _remove_debuff_eff(target: TargetType) -> SkillEffect:
    """디버프 제거 이펙트."""
    return SkillEffect(logic_type=LogicType.REMOVE_DEBUFF, target_type=target)


def _remove_buff_eff(target: TargetType) -> SkillEffect:
    """적 버프 제거 이펙트 (보호막·공버프·방버프 등 전부 제거)."""
    return SkillEffect(logic_type=LogicType.REMOVE_BUFF, target_type=target)


def _dmg_cond(target: TargetType, mult: float,
              condition: dict) -> SkillEffect:
    """조건부 데미지 이펙트 (target_hp_below, burn_bonus 등)."""
    return SkillEffect(logic_type=LogicType.DAMAGE, target_type=target,
                       multiplier=mult, condition=condition)


# ════════════════════════════════════════════════════════════════
# 화속성 (Element.FIRE)
# ════════════════════════════════════════════════════════════════

def make_morgan() -> CharacterData:
    """c283 모건 - 화/구속형
    ★콤보: Normal 2연타로 출혈 빠르게 중첩 → 카라라트리 burn_bonus 시너지
    """
    sid = "c283"
    return CharacterData(
        id=sid, name="모건", element=Element.FIRE, role=Role.MAGICIAN,
        side="ally",
        stats=StatBlock(atk=600, def_=400, hp=5000, spd=100),
        normal_skill=_normal(f"{sid}_n", "철화의 검",
            [_dmg(TargetType.ENEMY_NEAR, 1.80, hit_count=2)]),  # ★ 2연타 (0.90×2=1.80 총합 동일, DoT 2회 적용 기회)
        active_skill=_active(f"{sid}_a", "홍염의 비도",
            [_stat_eff(TargetType.SELF,
                _sb('atk', 0.15, 3, f"{sid}_a", "공격력", is_ratio=True))]),
        ultimate_skill=_ult(f"{sid}_u", "화도난무",
            [_dmg(TargetType.ALL_ENEMY, 3.20),
             _dot_eff(TargetType.ALL_ENEMY, _bleed(f"{sid}_u", dot_ratio=0.15, duration=2))],
            sp=4),
        tile_pos=(0, 1),
    )


def make_dabi() -> CharacterData:
    """c339 다비 - 화/구속형"""
    sid = "c339"
    return CharacterData(
        id=sid, name="다비", element=Element.FIRE, role=Role.MAGICIAN,
        side="ally",
        stats=StatBlock(atk=600, def_=400, hp=5000, spd=100),
        normal_skill=_normal(f"{sid}_n", "파이어리 서펀트",
            [_dmg(TargetType.ENEMY_NEAR, 4.00)]),
        active_skill=_active(f"{sid}_a", "화차",
            [_dmg(TargetType.ENEMY_RANDOM, 3.40),
             _dot_eff(TargetType.ENEMY_RANDOM, _burn(f"{sid}_a"))]),
        ultimate_skill=_ult(f"{sid}_u", "나비효과",
            [_dmg(TargetType.ALL_ENEMY, 2.80),
             _dot_eff(TargetType.ALL_ENEMY, _burn(f"{sid}_u"))],
            sp=4),
        tile_pos=(0, 0),
    )


def make_gumiho() -> CharacterData:
    """c417 구미호 - 화/마법형"""
    sid = "c417"
    return CharacterData(
        id=sid, name="구미호", element=Element.FIRE, role=Role.MAGICIAN,
        side="ally",
        stats=StatBlock(atk=600, def_=400, hp=5000, spd=100),
        normal_skill=_normal(f"{sid}_n", "꼬리의 매질",
            [_dmg(TargetType.ENEMY_NEAR, 3.00)]),
        active_skill=_active(f"{sid}_a", "원혼의 아홉 꼬리",
            [_dmg(TargetType.ENEMY_RANDOM, 4.00),
             _cc(CCType.PANIC, 1, f"{sid}_a", TargetType.ENEMY_RANDOM),
             _stat_eff(TargetType.ENEMY_RANDOM,
                _sb('def_', 0.15, 2, f"{sid}_a", "원혼 침식", is_debuff=True, is_ratio=True))]),  # ★ 공포+방깎 혼돈 콤보
        ultimate_skill=_ult(f"{sid}_u", "붉은 원망의 폭풍",
            [_dmg(TargetType.ALL_ENEMY, 5.00),
             _cc(CCType.PANIC, 1, f"{sid}_u", TargetType.ALL_ENEMY)],
            sp=4),
        tile_pos=(1, 1),
    )


def make_jiva() -> CharacterData:
    """c429 지바 - 화/힐러"""
    sid = "c429"
    return CharacterData(
        id=sid, name="지바", element=Element.FIRE, role=Role.HEALER,
        side="ally",
        stats=StatBlock(atk=400, def_=400, hp=4000, spd=90),
        normal_skill=_normal(f"{sid}_n", "물의 촉수",
            [_dmg(TargetType.ENEMY_NEAR, 2.00)]),
        active_skill=_active(f"{sid}_a", "생명수",
            [_heal_ratio(TargetType.ALLY_LOWEST_HP, 0.30),
             _stat_eff(TargetType.ALLY_LOWEST_HP,
                _sb('atk', 0.15, 2, f"{sid}_a", "공격력", is_ratio=True))]),
        ultimate_skill=_ult(f"{sid}_u", "대자연의 손길",
            [_heal_ratio(TargetType.ALL_ALLY, 0.30),
             _stat_eff(TargetType.ALL_ALLY,
                _sb('atk', 0.20, 2, f"{sid}_u", "공격력", is_ratio=True)),
             _sp_gain(1.0, TargetType.ALL_ALLY)],
            sp=3),
        tile_pos=(2, 1),
    )


def make_kararatri() -> CharacterData:
    """c445 카라라트리 - 화/공격형
    ★콤보: 아군 화상 스택에 비례해 Normal 추가 피해 (burn_bonus_per_stack=0.30)
    → 다비/드미테르가 화상 쌓을수록 카라라트리 Normal이 강해지는 시너지
    """
    sid = "c445"
    return CharacterData(
        id=sid, name="카라라트리", element=Element.FIRE, role=Role.ATTACKER,
        side="ally",
        stats=StatBlock(atk=800, def_=400, hp=4000, spd=80),
        normal_skill=_normal(f"{sid}_n", "무기법",
            [_dmg(TargetType.ENEMY_NEAR, 3.00, burn_bonus=0.30)]),  # ★ 화상 스택당 +0.40x (0.30→0.40)
        active_skill=_active(f"{sid}_a", "무루의 고통",
            [_dmg(TargetType.ENEMY_NEAR_ROW, 3.60),
             _dot_eff(TargetType.ENEMY_NEAR_ROW, _burn(f"{sid}_a"))]),
        ultimate_skill=_ult(f"{sid}_u", "출세간의 선법",
            [_dmg(TargetType.ALL_ENEMY, 2.60),
             _stat_eff(TargetType.ALL_ENEMY,
                _sb('def_', 0.20, 2, f"{sid}_u", "방어력", is_debuff=True, is_ratio=True))],
            sp=6),
        tile_pos=(1, 0),
    )


def make_deresa() -> CharacterData:
    """c462 데레사 - 화/방어형"""
    sid = "c462"
    return CharacterData(
        id=sid, name="데레사", element=Element.FIRE, role=Role.DEFENDER,
        side="ally",
        stats=StatBlock(atk=500, def_=600, hp=6000, spd=110),
        normal_skill=_normal(f"{sid}_n", "스틸 웨일링",
            [_dmg(TargetType.ENEMY_NEAR, 3.00)]),
        active_skill=_active(f"{sid}_a", "데털민트 소드",
            [_dmg(TargetType.ENEMY_NEAR, 3.60),
             _stat_eff(TargetType.SELF,
                _sb('def_', 0.30, 2, f"{sid}_a", "방어력", is_ratio=True)),
             _counter(2)]),
        ultimate_skill=_ult(f"{sid}_u", "새크리파이스",
            [_dmg(TargetType.ENEMY_NEAR_ROW, 5.00),
             _taunt(2)],
            sp=3),
        tile_pos=(0, 1),
    )


def make_ragaraja() -> CharacterData:
    """c501 라가라자 - 화/공격형"""
    sid = "c501"
    return CharacterData(
        id=sid, name="라가라자", element=Element.FIRE, role=Role.ATTACKER,
        side="ally",
        stats=StatBlock(atk=920, def_=460, hp=4600, spd=80),
        normal_skill=_normal(f"{sid}_n", "지장",
            [_dmg(TargetType.ENEMY_NEAR, 4.00),
             _stat_eff(TargetType.SELF,
                _sb('def_', 0.15, 2, f"{sid}_n", "방어력", is_ratio=True))]),
        active_skill=_active(f"{sid}_a", "관음",
            [_dmg(TargetType.ENEMY_NEAR, 3.00),
             _stat_eff(TargetType.ALL_ALLY,
                _sb('def_', 0.25, 2, f"{sid}_a", "방어력", is_ratio=True))]),  # DEF 0.20→0.25 (REMOVE_BUFF 제거 보상)
        ultimate_skill=_ult(f"{sid}_u", "맹화",
            [_dmg(TargetType.ALL_ENEMY, 4.40)],  # AoE 배율 3.40→2.80→2.50→2.20 (4차 너프)
            sp=6),
        tile_pos=(0, 2),
    )


def make_salmakis() -> CharacterData:
    """c562 살마키스 - 화/서포터"""
    sid = "c562"
    return CharacterData(
        id=sid, name="살마키스", element=Element.FIRE, role=Role.SUPPORTER,
        side="ally",
        stats=StatBlock(atk=500, def_=400, hp=5000, spd=120),
        normal_skill=_normal(f"{sid}_n", "물의 손길",
            [_dmg(TargetType.ENEMY_NEAR, 2.00)]),
        active_skill=_active(f"{sid}_a", "축복",
            [_stat_eff(TargetType.ALLY_LOWEST_HP,
                _sb('atk', 0.36, 2, f"{sid}_a", "공격력", is_ratio=True)),
             _stat_eff(TargetType.ALLY_LOWEST_HP,
                _sb('spd', 15.0, 2, f"{sid}_a", "속도", is_ratio=False))]),
        ultimate_skill=_ult(f"{sid}_u", "대축복",
            [_dmg(TargetType.ALL_ENEMY, 1.60),
             _stat_eff(TargetType.ALL_ENEMY,
                _sb('def_', 0.20, 2, f"{sid}_u", "방어력", is_debuff=True, is_ratio=True)),
             _stat_eff(TargetType.ALL_ALLY,
                _sb('atk', 0.20, 2, f"{sid}_u", "공격력", is_ratio=True))],
            sp=4),
        tile_pos=(2, 0),
    )


def make_demeter() -> CharacterData:
    """c354 드미테르 - 화/서포터 (2성)"""
    sid = "c354"
    return CharacterData(
        id=sid, name="드미테르", element=Element.FIRE, role=Role.SUPPORTER,
        side="ally",
        stats=StatBlock(atk=400, def_=320, hp=4000, spd=120),
        normal_skill=_normal(f"{sid}_n", "프릭킹 니들",
            [_dmg(TargetType.ENEMY_NEAR, 3.60)]),
        active_skill=_active(f"{sid}_a", "사이드 이펙트",
            [_dmg(TargetType.ALL_ENEMY, 1.00, burn_bonus=0.20),  # 0.35→0.50 + 화상 스택 비례 추가 피해
             _dot_eff(TargetType.ALL_ENEMY, _burn(f"{sid}_a", dot_ratio=0.20, duration=2)),
             _stat_eff(TargetType.ALL_ENEMY,
                _sb('spd', 0.15, 2, f"{sid}_a", "화상 감속", is_debuff=True, is_ratio=True))]),  # ★ 화상+감속+burn_bonus 콤보
        ultimate_skill=_ult(f"{sid}_u", "극약처방",
            [_dmg(TargetType.ENEMY_NEAR, 4.40),
             _stat_eff(TargetType.ENEMY_NEAR,
                _sb('def_', 0.20, 2, f"{sid}_u", "방어력", is_debuff=True, is_ratio=True))],
            sp=4),
        tile_pos=(0, 0),
    )


def make_dabi_sup() -> CharacterData:
    """c003 다비 - 화/구속형 (2성) — 구속형, 화상 CC 특화"""
    sid = "c003"
    return CharacterData(
        id=sid, name="다비", element=Element.FIRE, role=Role.MAGICIAN,
        side="ally",
        stats=StatBlock(atk=480, def_=320, hp=4000, spd=100),
        normal_skill=_normal(f"{sid}_n", "다비의 불꽃",
            [_dmg(TargetType.ENEMY_NEAR, 2.40)]),
        active_skill=_active(f"{sid}_a", "화상 촉진",
            [_stat_eff(TargetType.ALL_ALLY,
                _sb('atk', 0.15, 2, f"{sid}_a", "화상증폭", is_ratio=True)),
             _dot_eff(TargetType.ENEMY_NEAR, _burn(f"{sid}_a", dot_ratio=0.15, duration=2))]),
        ultimate_skill=_ult(f"{sid}_u", "업화",
            [_dmg(TargetType.ENEMY_NEAR_CROSS, 2.80),
             _dot_eff(TargetType.ENEMY_NEAR_CROSS, _burn(f"{sid}_u", dot_ratio=0.20, duration=3))],
            sp=4),
        tile_pos=(2, 1),
    )


def make_yuda() -> CharacterData:
    """c037 유다 - 화/방어형 (1성)"""
    sid = "c037"
    return CharacterData(
        id=sid, name="유다", element=Element.FIRE, role=Role.DEFENDER,
        side="ally",
        stats=StatBlock(atk=300, def_=360, hp=3600, spd=110),
        normal_skill=_normal(f"{sid}_n", "마탄",
            [_dmg(TargetType.ENEMY_NEAR, 2.40)]),
        active_skill=_active(f"{sid}_a", "악마의 방패",
            [_taunt(2),
             _shield(TargetType.SELF, 0.15)]),
        ultimate_skill=_ult(f"{sid}_u", "심판",
            [_dmg(TargetType.ALL_ENEMY, 1.80),
             _stat_eff(TargetType.ALL_ENEMY,
                _sb('atk', 0.15, 2, f"{sid}_u", "위축", is_debuff=True, is_ratio=True))],
            sp=3),
        tile_pos=(0, 1),
    )


def make_neide() -> CharacterData:
    """c083 네이드 - 화/공격형 (1성)"""
    sid = "c083"
    return CharacterData(
        id=sid, name="네이드", element=Element.FIRE, role=Role.ATTACKER,
        side="ally",
        stats=StatBlock(atk=480, def_=240, hp=2400, spd=80),
        normal_skill=_normal(f"{sid}_n", "파이어 스트라이크",
            [_dmg(TargetType.ENEMY_NEAR, 3.60)]),
        active_skill=_active(f"{sid}_a", "플레임 버스트",
            [_dmg(TargetType.ALL_ENEMY, 2.20),
             _dot_eff(TargetType.ALL_ENEMY, _burn(f"{sid}_a", dot_ratio=0.15, duration=2))]),
        ultimate_skill=_ult(f"{sid}_u", "인페르노",
            [_dmg(TargetType.ENEMY_NEAR, 6.40)],
            sp=6),
        tile_pos=(0, 2),
    )


def make_verdelet() -> CharacterData:
    """c286 베르들레 - 화/회복형 (1성)"""
    sid = "c286"
    return CharacterData(
        id=sid, name="베르들레", element=Element.FIRE, role=Role.HEALER,
        side="ally",
        stats=StatBlock(atk=240, def_=240, hp=2400, spd=90),
        normal_skill=_normal(f"{sid}_n", "생명의 불길",
            [_dmg(TargetType.ENEMY_NEAR, 2.00)]),
        active_skill=_active(f"{sid}_a", "화염 치유",
            [_heal_ratio(TargetType.ALL_ALLY, 0.45)]),
        ultimate_skill=_ult(f"{sid}_u", "불사조의 축복",
            [_heal_ratio(TargetType.ALL_ALLY, 0.55),
             _remove_debuff_eff(TargetType.ALL_ALLY)],
            sp=3),
        tile_pos=(2, 2),
    )


# ════════════════════════════════════════════════════════════════
# 수속성 (Element.WATER)
# ════════════════════════════════════════════════════════════════

def make_eve() -> CharacterData:
    """c124 이브 - 수/공격형
    ★콤보: 처형으로 적 처치 시 ON_KILL → Normal 추격공격 (HSR 토파즈 스타일)
    → 독살 → 이브 처형 → 킬 → 자동 추격 → 연쇄 처치
    """
    sid = "c124"
    return CharacterData(
        id=sid, name="이브", element=Element.WATER, role=Role.ATTACKER,
        side="ally",
        stats=StatBlock(atk=800, def_=400, hp=4000, spd=80),
        normal_skill=_normal(f"{sid}_n", "다크 미스트",
            [_dmg(TargetType.ENEMY_NEAR, 3.60)]),
        active_skill=_active(f"{sid}_a", "레인 드랍",
            [_dmg(TargetType.ENEMY_LOWEST_HP, 4.00),  # 기본 배율 4.50→3.00→2.50→2.00 (4차 너프)
             SkillEffect(logic_type=LogicType.DAMAGE, target_type=TargetType.ENEMY_LOWEST_HP,
                         multiplier=3.00, condition={'target_hp_below': 0.25})]),  # 처형 조건 0.30→0.25
        ultimate_skill=_ult(f"{sid}_u", "실낙원",
            [_dmg(TargetType.ENEMY_LOWEST_HP, 5.00),
             SkillEffect(logic_type=LogicType.DAMAGE, target_type=TargetType.ENEMY_LOWEST_HP,
                         multiplier=2.00, condition={'target_hp_below': 0.25})],  # 처형 조건 0.30→0.25
            sp=6),
        triggers=[
            TriggerData(event=TriggerEvent.ON_KILL, skill_id=f"{sid}_n"),  # ★ 처치 시 Normal 추격공격
        ],
        tile_pos=(0, 1),
    )


def make_sangah() -> CharacterData:
    """c167 상아 - 수/서포터"""
    sid = "c167"
    return CharacterData(
        id=sid, name="상아", element=Element.WATER, role=Role.SUPPORTER,
        side="ally",
        stats=StatBlock(atk=500, def_=400, hp=5000, spd=120),
        normal_skill=_normal(f"{sid}_n", "수류",
            [_dmg(TargetType.ENEMY_NEAR, 2.00)]),
        active_skill=_active(f"{sid}_a", "수렁",
            [_dmg(TargetType.ALL_ENEMY, 3.00),
             _stat_eff(TargetType.ALL_ENEMY,
                _sb('spd', 20.0, 2, f"{sid}_a", "속도", is_debuff=True, is_ratio=False)),
             _stat_eff(TargetType.ALL_ENEMY,
                _sb('def_', 0.15, 2, f"{sid}_a", "수렁", is_debuff=True, is_ratio=True)),
             _remove_buff_eff(TargetType.ALL_ENEMY)]),  # ★ 감속+방깎+버프스트립 (속도 격차 확대)
        ultimate_skill=_ult(f"{sid}_u", "대조수",
            [_stat_eff(TargetType.ALL_ENEMY,
                _sb('spd', 20.0, 2, f"{sid}_u", "속도", is_debuff=True, is_ratio=False)),
             _stat_eff(TargetType.ALL_ALLY,
                _sb('atk', 0.30, 2, f"{sid}_u", "공격력", is_ratio=True))],
            sp=4),
        tile_pos=(2, 2),
    )


def make_thisbe() -> CharacterData:
    """c281 티스베 - 수/회복형"""
    sid = "c281"
    return CharacterData(
        id=sid, name="티스베", element=Element.WATER, role=Role.HEALER,
        side="ally",
        stats=StatBlock(atk=400, def_=400, hp=4000, spd=90),
        normal_skill=_normal(f"{sid}_n", "오아시스",
            [_dmg(TargetType.ENEMY_NEAR, 2.00)]),
        active_skill=_active(f"{sid}_a", "하늘의 창문",
            [_stat_eff(TargetType.SELF,
                _sb('spd', 20.0, 2, f"{sid}_a", "속도", is_ratio=False)),
             _stat_eff(TargetType.ALLY_SAME_ROW,
                _sb('spd', 15.0, 2, f"{sid}_a", "속도", is_ratio=False))]),
        ultimate_skill=_ult(f"{sid}_u", "헤븐리 웰",
            [_stat_eff(TargetType.ALL_ALLY,
                _sb('spd', 15.0, 3, f"{sid}_u", "속도", is_ratio=False)),
             _heal_ratio(TargetType.ALL_ALLY, 0.22)],
            sp=3),
        tile_pos=(2, 1),
    )


def make_bari() -> CharacterData:
    """c318 바리 - 수/구속형"""
    sid = "c318"
    return CharacterData(
        id=sid, name="바리", element=Element.WATER, role=Role.MAGICIAN,
        side="ally",
        stats=StatBlock(atk=600, def_=400, hp=5000, spd=100),
        normal_skill=_normal(f"{sid}_n", "삼재",
            [_dmg(TargetType.ENEMY_NEAR, 1.50, hit_count=2),  # ★ 2연타 (독 2회 적용 → 빠른 스택)
             _dot_eff(TargetType.ENEMY_NEAR, _poison(f"{sid}_n"))]),
        active_skill=_active(f"{sid}_a", "천라홍수",
            [_dmg(TargetType.ENEMY_RANDOM_3, 2.40),
             _dot_eff(TargetType.ENEMY_RANDOM_3, _poison(f"{sid}_a"))]),
        ultimate_skill=_ult(f"{sid}_u", "은하수 곡성",
            [_dmg(TargetType.ALL_ENEMY, 2.00),
             _dot_eff(TargetType.ALL_ENEMY, _poison(f"{sid}_u"))],
            sp=4),
        tile_pos=(0, 0),
    )


def make_dogyehwa() -> CharacterData:
    """c502 도계화 - 수/마법형"""
    sid = "c502"
    return CharacterData(
        id=sid, name="도계화", element=Element.WATER, role=Role.MAGICIAN,
        side="ally",
        stats=StatBlock(atk=600, def_=400, hp=5000, spd=100),
        normal_skill=_normal(f"{sid}_n", "원거만리",
            [_dmg(TargetType.ENEMY_NEAR, 4.00)]),
        active_skill=_active(f"{sid}_a", "신행귀신 속거천리",
            [_dmg(TargetType.ENEMY_NEAR, 3.60),
             _dot_eff(TargetType.ENEMY_NEAR, _poison(f"{sid}_a")),
             _cc(CCType.STUN, 1, f"{sid}_a", TargetType.ENEMY_NEAR),
             _stat_eff(TargetType.ENEMY_NEAR,
                _sb('def_', 0.15, 2, f"{sid}_a", "독소 침식", is_debuff=True, is_ratio=True))]),  # ★ 독+스턴+방깎 콤보
        ultimate_skill=_ult(f"{sid}_u", "급급여율령",
            [_dmg(TargetType.ENEMY_BACK_ROW, 3.00),
             _dot_eff(TargetType.ENEMY_BACK_ROW,
                _poison(f"{sid}_u", dot_ratio=0.20, duration=3))],
            sp=4),
        tile_pos=(1, 2),
    )


def make_elysion() -> CharacterData:
    """c537 엘리시온 - 수/방어형"""
    sid = "c537"
    return CharacterData(
        id=sid, name="엘리시온", element=Element.WATER, role=Role.DEFENDER,
        side="ally",
        stats=StatBlock(atk=500, def_=600, hp=6000, spd=110),
        normal_skill=_normal(f"{sid}_n", "정화의 물",
            [_dmg(TargetType.ENEMY_NEAR, 2.00)]),
        active_skill=_active(f"{sid}_a", "생명수",
            [_heal_ratio(TargetType.ALLY_LOWEST_HP, 0.80),
             _shield(TargetType.ALLY_LOWEST_HP, 0.40),
             _taunt(2),
             _remove_debuff_eff(TargetType.ALLY_LOWEST_HP),
             _stat_eff(TargetType.ALL_ALLY,
                _sb('def_', 0.40, 3, f"{sid}_a", "성수 방어", is_ratio=True))]),  # ★ 팀 DEF+40% (M05 생존)
        ultimate_skill=_ult(f"{sid}_u", "성역",
            [_heal_ratio(TargetType.ALL_ALLY, 0.75),
             _stat_eff(TargetType.ALL_ALLY,
                _sb('def_', 0.20, 2, f"{sid}_u", "방어력", is_ratio=True)),
             _sp_gain(1.0, TargetType.ALL_ALLY)],
            sp=3),
        triggers=[
            TriggerData(event=TriggerEvent.ON_HIT, skill_id=f"{sid}_n",
                        once_per_battle=True),  # ★ 피격 시 Normal 반격 1회 (탱커 카운터)
        ],
        tile_pos=(2, 2),
    )


def make_nirrti() -> CharacterData:
    """c442 니르티 - 수/공격형 (3성)
    N: 근접 단일 2.25x
    A: 단일 3.50x + 방어비율+15%(2턴)
    U: 십자 1.90x + 전체아군 힐 20%
    """
    sid = "c442"
    return CharacterData(
        id=sid, name="니르티", element=Element.WATER, role=Role.ATTACKER,
        side="ally",
        stats=StatBlock(atk=800, def_=400, hp=4000, spd=80),
        normal_skill=_normal(f"{sid}_n", "암류의 일격",
            [_dmg(TargetType.ENEMY_NEAR, 5.00)]),
        active_skill=_active(f"{sid}_a", "심연의 창",
            [_dmg(TargetType.ENEMY_NEAR, 9.00),
             _stat_eff(TargetType.SELF,
                _sb('def_', 0.15, 2, f"{sid}_a", "방어비율", is_ratio=True))]),
        ultimate_skill=_ult(f"{sid}_u", "파도의 심판",
            [_dmg(TargetType.ENEMY_NEAR_CROSS, 5.00),
             _heal_ratio(TargetType.ALL_ALLY, 0.20)],
            sp=6),
        tile_pos=(0, 0),
    )


def make_arhat() -> CharacterData:
    """c464 아라한 - 수/서포터 (3성)
    N: 단일 4.28x (고배율 서포터)
    A: 단일 3.30x
    U: 전체 적 1.10x + 방어력-20%(2턴)
    """
    sid = "c464"
    return CharacterData(
        id=sid, name="아라한", element=Element.WATER, role=Role.SUPPORTER,
        side="ally",
        stats=StatBlock(atk=574, def_=460, hp=5750, spd=120),
        normal_skill=_normal(f"{sid}_n", "장풍",
            [_dmg(TargetType.ENEMY_NEAR, 8.56)]),
        active_skill=_active(f"{sid}_a", "진천뢰",
            [_dmg(TargetType.ENEMY_NEAR, 6.60)]),
        ultimate_skill=_ult(f"{sid}_u", "파천일격",
            [_dmg(TargetType.ALL_ENEMY, 2.20),
             _stat_eff(TargetType.ALL_ENEMY,
                _sb('def_', 0.20, 2, f"{sid}_u", "방어력", is_debuff=True, is_ratio=True))],
            sp=4),
        tile_pos=(2, 1),
    )


def make_lisa() -> CharacterData:
    """c002 리자 - 수/공격형 (2성)
    N: 단일 0.60x (저배율)
    A: 단일 1.35x
    U: 단일 0.30x + 아군 공격력+15%(2턴)
    """
    sid = "c002"
    return CharacterData(
        id=sid, name="리자", element=Element.WATER, role=Role.ATTACKER,
        side="ally",
        stats=StatBlock(atk=640, def_=320, hp=3200, spd=80),
        normal_skill=_normal(f"{sid}_n", "수정 화살",
            [_dmg(TargetType.ENEMY_NEAR, 1.20)]),
        active_skill=_active(f"{sid}_a", "얼음 창",
            [_dmg(TargetType.ENEMY_NEAR, 2.70)]),
        ultimate_skill=_ult(f"{sid}_u", "빙하 세례",
            [_dmg(TargetType.ENEMY_NEAR, 0.60),
             _stat_eff(TargetType.ALL_ALLY,
                _sb('atk', 0.15, 2, f"{sid}_u", "공격력", is_ratio=True))],
            sp=6),
        tile_pos=(1, 1),
    )


def make_virupa() -> CharacterData:
    """c193 비루파 - 수/공격형 (2성)"""
    sid = "c193"
    return CharacterData(
        id=sid, name="비루파", element=Element.WATER, role=Role.ATTACKER,
        side="ally",
        stats=StatBlock(atk=640, def_=320, hp=3200, spd=80),
        normal_skill=_normal(f"{sid}_n", "퇴마의 일격",
            [_dmg(TargetType.ENEMY_NEAR, 3.60)]),
        active_skill=_active(f"{sid}_a", "집중 강화",
            [_stat_eff(TargetType.SELF,
                _sb('atk', 0.25, 2, f"{sid}_a", "공격 집중", is_ratio=True)),
             _dmg(TargetType.ENEMY_NEAR, 3.00)]),
        ultimate_skill=_ult(f"{sid}_u", "파마의 일격",
            [_dmg(TargetType.ENEMY_NEAR, 7.00),
             _stat_eff(TargetType.SELF,
                _sb('atk', 0.20, 2, f"{sid}_u", "극한 집중", is_ratio=True))],
            sp=6),
        tile_pos=(0, 0),
    )


def make_euros() -> CharacterData:
    """c437 에우로스 - 수/회복형 (2성)"""
    sid = "c437"
    return CharacterData(
        id=sid, name="에우로스", element=Element.WATER, role=Role.HEALER,
        side="ally",
        stats=StatBlock(atk=320, def_=320, hp=3200, spd=90),
        normal_skill=_normal(f"{sid}_n", "바람의 속삭임",
            [_dmg(TargetType.ENEMY_NEAR, 2.00)]),
        active_skill=_active(f"{sid}_a", "회복의 바람",
            [_heal_ratio(TargetType.ALLY_LOWEST_HP, 0.30),
             _stat_eff(TargetType.ALLY_LOWEST_HP,
                _sb('def_', 0.15, 2, f"{sid}_a", "방어 강화", is_ratio=True))]),
        ultimate_skill=_ult(f"{sid}_u", "대기의 은혜",
            [_heal_ratio(TargetType.ALL_ALLY, 0.55),
             _remove_debuff_eff(TargetType.ALL_ALLY)],
            sp=3),
        tile_pos=(2, 1),
    )


def make_mayahuel() -> CharacterData:
    """c022 마야우엘 - 수/구속형 (1성) — 구속형, CC 특화"""
    sid = "c022"
    return CharacterData(
        id=sid, name="마야우엘", element=Element.WATER, role=Role.MAGICIAN,
        side="ally",
        stats=StatBlock(atk=360, def_=240, hp=3000, spd=120),
        normal_skill=_normal(f"{sid}_n", "물의 채찍",
            [_dmg(TargetType.ENEMY_NEAR, 2.40)]),
        active_skill=_active(f"{sid}_a", "빙결의 손길",
            [_cc(CCType.FREEZE, 1, f"{sid}_a", TargetType.ENEMY_NEAR),
             _dmg(TargetType.ENEMY_NEAR, 2.00),
             _stat_eff(TargetType.ENEMY_NEAR,
                _sb('def_', 0.20, 2, f"{sid}_a", "빙결 취약", is_debuff=True, is_ratio=True))]),  # ★ CC+DEF 쇄도 콤보
        ultimate_skill=_ult(f"{sid}_u", "얼어붙은 세계",
            [_dmg(TargetType.ALL_ENEMY, 5.00),  # AoE 데미지 1.00→1.50→2.50 (3차 버프)
             _cc(CCType.FREEZE, 2, f"{sid}_u", TargetType.ALL_ENEMY),
             _dot_eff(TargetType.ALL_ENEMY,
                _poison(f"{sid}_u", dot_ratio=0.15, duration=2)),
             _stat_eff(TargetType.ALL_ENEMY,
                _sb('spd', 0.30, 2, f"{sid}_u", "빙결 감속", is_debuff=True, is_ratio=True)),
             _stat_eff(TargetType.ALL_ENEMY,
                _sb('def_', 0.20, 2, f"{sid}_u", "빙결 취약", is_debuff=True, is_ratio=True))],  # ★ DEF-20% (CC창 딜 증폭)
            sp=4),
        tile_pos=(1, 2),
    )


def make_leo() -> CharacterData:
    """c362 레오 - 수/서포터 (1성) — 보조형"""
    sid = "c362"
    return CharacterData(
        id=sid, name="레오", element=Element.WATER, role=Role.SUPPORTER,
        side="ally",
        stats=StatBlock(atk=300, def_=240, hp=3000, spd=120),
        normal_skill=_normal(f"{sid}_n", "물결 타격",
            [_dmg(TargetType.ENEMY_NEAR, 2.40)]),
        active_skill=_active(f"{sid}_a", "수류 가호",
            [_stat_eff(TargetType.ALL_ALLY,
                _sb('def_', 0.15, 2, f"{sid}_a", "수류 방어", is_ratio=True))]),
        ultimate_skill=_ult(f"{sid}_u", "해류의 축복",
            [_stat_eff(TargetType.ALL_ALLY,
                _sb('atk', 0.20, 2, f"{sid}_u", "해류 공격", is_ratio=True)),
             _heal_ratio(TargetType.ALL_ALLY, 0.15)],
            sp=4),
        tile_pos=(2, 2),
    )


def make_deino() -> CharacterData:
    """c366 데이노 - 수/방어형 (1성)"""
    sid = "c366"
    return CharacterData(
        id=sid, name="데이노", element=Element.WATER, role=Role.DEFENDER,
        side="ally",
        stats=StatBlock(atk=300, def_=360, hp=3600, spd=110),
        normal_skill=_normal(f"{sid}_n", "수류 강타",
            [_dmg(TargetType.ENEMY_NEAR, 2.40)]),
        active_skill=_active(f"{sid}_a", "철벽 방어",
            [_taunt(2),
             _shield(TargetType.SELF, 0.20)]),
        ultimate_skill=_ult(f"{sid}_u", "해일의 장벽",
            [_shield(TargetType.ALL_ALLY, 0.15),
             _stat_eff(TargetType.ALL_ALLY,
                _sb('def_', 0.20, 2, f"{sid}_u", "해일 방어", is_ratio=True))],
            sp=3),
        tile_pos=(0, 1),
    )


# ════════════════════════════════════════════════════════════════
# 목속성 (Element.FOREST)
# ════════════════════════════════════════════════════════════════

def make_brownie() -> CharacterData:
    """c229 브라우니 - 목/힐러"""
    sid = "c229"
    return CharacterData(
        id=sid, name="브라우니", element=Element.FOREST, role=Role.HEALER,
        side="ally",
        stats=StatBlock(atk=400, def_=400, hp=4000, spd=90),
        normal_skill=_normal(f"{sid}_n", "고급정보입니다!",
            [_dmg(TargetType.ENEMY_NEAR, 2.00)]),
        active_skill=_active(f"{sid}_a", "특급정보입니다!",
            [_stat_eff(TargetType.ALLY_LOWEST_HP_2,
                _sb('spd', 15.0, 2, f"{sid}_a", "속도", is_ratio=False))]),
        ultimate_skill=_ult(f"{sid}_u", "데스페라도 친칠라",
            [_remove_debuff_eff(TargetType.ALL_ALLY),
             _heal_ratio(TargetType.ALL_ALLY, 0.28),
             _sp_gain(1.0, TargetType.ALL_ALLY)],
            sp=3),
        tile_pos=(2, 0),
    )


def make_batory() -> CharacterData:
    """c294 바토리 - 암/보조형"""
    sid = "c294"
    return CharacterData(
        id=sid, name="바토리", element=Element.DARK, role=Role.SUPPORTER,
        side="ally",
        stats=StatBlock(atk=500, def_=400, hp=5000, spd=120),
        normal_skill=_normal(f"{sid}_n", "동반자 예우",
            [_dmg(TargetType.ENEMY_NEAR, 4.40)]),
        active_skill=_active(f"{sid}_a", "피의 맹세",
            [_dmg(TargetType.ENEMY_NEAR_ROW, 4.50),
             _dot_eff(TargetType.ENEMY_NEAR_ROW, _bleed(f"{sid}_a"))]),
        ultimate_skill=_ult(f"{sid}_u", "에스코트",
            [_dmg(TargetType.ENEMY_NEAR, 7.00)],
            sp=4),
        tile_pos=(0, 2),
    )


def make_pan() -> CharacterData:
    """c336 판 - 목/마법형"""
    sid = "c336"
    return CharacterData(
        id=sid, name="판", element=Element.FOREST, role=Role.MAGICIAN,
        side="ally",
        stats=StatBlock(atk=600, def_=400, hp=5000, spd=100),
        normal_skill=_normal(f"{sid}_n", "목동의 휘파람",
            [_dmg(TargetType.ENEMY_NEAR, 3.00)]),
        active_skill=_active(f"{sid}_a", "작은 양을 위한 굴레",
            [_dmg(TargetType.ENEMY_RANDOM, 4.00),
             _cc(CCType.SLEEP, 1, f"{sid}_a", TargetType.ENEMY_RANDOM)]),
        ultimate_skill=_ult(f"{sid}_u", "고요한 봄의 들판",
            [_dmg(TargetType.ALL_ENEMY, 3.00),
             _cc(CCType.SLEEP, 1, f"{sid}_u", TargetType.ALL_ENEMY)],
            sp=4),
        tile_pos=(1, 1),
    )


def make_miriam() -> CharacterData:
    """c447 미리암 - 목/공격형"""
    sid = "c447"
    return CharacterData(
        id=sid, name="미리암", element=Element.FOREST, role=Role.ATTACKER,
        side="ally",
        stats=StatBlock(atk=800, def_=400, hp=4000, spd=80),
        normal_skill=_normal(f"{sid}_n", "웨이팅 포 딜",
            [_dmg(TargetType.ENEMY_NEAR, 3.40, burn_bonus=0.20)]),  # ★ 세멜레 화상 스택 비례 추가 피해
        active_skill=_active(f"{sid}_a", "크로스 더 루비콘",
            [_stat_eff(TargetType.SELF,
                _sb('atk', 0.30, 3, f"{sid}_a", "공격력", is_ratio=True))]),
        ultimate_skill=_ult(f"{sid}_u", "퓨리오스",
            [_dmg(TargetType.ALL_ENEMY, 7.50),
             _cc(CCType.PANIC, 2, f"{sid}_u", TargetType.ALL_ENEMY)],
            sp=6),
        tile_pos=(0, 1),
    )


def make_aurora() -> CharacterData:
    """c461 아우로라 - 목/서포터"""
    sid = "c461"
    return CharacterData(
        id=sid, name="아우로라", element=Element.FOREST, role=Role.SUPPORTER,
        side="ally",
        stats=StatBlock(atk=500, def_=400, hp=5000, spd=120),
        normal_skill=_normal(f"{sid}_n", "기다림의 끝",
            [_dmg(TargetType.ENEMY_NEAR, 2.00)]),
        active_skill=_active(f"{sid}_a", "지켜주는 나무",
            [_stat_eff(TargetType.ALLY_HIGHEST_ATK,
                _sb('atk', 0.25, 2, f"{sid}_a", "공격력", is_ratio=True)),
             _stat_eff(TargetType.ALLY_HIGHEST_ATK,
                _sb('cri_ratio', 0.15, 2, f"{sid}_a", "크리율", is_ratio=False))]),
        ultimate_skill=_ult(f"{sid}_u", "당신을 향한 고백",
            [_stat_eff(TargetType.ALL_ALLY,
                _sb('atk', 0.20, 3, f"{sid}_u", "공격력", is_ratio=True)),
             _stat_eff(TargetType.ALL_ALLY,
                _sb('cri_ratio', 0.10, 3, f"{sid}_u", "크리율", is_ratio=False))],
            sp=4),
        tile_pos=(2, 2),
    )


def make_metis() -> CharacterData:
    """c468 메티스 - 목/방어형"""
    sid = "c468"
    return CharacterData(
        id=sid, name="메티스", element=Element.FOREST, role=Role.DEFENDER,
        side="ally",
        stats=StatBlock(atk=500, def_=600, hp=6000, spd=110),
        normal_skill=_normal(f"{sid}_n", "지혜의 일격",
            [_dmg(TargetType.ENEMY_NEAR, 2.00)]),
        active_skill=_active(f"{sid}_a", "철벽 수호",
            [_dmg(TargetType.ALL_ENEMY, 1.60),
             _stat_eff(TargetType.ALL_ALLY,
                _sb('def_', 0.25, 2, f"{sid}_a", "방어력", is_ratio=True)),
             _remove_buff_eff(TargetType.ALL_ENEMY)]),  # ★ 적 버프 제거 (보호막·공버프 스트립)
        ultimate_skill=_ult(f"{sid}_u", "지혜의 방패",
            [_stat_eff(TargetType.ALL_ALLY,
                _sb('def_', 0.20, 2, f"{sid}_u", "방어력", is_ratio=True)),
             _stat_eff(TargetType.ALL_ENEMY,
                _sb('atk', 0.20, 2, f"{sid}_u", "공격력", is_debuff=True, is_ratio=True)),
             _remove_debuff_eff(TargetType.ALL_ALLY)],
            sp=3),
        tile_pos=(2, 1),
    )


def make_grilla() -> CharacterData:
    """c525 그릴라 - 목/서포터"""
    sid = "c525"
    return CharacterData(
        id=sid, name="그릴라", element=Element.FOREST, role=Role.SUPPORTER,
        side="ally",
        stats=StatBlock(atk=500, def_=400, hp=5000, spd=120),
        normal_skill=_normal(f"{sid}_n", "악마의 야망",
            [_dmg(TargetType.ENEMY_RANDOM, 4.00)]),
        active_skill=_active(f"{sid}_a", "발푸르기스의 밤",
            [_stat_eff(TargetType.ALL_ALLY,
                _sb('cri_ratio', 0.20, 2, f"{sid}_a", "크리율", is_ratio=False)),
             _stat_eff(TargetType.ALL_ALLY,
                _sb('atk', 0.15, 2, f"{sid}_a", "공격력", is_ratio=True))]),
        ultimate_skill=_ult(f"{sid}_u", "드림 오브 레기온",
            [_stat_eff(TargetType.ALL_ALLY,
                _sb('atk', 0.20, 2, f"{sid}_u", "공격력", is_ratio=True)),
             _stat_eff(TargetType.ALL_ENEMY,
                _sb('def_', 0.20, 2, f"{sid}_u", "방어력", is_debuff=True, is_ratio=True))],
            sp=4),
        triggers=[
            TriggerData(event=TriggerEvent.ON_BATTLE_START, skill_id=f"{sid}_a"),  # ★ 전투 시작 시 Active 자동 발동 (팀 CRI+ATK 버프)
        ],
        tile_pos=(1, 0),
    )


def make_danu() -> CharacterData:
    """c549 다누 - 목/공격형"""
    sid = "c549"
    return CharacterData(
        id=sid, name="다누", element=Element.FOREST, role=Role.ATTACKER,
        side="ally",
        stats=StatBlock(atk=800, def_=400, hp=4000, spd=80),
        normal_skill=_normal(f"{sid}_n", "생명의 손길",
            [_dmg(TargetType.ENEMY_NEAR, 8.00),  # 1.00→2.00→7.00→8.00 (ATK 800, M05 주력 딜러)
             _dot_eff(TargetType.ENEMY_NEAR, _poison(f"{sid}_n", 0.15, 2))]),  # ★ 독 추가 (철벽요새 칩데미지)
        active_skill=_active(f"{sid}_a", "대지의 치유",
            [_dmg(TargetType.ENEMY_NEAR, 4.00),  # ★ 딜+힐 하이브리드 (ATK 800 활용)
             _heal_ratio(TargetType.ALL_ALLY, 0.30),
             _remove_debuff_eff(TargetType.ALL_ALLY)]),
        ultimate_skill=_ult(f"{sid}_u", "부활의 땅",
            [_dmg(TargetType.ALL_ENEMY, 3.00),  # ★ AoE 추가 (M05 킬프레셔)
             _heal_ratio(TargetType.ALL_ALLY, 0.40),
             _revive(0.50)],
            sp=6),
        tile_pos=(2, 2),
    )


def make_mammon() -> CharacterData:
    """c180 맘몬 - 목/방어형 (2성)
    N: 근접 단일 1.80x
    A: 단일 1.35x + 넉백(CC 대체)
    U: 전체 적 1.60x
    """
    sid = "c180"
    return CharacterData(
        id=sid, name="맘몬", element=Element.FOREST, role=Role.DEFENDER,
        side="ally",
        stats=StatBlock(atk=400, def_=480, hp=4800, spd=110),
        normal_skill=_normal(f"{sid}_n", "대지의 주먹",
            [_dmg(TargetType.ENEMY_NEAR, 3.60)]),
        active_skill=_active(f"{sid}_a", "지진 강타",
            [_dmg(TargetType.ENEMY_NEAR, 2.70),
             _cc(CCType.STUN, 1, f"{sid}_a", TargetType.ENEMY_NEAR)]),
        ultimate_skill=_ult(f"{sid}_u", "대지 분쇄",
            [_dmg(TargetType.ALL_ENEMY, 3.20)],
            sp=3),
        triggers=[
            TriggerData(event=TriggerEvent.ON_HIT, skill_id=f"{sid}_n",
                        once_per_battle=True),  # ★ 피격 시 Normal 반격 1회 (광전사 탱커)
        ],
        tile_pos=(1, 0),
    )


def make_freya() -> CharacterData:
    """c031 프레이야 - 목/회복형 (1성)"""
    sid = "c031"
    return CharacterData(
        id=sid, name="프레이야", element=Element.FOREST, role=Role.HEALER,
        side="ally",
        stats=StatBlock(atk=240, def_=240, hp=2400, spd=90),
        normal_skill=_normal(f"{sid}_n", "자연의 가시",
            [_dmg(TargetType.ENEMY_NEAR, 2.00)]),
        active_skill=_active(f"{sid}_a", "생명의 꽃",
            [_heal_ratio(TargetType.ALLY_LOWEST_HP, 0.30),
             _remove_debuff_eff(TargetType.ALLY_LOWEST_HP)]),
        ultimate_skill=_ult(f"{sid}_u", "대지의 은총",
            [_heal_ratio(TargetType.ALL_ALLY, 0.35),
             _stat_eff(TargetType.ALL_ALLY,
                _sb('def_', 0.15, 2, f"{sid}_u", "대지 방어", is_ratio=True))],
            sp=3),
        tile_pos=(2, 2),
    )


def make_diana() -> CharacterData:
    """c033 다이아나 - 목/구속형 (1성) — 구속형, CC 특화"""
    sid = "c033"
    return CharacterData(
        id=sid, name="다이아나", element=Element.FOREST, role=Role.MAGICIAN,
        side="ally",
        stats=StatBlock(atk=360, def_=240, hp=3000, spd=120),
        normal_skill=_normal(f"{sid}_n", "달빛 화살",
            [_dmg(TargetType.ENEMY_NEAR, 2.40)]),
        active_skill=_active(f"{sid}_a", "숲의 속박",
            [_cc(CCType.STUN, 1, f"{sid}_a", TargetType.ENEMY_NEAR),
             _dmg(TargetType.ENEMY_NEAR, 2.00)]),
        ultimate_skill=_ult(f"{sid}_u", "달빛 심판",
            [_dmg(TargetType.ALL_ENEMY, 2.00),  # AoE 데미지 추가 (CC+딜 하이브리드)
             _cc(CCType.SLEEP, 2, f"{sid}_u", TargetType.ALL_ENEMY),
             _stat_eff(TargetType.ALL_ENEMY,
                _sb('spd', 0.20, 2, f"{sid}_u", "감속", is_debuff=True, is_ratio=True))],
            sp=4),
        tile_pos=(1, 2),
    )


def make_europe() -> CharacterData:
    """c062 에우로페 - 목/공격형 (1성)"""
    sid = "c062"
    return CharacterData(
        id=sid, name="에우로페", element=Element.FOREST, role=Role.ATTACKER,
        side="ally",
        stats=StatBlock(atk=480, def_=240, hp=2400, spd=80),
        normal_skill=_normal(f"{sid}_n", "넝쿨 타격",
            [_dmg(TargetType.ENEMY_NEAR, 3.60)]),
        active_skill=_active(f"{sid}_a", "자연의 분노",
            [_dmg(TargetType.ALL_ENEMY, 2.20),
             _dot_eff(TargetType.ALL_ENEMY, _poison(f"{sid}_a", dot_ratio=0.15, duration=2))]),
        ultimate_skill=_ult(f"{sid}_u", "가이아의 심판",
            [_dmg(TargetType.ENEMY_NEAR, 6.40)],
            sp=6),
        tile_pos=(0, 2),
    )


def make_midas() -> CharacterData:
    """c132 미다스 - 목/공격형 (2성)"""
    sid = "c132"
    return CharacterData(
        id=sid, name="미다스", element=Element.FOREST, role=Role.ATTACKER,
        side="ally",
        stats=StatBlock(atk=640, def_=320, hp=3200, spd=80),
        normal_skill=_normal(f"{sid}_n", "황금 주먹",
            [_dmg(TargetType.ENEMY_NEAR, 3.60)]),
        active_skill=_active(f"{sid}_a", "황금의 손길",
            [_dmg(TargetType.ENEMY_NEAR, 4.00),
             _stat_eff(TargetType.ENEMY_NEAR,
                _sb('def_', 0.20, 2, f"{sid}_a", "부식", is_debuff=True, is_ratio=True))]),
        ultimate_skill=_ult(f"{sid}_u", "황금폭풍",
            [_dmg(TargetType.ALL_ENEMY, 3.60),
             _stat_eff(TargetType.ALL_ENEMY,
                _sb('def_', 0.15, 2, f"{sid}_u", "황금 부식", is_debuff=True, is_ratio=True))],
            sp=6),
        tile_pos=(0, 0),
    )


def make_jacheongbi() -> CharacterData:
    """c398 자청비 - 목/서포터 (2성) — 보조형"""
    sid = "c398"
    return CharacterData(
        id=sid, name="자청비", element=Element.FOREST, role=Role.SUPPORTER,
        side="ally",
        stats=StatBlock(atk=400, def_=320, hp=4000, spd=120),
        normal_skill=_normal(f"{sid}_n", "바람의 일격",
            [_dmg(TargetType.ENEMY_NEAR, 2.40)]),
        active_skill=_active(f"{sid}_a", "숲의 가호",
            [_stat_eff(TargetType.ALL_ALLY,
                _sb('atk', 0.15, 2, f"{sid}_a", "숲의 힘", is_ratio=True)),
             _stat_eff(TargetType.ALL_ALLY,
                _sb('def_', 0.10, 2, f"{sid}_a", "숲의 보호", is_ratio=True)),
             _remove_buff_eff(TargetType.ALL_ENEMY)]),  # ★ 아군 버프 + 적 버프 스트립 (혼돈의밤 카오스)
        ultimate_skill=_ult(f"{sid}_u", "대자연의 축복",
            [_stat_eff(TargetType.ALL_ALLY,
                _sb('atk', 0.25, 2, f"{sid}_u", "자연의 힘", is_ratio=True)),
             _heal_ratio(TargetType.ALL_ALLY, 0.15)],
            sp=4),
        tile_pos=(2, 1),
    )


# ════════════════════════════════════════════════════════════════
# 광속성 (Element.LIGHT)
# ════════════════════════════════════════════════════════════════

def make_ashtoreth() -> CharacterData:
    """c194 아슈토레스 - 광/공격형"""
    sid = "c194"
    return CharacterData(
        id=sid, name="아슈토레스", element=Element.LIGHT, role=Role.ATTACKER,
        side="ally",
        stats=StatBlock(atk=800, def_=400, hp=4000, spd=80),
        normal_skill=_normal(f"{sid}_n", "밤의 속삭임",
            [_dmg(TargetType.ENEMY_RANDOM_2, 4.00)]),
        active_skill=_active(f"{sid}_a", "심연의 덫",
            [_dmg(TargetType.ENEMY_NEAR, 4.50)]),
        ultimate_skill=_ult(f"{sid}_u", "가시 무도회",
            [_dmg(TargetType.ENEMY_NEAR, 4.00)],  # 5.50→4.50→4.00 (M10 너프, 킬체인 제거)
            sp=6),
        tile_pos=(0, 0),
    )


def make_sitri() -> CharacterData:
    """c364 시트리 - 광/서포터"""
    sid = "c364"
    return CharacterData(
        id=sid, name="시트리", element=Element.LIGHT, role=Role.SUPPORTER,
        side="ally",
        stats=StatBlock(atk=500, def_=400, hp=5000, spd=120),
        normal_skill=_normal(f"{sid}_n", "폴 인 러브",
            [_dmg(TargetType.ENEMY_NEAR, 2.00)]),
        active_skill=_active(f"{sid}_a", "크런치 캔디",
            [_stat_eff(TargetType.ALL_ALLY,
                _sb('atk', 0.25, 3, f"{sid}_a", "공격력", is_ratio=True)),
             _stat_eff(TargetType.ALL_ALLY,
                _sb('spd', 10.0, 3, f"{sid}_a", "속도", is_ratio=False))]),
        ultimate_skill=_ult(f"{sid}_u", "라 돌체 비타",
            [_dmg(TargetType.ALL_ENEMY, 2.30),
             _stat_eff(TargetType.ALL_ALLY,
                _sb('atk', 0.25, 3, f"{sid}_u", "공격력", is_ratio=True)),
             _stat_eff(TargetType.ALL_ALLY,
                _sb('cri_dmg_ratio', 0.20, 3, f"{sid}_u", "크리피해", is_ratio=False))],
            sp=4),
        tile_pos=(2, 0),  # ON_BATTLE_START 제거 (M04 과도 버프 스택 방지)
    )


def make_mona() -> CharacterData:
    """c393 모나 - 광/방어형"""
    sid = "c393"
    return CharacterData(
        id=sid, name="모나", element=Element.LIGHT, role=Role.DEFENDER,
        side="ally",
        stats=StatBlock(atk=500, def_=600, hp=6000, spd=100),
        normal_skill=_normal(f"{sid}_n", "이클립스",
            [_dmg(TargetType.ENEMY_NEAR, 2.00)]),
        active_skill=_active(f"{sid}_a", "트릭스타",
            [_heal_ratio(TargetType.ALLY_LOWEST_HP, 0.20),
             _stat_eff(TargetType.ALLY_LOWEST_HP,
                _sb('spd', 15.0, 2, f"{sid}_a", "속도", is_ratio=False))]),
        ultimate_skill=_ult(f"{sid}_u", "사랑을 담아",
            [_stat_eff(TargetType.ALL_ALLY,
                _sb('spd', 15.0, 3, f"{sid}_u", "속도", is_ratio=False)),
             _heal_ratio(TargetType.ALL_ALLY, 0.10)],
            sp=3),
        tile_pos=(2, 2),
    )


def make_semele() -> CharacterData:
    """c438 세멜레 - 광/구속형"""
    sid = "c438"
    return CharacterData(
        id=sid, name="세멜레", element=Element.LIGHT, role=Role.MAGICIAN,
        side="ally",
        stats=StatBlock(atk=600, def_=400, hp=5000, spd=100),
        normal_skill=_normal(f"{sid}_n", "신성 강타",
            [_dmg(TargetType.ENEMY_NEAR, 2.00, hit_count=2)]),  # ★ 2연타 (화상 2회 적용 → 미리암 burn_bonus 시너지)
        active_skill=_active(f"{sid}_a", "제우스의 불꽃",
            [_dot_eff(TargetType.ENEMY_NEAR, _burn(f"{sid}_a")),
             _stat_eff(TargetType.ENEMY_NEAR,
                _sb('atk', 0.20, 2, f"{sid}_a", "공격력", is_debuff=True, is_ratio=True))]),
        ultimate_skill=_ult(f"{sid}_u", "신의 번개",
            [_dmg(TargetType.ALL_ENEMY, 6.00),
             _dot_eff(TargetType.ALL_ENEMY, _burn(f"{sid}_u"))],
            sp=4),
        tile_pos=(0, 2),
    )


def make_tiwaz() -> CharacterData:
    """c455 티와즈 - 광/회복형"""
    sid = "c455"
    return CharacterData(
        id=sid, name="티와즈", element=Element.LIGHT, role=Role.HEALER,
        side="ally",
        stats=StatBlock(atk=400, def_=400, hp=4000, spd=90),
        normal_skill=_normal(f"{sid}_n", "전쟁신의 검",
            [_dmg(TargetType.ENEMY_NEAR, 4.00)]),
        active_skill=_active(f"{sid}_a", "관통 공격",
            [_dmg(TargetType.ENEMY_SAME_COL, 5.00)]),
        ultimate_skill=_ult(f"{sid}_u", "신의 선언",
            [_dmg(TargetType.ALL_ENEMY, 3.00),
             _stat_eff(TargetType.ALL_ENEMY,
                _sb('def_', 0.25, 2, f"{sid}_u", "방어력", is_debuff=True, is_ratio=True))],
            sp=3),
        tile_pos=(0, 1),
    )


def make_titania() -> CharacterData:
    """c473 티타니아 - 광/방어형"""
    sid = "c473"
    return CharacterData(
        id=sid, name="티타니아", element=Element.LIGHT, role=Role.DEFENDER,
        side="ally",
        stats=StatBlock(atk=500, def_=600, hp=6000, spd=110),
        normal_skill=_normal(f"{sid}_n", "요정의 손길",
            [_dmg(TargetType.ENEMY_NEAR, 2.00)]),
        active_skill=_active(f"{sid}_a", "요정의 축복",
            [_heal_ratio(TargetType.ALL_ALLY, 0.15),
             _stat_eff(TargetType.ALL_ALLY,
                _sb('cri_ratio', 0.15, 2, f"{sid}_a", "크리율", is_ratio=False))]),
        ultimate_skill=_ult(f"{sid}_u", "요정의 여왕",
            [_heal_ratio(TargetType.ALL_ALLY, 0.20),
             _stat_eff(TargetType.ALL_ALLY,
                _sb('atk', 0.20, 3, f"{sid}_u", "공격력", is_ratio=True)),
             _stat_eff(TargetType.ALL_ALLY,
                _sb('spd', 10.0, 3, f"{sid}_u", "속도", is_ratio=False))],
            sp=3),
        tile_pos=(2, 1),
    )


def make_oneiroi() -> CharacterData:
    """c533 오네이로이 - 광/보조형"""
    sid = "c533"
    return CharacterData(
        id=sid, name="오네이로이", element=Element.LIGHT, role=Role.SUPPORTER,
        side="ally",
        stats=StatBlock(atk=500, def_=400, hp=5000, spd=120),
        normal_skill=_normal(f"{sid}_n", "꿈의 속삭임",
            [_dmg(TargetType.ENEMY_NEAR, 3.00)]),
        active_skill=_active(f"{sid}_a", "잠의 손길",
            [_dmg(TargetType.ENEMY_RANDOM, 5.00),
             _cc(CCType.SLEEP, 1, f"{sid}_a", TargetType.ENEMY_RANDOM),
             _stat_eff(TargetType.ENEMY_RANDOM,
                _sb('def_', 0.15, 2, f"{sid}_a", "꿈의 침식", is_debuff=True, is_ratio=True))]),  # ★ 수면+방깎 (DPS 셋업)
        ultimate_skill=_ult(f"{sid}_u", "영원한 꿈",
            [_dmg(TargetType.ALL_ENEMY, 3.00),
             _cc(CCType.SLEEP, 2, f"{sid}_u", TargetType.ALL_ENEMY)],
            sp=4),
        tile_pos=(1, 2),
    )


def make_c600() -> CharacterData:
    """c600 루미나 - 광/구속형 (OP)
    시트리+엘리시온+브라우니의 장점을 통합한 최상위 서포터.
    SPD 100(구속형 룰), Active 전체버프+정화, Ult 힐+ATK+CRI_DMG+SP.
    """
    sid = "c600"
    return CharacterData(
        id=sid, name="루미나", element=Element.LIGHT, role=Role.MAGICIAN,
        side="ally",
        stats=StatBlock(atk=690, def_=460, hp=5750, spd=100),
        normal_skill=_normal(f"{sid}_n", "성광의 채찍",
            [_dmg(TargetType.ENEMY_NEAR, 2.40)]),
        active_skill=_active(f"{sid}_a", "빛의 축복",
            [_stat_eff(TargetType.ALL_ALLY,
                _sb('atk', 0.15, 2, f"{sid}_a", "공격력", is_ratio=True)),
             _stat_eff(TargetType.ALL_ALLY,
                _sb('spd', 15.0, 2, f"{sid}_a", "속도", is_ratio=False)),
             _remove_debuff_eff(TargetType.ALL_ALLY)]),  # REMOVE_BUFF 제거 (M04 과도 우위 방지)
        ultimate_skill=_ult(f"{sid}_u", "성역의 은총",
            [_heal_ratio(TargetType.ALL_ALLY, 0.25),
             _stat_eff(TargetType.ALL_ALLY,
                _sb('atk', 0.25, 3, f"{sid}_u", "공격력", is_ratio=True)),
             _stat_eff(TargetType.ALL_ALLY,
                _sb('cri_dmg_ratio', 0.30, 3, f"{sid}_u", "크리피해", is_ratio=False))],
            sp=4),
        tile_pos=(2, 0),
    )


def make_dana() -> CharacterData:
    """c183 다나 - 광/힐러 (2성)
    N: 단일 4.28x (고배율 힐러)
    A: 아군 최저HP 힐 25%
    U: 전체 아군 힐 30% + 공격력+20%(3턴)
    """
    sid = "c183"
    return CharacterData(
        id=sid, name="다나", element=Element.LIGHT, role=Role.HEALER,
        side="ally",
        stats=StatBlock(atk=320, def_=320, hp=3200, spd=90),
        normal_skill=_normal(f"{sid}_n", "빛의 화살",
            [_dmg(TargetType.ENEMY_NEAR, 8.56)]),
        active_skill=_active(f"{sid}_a", "성스러운 기도",
            [_heal_ratio(TargetType.ALLY_LOWEST_HP, 0.25)]),
        ultimate_skill=_ult(f"{sid}_u", "빛의 은총",
            [_heal_ratio(TargetType.ALL_ALLY, 0.30),
             _stat_eff(TargetType.ALL_ALLY,
                _sb('atk', 0.20, 3, f"{sid}_u", "공격력", is_ratio=True))],
            sp=3),
        tile_pos=(2, 1),
    )


def make_hildr() -> CharacterData:
    """c296 힐드 - 광/공격형 (2성)
    N: 단일 2.25x
    A: 단일 0.40x + 적 명중-20(2턴)
    U: 행 3.20x + SP 증가
    """
    sid = "c296"
    return CharacterData(
        id=sid, name="힐드", element=Element.LIGHT, role=Role.ATTACKER,
        side="ally",
        stats=StatBlock(atk=640, def_=320, hp=3200, spd=80),
        normal_skill=_normal(f"{sid}_n", "빛의 검",
            [_dmg(TargetType.ENEMY_NEAR, 4.50)]),
        active_skill=_active(f"{sid}_a", "섬광 베기",
            [_dmg(TargetType.ENEMY_NEAR, 0.80),
             _stat_eff(TargetType.ENEMY_NEAR,
                _sb('acc', 20.0, 2, f"{sid}_a", "명중", is_debuff=True, is_ratio=False))]),
        ultimate_skill=_ult(f"{sid}_u", "발키리의 심판",
            [_dmg(TargetType.ENEMY_NEAR_ROW, 6.40),
             _sp_gain(1.0, TargetType.SELF)],
            sp=6),
        tile_pos=(0, 1),
    )


def make_charlotte() -> CharacterData:
    """c353 샤를 - 광/방어형 (1성)
    N: 단일 1.20x
    A: 보호막 30% (전체 아군)
    U: 행 2.00x + 보호막 35% (전체 아군)
    """
    sid = "c353"
    return CharacterData(
        id=sid, name="샤를", element=Element.LIGHT, role=Role.DEFENDER,
        side="ally",
        stats=StatBlock(atk=300, def_=360, hp=3600, spd=110),
        normal_skill=_normal(f"{sid}_n", "빛의 방패",
            [_dmg(TargetType.ENEMY_NEAR, 2.40)]),
        active_skill=_active(f"{sid}_a", "성벽",
            [_shield(TargetType.ALL_ALLY, 1.00)]),
        ultimate_skill=_ult(f"{sid}_u", "수호의 빛",
            [_dmg(TargetType.ENEMY_NEAR_ROW, 4.00),
             _heal_ratio(TargetType.ALL_ALLY, 0.50),
             _shield(TargetType.ALL_ALLY, 1.00)],
            sp=3),
        triggers=[
            TriggerData(event=TriggerEvent.ON_BATTLE_START, skill_id=f"{sid}_a"),  # ★ 전투 시작 시 팀 배리어 60% 선배치
        ],
        tile_pos=(1, 0),
    )


def make_leda() -> CharacterData:
    """c028 레다 - 광/서포터 (1성) — 보조형"""
    sid = "c028"
    return CharacterData(
        id=sid, name="레다", element=Element.LIGHT, role=Role.SUPPORTER,
        side="ally",
        stats=StatBlock(atk=300, def_=240, hp=3000, spd=120),
        normal_skill=_normal(f"{sid}_n", "빛의 화살",
            [_dmg(TargetType.ENEMY_NEAR, 2.40)]),
        active_skill=_active(f"{sid}_a", "성광의 가호",
            [_stat_eff(TargetType.ALL_ALLY,
                _sb('atk', 0.15, 2, f"{sid}_a", "성광 공격", is_ratio=True)),
             _heal_ratio(TargetType.ALL_ALLY, 0.40)]),
        ultimate_skill=_ult(f"{sid}_u", "빛의 은혜",
            [_dmg(TargetType.ALL_ENEMY, 3.50),  # ★ AoE 데미지 추가 (철벽요새 킬프레셔)
             _stat_eff(TargetType.ALL_ALLY,
                _sb('atk', 0.15, 2, f"{sid}_u", "빛의 축복", is_ratio=True)),
             _stat_eff(TargetType.ALL_ALLY,
                _sb('def_', 0.20, 2, f"{sid}_u", "빛의 보호", is_ratio=True))],
            sp=4),
        tile_pos=(2, 2),
    )


def make_yana() -> CharacterData:
    """c221 야나 - 광/공격형 (1성)"""
    sid = "c221"
    return CharacterData(
        id=sid, name="야나", element=Element.LIGHT, role=Role.ATTACKER,
        side="ally",
        stats=StatBlock(atk=480, def_=240, hp=2400, spd=80),
        normal_skill=_normal(f"{sid}_n", "광선 타격",
            [_dmg(TargetType.ENEMY_NEAR, 3.60)]),
        active_skill=_active(f"{sid}_a", "섬광 일격",
            [_dmg(TargetType.ENEMY_NEAR, 4.40),
             _stat_eff(TargetType.ENEMY_NEAR,
                _sb('def_', 0.15, 2, f"{sid}_a", "방어 감소", is_debuff=True, is_ratio=True))]),
        ultimate_skill=_ult(f"{sid}_u", "광폭발",
            [_dmg(TargetType.ALL_ENEMY, 3.60)],
            sp=6),
        tile_pos=(0, 2),
    )


def make_mafdet() -> CharacterData:
    """c227 마프데트 - 광/구속형 (2성) — 구속형, CC 특화"""
    sid = "c227"
    return CharacterData(
        id=sid, name="마프데트", element=Element.LIGHT, role=Role.MAGICIAN,
        side="ally",
        stats=StatBlock(atk=480, def_=320, hp=4000, spd=120),
        normal_skill=_normal(f"{sid}_n", "빛의 발톱",
            [_dmg(TargetType.ENEMY_NEAR, 2.40)]),
        active_skill=_active(f"{sid}_a", "심판의 사슬",
            [_cc(CCType.STUN, 1, f"{sid}_a", TargetType.ENEMY_NEAR),
             _stat_eff(TargetType.ENEMY_NEAR,
                _sb('spd', 0.20, 2, f"{sid}_a", "구속", is_debuff=True, is_ratio=True))]),
        ultimate_skill=_ult(f"{sid}_u", "정의의 심판",
            [_dmg(TargetType.ALL_ENEMY, 7.50),  # AoE 2.50→2.80 (CC창 킬파워 보강)
             _cc(CCType.STUN, 2, f"{sid}_u", TargetType.ALL_ENEMY),
             _stat_eff(TargetType.ALL_ENEMY,
                _sb('atk', 0.20, 2, f"{sid}_u", "약화", is_debuff=True, is_ratio=True))],
            sp=4),
        tile_pos=(1, 2),
    )


# ════════════════════════════════════════════════════════════════
# 암속성 (Element.DARK)
# ════════════════════════════════════════════════════════════════

def make_frey() -> CharacterData:
    """c051 프레이 - 암/방어형"""
    sid = "c051"
    return CharacterData(
        id=sid, name="프레이", element=Element.DARK, role=Role.DEFENDER,
        side="ally",
        stats=StatBlock(atk=500, def_=600, hp=6000, spd=110),
        normal_skill=_normal(f"{sid}_n", "그림 리퍼",
            [_dmg(TargetType.ENEMY_NEAR, 3.00)]),
        active_skill=_active(f"{sid}_a", "사신의 잔상",
            [_stat_eff(TargetType.SELF,
                _sb('atk', 0.25, 2, f"{sid}_a", "공격력", is_ratio=True)),
             _stat_eff(TargetType.SELF,
                _sb('cri_ratio', 0.40, 2, f"{sid}_a", "크리율", is_ratio=False)),
             _counter(2)]),
        ultimate_skill=_ult(f"{sid}_u", "트릭스터",
            [_dmg(TargetType.ENEMY_NEAR_ROW, 4.00),
             _stat_eff(TargetType.ENEMY_NEAR_ROW,
                _sb('def_', 0.25, 2, f"{sid}_u", "방어력", is_debuff=True, is_ratio=True))],
            sp=3),
        triggers=[
            TriggerData(event=TriggerEvent.ON_HIT, skill_id=f"{sid}_n",
                        once_per_battle=True),  # ★ 피격 시 Normal 반격 1회 (카운터 탱커)
        ],
        tile_pos=(0, 1),
    )


def make_banshee() -> CharacterData:
    """c400 반시 - 암/구속형"""
    sid = "c400"
    return CharacterData(
        id=sid, name="반시", element=Element.DARK, role=Role.MAGICIAN,
        side="ally",
        stats=StatBlock(atk=600, def_=400, hp=5000, spd=100),
        normal_skill=_normal(f"{sid}_n", "4연격",
            [_dmg(TargetType.ENEMY_NEAR, 2.00, hit_count=4)]),
        active_skill=_active(f"{sid}_a", "전투 기도",
            [_stat_eff(TargetType.SELF,
                _sb('atk', 0.30, 2, f"{sid}_a", "공격력", is_ratio=True)),
             _stat_eff(TargetType.SELF,
                _sb('cri_ratio', 0.20, 2, f"{sid}_a", "크리율", is_ratio=False))]),
        ultimate_skill=_ult(f"{sid}_u", "뱅시의 절규",
            [_dmg(TargetType.ALL_ENEMY, 3.00)],
            sp=4),
        tile_pos=(0, 0),
    )


def make_artemis() -> CharacterData:
    """c432 아르테미스 - 암/구속형"""
    sid = "c432"
    return CharacterData(
        id=sid, name="아르테미스", element=Element.DARK, role=Role.MAGICIAN,
        side="ally",
        stats=StatBlock(atk=600, def_=400, hp=5000, spd=100),
        normal_skill=_normal(f"{sid}_n", "나이트메어 이블",
            [_dmg(TargetType.ENEMY_RANDOM, 4.00, hit_count=4)]),
        active_skill=_active(f"{sid}_a", "광포한 분노",
            [_dmg(TargetType.ENEMY_NEAR, 3.00),
             _stat_eff(TargetType.ENEMY_NEAR,
                _sb('def_', 0.25, 2, f"{sid}_a", "방어력", is_debuff=True, is_ratio=True)),
             _remove_buff_eff(TargetType.ENEMY_NEAR)]),  # ★ 방깎+버프스트립 (디버프 전문)
        ultimate_skill=_ult(f"{sid}_u", "침식하는 어둠",
            [_dmg(TargetType.ALL_ENEMY, 5.00),
             _stat_eff(TargetType.ALL_ENEMY,
                _sb('def_', 0.20, 2, f"{sid}_u", "방어력", is_debuff=True, is_ratio=True))],
            sp=4),
        tile_pos=(0, 2),
    )


def make_mircalla() -> CharacterData:
    """c448 미르칼라 - 암/회복형"""
    sid = "c448"
    return CharacterData(
        id=sid, name="미르칼라", element=Element.DARK, role=Role.HEALER,
        side="ally",
        stats=StatBlock(atk=400, def_=400, hp=4000, spd=90),
        normal_skill=_normal(f"{sid}_n", "흡혈",
            [_dmg(TargetType.ENEMY_NEAR, 3.60)]),
        active_skill=_active(f"{sid}_a", "핏빛 저주",
            [_dmg(TargetType.ENEMY_NEAR, 4.00),
             _dot_eff(TargetType.ENEMY_NEAR,
                _bleed(f"{sid}_a", dot_ratio=0.15, duration=3)),
             _stat_eff(TargetType.ENEMY_NEAR,
                _sb('atk', 0.20, 2, f"{sid}_a", "공격력", is_debuff=True, is_ratio=True))]),
        ultimate_skill=_ult(f"{sid}_u", "뱀파이어 폭풍",
            [_dmg(TargetType.ALL_ENEMY, 3.60),
             _dot_eff(TargetType.ALL_ENEMY, _bleed(f"{sid}_u"))],
            sp=3),
        tile_pos=(1, 0),
    )


def make_yuna() -> CharacterData:
    """c485 유나 - 암/서포터"""
    sid = "c485"
    return CharacterData(
        id=sid, name="유나", element=Element.DARK, role=Role.SUPPORTER,
        side="ally",
        stats=StatBlock(atk=500, def_=400, hp=5000, spd=120),
        normal_skill=_normal(f"{sid}_n", "달그림자",
            [_dmg(TargetType.ENEMY_NEAR, 2.00)]),
        active_skill=_active(f"{sid}_a", "어둠의 가호",
            [_heal_ratio(TargetType.ALLY_LOWEST_HP, 0.25),
             _stat_eff(TargetType.ALLY_LOWEST_HP,
                _sb('def_', 0.20, 2, f"{sid}_a", "방어력", is_ratio=True)),
             _stat_eff(TargetType.ALL_ENEMY,
                _sb('spd', 15.0, 2, f"{sid}_a", "어둠 감속", is_debuff=True, is_ratio=False))]),  # ★ 적 SPD-15 (카운터 유도)
        ultimate_skill=_ult(f"{sid}_u", "달의 수호",
            [_stat_eff(TargetType.ALL_ALLY,
                _sb('atk', 0.20, 2, f"{sid}_u", "공격력", is_ratio=True)),
             _stat_eff(TargetType.ALL_ALLY,
                _sb('def_', 0.20, 2, f"{sid}_u", "방어력", is_ratio=True))],
            sp=4),
        tile_pos=(2, 2),
    )


def make_kubaba() -> CharacterData:
    """c486 쿠바바 - 암/공격형"""
    sid = "c486"
    return CharacterData(
        id=sid, name="쿠바바", element=Element.DARK, role=Role.ATTACKER,
        side="ally",
        stats=StatBlock(atk=800, def_=400, hp=4000, spd=80),
        normal_skill=_normal(f"{sid}_n", "와일드 로드",
            [_dmg(TargetType.ENEMY_NEAR, 3.80)]),
        active_skill=_active(f"{sid}_a", "오버 더 리밋",
            [_dmg(TargetType.ALL_ENEMY, 3.60),
             _stat_eff(TargetType.ALL_ENEMY,
                _sb('def_', 0.20, 2, f"{sid}_a", "방어력", is_debuff=True, is_ratio=True))]),
        ultimate_skill=_ult(f"{sid}_u", "데스 스키드 마크",
            [_dmg(TargetType.ENEMY_NEAR, 7.00)],  # 3.80→3.50 (M04 원킬 억제)
            sp=6),
        triggers=[
            TriggerData(event=TriggerEvent.ON_KILL, skill_id=f"{sid}_n"),  # ★ 처치 시 Normal 추격 (킬 스노우볼)
        ],
        tile_pos=(0, 0),
    )


def make_anubis() -> CharacterData:
    """c532 아누비스 - 암/공격형"""
    sid = "c532"
    return CharacterData(
        id=sid, name="아누비스", element=Element.DARK, role=Role.ATTACKER,
        side="ally",
        stats=StatBlock(atk=920, def_=460, hp=4600, spd=80),
        normal_skill=_normal(f"{sid}_n", "사자의 인도",
            [_dmg(TargetType.ENEMY_NEAR, 3.40)]),
        active_skill=_active(f"{sid}_a", "직선 심판",
            [_dmg(TargetType.ENEMY_SAME_COL, 4.00, hit_count=3)]),  # 2.50×3→2.00×3 (관통 유지, 총합 6.00x)
        ultimate_skill=_ult(f"{sid}_u", "심판의 저울",
            [_dmg(TargetType.ENEMY_LOWEST_HP, 6.00)],
            sp=6),
        triggers=[
            TriggerData(event=TriggerEvent.ON_KILL, skill_id=f"{sid}_n"),  # ★ 처치 시 Normal 추격 (반격요새 딜러)
        ],
        tile_pos=(0, 1),
    )


def make_c601() -> CharacterData:
    """c601 에레보스 - 목/구속형 (OP)
    이브+쿠바바+아르테미스의 장점을 통합한 최상위 딜러.
    ATK 530(최고), CRI 35%, PEN 20%, Normal 2연타, Active 처형, Ult AoE+디버프+출혈.
    """
    sid = "c601"
    return CharacterData(
        id=sid, name="에레보스", element=Element.FOREST, role=Role.MAGICIAN,
        side="ally",
        stats=StatBlock(atk=690, def_=460, hp=5750, spd=100),
        normal_skill=_normal(f"{sid}_n", "심연의 쌍격",
            [_dmg(TargetType.ENEMY_NEAR, 4.00, hit_count=2)]),
        active_skill=_active(f"{sid}_a", "종결자의 일격",
            [_dmg(TargetType.ENEMY_LOWEST_HP, 5.00),  # 기본 배율 5.00→3.50→2.80→2.50 (4차 너프)
             SkillEffect(logic_type=LogicType.DAMAGE, target_type=TargetType.ENEMY_LOWEST_HP,
                         multiplier=2.40, condition={'target_hp_below': 0.50}),  # 처형 배율 2.00→1.50→1.20
             _stat_eff(TargetType.ENEMY_LOWEST_HP,
                _sb('def_', 0.25, 2, f"{sid}_a", "방어력", is_debuff=True, is_ratio=True))]),
        ultimate_skill=_ult(f"{sid}_u", "심판의 심연",
            [_dmg(TargetType.ALL_ENEMY, 3.40),  # AoE 배율 3.50→2.50→2.00→1.70 (3차 너프)
             _stat_eff(TargetType.ALL_ENEMY,
                _sb('def_', 0.15, 2, f"{sid}_u", "방어력", is_debuff=True, is_ratio=True)),
             _dot_eff(TargetType.ALL_ENEMY,
                _bleed(f"{sid}_u", dot_ratio=0.20, duration=3))],
            sp=4),
        triggers=[
            TriggerData(event=TriggerEvent.ON_KILL, skill_id=f"{sid}_n",
                        once_per_battle=True),  # ★ AoE 처치 시 Normal 추격 1회 (무한체인 방지)
        ],
        tile_pos=(0, 2),
    )


def make_cain() -> CharacterData:
    """c412 카인 - 화/공격형 (2성)
    N: 단일 4.43x (고배율)
    A: 자기버프 (특수 공격력 강화)
    U: 전체 적 1.30x
    """
    sid = "c412"
    return CharacterData(
        id=sid, name="카인", element=Element.FIRE, role=Role.ATTACKER,
        side="ally",
        stats=StatBlock(atk=640, def_=320, hp=3200, spd=80),
        normal_skill=_normal(f"{sid}_n", "암흑 참격",
            [_dmg(TargetType.ENEMY_NEAR, 4.00)]),  # 5.00→4.00 (M10 너프)
        active_skill=_active(f"{sid}_a", "광기의 힘",
            [_stat_eff(TargetType.SELF,
                _sb('atk', 0.30, 2, f"{sid}_a", "공격력", is_ratio=True)),
             _stat_eff(TargetType.SELF,
                _sb('cri_ratio', 0.20, 2, f"{sid}_a", "크리율", is_ratio=False))]),
        ultimate_skill=_ult(f"{sid}_u", "어둠의 폭풍",
            [_dmg(TargetType.ALL_ENEMY, 2.60)],
            sp=6),
        tile_pos=(0, 0),
    )


def make_elizabeth() -> CharacterData:
    """c156 에르제베트 - 암/공격형 (2성)
    N: 단일 4.43x (고배율)
    A: 단일 3.20x + 명중+15(2턴)
    U: 전체 적 0.40x + 독 30%(2턴)
    """
    sid = "c156"
    return CharacterData(
        id=sid, name="에르제베트", element=Element.DARK, role=Role.ATTACKER,
        side="ally",
        stats=StatBlock(atk=640, def_=320, hp=3200, spd=80),
        normal_skill=_normal(f"{sid}_n", "피의 채찍",
            [_dmg(TargetType.ENEMY_NEAR, 7.50, hit_count=2)]),  # ★ 2연타 3.25→3.75 (CC창 킬파워 강화)
        active_skill=_active(f"{sid}_a", "선혈의 창",
            [_dmg(TargetType.ENEMY_NEAR, 8.00),
             _stat_eff(TargetType.SELF,
                _sb('acc', 15.0, 2, f"{sid}_a", "명중", is_ratio=False)),
             _stat_eff(TargetType.SELF,
                _sb('atk', 0.30, 2, f"{sid}_a", "피의 광기", is_ratio=True))]),
        ultimate_skill=_ult(f"{sid}_u", "핏빛 향연",
            [_dmg(TargetType.ALL_ENEMY, 2.00),
             _dot_eff(TargetType.ALL_ENEMY,
                _poison(f"{sid}_u", dot_ratio=0.30, duration=2))],
            sp=6),
        triggers=[
            TriggerData(event=TriggerEvent.ON_KILL, skill_id=f"{sid}_n"),  # ★ 처치 시 Normal 추격 (CC창 킬체인)
        ],
        tile_pos=(0, 1),
    )


def make_duetsha() -> CharacterData:
    """c514 두엣샤 - 암/구속형 (2성)
    N: 단일 2.25x
    A: 단일 0.40x
    U: 행 3.20x
    """
    sid = "c514"
    return CharacterData(
        id=sid, name="두엣샤", element=Element.DARK, role=Role.MAGICIAN,
        side="ally",
        stats=StatBlock(atk=480, def_=320, hp=4000, spd=100),
        normal_skill=_normal(f"{sid}_n", "그림자 베기",
            [_dmg(TargetType.ENEMY_NEAR, 4.50)]),
        active_skill=_active(f"{sid}_a", "이중 참격",
            [_dmg(TargetType.ALL_ENEMY, 2.40),  # ★ 단일→AoE 개편 (전멸폭격 웨이브 기여)
             _stat_eff(TargetType.ALL_ENEMY,
                _sb('def_', 0.10, 1, f"{sid}_a", "파쇄", is_debuff=True, is_ratio=True))]),  # ★ 1턴 DEF 깎기 (후속 AoE 준비)
        ultimate_skill=_ult(f"{sid}_u", "심연의 무도",
            [_dmg(TargetType.ENEMY_NEAR_ROW, 5.00)],
            sp=4),
        tile_pos=(0, 2),
    )


def make_mona_dark() -> CharacterData:
    """c001 모나 - 암/방어형 (2성)"""
    sid = "c001"
    return CharacterData(
        id=sid, name="모나", element=Element.DARK, role=Role.DEFENDER,
        side="ally",
        stats=StatBlock(atk=400, def_=480, hp=4800, spd=110),
        normal_skill=_normal(f"{sid}_n", "암흑 타격",
            [_dmg(TargetType.ENEMY_NEAR, 2.40)]),
        active_skill=_active(f"{sid}_a", "암흑 장벽",
            [_taunt(2),
             _shield(TargetType.SELF, 0.20)]),
        ultimate_skill=_ult(f"{sid}_u", "어둠의 수호",
            [_shield(TargetType.ALL_ALLY, 0.20),
             _stat_eff(TargetType.ALL_ENEMY,
                _sb('atk', 0.20, 2, f"{sid}_u", "어둠 약화", is_debuff=True, is_ratio=True))],
            sp=3),
        tile_pos=(0, 0),
    )


def make_persephone() -> CharacterData:
    """c035 페르세포네 - 암/서포터 (1성) — 보조형"""
    sid = "c035"
    return CharacterData(
        id=sid, name="페르세포네", element=Element.DARK, role=Role.SUPPORTER,
        side="ally",
        stats=StatBlock(atk=300, def_=240, hp=3000, spd=120),
        normal_skill=_normal(f"{sid}_n", "암흑의 가시",
            [_dmg(TargetType.ENEMY_NEAR, 2.40)]),
        active_skill=_active(f"{sid}_a", "명계의 축복",
            [_stat_eff(TargetType.ALL_ALLY,
                _sb('atk', 0.15, 2, f"{sid}_a", "명계의 힘", is_ratio=True)),
             _stat_eff(TargetType.ALL_ALLY,
                _sb('def_', 0.10, 2, f"{sid}_a", "명계의 보호", is_ratio=True))]),
        ultimate_skill=_ult(f"{sid}_u", "명계의 꽃",
            [_stat_eff(TargetType.ALL_ALLY,
                _sb('atk', 0.25, 2, f"{sid}_u", "꽃의 힘", is_ratio=True)),
             _heal_ratio(TargetType.ALL_ALLY, 0.15)],
            sp=4),
        tile_pos=(2, 1),
    )


def make_nevan() -> CharacterData:
    """c048 네반 - 암/회복형 (1성)"""
    sid = "c048"
    return CharacterData(
        id=sid, name="네반", element=Element.DARK, role=Role.HEALER,
        side="ally",
        stats=StatBlock(atk=240, def_=240, hp=2400, spd=90),
        normal_skill=_normal(f"{sid}_n", "어둠의 손길",
            [_dmg(TargetType.ENEMY_NEAR, 2.00)]),
        active_skill=_active(f"{sid}_a", "암흑 치유",
            [_heal_ratio(TargetType.ALLY_LOWEST_HP, 0.65),
             _remove_debuff_eff(TargetType.ALLY_LOWEST_HP),
             _shield(TargetType.ALLY_LOWEST_HP, 0.35)]),  # ★ 힐+정화+배리어 콤보 (철벽요새 시너지)
        ultimate_skill=_ult(f"{sid}_u", "명계의 은혜",
            [_heal_ratio(TargetType.ALL_ALLY, 0.75),
             _shield(TargetType.ALL_ALLY, 0.55)],
            sp=3),
        tile_pos=(2, 2),
    )


def make_medusa() -> CharacterData:
    """c064 메두사 - 암/공격형 (1성)"""
    sid = "c064"
    return CharacterData(
        id=sid, name="메두사", element=Element.DARK, role=Role.ATTACKER,
        side="ally",
        stats=StatBlock(atk=480, def_=240, hp=2400, spd=80),
        normal_skill=_normal(f"{sid}_n", "석화의 눈",
            [_dmg(TargetType.ENEMY_NEAR, 3.60)]),
        active_skill=_active(f"{sid}_a", "독사의 일격",
            [_dmg(TargetType.ENEMY_NEAR, 4.00),
             _cc(CCType.STONE, 1, f"{sid}_a", TargetType.ENEMY_NEAR)]),
        ultimate_skill=_ult(f"{sid}_u", "석화의 시선",
            [_dmg(TargetType.ALL_ENEMY, 3.20),
             _cc(CCType.STONE, 1, f"{sid}_u", TargetType.ALL_ENEMY)],
            sp=6),
        tile_pos=(0, 1),
    )


# ════════════════════════════════════════════════════════════════
# 몬스터 (Enemy side)
# ════════════════════════════════════════════════════════════════

def make_teddy_a() -> CharacterData:
    """봉제인형A - 화/방어형 (적)"""
    sid = "cteddy_a"
    return CharacterData(
        id=sid, name="봉제인형A", element=Element.FIRE, role=Role.DEFENDER,
        side="enemy",
        stats=StatBlock(atk=560, def_=300, hp=5000, spd=110),
        normal_skill=_normal(f"{sid}_n", "봉제 강타",
            [_dmg(TargetType.ENEMY_NEAR, 3.00)]),
        active_skill=_active(f"{sid}_a", "봉제 난타",
            [_dmg(TargetType.ENEMY_RANDOM_3, 2.40)]),
        ultimate_skill=_ult(f"{sid}_u", "봉제 분노",
            [_dmg(TargetType.ALL_ENEMY, 2.00)],
            sp=3),
        tile_pos=(0, 1),
    )


def make_teddy_b() -> CharacterData:
    """봉제인형B - 화/방어형 (적, 탱커)"""
    sid = "cteddy_b"
    return CharacterData(
        id=sid, name="봉제인형B", element=Element.FIRE, role=Role.DEFENDER,
        side="enemy",
        stats=StatBlock(atk=440, def_=400, hp=7000, spd=110),
        normal_skill=_normal(f"{sid}_n", "방어 강타",
            [_dmg(TargetType.ENEMY_NEAR, 2.60)]),
        active_skill=_active(f"{sid}_a", "수비 반격",
            [_dmg(TargetType.ENEMY_RANDOM_3, 2.00)]),
        ultimate_skill=_ult(f"{sid}_u", "방패 격돌",
            [_dmg(TargetType.ENEMY_NEAR_ROW, 2.40)],
            sp=3),
        tile_pos=(0, 0),
    )


def make_teddy_c() -> CharacterData:
    """봉제인형C - 화/방어형 (적, 회복형)"""
    sid = "cteddy_c"
    return CharacterData(
        id=sid, name="봉제인형C", element=Element.FIRE, role=Role.DEFENDER,
        side="enemy",
        stats=StatBlock(atk=360, def_=320, hp=6000, spd=110),
        normal_skill=_normal(f"{sid}_n", "회복 강타",
            [_dmg(TargetType.ENEMY_NEAR, 2.00)]),
        active_skill=_active(f"{sid}_a", "힐링 파티",
            [_dmg(TargetType.ENEMY_RANDOM_3, 2.00)]),
        ultimate_skill=_ult(f"{sid}_u", "대회복",
            [_heal_ratio(TargetType.ALL_ALLY, 0.20)],
            sp=3),
        tile_pos=(1, 1),
    )


def make_teddy_d() -> CharacterData:
    """봉제인형D - 화/방어형 (적, 속도감소형)"""
    sid = "cteddy_d"
    return CharacterData(
        id=sid, name="봉제인형D", element=Element.FIRE, role=Role.DEFENDER,
        side="enemy",
        stats=StatBlock(atk=500, def_=330, hp=5500, spd=110),
        normal_skill=_normal(f"{sid}_n", "속박",
            [_dmg(TargetType.ENEMY_NEAR, 2.00)]),
        active_skill=_active(f"{sid}_a", "속도 제한",
            [_dmg(TargetType.ENEMY_RANDOM_3, 3.00),
             _stat_eff(TargetType.ALL_ENEMY,
                _sb('spd', 20.0, 2, f"{sid}_a", "속도", is_debuff=True, is_ratio=False))]),
        ultimate_skill=_ult(f"{sid}_u", "속박의 사슬",
            [_stat_eff(TargetType.ALL_ENEMY,
                _sb('spd', 20.0, 3, f"{sid}_u", "속도", is_debuff=True, is_ratio=False))],
            sp=3),
        tile_pos=(1, 0),
    )


def make_teddy_e() -> CharacterData:
    """봉제인형E - 화/힐러 (적)"""
    sid = "cteddy_e"
    return CharacterData(
        id=sid, name="봉제인형E", element=Element.FIRE, role=Role.HEALER,
        side="enemy",
        stats=StatBlock(atk=400, def_=310, hp=5800, spd=90),
        normal_skill=_normal(f"{sid}_n", "치유 강타",
            [_dmg(TargetType.ENEMY_NEAR, 2.00)]),
        active_skill=_active(f"{sid}_a", "집단 치료",
            [_dmg(TargetType.ENEMY_RANDOM_3, 2.40),
             _heal_ratio(TargetType.ALL_ALLY, 0.15)]),
        ultimate_skill=_ult(f"{sid}_u", "대치유",
            [_heal_ratio(TargetType.ALL_ALLY, 0.30)],
            sp=3),
        tile_pos=(2, 1),
    )


# ════════════════════════════════════════════════════════════════
# ─── 파티 빌더 ─────────────────────────────────────────────────
# ════════════════════════════════════════════════════════════════

def get_party_fire():
    """화속성 파티 (5명): 모건, 지바, 카라라트리, 라가라자, 살마키스"""
    return [make_morgan(), make_jiva(), make_kararatri(), make_ragaraja(), make_salmakis()]


def get_party_water():
    """수속성 파티 (5명): 이브, 상아, 티스베, 바리, 도계화"""
    return [make_eve(), make_sangah(), make_thisbe(), make_bari(), make_dogyehwa()]


def get_party_forest():
    """목속성 파티 (5명): 바토리, 판, 미리암, 아우로라, 브라우니"""
    return [make_batory(), make_pan(), make_miriam(), make_aurora(), make_brownie()]


def get_party_light():
    """광속성 파티 (5명): 아슈토레스, 시트리, 티와즈, 티타니아, 모나"""
    return [make_ashtoreth(), make_sitri(), make_tiwaz(), make_titania(), make_mona()]


def get_party_dark():
    """암속성 파티 (5명): 쿠바바, 아르테미스, 아누비스, 프레이, 유나"""
    return [make_kubaba(), make_artemis(), make_anubis(), make_frey(), make_yuna()]


def get_party_mixed():
    """혼합 파티 (5명): 각 속성 대표 1명"""
    return [make_morgan(), make_eve(), make_batory(), make_ashtoreth(), make_kubaba()]


def get_enemies_3():
    """기본 적군 3마리: A/B/C형 봉제인형"""
    return [make_teddy_a(), make_teddy_b(), make_teddy_c()]


def get_enemies_5():
    """5마리 적군: A/B/C/D/E형 봉제인형"""
    return [make_teddy_a(), make_teddy_b(), make_teddy_c(), make_teddy_d(), make_teddy_e()]


# ════════════════════════════════════════════════════════════════
# ─── 메타 조합 (8개) ────────────────────────────────────────────
# ════════════════════════════════════════════════════════════════

def get_meta_burst():
    """1. 극딜 버스트: 루미나, 이브, 쿠바바, 엘리시온, 아우로라
    루미나 OP 버프(ATK+30%, CRI_DMG+0.50) → 이브(ATK545)+쿠바바 극딜 → 힐+서포트.
    """
    return [make_c600(), make_eve(), make_kubaba(), make_elysion(), make_aurora()]


def get_meta_op_duo():
    """2. OP 듀오: 루미나, 에레보스, 시트리, 아르테미스, 다누
    OP 2명(루미나 SPD125 버프 + 에레보스 ATK530) + 시트리 버프 중첩 + 아르테미스 CRI48% 보조딜 + 다누 힐.
    """
    return [make_c600(), make_c601(), make_sitri(), make_artemis(), make_danu()]


def get_meta_fire_burn():
    """3. 화상 시너지: 카라라트리, 다비, 라가라자, 데레사, 지바
    화속 단일, 화상 스택 누적 → 스택 비례 추가 데미지. 지바 힐로 지구전.
    """
    return [make_kararatri(), make_dabi(), make_ragaraja(), make_deresa(), make_jiva()]


def get_meta_cc_control():
    """4. CC 컨트롤: 오네이로이, 판, 미리암, 그릴라, 브라우니
    CC(기절/수면/공포) 체인으로 적 행동 봉쇄. 미리암 ATK478 피니시.
    """
    return [make_oneiroi(), make_pan(), make_miriam(), make_grilla(), make_brownie()]


def get_meta_water_tempo():
    """5. 수속 템포: 이브, 상아, 티스베, 도계화, 엘리시온
    수속 단일 + 고SPD 서포터 3명(상아·티스베·엘리시온) → SP 빠른 충전 → 이브 Ult 선제.
    """
    return [make_eve(), make_sangah(), make_thisbe(), make_dogyehwa(), make_elysion()]


def get_meta_dark_assault():
    """6. 암속 강공: 아르테미스, 쿠바바, 아누비스, 유나, 프레이
    암속 순수 — ATK 3명(아르테미스 CRI48%, 쿠바바, 아누비스) + 유나 서포트 + 프레이 탱킹.
    광속성 상대 속성 우위.
    """
    return [make_artemis(), make_kubaba(), make_anubis(), make_yuna(), make_frey()]


def get_meta_light_holy():
    """7. 광속 순수: 아슈토레스, 시트리, 티와즈, 티타니아, 모나
    광속 단일 — 아슈토레스(ATK465 CRI27% PEN25%) 에이스 + 3 서포터 버프 + 모나 힐.
    암속성 상대 속성 우위.
    """
    return [make_ashtoreth(), make_sitri(), make_tiwaz(), make_titania(), make_mona()]


def get_meta_forest_rush():
    """8. 목속 돌격: 에레보스, 미리암, 바토리, 아우로라, 메티스
    목속 순수 — 에레보스(ATK530 OP) + 미리암(ATK478) 쌍두 딜 + 바토리 CRI18% 보조딜.
    아우로라·메티스 서포트. 수속성 상대 속성 우위.
    """
    return [make_c601(), make_miriam(), make_batory(), make_aurora(), make_metis()]
