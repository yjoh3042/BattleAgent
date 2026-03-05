"""불변 데이터 모델 정의 - 캐릭터, 스킬, 버프의 기획 데이터"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from battle.enums import Element, Role, SkillType, LogicType, CCType, TargetType, StatType, TriggerEvent


@dataclass
class StatBlock:
    """캐릭터 기본 스탯"""
    atk: float
    def_: float
    hp: float
    spd: float
    cri_ratio: float = 0.15        # 크리 확률 (0.0 ~ 1.0)
    cri_dmg_ratio: float = 1.5     # 크리 배율 (기본 1.5 = 150%)
    cri_resist: float = 0.0        # 크리 저항
    acc: float = 1.0               # 명중률
    dodge: float = 0.0             # 회피율
    penetration: float = 0.0      # 관통 (방어력 직접 감소)


@dataclass
class TriggerData:
    """트리거 조건 및 효과 정의"""
    event: TriggerEvent
    condition: Optional[Dict[str, Any]] = None   # {'hp_threshold': 0.5, 'tag': 'burn', 'count': 1, ...}
    skill_id: Optional[str] = None               # 발동할 스킬 ID
    buff_id: Optional[str] = None                # 부여할 버프 ID
    once_per_battle: bool = False                # 전투당 1회 제한


@dataclass
class BuffData:
    """버프/디버프 데이터 정의 (불변)"""
    id: str
    name: str
    source_skill_id: str           # 어느 스킬에서 부여됐는지
    logic_type: LogicType
    stat: Optional[str] = None     # STAT_CHANGE 시 대상 스탯 ('atk', 'spd', 'def_', ...)
    value: float = 0.0             # 변경량 (절댓값 or 비율)
    is_ratio: bool = False         # True면 비율(%), False면 절댓값
    duration: int = 2              # 지속 턴 수
    cc_type: Optional[CCType] = None   # CC 타입
    dot_type: Optional[str] = None     # DoT 종류 ('burn', 'poison', ...)
    is_debuff: bool = False
    max_stacks: int = 1            # 최대 중첩 수 (DoT 계열)
    tags: List[str] = field(default_factory=list)


@dataclass
class SkillEffect:
    """스킬 하나의 효과 단위 (하나의 스킬은 여러 Effect를 가질 수 있음)"""
    logic_type: LogicType
    target_type: TargetType
    value: float = 0.0              # 기본값 (힐 비율, SP 증가량 등)
    multiplier: float = 1.0         # 데미지 배율
    buff_data: Optional[BuffData] = None   # STAT_CHANGE, DOT, CC 등 부여할 버프
    hit_count: int = 1              # 타격 횟수 (다단 히트)
    condition: Optional[Dict[str, Any]] = None  # 발동 조건


@dataclass
class SkillData:
    """스킬 데이터 정의 (불변)"""
    id: str
    name: str
    skill_type: SkillType
    effects: List[SkillEffect]
    sp_cost: int = 0               # Ultimate 전용 SP 소모량
    cooldown_turns: int = 0        # Active 스킬 쿨타임 (기본 2)
    description: str = ""


@dataclass
class CharacterData:
    """캐릭터 기획 데이터 (불변)"""
    id: str
    name: str
    element: Element
    role: Role
    side: str                       # 'ally' or 'enemy'
    stats: StatBlock
    normal_skill: SkillData
    active_skill: SkillData
    ultimate_skill: SkillData
    sp_cost: int = 5               # 얼티밋 SP 비용 (4~6)
    triggers: List[TriggerData] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)   # 기본 태그 (e.g. 'burn_synergy')
