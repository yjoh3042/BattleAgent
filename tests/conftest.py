"""공통 테스트 fixture"""
import sys
import os

# src/ 디렉토리를 path에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import pytest
from battle.enums import Element, Role, SkillType, LogicType, TargetType
from battle.models import StatBlock, SkillData, SkillEffect, CharacterData, BuffData
from battle.battle_unit import BattleUnit


@pytest.fixture
def make_simple_unit():
    """간단한 테스트용 유닛 팩토리"""
    _counter = [0]

    def _factory(
        name="테스트유닛",
        side="ally",
        atk=300, def_=150, hp=5000, spd=100,
        cri_ratio=0.15, cri_dmg_ratio=1.5,
        element=Element.FIRE, role=Role.ATTACKER,
        penetration=0.0, acc=1.0, dodge=0.0,
    ) -> BattleUnit:
        _counter[0] += 1
        uid = f"test_{name}_{_counter[0]}"
        stats = StatBlock(
            atk=atk, def_=def_, hp=hp, spd=spd,
            cri_ratio=cri_ratio, cri_dmg_ratio=cri_dmg_ratio,
            penetration=penetration, acc=acc, dodge=dodge,
        )
        normal = SkillData(
            id=f"{uid}_normal", name="기본공격", skill_type=SkillType.NORMAL,
            effects=[SkillEffect(logic_type=LogicType.DAMAGE, target_type=TargetType.ENEMY_LOWEST_HP, multiplier=1.0)],
        )
        active = SkillData(
            id=f"{uid}_active", name="액티브", skill_type=SkillType.ACTIVE,
            effects=[SkillEffect(logic_type=LogicType.DAMAGE, target_type=TargetType.ALL_ENEMY, multiplier=1.5)],
            cooldown_turns=2,
        )
        ultimate = SkillData(
            id=f"{uid}_ult", name="얼티밋", skill_type=SkillType.ULTIMATE,
            effects=[SkillEffect(logic_type=LogicType.DAMAGE, target_type=TargetType.ALL_ENEMY, multiplier=2.0)],
            sp_cost=5,
        )
        char = CharacterData(
            id=uid, name=name, element=element, role=role, side=side,
            stats=stats, normal_skill=normal, active_skill=active, ultimate_skill=ultimate,
        )
        return BattleUnit(char)

    return _factory
