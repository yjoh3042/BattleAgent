"""데미지 계산 모듈
공식: Final = floor(Base × SkillMult × ElemMult × CritMult)
Base = Atk × (1 - Def / (Atk + Def))
"""
from __future__ import annotations
import math
import random
from typing import Optional, TYPE_CHECKING

from battle.enums import Element

if TYPE_CHECKING:
    from battle.battle_unit import BattleUnit


# ─── 속성 상성 테이블 ─────────────────────────────────────────────
# (공격 속성, 방어 속성) → 배율
ELEMENT_TABLE: dict[tuple, float] = {
    (Element.FIRE,   Element.FOREST): 1.2,
    (Element.FOREST, Element.WATER):  1.2,
    (Element.WATER,  Element.FIRE):   1.2,
    (Element.LIGHT,  Element.DARK):   1.2,
    (Element.DARK,   Element.LIGHT):  1.2,
}


# ─── 기본 데미지 ──────────────────────────────────────────────────
def calc_base_damage(atk: float, def_: float, penetration: float = 0.0) -> float:
    """
    비율 기반 방어 경감 공식.
    effective_def = max(0, Def - Penetration)
    Base = Atk × (1 - effective_def / (Atk + effective_def))
    """
    effective_def = max(0.0, def_ - penetration)
    if atk + effective_def <= 0:
        return 0.0
    return atk * (1.0 - effective_def / (atk + effective_def))


# ─── 속성 배율 ────────────────────────────────────────────────────
def get_element_mult(atk_elem: Element, def_elem: Element) -> float:
    """속성 상성 배율. 우위 속성 → 1.2, 그 외 → 1.0"""
    return ELEMENT_TABLE.get((atk_elem, def_elem), 1.0)


# ─── 회피 판정 ───────────────────────────────────────────────────
def roll_dodge(dodge: float, acc: float) -> bool:
    """회피 판정. 회피 성공 = Random(0~1) < (dodge - (1 - acc))"""
    effective = max(0.0, dodge - (1.0 - acc))
    if effective <= 0:
        return False
    return random.random() < effective


# ─── 크리티컬 ─────────────────────────────────────────────────────
def roll_crit(cri_ratio: float, cri_resist: float = 0.0) -> bool:
    """크리 판정. 유효 크리율 = max(0, cri_ratio - cri_resist)"""
    effective = max(0.0, cri_ratio - cri_resist)
    return random.random() < effective


def get_crit_mult(cri_dmg_ratio: float, is_crit: bool) -> float:
    """크리 배율 반환. 크리 아니면 1.0"""
    return cri_dmg_ratio if is_crit else 1.0


# ─── 최종 데미지 ──────────────────────────────────────────────────
def calc_final_damage(
    base: float,
    skill_mult: float,
    elem_mult: float,
    crit_mult: float,
    burn_bonus: float = 1.0,   # 화상 스택 보너스 배율
) -> int:
    """
    최종 데미지 = floor(Base × SkillMult × ElemMult × CritMult × BurnBonus)
    """
    return max(0, math.floor(base * skill_mult * elem_mult * crit_mult * burn_bonus))


# ─── 힐 계산 ──────────────────────────────────────────────────────
def calc_heal(
    healer_atk: float,
    target_max_hp: float,
    skill_mult: float = 1.0,
    hp_ratio: Optional[float] = None,
) -> float:
    """
    힐 계산.
    - hp_ratio 지정 시: target_max_hp × hp_ratio
    - 그 외: healer_atk × skill_mult (공격력 기반 힐)
    """
    if hp_ratio is not None:
        return target_max_hp * hp_ratio
    return healer_atk * skill_mult


# ─── DoT 계산 ─────────────────────────────────────────────────────
def calc_dot_damage(
    target_max_hp: float,
    dot_ratio: float,
    stack_count: int = 1,
) -> int:
    """
    DoT (화상, 독 등) 피해 계산.
    damage = floor(target_max_hp × dot_ratio × stack_count)
    """
    return max(1, math.floor(target_max_hp * dot_ratio * stack_count))


# ─── 화상 보너스 배율 ─────────────────────────────────────────────
def get_burn_bonus_mult(burn_stack: int, bonus_per_stack: float = 0.5) -> float:
    """
    카인(화상 딜러) 계열: 화상 스택당 추가 대미지.
    예: 1스택 → 150%, 2스택 → 200% (bonus_per_stack=0.5 기준)
    """
    if burn_stack <= 0:
        return 1.0
    return 1.0 + bonus_per_stack * burn_stack


# ─── 전체 데미지 파이프라인 ───────────────────────────────────────
def compute_damage(
    attacker: "BattleUnit",
    defender: "BattleUnit",
    skill_mult: float,
    burn_bonus_per_stack: float = 0.0,
) -> tuple[int, bool, bool]:
    """
    공격자 → 방어자 데미지 계산 전체 파이프라인.
    반환: (final_damage, is_crit, is_dodged)
    """
    # 회피 판정
    if roll_dodge(defender.dodge, attacker.acc):
        return 0, False, True

    base = calc_base_damage(attacker.atk, defender.def_, attacker.penetration)
    elem_mult = get_element_mult(attacker.data.element, defender.data.element)
    is_crit = roll_crit(attacker.cri_ratio, defender.cri_resist)
    crit_mult = get_crit_mult(attacker.cri_dmg_ratio, is_crit)

    burn_stack = defender.get_tag_count("burn") if burn_bonus_per_stack > 0 else 0
    burn_bonus = get_burn_bonus_mult(burn_stack, burn_bonus_per_stack) if burn_stack > 0 else 1.0

    final = calc_final_damage(base, skill_mult, elem_mult, crit_mult, burn_bonus)
    return final, is_crit, False
