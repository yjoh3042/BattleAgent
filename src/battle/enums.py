"""열거형 정의 모듈 - 전투 시스템의 모든 Enum 타입"""
from enum import Enum, auto


class Element(Enum):
    """속성 (원소)"""
    FIRE = "fire"
    WATER = "water"
    FOREST = "forest"
    LIGHT = "light"
    DARK = "dark"
    NONE = "none"


class Role(Enum):
    """캐릭터 역할"""
    ATTACKER = "attacker"
    DEFENDER = "defender"
    MAGICIAN = "magician"
    SUPPORTER = "supporter"
    HEALER = "healer"


class SkillType(Enum):
    """스킬 종류"""
    NORMAL = "normal"      # 기본 공격, 쿨타임 없음
    ACTIVE = "active"      # 액티브 스킬, 사용 후 2턴 쿨타임
    ULTIMATE = "ultimate"  # 얼티밋, SP 소모 + 엑스트라 턴


class LogicType(Enum):
    """스킬/버프 로직 타입"""
    DAMAGE = "damage"                          # 데미지
    HEAL = "heal"                              # 힐 (최대 HP 비율 또는 고정값)
    HEAL_HP_RATIO = "heal_hp_ratio"            # 최대 HP % 힐
    STAT_CHANGE = "stat_change"                # 스탯 버프/디버프
    DOT = "dot"                                # 지속 피해 (화상 등)
    DOT_HEAL_HP_RATIO = "dot_heal_hp_ratio"    # 지속 회복 (최대 HP %)
    BARRIER = "barrier"                        # 보호막
    TAUNT = "taunt"                            # 도발
    REVIVE = "revive"                          # 부활
    SP_INCREASE = "sp_increase"                # SP 증가
    CC = "cc"                                  # 상태이상 부여
    REMOVE_BUFF = "remove_buff"                # 버프 제거
    REMOVE_DEBUFF = "remove_debuff"            # 디버프 제거
    COUNTER = "counter"                        # 반격 준비 상태
    ABSORB = "absorb"                          # 피해 흡수


class CCType(Enum):
    """상태이상 타입"""
    # Hard CC (행동 불가)
    STUN = "stun"
    SLEEP = "sleep"
    FREEZE = "freeze"
    STONE = "stone"
    ABNORMAL_SKILL = "abnormal_skill"
    # Soft CC (확률적)
    ELECTRIC_SHOCK = "electric_shock"   # 30% 확률로 행동 불가
    PANIC = "panic"                     # 30% 확률로 행동 불가
    # 디버프성
    POISON = "poison"
    BURN = "burn"
    BLIND = "blind"
    SILENCE = "silence"


class TargetType(Enum):
    """타겟 선택 방식"""
    SELF = "self"
    ALLY_LOWEST_HP = "ally_lowest_hp"
    ALLY_HIGHEST_ATK = "ally_highest_atk"
    ALL_ALLY = "all_ally"
    ENEMY_LOWEST_HP = "enemy_lowest_hp"
    ENEMY_HIGHEST_HP = "enemy_highest_hp"
    ENEMY_HIGHEST_SPD = "enemy_highest_spd"
    ENEMY_RANDOM = "enemy_random"
    ALL_ENEMY = "all_enemy"
    ENEMY_RANDOM_2 = "enemy_random_2"   # 랜덤 최대 2명
    ENEMY_RANDOM_3 = "enemy_random_3"   # 랜덤 최대 3명
    ALLY_DEAD_RANDOM = "ally_dead_random"  # 사망한 아군 1명 (부활용)
    ALLY_LOWEST_HP_2 = "ally_lowest_hp_2"  # 체력 낮은 아군 2명
    ALLY_ROLE_ATTACKER = "ally_role_attacker"  # 공격형 아군 전체


class TriggerEvent(Enum):
    """트리거 발동 이벤트"""
    ON_BATTLE_START = "on_battle_start"
    ON_ROUND_START = "on_round_start"
    ON_TURN_START = "on_turn_start"
    ON_TURN_END = "on_turn_end"
    ON_HIT = "on_hit"           # 피격 시
    ON_ATTACK = "on_attack"     # 공격 시
    ON_KILL = "on_kill"
    ON_DEATH = "on_death"
    ON_HP_THRESHOLD = "on_hp_threshold"   # HP가 특정 % 이하
    ON_BURN_APPLIED = "on_burn_applied"   # 화상 부여 시
    ON_STATUS_APPLIED = "on_status_applied"


class Side(Enum):
    """진영"""
    ALLY = "ally"
    ENEMY = "enemy"


class BattleResult(Enum):
    """전투 결과"""
    ALLY_WIN = "ally_win"
    ENEMY_WIN = "enemy_win"
    TIME_OVER = "time_over"
    IN_PROGRESS = "in_progress"


class StatType(Enum):
    """버프/디버프 대상 스탯"""
    ATK = "atk"
    DEF = "def_"
    HP = "hp"
    SPD = "spd"
    CRI_RATIO = "cri_ratio"
    CRI_DMG_RATIO = "cri_dmg_ratio"
    CRI_RESIST = "cri_resist"
    BURN_STACK_BONUS = "burn_stack_bonus"   # 화상 스택당 추가 대미지
