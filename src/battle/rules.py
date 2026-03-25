"""밸런스 룰 상수 — 스탯 고정 + 스킬 밸런싱 프레임워크

═══════════════════════════════════════════════════════════════
밸런싱 정책 (v2.0)
═══════════════════════════════════════════════════════════════
1. 스탯(ATK/DEF/HP)은 역할×등급으로 **완전 고정** (ROLE_STAT_STANDARD).
   → 개별 캐릭터의 스탯 조정은 금지. 밸런스 패치 대상이 아님.
   → SPD, SP 비용도 역할 고정.

2. 캐릭터 개성화는 **스킬**로만 수행:
   → 액티브/얼티밋의 배율(multiplier), 타겟(targeting), 부가효과(effects)
   → 역할별 스킬 템플릿(ROLE_SKILL_TEMPLATE)을 기준으로 ±조정
   → 배율 범위(SKILL_MULTIPLIER_RANGE)를 벗어나지 않도록 관리

3. 밸런싱 축 우선순위: 스킬 배율 > 타겟 범위 > 부가효과 > (스탯 금지)
═══════════════════════════════════════════════════════════════
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional

from battle.enums import Role

# ────────────────────────────────────────────────────────────
# 전투 기본 상수 (Base 시트)
# ────────────────────────────────────────────────────────────
BATTLE_LENGTH: int = 300          # 배틀 길이 (턴 공식 분자)
MAX_TURN_TIME: int = 10           # 배틀 턴 최대 시간
MAX_TURNS: int = 200              # 최대 턴 수
MAX_TIME: float = 300.0           # 최대 전투 시간
# Turn Formula = BATTLE_LENGTH / Spd

# ────────────────────────────────────────────────────────────
# 덱 타입 & 타임오버 룰
# ────────────────────────────────────────────────────────────
# 전투는 두 가지 덱 타입으로 구분된다:
#
# ┌──────────┬────────────────────────────────────────────┐
# │ 덱 타입   │ 타임오버 시 결과                             │
# ├──────────┼────────────────────────────────────────────┤
# │ 공격덱    │ 패배 (적 전멸 실패 = 공격 목표 미달성)       │
# │ (OFFENSE) │ → 제한 시간 내 적을 처치해야 승리            │
# │          │ → 공격력 확보가 편성의 필수 조건              │
# ├──────────┼────────────────────────────────────────────┤
# │ 방어덱    │ 승리 (생존 성공 = 방어 목표 달성)            │
# │ (DEFENSE) │ → 제한 시간 동안 살아남으면 승리             │
# │          │ → 생존력 확보가 편성의 필수 조건              │
# └──────────┴────────────────────────────────────────────┘
#
# 기본값: OFFENSE (공격덱) — 기존 동작과 동일.
# MAX_TURNS(200턴) 또는 MAX_TIME(300.0) 초과 시 덱 타입에 따라 판정.
DEFAULT_DECK_TYPE: str = "offense"  # enums.DeckType.OFFENSE

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
# 등급별 스탯 스케일링 룰
# ────────────────────────────────────────────────────────────
# 등급별 스케일링: 3성 = 100% (기준), 2성 = 75%, 1성 = 50%, 3.5성 = 115%
# ATK, DEF, HP에 적용. SPD, SP는 역할 고정값이므로 스케일링 미적용.
# → 3성 캐릭터가 압도적 성능, 1성은 절반 수준
# → 3.5성은 프리미엄 등급으로 3성 대비 15% 상향
# → 편성 시 등급 조합이 전략적 선택 요소가 됨
GRADE_STAT_SCALE: dict[float, float] = {
    3.5: 1.15,  # 3.5성: 115% (프리미엄)
    3:   1.00,  # 3성: 풀 스탯
    2:   0.75,  # 2성: 75%
    1:   0.50,  # 1성: 50%
}


# ────────────────────────────────────────────────────────────
# 역할별 등급 기준 스탯표 (스탯 규약.xlsx 기준)
# ────────────────────────────────────────────────────────────
# 개별 캐릭터는 역할 기본값에서 ±조정된 고유 스탯을 가지며,
# 등급 스케일링(GRADE_STAT_SCALE)은 해당 캐릭터의 3성 스탯에 적용한다.
#
# 아래 표는 설계 참조용 표준 기본값 (스탯 규약.xlsx 원본).
ROLE_STAT_STANDARD: dict[Role, dict[str, dict[float, int]]] = {
    Role.ATTACKER: {
        "hp":  {1: 2400, 2: 3200, 3: 4000, 3.5: 4600},
        "atk": {1: 240,  2: 320,  3: 400,  3.5: 460},
        "def": {1: 120,  2: 160,  3: 200,  3.5: 230},
    },
    Role.DEFENDER: {
        "hp":  {1: 3600, 2: 4800, 3: 6000, 3.5: 6900},
        "atk": {1: 150,  2: 200,  3: 250,  3.5: 287},
        "def": {1: 180,  2: 240,  3: 300,  3.5: 345},
    },
    Role.MAGICIAN: {
        "hp":  {1: 3000, 2: 4000, 3: 5000, 3.5: 5750},
        "atk": {1: 180,  2: 240,  3: 300,  3.5: 345},
        "def": {1: 120,  2: 160,  3: 200,  3.5: 230},
    },
    Role.SUPPORTER: {
        "hp":  {1: 3000, 2: 4000, 3: 5000, 3.5: 5750},
        "atk": {1: 150,  2: 200,  3: 250,  3.5: 287},
        "def": {1: 120,  2: 160,  3: 200,  3.5: 230},
    },
    Role.HEALER: {
        "hp":  {1: 2400, 2: 3200, 3: 4000, 3.5: 4600},
        "atk": {1: 120,  2: 160,  3: 200,  3.5: 230},
        "def": {1: 120,  2: 160,  3: 200,  3.5: 230},
    },
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


def grade_scale(grade: float) -> float:
    """등급에 해당하는 스탯 스케일링 비율 반환 (3성=1.0, 3.5성=1.15)."""
    return GRADE_STAT_SCALE.get(grade, 1.0)


def scale_stat(base_value: int, grade: float) -> int:
    """3성 기준 스탯을 주어진 등급으로 스케일링. (올림)"""
    return math.ceil(base_value * grade_scale(grade))


def standard_stat(role: Role, stat: str, grade: float) -> int:
    """역할/등급에 대한 표준 기준값 반환 (스탯 규약.xlsx 기준)."""
    return ROLE_STAT_STANDARD[role][stat][grade]


# ════════════════════════════════════════════════════════════════
# 스킬 밸런싱 프레임워크 (v2.0)
# ════════════════════════════════════════════════════════════════
# 스탯이 역할×등급으로 고정된 이후, 캐릭터 개성화의 유일한 축.
# 아래 템플릿과 범위를 기준으로 개별 캐릭터 스킬을 설계한다.


# ────────────────────────────────────────────────────────────
# 스킬 배율 범위: 역할별 허용 배율 (min, max)
# ────────────────────────────────────────────────────────────
# 개별 캐릭터의 스킬 배율은 이 범위 안에서만 조정한다.
# 범위를 벗어나면 밸런스 검증에서 경고가 발생한다.

@dataclass(frozen=True)
class MultRange:
    """스킬 배율 허용 범위."""
    min: float
    max: float


SKILL_MULTIPLIER_RANGE: dict[Role, dict[str, MultRange]] = {
    # ── 딜러: 높은 단일 타겟 배율, 궁극기 최대 폭딜 ──
    Role.ATTACKER: {
        "normal":   MultRange(2.00, 5.00),   # 기본공격: 안정적 딜
        "active":   MultRange(2.40, 5.60),   # 액티브: 메인 딜 스킬
        "ultimate": MultRange(4.00, 8.00),   # 궁극기: 최대 단일 폭딜
    },
    # ── 마법사: AoE 특화, 개별 배율은 낮지만 총합 높음 ──
    Role.MAGICIAN: {
        "normal":   MultRange(1.60, 4.40),   # 기본: 단일 or 소범위
        "active":   MultRange(0.80, 3.60),   # 액티브: AoE 주력
        "ultimate": MultRange(1.60, 5.00),   # 궁극기: AoE 광역
    },
    # ── 탱커: 낮은 배율, 자힐/도발에 가치 집중 ──
    Role.DEFENDER: {
        "normal":   MultRange(0.60, 2.00),
        "active":   MultRange(0.40, 1.60),   # AoE + 자힐/도발
        "ultimate": MultRange(0.00, 1.00),   # 데미지 미미, 전체힐/보호막
    },
    # ── 힐러: 힐 배율(ATK×계수), 궁극기는 %HP 힐 ──
    Role.HEALER: {
        "normal":   MultRange(0.40, 1.60),   # 미미한 공격
        "active":   MultRange(1.60, 4.00),   # 힐 계수 (ATK×value×0.40)
        "ultimate": MultRange(0.40, 0.80),   # %maxHP 전체힐 비율
    },
    # ── 서포터: 중간 배율 + 버프 부여가 핵심 ──
    Role.SUPPORTER: {
        "normal":   MultRange(0.80, 2.40),
        "active":   MultRange(1.00, 3.00),   # 데미지 + 버프
        "ultimate": MultRange(1.20, 3.60),   # 데미지 + 강화 버프
    },
}


# ────────────────────────────────────────────────────────────
# 역할별 스킬 템플릿 (기본값)
# ────────────────────────────────────────────────────────────
# 새 캐릭터 설계 시 이 템플릿에서 시작하여 개성을 부여한다.
# 각 필드는 스킬의 "기준점"이며, 실제 캐릭터는 여기서 변형.
#
# 밸런싱 조정 축 (우선순위 순):
#   1. multiplier  — 스킬 배율 (데미지/힐 강도)
#   2. target      — 타겟 범위 (단일↔AoE↔범위)
#   3. effects     — 부가효과 (버프/디버프/DoT/CC/쉴드 등)
#   4. hit_count   — 다단 히트 수
#   5. cooldown    — 액티브 쿨타임 (기본 3턴)

@dataclass(frozen=True)
class SkillTemplate:
    """역할별 스킬 기준 설정."""
    multiplier: float           # 기본 배율
    target: str                 # 기본 타겟 (TargetType.value)
    effect_desc: str            # 기본 부가효과 설명
    cooldown: int = 0           # 액티브 쿨타임 (normal=0)
    hit_count: int = 1          # 기본 히트 수
    aoe: bool = False           # AoE 여부
    note: str = ""              # 밸런싱 참고사항


ROLE_SKILL_TEMPLATE: dict[Role, dict[str, SkillTemplate]] = {
    # ════════════════════════════════════════════
    # 딜러 (ATTACKER): 단일 타겟 폭딜 전문
    # ════════════════════════════════════════════
    Role.ATTACKER: {
        "normal": SkillTemplate(
            multiplier=1.50,
            target="enemy_near",
            effect_desc="단순 데미지",
            note="기본 DPS 소스. 1.0~2.5× 범위에서 조정",
        ),
        "active": SkillTemplate(
            multiplier=1.80,
            target="enemy_lowest_hp",
            effect_desc="단일 고데미지",
            cooldown=3,
            note="메인 딜 스킬. 타겟을 바꿔 개성화 (near/lowest_hp/random_2)",
        ),
        "ultimate": SkillTemplate(
            multiplier=3.00,
            target="enemy_lowest_hp",
            effect_desc="단일 극대 폭딜",
            note="SP6. 원킬 잠재력. 배율로 캐릭터 등급감 조절",
        ),
    },

    # ════════════════════════════════════════════
    # 마법사 (MAGICIAN): AoE 광역 전문
    # ════════════════════════════════════════════
    Role.MAGICIAN: {
        "normal": SkillTemplate(
            multiplier=1.20,
            target="enemy_near",
            effect_desc="단일 데미지",
            note="기본공격은 단일. 일부 MAG는 소범위(near_row) 가능",
        ),
        "active": SkillTemplate(
            multiplier=0.60,
            target="all_enemy",
            effect_desc="AoE 전체 데미지",
            cooldown=3,
            aoe=True,
            note="AoE 주력. 배율 낮지만 ×5 총합이 핵심. 0.4~1.8× 범위",
        ),
        "ultimate": SkillTemplate(
            multiplier=1.00,
            target="all_enemy",
            effect_desc="AoE 전체 강화 데미지",
            aoe=True,
            note="SP4. AoE 궁극기. 부가효과(DoT/디버프)로 개성화",
        ),
    },

    # ════════════════════════════════════════════
    # 탱커 (DEFENDER): 생존+보호 전문
    # ════════════════════════════════════════════
    Role.DEFENDER: {
        "normal": SkillTemplate(
            multiplier=0.50,
            target="enemy_near",
            effect_desc="약한 데미지",
            note="데미지 미미. 도발/자힐 부가효과가 핵심",
        ),
        "active": SkillTemplate(
            multiplier=0.35,
            target="all_enemy",
            effect_desc="AoE 약데미지 + 자힐 15%maxHP",
            cooldown=3,
            aoe=True,
            note="자힐(10~20%), 도발(1~2턴), 보호막 등으로 개성화",
        ),
        "ultimate": SkillTemplate(
            multiplier=0.00,
            target="all_ally",
            effect_desc="전체 아군 20%maxHP 회복",
            note="SP3. 힐/보호막/부활 등 팀 생존 기여. 데미지는 0~최소",
        ),
    },

    # ════════════════════════════════════════════
    # 힐러 (HEALER): 회복 전문
    # ════════════════════════════════════════════
    Role.HEALER: {
        "normal": SkillTemplate(
            multiplier=0.30,
            target="enemy_random",
            effect_desc="약한 데미지",
            note="딜 기여 미미. 일부 힐러는 normal에 소량 힐 가능",
        ),
        "active": SkillTemplate(
            multiplier=1.20,
            target="ally_lowest_hp",
            effect_desc="단일 힐 (ATK × mult × 0.40)",
            cooldown=3,
            note="힐 주력. 배율로 힐량 조절. 타겟(단일/2인)으로 개성화",
        ),
        "ultimate": SkillTemplate(
            multiplier=0.30,
            target="all_ally",
            effect_desc="전체 아군 30%maxHP 회복",
            note="SP3. %maxHP 전체힐. 비율(20~40%)로 캐릭터 격차",
        ),
    },

    # ════════════════════════════════════════════
    # 서포터 (SUPPORTER): 버프+보조딜 전문
    # ════════════════════════════════════════════
    Role.SUPPORTER: {
        "normal": SkillTemplate(
            multiplier=0.60,
            target="enemy_random",
            effect_desc="약한 데미지",
            note="기본 딜 약함. 일부 SUP는 normal에 소량 버프 가능",
        ),
        "active": SkillTemplate(
            multiplier=0.70,
            target="enemy_random",
            effect_desc="데미지 + 아군 ATK+20% 2턴 버프",
            cooldown=3,
            note="버프가 핵심. 버프 종류/강도/대상으로 개성화",
        ),
        "ultimate": SkillTemplate(
            multiplier=0.80,
            target="enemy_random",
            effect_desc="데미지 + 아군 ATK+30% 2턴 버프",
            note="SP4. 강화 버프. 버프 대상(전체/역할별)/디버프 부여로 개성화",
        ),
    },
}


# ────────────────────────────────────────────────────────────
# 스킬 밸런싱 개성화 가이드
# ────────────────────────────────────────────────────────────
# 동일 역할/등급의 캐릭터가 같은 스탯을 가지므로,
# 아래 축을 조합하여 캐릭터별 고유 전투 정체성을 부여한다.
#
# ┌─────────────┬──────────────────────────────────────────┐
# │ 조정 축      │ 예시                                      │
# ├─────────────┼──────────────────────────────────────────┤
# │ 배율 상향    │ 궁극기 3.0→3.4× (화력 특화)              │
# │ 배율 하향    │ 궁극기 3.0→2.5× + DoT 추가 (지속 데미지) │
# │ 타겟 확장    │ 단일→2명→행→십자 (범위 확대)              │
# │ 타겟 축소    │ 전체→단일 (집중 화력)                     │
# │ CC 부가      │ 기절/동결/수면 1턴 (행동 제어)            │
# │ DoT 부가     │ 화상/중독/출혈 (지속 피해)                │
# │ 버프 부가    │ 공+방, 크리율, 관통 (복합 버프)           │
# │ 디버프 부가  │ DEF-20%, SPD-15% (약화)                  │
# │ 보호막       │ maxHP 10~20% 쉴드 (생존 보조)            │
# │ 다단 히트    │ hit_count 2~3 (DoT 중첩 시너지)          │
# │ 쿨타임 조정  │ CD 2턴(공격적) / CD 4턴(강력한 효과)     │
# │ 자힐 비율    │ 탱커 자힐 10~20% (생존력 조절)           │
# │ 전체힐 비율  │ 힐러 궁극 20~40%maxHP (힐량 격차)        │
# │ SP 비용      │ ATK SP 5~7 / MAG SP 3~5 (궁극 빈도)     │
# └─────────────┴──────────────────────────────────────────┘
#
# 트레이드오프 원칙:
#   - 배율 ↑ → 부가효과 ↓ (순수 폭딜형)
#   - 배율 ↓ → 부가효과 ↑ (유틸형)
#   - 타겟 넓음 → 배율 ↓ (AoE 패널티)
#   - 타겟 좁음 → 배율 ↑ (집중 보상)
#   - CC 강함(기절 2턴) → 데미지 배율 대폭 ↓
#   - DoT 강함(3스택) → 기본 배율 소폭 ↓


# ────────────────────────────────────────────────────────────
# 헬퍼: 스킬 배율 검증
# ────────────────────────────────────────────────────────────

def validate_skill_mult(role: Role, skill_type: str, mult: float) -> tuple[bool, MultRange]:
    """스킬 배율이 역할별 허용 범위 내인지 검증. (통과여부, 범위) 반환."""
    mr = SKILL_MULTIPLIER_RANGE[role][skill_type]
    return (mr.min <= mult <= mr.max), mr


def skill_template(role: Role, skill_type: str) -> SkillTemplate:
    """역할/스킬타입에 대한 기본 템플릿 반환."""
    return ROLE_SKILL_TEMPLATE[role][skill_type]


# ════════════════════════════════════════════════════════════════
# 3×3 그리드 포지셔닝 룰 (v3.0)
# ════════════════════════════════════════════════════════════════
# 양 진영은 3×3 그리드(전열·중열·후열 × 좌·중·우)에 배치된다.
# 두 그리드는 전열(row 0)끼리 마주보고, 후열(row 2)이 가장 먼 위치.
#
# ┌───────────────────────────────────────────┐
# │ 아군 그리드          적군 그리드           │
# │ [후열2] [중열1] [전열0] ↔ [전열0] [중열1] [후열2] │
# └───────────────────────────────────────────┘
#
# 타일 거리 = caster.row + target.row + |caster.col - target.col|
# (row 0끼리 최소 거리 0, row 2끼리 최대 거리 4)

# ────────────────────────────────────────────────────────────
# 행(Row)별 피해 보정
# ────────────────────────────────────────────────────────────
# 전열(row 0): 피해 +5% (전투 전면에 노출)
# 중열(row 1): 기본 (보정 없음)
# 후열(row 2): 피해 -10% (후방 보호 효과)
ROW_DAMAGE_TAKEN_MULT: dict[int, float] = {
    0: 1.05,   # 전열: 받는 피해 +5%
    1: 1.00,   # 중열: 기본
    2: 0.90,   # 후열: 받는 피해 -10%
}

# ────────────────────────────────────────────────────────────
# 행(Row)별 DEF 보정
# ────────────────────────────────────────────────────────────
# 전열(row 0): DEF +15% (방패벽 효과)
# 중열(row 1): 기본
# 후열(row 2): DEF -5% (방어 태세 약화)
ROW_DEF_BONUS: dict[int, float] = {
    0: 0.15,    # 전열: DEF +15%
    1: 0.00,    # 중열: 기본
    2: -0.05,   # 후열: DEF -5%
}

# ────────────────────────────────────────────────────────────
# 전열 보호 (Front-Row Protection)
# ────────────────────────────────────────────────────────────
# 전열에 살아있는 아군이 있으면, 적의 ENEMY_NEAR 단일 타겟 공격은
# 반드시 전열 유닛을 우선 타격한다 (관통/후열 지정 타겟 제외).
# → 탱커가 전열에 서서 후열 딜러/힐러를 보호하는 전략적 배치 유도
FRONT_ROW_PROTECTION_ENABLED: bool = True

# ────────────────────────────────────────────────────────────
# 넉백 (Knockback) 룰
# ────────────────────────────────────────────────────────────
# 넉백 시 대상을 현재 행에서 +1 행(후열 방향)으로 밀어냄.
# row 2(최후열)에서 넉백 시 추가 피해(벽꿍 대미지) 발생.
KNOCKBACK_ROWS: int = 1               # 넉백 이동 행 수
KNOCKBACK_WALL_DAMAGE_RATIO: float = 0.10  # 벽꿍 피해 (최대 HP의 10%)

# ────────────────────────────────────────────────────────────
# 위치 기반 대미지 스케일링 (DAMAGE_POSITION_SCALE)
# ────────────────────────────────────────────────────────────
# 대상의 행에 따라 대미지 추가 배율:
# 전열(row 0) 대상: value × 2 추가 배율
# 중열(row 1) 대상: value × 1 추가 배율
# 후열(row 2) 대상: value × 0 추가 배율
# 예: value=0.15이면, 전열 대상 +30%, 중열 +15%, 후열 +0%
POSITION_SCALE_ROW_WEIGHT: dict[int, float] = {
    0: 2.0,   # 전열: 가중치 ×2
    1: 1.0,   # 중열: 가중치 ×1
    2: 0.0,   # 후열: 가중치 ×0
}


# ────────────────────────────────────────────────────────────
# 헬퍼 함수
# ────────────────────────────────────────────────────────────

def get_row_damage_taken_mult(row: int) -> float:
    """행별 받는 피해 배율 반환."""
    return ROW_DAMAGE_TAKEN_MULT.get(row, 1.0)


def get_row_def_bonus(row: int) -> float:
    """행별 DEF 보정 비율 반환."""
    return ROW_DEF_BONUS.get(row, 0.0)


def get_position_scale_mult(target_row: int, base_value: float) -> float:
    """위치 기반 추가 대미지 배율. 1.0 + base_value × row_weight."""
    weight = POSITION_SCALE_ROW_WEIGHT.get(target_row, 0.0)
    return 1.0 + base_value * weight
