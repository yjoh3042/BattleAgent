"""밸런스 룰 상수 - 역할(Role)별 기본 스탯 가이드라인

새 캐릭터를 설계할 때 아래 수치를 기준값으로 사용한다.
기존 캐릭터는 밸런스 패치로 개별 조정된 값을 우선한다.
"""
from __future__ import annotations

from battle.enums import Role

# ────────────────────────────────────────────────────────────
# 전투 기본 상수 (Base 시트)
# ────────────────────────────────────────────────────────────
BATTLE_LENGTH: int = 300          # 배틀 길이 (턴 공식 분자)
MAX_TURN_TIME: int = 10           # 배틀 턴 최대 시간
# Turn Formula = BATTLE_LENGTH / Spd

# ────────────────────────────────────────────────────────────
# 속도 룰: 역할별 기본 SPD
# ────────────────────────────────────────────────────────────
ROLE_BASE_SPD: dict[Role, int] = {
    Role.ATTACKER:  80,
    Role.HEALER:    90,
    Role.MAGICIAN: 100,
    Role.DEFENDER: 110,
    Role.SUPPORTER: 120,
}

# ────────────────────────────────────────────────────────────
# SP 룰: 역할별 얼티밋 SP 비용
# ────────────────────────────────────────────────────────────
ROLE_BASE_SP: dict[Role, int] = {
    Role.ATTACKER:  6,
    Role.HEALER:    3,
    Role.MAGICIAN:  4,
    Role.DEFENDER:  3,
    Role.SUPPORTER: 4,
}

# ────────────────────────────────────────────────────────────
# 얼티밋 쿨타임 룰: 전 직업 공통 4턴 (자기 턴 기준 감소)
# 얼티밋 사용 후 자신의 턴이 4번 돌아와야 재사용 가능
# ────────────────────────────────────────────────────────────
ULT_COOLDOWN: int = 4  # 전 직업 공통 얼티밋 쿨타임

ROLE_ULT_COOLDOWN: dict[Role, int] = {
    Role.ATTACKER:  ULT_COOLDOWN,  # 4턴
    Role.HEALER:    ULT_COOLDOWN,  # 4턴
    Role.MAGICIAN:  ULT_COOLDOWN,  # 4턴
    Role.DEFENDER:  ULT_COOLDOWN,  # 4턴
    Role.SUPPORTER: ULT_COOLDOWN,  # 4턴
}


# ────────────────────────────────────────────────────────────
# 스탯 기본값 룰: 역할별 ATK / DEF / HP 평균(기본) 값
# ────────────────────────────────────────────────────────────

ROLE_BASE_ATK: dict[Role, int] = {
    Role.ATTACKER:  420,
    Role.HEALER:    168,
    Role.MAGICIAN:  341,
    Role.DEFENDER:  252,
    Role.SUPPORTER: 198,
}

ROLE_BASE_DEF: dict[Role, int] = {
    Role.ATTACKER:  120,
    Role.HEALER:    151,
    Role.MAGICIAN:  108,
    Role.DEFENDER:  240,
    Role.SUPPORTER: 142,
}

ROLE_BASE_HP: dict[Role, int] = {
    Role.ATTACKER:  5100,
    Role.HEALER:    6475,
    Role.MAGICIAN:  4743,
    Role.DEFENDER:  8650,
    Role.SUPPORTER: 5909,
}


# ────────────────────────────────────────────────────────────
# 헬퍼 함수
# ────────────────────────────────────────────────────────────

def default_spd(role: Role) -> int:
    """역할에 해당하는 기본 SPD 반환."""
    return ROLE_BASE_SPD[role]


def default_sp(role: Role) -> int:
    """역할에 해당하는 기본 SP 비용 반환."""
    return ROLE_BASE_SP[role]


def default_ult_cooldown(role: Role) -> int:
    """역할에 해당하는 얼티밋 쿨타임 반환 (전 직업 4턴)."""
    return ROLE_ULT_COOLDOWN[role]


def default_atk(role: Role) -> int:
    """역할에 해당하는 기본 ATK 반환."""
    return ROLE_BASE_ATK[role]


def default_def(role: Role) -> int:
    """역할에 해당하는 기본 DEF 반환."""
    return ROLE_BASE_DEF[role]


def default_hp(role: Role) -> int:
    """역할에 해당하는 기본 HP 반환."""
    return ROLE_BASE_HP[role]
