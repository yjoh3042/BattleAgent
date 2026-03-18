# 전투 로직 명세서 (Battle Logic Specification)

> **버전**: 1.0
> **기준 소스**: `src/battle/` 모듈 전체
> **작성 기준**: 실제 구현 코드 역추적 (rules.py, battle_engine.py 등)

---

## 목차

1. [전투 시스템 개요](#1-전투-시스템-개요)
2. [턴 관리 시스템 (TurnManager)](#2-턴-관리-시스템-turnmanager)
3. [SP 시스템 (SPManager)](#3-sp-시스템-spmanager)
4. [스킬 시스템](#4-스킬-시스템)
5. [데미지 공식 (damage_calc)](#5-데미지-공식-damage_calc)
6. [힐 공식](#6-힐-공식)
7. [14종 LogicType 상세](#7-14종-logictype-상세)
8. [상태이상 (CC) 시스템](#8-상태이상-cc-시스템)
9. [DoT (지속 피해) 시스템](#9-dot-지속-피해-시스템)
10. [버프/디버프 생명주기 (BuffManager)](#10-버프디버프-생명주기-buffmanager)
11. [타겟 선택 시스템 (TargetSelector)](#11-타겟-선택-시스템-targetselector)
12. [트리거 시스템 (TriggerSystem)](#12-트리거-시스템-triggersystem)
13. [조건부 스킬 효과](#13-조건부-스킬-효과)
14. [반격 시스템](#14-반격-시스템)
15. [속성 상성 테이블](#15-속성-상성-테이블)
16. [원본 기획 로직 전체 명세 (Buff.xlsx + LogicFormula.xlsx + Notion)](#16-원본-기획-로직-전체-명세-buffxlsx--logicformulaxlsx--notion)

---

## 1. 전투 시스템 개요

> 소스: `src/battle/battle_engine.py`, `src/battle/rules.py`

### 1.1 CTB 메인 루프 흐름도

전투 엔진은 ATB(Active Time Battle) 기획을 CTB(Conditional Turn-Based) heapq 큐로 시뮬레이션한다.
두 방식은 행동 간격 = `BATTLE_LENGTH / SPD` 공식이 동일하여 결과가 같다.

```
전투 시작
    │
    ├─ TurnManager.initialize(all_units)     ← 전체 유닛 첫 행동시간 등록
    ├─ SPManager 초기화 (ally=0, enemy=0)
    └─ TriggerSystem.evaluate_battle_start() ← ON_BATTLE_START 트리거
         │
         ▼
┌─────────────────────────────────────────────────────┐
│                   메인 루프 (while turn_count < MAX_TURNS)     │
│                                                       │
│  entry = TurnManager.pop_next()   ← heapq에서 최소 action_time 팝  │
│         │                                             │
│         ├─[entry is None]─────────────────────► BREAK │
│         │                                             │
│         ├─[unit 사망]──────────────────────────► CONTINUE │
│         │                                             │
│         ├─[current_time > MAX_TIME]                   │
│         │      └─► _resolve_time_over() → 결과 반환  │
│         │                                             │
│         ├─[배틀 라운드 전환 체크]                     │
│         │      └─► SP 리셋 + 얼티밋 플래그 리셋       │
│         │          + 전원 행동큐 재계산               │
│         │          + ON_ROUND_START 트리거            │
│         │                                             │
│         ├─[is_extra=False] SP.charge_on_turn_start()  │
│         │                                             │
│         ├─[Hard CC] 버프틱만 처리 → reschedule → CONTINUE │
│         │                                             │
│         ├─[Soft CC] 30% 확률 → 버프틱만 처리 → CONTINUE │
│         │                                             │
│         ├─[is_extra=False] BuffManager.tick_turn_start()  │
│         │      └─► DoT 틱 발동 + CharacterTurnStart 버프 만료  │
│         │                                             │
│         ├─[is_extra=False] _try_ultimate()            │
│         │      └─► SP 충분 + 쿨타임 없음 → Extra Turn 등록  │
│         │                                             │
│         ├─ 스킬 결정:                                 │
│         │   is_extra=True  → ultimate_skill 실행      │
│         │   is_extra=False → _decide_skill()          │
│         │                                             │
│         ├─ SkillExecutor.execute(caster, skill, ctx)  │
│         │      └─► Effect별 LogicType 분기 처리       │
│         │          ON_HIT 트리거 (피격 패시브)         │
│         │          화상반격 체크                       │
│         │                                             │
│         ├─ 킬 발생 시: TurnManager.remove_unit()      │
│         │             ON_KILL 트리거                  │
│         │                                             │
│         ├─[is_extra=False] BuffManager.tick_turn_end()│
│         │      └─► CharacterTurnEnd 버프 만료         │
│         │          CC/쿨타임/도발 틱                  │
│         │          ON_TURN_END 트리거                 │
│         │                                             │
│         ├─[is_extra=False] TurnManager.reschedule_unit()  │
│         │                                             │
│         └─ _check_victory() → 전멸 판정              │
│                                                       │
└─────────────────────────────────────────────────────┘
         │
         ▼
    MAX_TURNS 초과
    └─► _resolve_time_over() → BattleResult 반환
```

### 1.2 핵심 상수

| 상수명 | 값 | 정의 위치 | 설명 |
|--------|-----|----------|------|
| `BATTLE_LENGTH` | 300 | `rules.py` | 행동 간격 계산 분자 (Turn Formula = BATTLE_LENGTH / SPD) |
| `MAX_TURNS` | 500 | `battle_engine.py` | 무한 루프 방지 최대 턴 수 (rules.py의 200과 별도 상수) |
| `MAX_TIME` | 300.0 | `battle_engine.py` | 최대 전투 시간 (타임오버 판정 기준) |
| `MAX_TURN_TIME` | 10 | `rules.py` | 배틀 라운드 전환 간격 (10 time unit마다) |
| `ULT_COOLDOWN` | 4 | `rules.py` | 전 직업 공통 얼티밋 쿨타임 (자기 턴 4회) |

> **주의**: `rules.py`의 `MAX_TURNS=200`과 `battle_engine.py`의 `MAX_TURNS=500`은 별개 상수이다.
> 실제 메인 루프는 `battle_engine.py`의 500을 사용한다.

### 1.3 전투 종료 조건

```python
# 1) 적군 전멸
if not alive_enemies:
    return BattleResult.ALLY_WIN

# 2) 아군 전멸
if not alive_allies:
    return BattleResult.ENEMY_WIN

# 3) 타임오버 (current_time > MAX_TIME)
#    또는 턴 한계 초과 (turn_count >= MAX_TURNS)
return _resolve_time_over()
```

### 1.4 덱 타입별 타임오버 판정

`_resolve_time_over()` 함수는 `DeckType`에 따라 타임오버 승패를 결정한다.

```python
def _resolve_time_over(self) -> BattleResult:
    if self.deck_type == DeckType.DEFENSE:
        return BattleResult.ALLY_WIN   # 방어덱: 생존 성공 = 승리
    return BattleResult.ENEMY_WIN     # 공격덱: 전멸 실패 = 패배
```

| 덱 타입 | 타임오버 결과 | 전략 방향 |
|---------|------------|---------|
| `OFFENSE` (기본값) | `ENEMY_WIN` (아군 패배) | 제한 시간 내 적 전멸 필수 |
| `DEFENSE` | `ALLY_WIN` (아군 승리) | 제한 시간 동안 생존하면 승리 |

---

## 2. 턴 관리 시스템 (TurnManager)

> 소스: `src/battle/turn_manager.py`

### 2.1 heapq 기반 CTB 큐 동작 원리

`TurnManager`는 Python `heapq`를 이용한 최소 힙(min-heap)으로 구현된다.
`TurnEntry.action_time`이 가장 작은 유닛이 먼저 행동한다.

```python
@dataclass(order=True)
class TurnEntry:
    action_time: float     # 정렬 기준 (작을수록 먼저 행동)
    sequence: int          # 동일 시간 타이브레이커 (먼저 등록된 쪽 우선)
    unit_id: str           # compare=False
    is_extra: bool         # compare=False, Extra Turn 여부
```

**무효화 메커니즘**: 속도 변화로 인한 재스케줄 시, 기존 엔트리는 힙에서 삭제하지 않고
`_unit_next_time[unit_id]`를 새 값으로 덮어쓴다. 이후 `pop_next()` 시 시간이 불일치하는
엔트리는 자동 스킵된다.

```python
def pop_next(self) -> Optional[TurnEntry]:
    while self._heap:
        entry = heapq.heappop(self._heap)
        if not entry.is_extra:
            # 무효화된 일반 턴 엔트리 스킵
            if self._unit_next_time.get(entry.unit_id) != entry.action_time:
                continue
        self.current_time = entry.action_time
        return entry
    return None
```

### 2.2 action_time 계산

```
초기 action_time = BATTLE_LENGTH / SPD
재스케줄 후 = current_time + BATTLE_LENGTH / SPD
```

**예시**: SPD=80인 딜러(카라라트리, 이브 등)의 첫 행동 시간

```
action_time = 300 / 80 = 3.75
```

**예시**: SPD=120인 서포터의 첫 행동 시간

```
action_time = 300 / 120 = 2.5
```

즉, SPD가 높을수록 더 빨리 행동한다. SPD=120 서포터는 SPD=80 딜러보다 1.5배 자주 행동한다.

### 2.3 배틀 라운드 전환 규칙

`ROUND_INTERVAL = float(MAX_TURN_TIME) = 10.0` 단위마다 배틀 라운드가 전환된다.

```python
def check_battle_round(self) -> bool:
    new_round = int(self.current_time // ROUND_INTERVAL)
    if new_round > self.battle_round:
        self.battle_round = new_round
        return True
    return False
```

라운드 전환 시 처리 내용:
1. `sp_manager.reset()` — SP를 양쪽 모두 0으로 초기화
2. `used_ultimate_this_round = False` — 얼티밋 사용 플래그 리셋
3. `turn_manager.recalculate_all(alive_units)` — 전원 행동큐 현재 SPD 기준 재계산
4. `trigger_system.evaluate_round_start()` — ON_ROUND_START 트리거 발동

**재계산 공식**:
```python
round_boundary = self.battle_round * ROUND_INTERVAL
next_time = round_boundary + TURN_LENGTH / unit.spd
```

### 2.4 Extra Turn (얼티밋 끼어들기) 동작

얼티밋 발동 조건 충족 시 `add_extra_turn()`으로 현재 시간보다 약간 앞에 배치하여 최우선 실행한다.

```python
EXTRA_TURN_EPSILON: float = 1e-6

def add_extra_turn(self, unit: BattleUnit) -> bool:
    if self._extra_turn_count >= MAX_EXTRA_TURNS:  # 최대 100회
        return False
    extra_time = self.current_time - EXTRA_TURN_EPSILON * (self._extra_turn_count + 1)
    entry = TurnEntry(extra_time, self._sequence, unit.id, is_extra=True)
    heapq.heappush(self._heap, entry)
    self._extra_turn_count += 1
    return True
```

Extra Turn 엔트리는 `is_extra=True`이므로 `_unit_next_time` 무효화 체크를 받지 않는다.
`MAX_EXTRA_TURNS = 100`으로 무한 루프를 방지한다.

### 2.5 속도 변화 즉시 반영

SPD 버프/디버프 적용 시 `on_spd_change()`로 남은 거리를 새 SPD 기준으로 재계산한다.

```python
def on_spd_change(self, unit: BattleUnit, old_spd: float):
    remaining_distance = (old_next - self.current_time) * old_spd
    new_next = self.current_time + remaining_distance / unit.spd
    self._push(new_next, unit.id, is_extra=False)
    # 기존 엔트리는 _unit_next_time 덮어쓰기로 자동 무효화
```

최솟값 보장: `unit.spd` 프로퍼티는 항상 `max(25.0, ...)` 적용.

---

## 3. SP 시스템 (SPManager)

> 소스: `src/battle/sp_manager.py`

### 3.1 공유 풀 개념

아군(`ally_sp`)과 적군(`enemy_sp`)이 각각 독립된 SP 풀을 보유한다.

```python
class SPManager:
    MAX_SP: int = 10

    def __init__(self):
        self.ally_sp: int = 0
        self.enemy_sp: int = 0
```

### 3.2 충전 규칙

**매 턴 시작** 시 피아 구분 없이 누군가의 턴이 시작될 때 **양측 동시** +1 충전.
단, Extra Turn에서는 SP를 충전하지 않는다.

```python
def charge_on_turn_start(self):
    self.ally_sp = min(self.MAX_SP, self.ally_sp + 1)
    self.enemy_sp = min(self.MAX_SP, self.enemy_sp + 1)

# 호출 조건 (battle_engine.py):
if not entry.is_extra:
    self.sp_manager.charge_on_turn_start()
```

최대 10SP를 초과하지 않는다.

### 3.3 소모 규칙

얼티밋 발동 시 해당 진영의 SP를 `sp_cost`만큼 차감한다.

```python
def spend(self, side: str, amount: int) -> bool:
    if not self.can_spend(side, amount):
        return False
    if side == "ally":
        self.ally_sp -= amount
    else:
        self.enemy_sp -= amount
    return True
```

역할별 기본 SP 비용 (`rules.py` 기준):

| 역할 | SP 비용 |
|------|--------|
| ATTACKER | 6 |
| MAGICIAN | 4 |
| SUPPORTER | 4 |
| DEFENDER | 3 |
| HEALER | 3 |

### 3.4 라운드 리셋

배틀 라운드 전환 시 양측 SP를 모두 0으로 초기화한다.

```python
def reset(self):
    self.ally_sp = 0
    self.enemy_sp = 0
```

### 3.5 SP 직접 증가 (스킬 효과)

`LogicType.SP_INCREASE` 스킬 효과로 아군 SP를 직접 증가시킬 수 있다.
최대 10SP를 초과하지 않는다.

```python
def add_sp(self, side: str, amount: int):
    if side == "ally":
        self.ally_sp = min(self.MAX_SP, self.ally_sp + amount)
    else:
        self.enemy_sp = min(self.MAX_SP, self.enemy_sp + amount)
```

---

## 4. 스킬 시스템

> 소스: `src/battle/battle_engine.py`, `src/battle/battle_unit.py`, `src/battle/models.py`

### 4.1 3종 스킬 타입 상세

#### Normal (기본 공격)
- 쿨타임 없음 — 매 턴 사용 가능
- SP 소모 없음
- 가장 낮은 우선순위 (Active/Ultimate 사용 불가 시 폴백)

```python
# SkillType.NORMAL = "normal"  # 기본 공격, 쿨타임 없음
```

**예시** — 카라라트리의 기본공격 "무기법":
`ENEMY_NEAR` 대상, DMG 3.00x + 화상 스택당 추가 피해(30%/스택)

#### Active (액티브 스킬)
- 기본 쿨타임 2~3턴 (`cooldown_turns`, 미지정 시 `use_active_skill()`에서 2 적용)
- SP 소모 없음
- Normal보다 우선 선택 (쿨타임 없으면 항상 Active 사용)

```python
def use_active_skill(self):
    self.active_skill_cooldown = self.data.active_skill.cooldown_turns or 2

def can_use_active(self) -> bool:
    return self.active_skill_cooldown <= 0
```

**예시** — 카라라트리의 액티브 "무루의 고통":
`ENEMY_NEAR_ROW` 대상, DMG 3.60x + 화상 15% 2턴 부여

#### Ultimate (얼티밋)
- SP 소모 (`sp_cost`, 기본값 캐릭터 데이터에 설정)
- Extra Turn 발동 (일반 턴 중 _try_ultimate로 끼어들기 예약)
- 사용 후 4턴 쿨타임 (`ULT_COOLDOWN = 4`, 자기 턴 기준)
- 라운드당 1회 제한 (`used_ultimate_this_round`)

```python
def can_use_ultimate(self) -> bool:
    return self.ultimate_cooldown <= 0 and not self.used_ultimate_this_round

def use_ultimate_skill(self):
    from battle.rules import ULT_COOLDOWN
    cd = self.data.ultimate_skill.cooldown_turns
    if cd <= 0:
        cd = ULT_COOLDOWN  # 전 직업 공통 4턴
    self.ultimate_cooldown = cd
```

### 4.2 스킬 결정 로직 (_decide_skill)

```python
def _decide_skill(self, unit: BattleUnit):
    if self.allow_active and unit.can_use_active():
        return unit.data.active_skill
    return unit.data.normal_skill
```

우선순위: Active (쿨타임 없음) > Normal

### 4.3 얼티밋 발동 조건 및 흐름 (_try_ultimate)

```
일반 턴 시작
    │
    ├─[allow_ultimate=False] → 종료
    ├─[can_use_ultimate()=False] → 종료  (쿨타임 or 라운드 사용)
    ├─[SP 부족] → 종료
    │
    ├─ ultimate_mode == "auto":
    │      → should_use = True (SP 충족 즉시 발동)
    │
    ├─ ultimate_mode == "manual_ordered":
    │      → ultimate_order 리스트에서 현재 idx 위치 유닛인지 확인
    │      → 해당 유닛이면 should_use = True
    │
    └─[should_use=True]:
           sp_manager.spend(unit.side, sp_cost)
           unit.used_ultimate_this_round = True
           TurnManager.add_extra_turn(unit)  ← Extra Turn 등록
           (다음 pop_next()에서 현재 시간 - ε 로 즉시 행동)
```

Extra Turn에서 실행되는 내용:
```python
if entry.is_extra:
    skill = unit.data.ultimate_skill
    unit.use_ultimate_skill()   # 얼티밋 쿨타임 4턴 시작
```

Extra Turn에서는 `tick_turn_start`, `tick_turn_end`, `reschedule_unit`이 **호출되지 않는다**.

---

## 5. 데미지 공식 (damage_calc)

> 소스: `src/battle/damage_calc.py`

### 5.1 기본 데미지 (Base Damage)

비율 기반 방어 경감 공식. 관통(penetration)으로 방어력을 직접 감소시킨다.

```python
def calc_base_damage(atk: float, def_: float, penetration: float = 0.0) -> float:
    effective_def = max(0.0, def_ - penetration)
    if atk + effective_def <= 0:
        return 0.0
    return atk * (1.0 - effective_def / (atk + effective_def))
```

수식:
```
effective_def = max(0, DEF - penetration)
Base = ATK × (1 - effective_def / (ATK + effective_def))
```

**수치 예시** — 카라라트리(ATK=800) vs 일반 ATTACKER 적(DEF=120):
```
effective_def = max(0, 120 - 0) = 120
Base = 800 × (1 - 120 / (800 + 120))
     = 800 × (1 - 0.1304)
     = 800 × 0.8696
     = 695.7
```

### 5.2 크리티컬

```python
def roll_crit(cri_ratio: float, cri_resist: float = 0.0) -> bool:
    effective = max(0.0, cri_ratio - cri_resist)
    return random.random() < effective

def get_crit_mult(cri_dmg_ratio: float, is_crit: bool) -> float:
    return cri_dmg_ratio if is_crit else 1.0
```

- 기본 크리 확률: `cri_ratio = 0.15` (15%)
- 기본 크리 배율: `cri_dmg_ratio = 1.5` (150%)
- 크리 저항: `cri_resist` (방어자 스탯, 크리 확률 감소)
- 유효 크리율 = max(0, cri_ratio - cri_resist)

### 5.3 속성 상성 배율

```python
def get_element_mult(atk_elem: Element, def_elem: Element) -> float:
    return ELEMENT_TABLE.get((atk_elem, def_elem), 1.0)
```

상세 테이블은 [섹션 15](#15-속성-상성-테이블) 참조.

### 5.4 관통 (Penetration)

`effective_def = max(0, DEF - penetration)`으로 DEF를 직접 감소시킨다.
캐릭터 스탯 `StatBlock.penetration` 또는 STAT_CHANGE 버프로 부여 가능.

### 5.5 회피 (Dodge)

```python
def roll_dodge(dodge: float, acc: float) -> bool:
    effective = max(0.0, dodge - (1.0 - acc))
    if effective <= 0:
        return False
    return random.random() < effective
```

유효 회피율 = max(0, dodge - (1 - acc))
회피 성공 시 데미지 0, `is_dodged=True` 반환.

### 5.6 화상 스택 보너스 (burn_bonus_per_stack)

```python
def get_burn_bonus_mult(burn_stack: int, bonus_per_stack: float = 0.5) -> float:
    if burn_stack <= 0:
        return 1.0
    return 1.0 + bonus_per_stack * burn_stack
```

**예시** — 카라라트리의 "무기법" (burn_bonus_per_stack=0.3):
- 화상 0스택: 보너스 없음 (×1.0)
- 화상 1스택: ×1.3 (130%)
- 화상 2스택: ×1.6 (160%)
- 화상 3스택: ×1.9 (190%)

### 5.7 최종 데미지 공식

```python
def calc_final_damage(base, skill_mult, elem_mult, crit_mult, burn_bonus=1.0) -> int:
    return max(0, math.floor(base * skill_mult * elem_mult * crit_mult * burn_bonus))
```

```
Final = floor(Base × SkillMult × ElemMult × CritMult × BurnBonus)
```

### 5.8 전체 데미지 파이프라인 (compute_damage)

```python
def compute_damage(attacker, defender, skill_mult, burn_bonus_per_stack=0.0):
    # 1) 회피 판정
    if roll_dodge(defender.dodge, attacker.acc):
        return 0, False, True

    # 2) 기본 데미지
    base = calc_base_damage(attacker.atk, defender.def_, attacker.penetration)

    # 3) 속성 배율
    elem_mult = get_element_mult(attacker.data.element, defender.data.element)

    # 4) 크리 판정
    is_crit = roll_crit(attacker.cri_ratio, defender.cri_resist)
    crit_mult = get_crit_mult(attacker.cri_dmg_ratio, is_crit)

    # 5) 화상 보너스
    burn_stack = defender.get_tag_count("burn") if burn_bonus_per_stack > 0 else 0
    burn_bonus = get_burn_bonus_mult(burn_stack, burn_bonus_per_stack) if burn_stack > 0 else 1.0

    # 6) 최종 데미지
    final = calc_final_damage(base, skill_mult, elem_mult, crit_mult, burn_bonus)
    return final, is_crit, False
```

**완전 계산 예시** — 이브(ATK=800, 수속성)의 "다크 미스트" (배율 3.60x) vs ATTACKER 적(DEF=120, 화속성):
```
effective_def = 120
Base = 800 × (1 - 120/920) = 800 × 0.8696 = 695.7
ElemMult = 수→화 = 1.2 (유리)
CritMult = 0.15 확률 → 크리 발동 가정 시 1.5, 비크리 시 1.0
BurnBonus = 1.0 (이브는 burn_bonus 없음)

비크리: floor(695.7 × 3.60 × 1.2 × 1.0) = floor(3005.8) = 3005
크리:   floor(695.7 × 3.60 × 1.2 × 1.5) = floor(4508.7) = 4508
```

---

## 6. 힐 공식

> 소스: `src/battle/damage_calc.py`, `src/battle/skill_executor.py`

### 6.1 ATK 기반 힐 (LogicType.HEAL)

```python
def calc_heal(healer_atk, target_max_hp, skill_mult=1.0, hp_ratio=None) -> float:
    if hp_ratio is not None:
        return target_max_hp * hp_ratio
    return healer_atk * skill_mult
```

```
HealAmount = healer_atk × skill_mult
```

실제 적용 (skill_executor.py):
```python
amount = calc_heal(caster.atk, target.max_hp, effect.multiplier)
actual = target.heal(amount)
```

### 6.2 maxHP 비율 힐 (LogicType.HEAL_HP_RATIO)

```python
amount = calc_heal(caster.atk, target.max_hp, hp_ratio=effect.value)
```

```
HealAmount = target.max_hp × hp_ratio
```

**예시**: HEALER(ATK=200) 얼티밋 30% maxHP 힐 vs DEFENDER 대상(maxHP=8650):
```
HealAmount = 8650 × 0.30 = 2595
```

### 6.3 오버힐 불가

```python
def heal(self, amount: float) -> float:
    if amount <= 0 or not self.is_alive:
        return 0.0
    old = self.current_hp
    self.current_hp = min(self.max_hp, self.current_hp + amount)
    return self.current_hp - old  # 실제 회복량 반환
```

`current_hp`는 `max_hp`를 초과할 수 없다. 오버힐 분은 소실된다.

---

## 7. 14종 LogicType 상세

> 소스: `src/battle/enums.py`, `src/battle/skill_executor.py`

### 7.1 DAMAGE

**동작**: 데미지 계산 → 보호막 우선 흡수 → HP 차감 → 사망 판정 → ON_HIT 트리거
**파라미터**: `multiplier` (배율), `condition` (burn_bonus_per_stack, target_hp_below)

```python
dmg, is_crit, is_dodged = compute_damage(caster, target, effect.multiplier, burn_bonus)
if is_dodged:
    return  # 회피
actual = target.take_damage(dmg)

# ON_HIT 트리거
if target.is_alive and ctx.trigger_system:
    ctx.trigger_system.evaluate_on_hit(target, caster, int(actual), ctx)

if not target.is_alive:
    self._killed_this_skill.append(target)
```

**보호막 우선 흡수** (take_damage):
```python
def take_damage(self, amount: float) -> float:
    actual = amount
    if self.barrier_hp > 0:
        absorbed = min(self.barrier_hp, amount)
        self.barrier_hp -= absorbed
        actual = amount - absorbed
    self.current_hp = max(0.0, self.current_hp - actual)
    return actual
```

**예시**: 이브의 "레인 드랍" — `target_hp_below: 0.25` 조건으로 HP 25% 이하 적에게 추가 DMG 3.00x 발동

### 7.2 HEAL

**동작**: 시전자 ATK × 배율 만큼 회복. 오버힐 불가.
**파라미터**: `multiplier` (배율)

```python
amount = calc_heal(caster.atk, target.max_hp, effect.multiplier)
actual = target.heal(amount)
```

### 7.3 HEAL_HP_RATIO

**동작**: 대상 maxHP × 비율 만큼 회복. 오버힐 불가.
**파라미터**: `value` (비율, 예: 0.30 = 30% maxHP)

```python
amount = calc_heal(caster.atk, target.max_hp, hp_ratio=effect.value)
actual = target.heal(amount)
```

**예시**: DEFENDER 얼티밋 전체 아군 20% maxHP 회복 → `value=0.20`

### 7.4 STAT_CHANGE

**동작**: 버프/디버프를 적용하여 ATK/DEF/SPD/크리 등 스탯을 변경.
**파라미터**: `buff_data.stat` (대상 스탯), `buff_data.value` (변경량), `buff_data.is_ratio` (비율 여부), `buff_data.duration` (지속 턴)

```python
ctx.buff_manager.apply_buff(target, effect.buff_data, caster.id)
```

스탯 반영 (`_get_buff_delta`):
```python
for ab in self.active_buffs:
    bd = ab.buff_data
    if bd.logic_type == LogicType.STAT_CHANGE and bd.stat == stat:
        if bd.is_ratio:
            total += base * bd.value * ab.stack_count  # 비율: base × value
        else:
            total += bd.value * ab.stack_count          # 절대값: value 그대로
```

**예시**: 카라라트리 얼티밋 "출세간의 선법" → 적 전체 DEF -20% 2턴 (`is_ratio=True`, `value=-0.20`)

### 7.5 DOT

**동작**: 지속 피해(화상/독/출혈) 버프를 부여. 매 턴 시작 시 발동.
**파라미터**: `buff_data.dot_type` ('burn'/'poison'/'bleed'), `buff_data.value` (maxHP 대비 비율), `buff_data.duration` (지속 턴), `buff_data.max_stacks` (최대 스택)

화상 부여 시 추가로 `burn` 태그 +1 처리:
```python
if buff_data.logic_type == LogicType.DOT and buff_data.dot_type == "burn":
    unit.add_tag("burn", 1)
```

**예시**: 카라라트리 액티브 "무루의 고통" → 화상 15%(maxHP 대비) 2턴 부여

### 7.6 DOT_HEAL_HP_RATIO

**동작**: 지속 회복 버프를 부여. 매 턴 시작 시 maxHP × value 만큼 회복.
**파라미터**: `buff_data.value` (maxHP 대비 비율)

```python
elif bd.logic_type == LogicType.DOT_HEAL_HP_RATIO:
    heal = unit.max_hp * bd.value
    actual = unit.heal(heal)
```

### 7.7 BARRIER

**동작**: 보호막 부여. HP 대신 피해를 흡수. 중첩 가능 (barrier_hp 누적).
**파라미터**: `multiplier` (caster.atk × multiplier), `value` (고정값)

```python
barrier_amount = caster.atk * effect.multiplier if effect.multiplier else effect.value
target.add_barrier(barrier_amount)
```

```python
def add_barrier(self, amount: float):
    self.barrier_hp += amount  # 누적 합산
```

보호막은 `take_damage()`에서 HP보다 먼저 차감된다.

### 7.8 TAUNT

**동작**: 시전자(탱커)가 적 전체에게 도발을 부여. 도발 받은 적은 반드시 시전자를 공격.
**파라미터**: `value` (지속 턴, 기본 2)

```python
TargetSelector.apply_taunt_to_enemies(caster, ctx.get_enemies_of(caster), duration)
```

```python
@staticmethod
def apply_taunt_to_enemies(taunter, enemies, duration=2):
    for enemy in enemies:
        if enemy.is_alive:
            enemy.apply_taunt(taunter.id, duration)
```

도발 처리 규칙: [섹션 11.4](#114-도발taunt-강제-타겟팅-규칙) 참조.

### 7.9 REVIVE

**동작**: 사망한 아군을 부활. HP를 maxHP의 일정 비율로 회복. 턴 큐에 재등록.
**파라미터**: `value` (부활 HP 비율, 기본 0.30 = 30%)
**타겟 타입**: `ALLY_DEAD_RANDOM` (사망 아군 중 랜덤 1명)

```python
if not target.is_alive:
    hp_ratio = effect.value if effect.value else 0.3
    target.revive(hp_ratio)
    ctx.turn_manager.reschedule_unit(target)  # 턴 큐 재등록
```

```python
def revive(self, hp_ratio: float = 0.3):
    self.current_hp = self.max_hp * hp_ratio
    self.hard_cc = None
    self.hard_cc_duration = 0
```

### 7.10 SP_INCREASE

**동작**: 아군 SP를 직접 증가. MAX_SP(10) 초과 불가.
**파라미터**: `value` (증가량)

```python
amount = int(effect.value)
ctx.sp_manager.add_sp(caster.side, amount)
```

### 7.11 CC

**동작**: 상태이상(CC)을 부여. 화상 스택 조건 충족 시에만 발동 가능.
**파라미터**: `buff_data.cc_type` (CCType), `buff_data.duration` (지속 턴)
**조건**: `effect.condition.target_burn_min` — 대상의 화상 스택이 N 이상이어야 발동

```python
if effect.condition:
    burn_min = effect.condition.get('target_burn_min', 0)
    if burn_min > 0 and target.get_tag_count('burn') < burn_min:
        return  # 조건 미충족
ctx.buff_manager.apply_buff(target, effect.buff_data, caster.id)
```

상세 CC 규칙: [섹션 8](#8-상태이상-cc-시스템) 참조.

### 7.12 REMOVE_BUFF

**동작**: 대상의 모든 버프(is_debuff=False)를 제거.
**대상**: 보통 적 단일 타겟

```python
ctx.buff_manager.remove_buffs(target)
# → unit.remove_buffs(is_debuff=False)
# → active_buffs에서 is_debuff==False인 버프 전체 제거
```

### 7.13 REMOVE_DEBUFF

**동작**: 대상의 모든 디버프(is_debuff=True)를 제거.
**대상**: 보통 아군 단일 또는 전체

```python
ctx.buff_manager.remove_debuffs(target)
# → unit.remove_buffs(is_debuff=True)
```

### 7.14 COUNTER

**동작**: 반격 준비 마커 버프(`counter_burn_active`)를 부여. 피격 시 공격자에게 화상 반격.
**파라미터**: `value` (지속 턴, 기본 2)

```python
counter_marker = BuffData(
    id="counter_burn_active",
    name="화상반격",
    source_skill_id=skill.id,
    logic_type=LogicType.STAT_CHANGE,
    stat="def_",
    value=0,          # 실제 스탯 변화 없음 (마커 역할만)
    duration=duration,
    is_debuff=False,
)
ctx.buff_manager.apply_buff(target, counter_marker, caster.id)
```

상세 반격 흐름: [섹션 14](#14-반격-시스템) 참조.

### 7.15 ABSORB

**동작**: 피해 흡수 (미구현).
현재 코드에서 `LogicType.ABSORB`는 열거형에 정의되어 있으나 `skill_executor.py`에 처리 분기 없음.

---

## 8. 상태이상 (CC) 시스템

> 소스: `src/battle/enums.py`, `src/battle/battle_unit.py`

### 8.1 Hard CC (행동 100% 불가)

Hard CC 상태의 유닛은 완전히 행동 불가. 버프 틱만 처리된다.

| CC 타입 | 값 | 설명 |
|---------|----|----- |
| `STUN` | "stun" | 기절 — 모든 행동 불가 |
| `SLEEP` | "sleep" | 수면 — 모든 행동 불가 |
| `FREEZE` | "freeze" | 빙결 — 모든 행동 불가 |
| `STONE` | "stone" | 석화 — 모든 행동 불가 |
| `ABNORMAL_SKILL` | "abnormal_skill" | 스킬 이상 — 행동 불가 |

```python
hard_cc_types = {CCType.STUN, CCType.SLEEP, CCType.FREEZE, CCType.STONE, CCType.ABNORMAL_SKILL}

# battle_engine.py: Hard CC 처리
if unit.hard_cc:
    self._log.append(f"  ⛔ {unit.name} {unit.hard_cc.value}로 행동 불가")
    self.buff_manager.tick_turn_start(unit)   # DoT 틱 발동
    self.buff_manager.tick_turn_end(unit)     # 버프 지속시간 감소
    if not entry.is_extra:
        self.turn_manager.reschedule_unit(unit)
    continue  # 스킬 실행 없이 다음 턴
```

### 8.2 Soft CC (30% 확률 행동 실패)

Soft CC 상태의 유닛은 **30% 확률**로 행동 실패. 70% 확률로 정상 행동.

| CC 타입 | 값 | 설명 |
|---------|----|----- |
| `ELECTRIC_SHOCK` | "electric_shock" | 감전 — 30% 확률 행동 불가 |
| `PANIC` | "panic" | 패닉 — 30% 확률 행동 불가 |

```python
if unit.soft_cc:
    if random.random() < 0.3:
        # 행동 실패
        self.buff_manager.tick_turn_start(unit)
        self.buff_manager.tick_turn_end(unit)
        continue
    # 30% 미발동 시 정상 행동
```

### 8.3 디버프성 CC

행동 자체를 막지는 않지만 불리한 효과를 부여하는 CC.

| CC 타입 | 값 | 설명 |
|---------|----|----- |
| `POISON` | "poison" | 중독 — DoT 효과 (LogicType.DOT와 별개) |
| `BURN` | "burn" | 화상 — DoT 효과 |
| `BLIND` | "blind" | 실명 — 명중률 감소 |
| `SILENCE` | "silence" | 침묵 — 스킬 사용 불가 |

> **주의**: `CCType.BURN/POISON`은 열거형 정의에 있으나, 실제 DoT 처리는
> `LogicType.DOT + dot_type="burn"/"poison"`으로 구현된다.

### 8.4 CC 부여 규칙

```python
def apply_cc(self, cc_type: CCType, duration: int = 1):
    hard_cc_types = {CCType.STUN, CCType.SLEEP, CCType.FREEZE, CCType.STONE, CCType.ABNORMAL_SKILL}
    if cc_type in hard_cc_types:
        self.hard_cc = cc_type
        self.hard_cc_duration = max(self.hard_cc_duration, duration)  # 더 긴 쪽 채택
    else:
        self.soft_cc = cc_type
        self.soft_cc_duration = max(self.soft_cc_duration, duration)
```

중첩 규칙: 동일 CC가 이미 있으면 **더 긴 지속시간**으로 덮어쓴다 (`max` 적용).

### 8.5 CC 틱 (지속시간 감소)

`on_turn_end()` → `tick_cc()` 에서 처리된다 (CharacterTurnEnd 타이밍).

```python
def tick_cc(self):
    if self.hard_cc_duration > 0:
        self.hard_cc_duration -= 1
        if self.hard_cc_duration <= 0:
            self.hard_cc = None
    if self.soft_cc_duration > 0:
        self.soft_cc_duration -= 1
        if self.soft_cc_duration <= 0:
            self.soft_cc = None
```

---

## 9. DoT (지속 피해) 시스템

> 소스: `src/battle/damage_calc.py`, `src/battle/buff_manager.py`, `src/battle/models.py`

### 9.1 3종 DoT 타입

| 종류 | `dot_type` 값 | 설명 |
|------|--------------|------|
| 화상 | `"burn"` | 화속성 계열, 스택 시너지(burn_bonus) 연동 |
| 중독 | `"poison"` | 수속성 계열 |
| 출혈 | `"bleed"` | 근거리 계열 (물리 피해) |

### 9.2 틱 타이밍

DoT 버프는 `buff_turn_reduce_timing = "CharacterTurnStart"`로 설정된다.
**매 턴 시작 시** (`tick_turn_start`) DoT 피해가 발동된 **후** 지속시간이 감소한다.

```python
# buff_manager.py
def tick_turn_start(self, unit: BattleUnit):
    self._apply_dots(unit)              # 1. DoT 틱 발동 (버프가 살아있을 때)
    expired = unit.on_turn_start_tick() # 2. remaining_turns -1, 만료 처리
    self._handle_expired(unit, expired, old_spd, timing_label="턴시작")
```

핵심: **틱 발동이 먼저, 만료 처리가 나중**이므로 duration=1인 DoT도 1번은 반드시 발동한다.

### 9.3 DoT 데미지 계산

```python
def calc_dot_damage(target_max_hp, dot_ratio, stack_count=1, target_def=0.0) -> int:
    mitigation = target_def / (target_def + 300.0)
    raw = target_max_hp * dot_ratio * stack_count * (1.0 - mitigation)
    return max(1, math.floor(raw))
```

```
DoT 피해 = floor(maxHP × dot_ratio × stacks × (1 - DEF/(DEF+300)))
최솟값: 1
```

DEF 경감 예시:
- DEF=120 (ATTACKER): mitigation = 120 / 420 = 28.6% 경감
- DEF=240 (DEFENDER): mitigation = 240 / 540 = 44.4% 경감

**실제 수치 예시** — 화상 15%(dot_ratio=0.15) vs ATTACKER(maxHP=4000, DEF=120):
```
mitigation = 120 / (120+300) = 0.286
DoT = floor(4000 × 0.15 × 1 × (1-0.286))
    = floor(4000 × 0.15 × 0.714)
    = floor(428.4) = 428
```

### 9.4 스택 규칙

```python
# buff_manager.py apply_buff에서 호출되는 battle_unit.py apply_buff

for ab in self.active_buffs:
    if ab.buff_data.source_skill_id == buff_data.source_skill_id and ab.buff_data.id == buff_data.id:
        if is_dot:
            if ab.stack_count < buff_data.max_stacks:
                ab.stack_count += 1   # 스택 증가
            ab.remaining_turns = buff_data.duration  # 지속시간 갱신
```

- **동일 출처** (source_skill_id 동일): 스택 증가 + 지속시간 갱신
- **다른 출처**: 독립적인 새 DoT 인스턴스 추가 (무한 중첩 가능)
- 최대 스택: `max_stacks`로 제한 (일반적으로 3)

### 9.5 태그 시스템과 burn 태그 카운팅

화상 DoT 부여 시 `burn` 태그가 추가된다. 이 태그 카운트가 burn_bonus 계산에 사용된다.

```python
# buff_manager.py
if buff_data.logic_type == LogicType.DOT and buff_data.dot_type == "burn":
    unit.add_tag("burn", 1)
    # → unit._tags["burn"] += 1
```

화상 DoT 만료 시 태그 제거:
```python
for e in expired:
    buff = e.get('buff')
    if buff and buff.buff_data.logic_type == LogicType.DOT and buff.buff_data.dot_type == "burn":
        for _ in range(buff.stack_count):
            unit.remove_tag("burn")
```

`burn` 태그 카운트 = 현재 활성 화상 스택 수

---

## 10. 버프/디버프 생명주기 (BuffManager)

> 소스: `src/battle/buff_manager.py`, `src/battle/battle_unit.py`

### 10.1 적용 (apply_buff)

```
apply_buff(unit, buff_data, source_unit_id)
    │
    ├─ old_spd 기록 (SPD 변화 감지용)
    │
    ├─ unit.apply_buff() 호출
    │      ├─ [동일 source_skill_id + 동일 buff_id 존재]
    │      │      ├─ DoT: stack_count +1 (max_stacks 이하)
    │      │      │        remaining_turns = duration (갱신)
    │      │      └─ 기타: remaining_turns = duration (갱신)
    │      │         return False (갱신)
    │      │
    │      └─ [새 버프]
    │             active_buffs.append(ActiveBuff(...))
    │             return True (신규 추가)
    │
    ├─ [CC 타입] unit.apply_cc() 호출
    │
    ├─ [DOT + burn] unit.add_tag("burn", 1) 호출
    │
    └─ [SPD 변화 감지] TurnManager.on_spd_change() 호출
```

### 10.2 틱 — 턴 시작 (tick_turn_start)

`CharacterTurnStart` 타이밍 버프 처리 (DoT/HoT 계열):

```
tick_turn_start(unit)
    │
    ├─ 1. _apply_dots(unit)      ← DoT/HoT 틱 발동 (현재 스택 기준)
    │
    └─ 2. on_turn_start_tick()   ← CharacterTurnStart 버프 remaining_turns -1
               만료된 버프 제거 + burn 태그 정리
```

### 10.3 틱 — 턴 종료 (tick_turn_end)

`CharacterTurnEnd` 타이밍 버프 처리 (스탯 버프/CC/쿨타임 계열):

```
tick_turn_end(unit)
    │
    ├─ 1. on_turn_end()          ← CharacterTurnEnd 버프 remaining_turns -1
    │         만료된 버프 제거
    │
    ├─ 2. tick_cc()              ← Hard/Soft CC 지속시간 -1
    ├─ 3. tick_cooldown()        ← Active/Ultimate 쿨타임 -1
    └─ 4. tick_taunt()           ← 도발 지속시간 -1
```

### 10.4 만료 처리

`remaining_turns`가 0 이하가 되면 `active_buffs`에서 제거된다.
SPD 버프가 만료되면 `TurnManager.on_spd_change()`를 통해 턴 큐가 자동 재계산된다.

### 10.5 스탯 반영

스탯은 캐시 없이 **실시간 합산**으로 계산된다 (`_get_buff_delta`):

```python
@property
def atk(self) -> float:
    return max(1.0, self.data.stats.atk + self._get_buff_delta("atk"))

def _get_buff_delta(self, stat: str) -> float:
    total = 0.0
    base = getattr(self.data.stats, stat, 0.0)
    for ab in self.active_buffs:
        bd = ab.buff_data
        if bd.logic_type == LogicType.STAT_CHANGE and bd.stat == stat:
            if bd.is_ratio:
                total += base * bd.value * ab.stack_count  # 기본 스탯의 비율
            else:
                total += bd.value * ab.stack_count          # 절대값
    return total
```

**스탯 최솟값 보장**:
- `atk`: max(1.0, ...)
- `def_`: max(0.0, ...)
- `spd`: max(25.0, ...)
- `cri_ratio`: min(1.0, max(0.0, ...))
- `cri_dmg_ratio`: max(1.0, ...)

### 10.6 is_ratio vs 절대값

| `is_ratio` | 계산 방식 | 예시 |
|-----------|---------|-----|
| `True` | `base × value` | ATK +20% → delta = base_atk × 0.20 |
| `False` | `value` 직접 | ATK +100 → delta = 100 |

### 10.7 buff_turn_reduce_timing 타이밍 구분

| 값 | 감소 타이밍 | 해당 버프 종류 |
|---|----------|-------------|
| `"CharacterTurnStart"` | 턴 시작 시 (tick_turn_start) | DoT, HoT (틱 발동 후 감소) |
| `"CharacterTurnEnd"` | 턴 종료 시 (tick_turn_end) | 스탯 버프, CC, 쿨타임 마커 등 |

기본값은 `"CharacterTurnEnd"` (`BuffData.buff_turn_reduce_timing` 기본값).

---

## 11. 타겟 선택 시스템 (TargetSelector)

> 소스: `src/battle/target_selector.py`

### 11.1 3×3 타일 그리드

두 진영이 서로 마주보는 3×3 그리드로 배치된다.

```
아군 진영               적군 진영
┌─────────────────┐   ┌─────────────────┐
│ (0,0) (0,1) (0,2)│   │(0,0) (0,1) (0,2)│
│ 전열  전열  전열 │◄─►│전열  전열  전열  │
├─────────────────┤   ├─────────────────┤
│ (1,0) (1,1) (1,2)│   │(1,0) (1,1) (1,2)│
│ 중열  중열  중열 │   │중열  중열  중열  │
├─────────────────┤   ├─────────────────┤
│ (2,0) (2,1) (2,2)│   │(2,0) (2,1) (2,2)│
│ 후열  후열  후열 │   │후열  후열  후열  │
└─────────────────┘   └─────────────────┘
row 0=전열, 1=중열, 2=후열
col 0=좌,   1=중,   2=우
```

`tile_pos = (row, col)` — `CharacterData.tile_pos`에 저장된다.

### 11.2 타일 거리 계산

```python
@staticmethod
def _tile_distance(caster: BattleUnit, target: BattleUnit) -> int:
    return caster.tile_row + target.tile_row + abs(caster.tile_col - target.tile_col)
```

```
거리 = caster.row + target.row + |caster.col - target.col|
```

양 진영의 row 0끼리(전열 대 전열)가 가장 가깝다.
동거리일 때는 HP가 낮은 유닛을 우선 선택한다.

**거리 예시**:
- 아군 (0,1) vs 적군 (0,1): 거리 = 0+0+0 = 0
- 아군 (0,1) vs 적군 (0,0): 거리 = 0+0+1 = 1
- 아군 (0,1) vs 적군 (2,1): 거리 = 0+2+0 = 2
- 아군 (2,2) vs 적군 (2,0): 거리 = 2+2+2 = 6

### 11.3 TargetType 전체 설명 테이블

| TargetType | 선택 대상 | 비고 |
|-----------|---------|------|
| `SELF` | 시전자 자신 | 도발 무시 |
| `ALLY_LOWEST_HP` | 아군 중 HP 비율 최소 1명 | 도발 무시 |
| `ALLY_HIGHEST_ATK` | 아군 중 ATK 최고 1명 | 도발 무시 |
| `ALL_ALLY` | 아군 전체 | 도발 무시 |
| `ALLY_LOWEST_HP_2` | 아군 중 HP 낮은 순 2명 | 도발 무시 |
| `ALLY_ROLE_ATTACKER` | 아군 ATTACKER 역할 전체 | 없으면 전체 아군 |
| `ALLY_ROLE_DEFENDER` | 아군 DEFENDER 역할 전체 | 없으면 전체 아군 |
| `ALLY_DEAD_RANDOM` | 사망한 아군 1명 (랜덤) | 부활 스킬 전용 |
| `ALLY_SAME_ROW` | 시전자와 같은 행(row)의 아군 (자신 제외) | 도발 무시 |
| `ALLY_BEHIND` | 시전자 바로 뒤 1칸 (row+1, 같은 col) | 없으면 [] |
| `ENEMY_LOWEST_HP` | 적 중 현재 HP 최소 1명 | 도발 강제 |
| `ENEMY_HIGHEST_HP` | 적 중 현재 HP 최대 1명 | 도발 강제 |
| `ENEMY_HIGHEST_SPD` | 적 중 SPD 최고 1명 | 도발 강제 |
| `ENEMY_RANDOM` | 적 중 랜덤 1명 | 도발 강제 |
| `ALL_ENEMY` | 적 전체 | 도발 강제 포함 |
| `ENEMY_RANDOM_2` | 적 중 랜덤 최대 2명 | |
| `ENEMY_RANDOM_3` | 적 중 랜덤 최대 3명 | |
| `ENEMY_NEAR` | 타일 거리 가장 가까운 적 1명 | 동거리 시 HP 낮은 쪽 |
| `ENEMY_NEAR_ROW` | 가장 가까운 적 + 해당 적의 동일 행 전체 | |
| `ENEMY_NEAR_CROSS` | 가장 가까운 적 + 십자 형태 인접 1칸 | |
| `ENEMY_FRONT_ROW` | 적 생존자 중 최전열(row 최솟값) 전체 | |
| `ENEMY_BACK_ROW` | 적 생존자 중 최후열(row 최댓값) 전체 | |
| `ENEMY_LAST_COL` | 적 생존자 중 최우열(col 최댓값) 전체 | |
| `ENEMY_SAME_COL` | 시전자와 동일 열(col)의 적 전체 | 없으면 전체 적 |
| `ENEMY_ADJACENT` | 시전자 기준 ±1행·±1열 인접 타일의 적 | 없으면 전체 적 |

### 11.4 도발(Taunt) 강제 타겟팅 규칙

```python
def _apply_taunt(self, caster, selected, alive_enemies, target_type):
    if not caster.taunted_by:
        return selected

    taunter = next((u for u in alive_enemies if u.id == caster.taunted_by), None)
    if taunter is None:
        caster.taunted_by = None
        return selected

    # 아군 타겟 스킬은 도발 무시
    if target_type in _ALLY_TARGET_TYPES:
        return selected

    # 단일 타겟 → 도발자로 강제 교체
    if target_type in (ENEMY_NEAR, ENEMY_LOWEST_HP, ENEMY_HIGHEST_HP,
                       ENEMY_HIGHEST_SPD, ENEMY_RANDOM):
        return [taunter]

    # 다중 타겟 → 도발자 반드시 포함 (없으면 추가)
    if taunter not in selected:
        selected = list(selected) + [taunter]
    return selected
```

- 도발자가 사망하면 `taunted_by = None`으로 자동 해제
- 아군 타겟 스킬(SELF, ALL_ALLY 등)은 도발의 영향을 받지 않음

---

## 12. 트리거 시스템 (TriggerSystem)

> 소스: `src/battle/trigger_system.py`, `src/battle/models.py`

### 12.1 활성 이벤트 (실제 와이어링됨)

| 이벤트 | 발동 시점 | 발동 위치 |
|--------|---------|---------|
| `ON_BATTLE_START` | 전투 시작 직후 | `evaluate_battle_start()` |
| `ON_ROUND_START` | 배틀 라운드 전환 시 | `evaluate_round_start()` |
| `ON_HIT` | 피격 직후 (DAMAGE 로직 처리 후) | `evaluate_on_hit(defender, ...)` |
| `ON_KILL` | 킬 발생 시 | `evaluate_on_kill(killer, ...)` |
| `ON_TURN_END` | 턴 종료 시 | `evaluate(ON_TURN_END, unit, ...)` |

### 12.2 정의만 있는 이벤트 (미와이어링)

열거형에 정의되어 있으나 `battle_engine.py`에서 아직 발동되지 않는 이벤트:

| 이벤트 | 예상 발동 시점 |
|--------|-------------|
| `ON_TURN_START` | 턴 시작 시 |
| `ON_ATTACK` | 공격 시 (피격 역방향) |
| `ON_DEATH` | 사망 시 |
| `ON_HP_THRESHOLD` | HP가 특정 % 이하로 하락 시 |
| `ON_BURN_APPLIED` | 화상 부여 시 |
| `ON_STATUS_APPLIED` | 상태이상 부여 시 |

### 12.3 TriggerData 구조

```python
@dataclass
class TriggerData:
    event: TriggerEvent
    condition: Optional[Dict[str, Any]] = None
    # 조건 키:
    # - hp_threshold: float → 자신 HP% 이하일 때
    # - tag: str + count: int → 태그 N 이상 스택 시
    # - burn_stack_min: int → 적 화상 스택 N 이상일 때
    # - target_has_burn: bool → 타겟(피해자)이 화상 상태일 때
    skill_id: Optional[str] = None     # 발동할 스킬 ID
    buff_id: Optional[str] = None      # 부여할 버프 ID
    once_per_battle: bool = False      # 전투당 1회 제한
```

### 12.4 조건 평가 (_check_condition)

```python
def _check_condition(self, unit, trigger, ctx, extra):
    cond = trigger.condition
    if not cond:
        return True

    # HP 임계값
    if 'hp_threshold' in cond:
        if unit.hp_ratio > cond['hp_threshold']:
            return False

    # 태그 스택
    if 'tag' in cond:
        tag = cond['tag']
        min_count = cond.get('count', 1)
        if unit.get_tag_count(tag) < min_count:
            return False

    # 적의 화상 스택 (전체 적 중 최대값)
    if 'burn_stack_min' in cond:
        enemies = ctx.get_enemies_of(unit)
        max_burn = max((e.get_tag_count('burn') for e in enemies), default=0)
        if max_burn < cond['burn_stack_min']:
            return False

    # 타겟이 화상 상태 (ON_KILL의 killed, ON_HIT의 attacker 기준)
    if cond.get('target_has_burn') and extra:
        target = extra.get('killed') or extra.get('attacker')
        if target and target.get_tag_count('burn') == 0:
            return False

    return True
```

### 12.5 발동 흐름

```
이벤트 발생 (예: 피격)
    │
    └─ evaluate(ON_HIT, defender, ctx, extra={'attacker': attacker})
             │
             └─ unit.data.triggers 순회
                     │
                     ├─[trigger.event != ON_HIT] → SKIP
                     │
                     ├─[once_per_battle + was_triggered()] → SKIP
                     │
                     ├─ _check_condition() → False → SKIP
                     │
                     └─[조건 충족]
                             ├─ mark_triggered() (once_per_battle인 경우)
                             ├─[skill_id] → _find_skill() → executor.execute()
                             └─[buff_id] → _find_buff() → buff_manager.apply_buff()
```

### 12.6 once_per_battle 중복 방지

```python
# 트리거 키: "{unit_id}_{event_value}_{skill_id}"
trigger_key = f"{unit.id}_{trigger.event.value}_{trigger.skill_id}"

if trigger.once_per_battle and unit.was_triggered(trigger_key):
    continue  # 이미 발동됨

# 발동 후:
if trigger.once_per_battle:
    unit.mark_triggered(trigger_key)
    # → self._triggered_once.add(trigger_key)
```

---

## 13. 조건부 스킬 효과

> 소스: `src/battle/skill_executor.py`

### 13.1 target_hp_below (처형 보너스)

타겟의 HP 비율이 지정값 이하일 때만 해당 Effect를 적용한다.

```python
if 'target_hp_below' in effect.condition:
    if target.hp_ratio > effect.condition['target_hp_below']:
        return  # 타겟 HP 조건 미달 → Effect 스킵
```

**실제 예시** — 이브의 "레인 드랍":
```
effects:
  1) DMG 4.00x  (무조건)
  2) DMG 3.00x  (condition: target_hp_below=0.25 → HP 25% 이하 시만 발동)
```

HP 25% 이하 타겟에게는 총 7.00x 데미지 (4.00 + 3.00).

**이브의 얼티밋 "실낙원"**:
```
effects:
  1) DMG 5.00x  (무조건)
  2) DMG 2.00x  (condition: target_hp_below=0.25)
```

HP 25% 이하 타겟에게는 총 7.00x 데미지 (5.00 + 2.00).

### 13.2 burn_bonus_per_stack (화상 스택 비례 추가 피해)

`effect.condition['burn_bonus_per_stack']` 값이 있으면 타겟의 화상 스택 수에 비례하여
최종 데미지 배율이 상승한다.

```python
burn_bonus = effect.condition.get('burn_bonus_per_stack', 0.0)
dmg, is_crit, is_dodged = compute_damage(caster, target, effect.multiplier, burn_bonus)
```

`compute_damage` 내부:
```python
burn_stack = defender.get_tag_count("burn") if burn_bonus_per_stack > 0 else 0
burn_bonus = get_burn_bonus_mult(burn_stack, burn_bonus_per_stack)
# = 1.0 + bonus_per_stack × burn_stack
```

**실제 예시** — 카라라트리의 "무기법" (burn_bonus_per_stack=0.30):
```
화상 0스택: Final = floor(Base × 3.00 × ElemMult × CritMult × 1.0)
화상 1스택: Final = floor(Base × 3.00 × ElemMult × CritMult × 1.3)
화상 2스택: Final = floor(Base × 3.00 × ElemMult × CritMult × 1.6)
화상 3스택: Final = floor(Base × 3.00 × ElemMult × CritMult × 1.9)
```

### 13.3 requires_burn (화상 보유 적 대상 조건)

적 중 화상 상태인 유닛이 **1명 이상** 있을 때만 해당 Effect를 적용.

```python
if 'requires_burn' in condition:
    enemies = ctx.get_enemies_of(caster)
    has_burn = any(e.get_tag_count('burn') > 0 for e in enemies)
    if condition['requires_burn'] and not has_burn:
        return False
```

### 13.4 requires_tag (태그 보유 조건)

시전자 자신이 특정 태그를 N개 이상 보유할 때만 Effect 적용.

```python
if 'requires_tag' in condition:
    tag = condition['requires_tag']
    min_count = condition.get('tag_min_count', 1)
    if caster.get_tag_count(tag) < min_count:
        return False
```

### 13.5 hp_threshold (자신 HP% 이하 조건)

시전자 자신의 HP 비율이 지정값 이하일 때만 Effect 적용.

```python
if 'hp_threshold' in condition:
    if caster.hp_ratio > condition['hp_threshold']:
        return False
```

**예시**: `hp_threshold=0.5` → 시전자 HP 50% 이하일 때만 추가 효과 발동.

---

## 14. 반격 시스템

> 소스: `src/battle/skill_executor.py`

### 14.1 COUNTER LogicType: 반격 준비 마커 버프

`LogicType.COUNTER`를 실행하면 `counter_burn_active` ID를 가진 마커 버프를 부여한다.
이 버프는 실제 스탯 변화 없이 **반격 준비 상태 플래그** 역할만 한다.

```python
elif logic == LogicType.COUNTER:
    duration = int(effect.value) if effect.value else 2
    counter_marker = BuffData(
        id="counter_burn_active",
        name="화상반격",
        source_skill_id=skill.id,
        logic_type=LogicType.STAT_CHANGE,
        stat="def_",
        value=0,          # 스탯 변화 없음
        duration=duration,
        is_debuff=False,
    )
    ctx.buff_manager.apply_buff(target, counter_marker, caster.id)
```

### 14.2 화상반격 발동 흐름

피격(DAMAGE) 처리 중 `counter_burn_active` 버프 확인 → 공격자에게 화상 부여:

```python
# DAMAGE 처리 이후:
elif target.is_alive and any(
    ab.buff_data.id == "counter_burn_active" for ab in target.active_buffs
):
    counter_burn = BuffData(
        id="counter_burn_proc",
        name="화상(반격)",
        source_skill_id="counter_proc",
        logic_type=LogicType.DOT,
        dot_type="burn",
        value=0.05,       # maxHP 5% DoT
        duration=1,
        is_debuff=True,
        max_stacks=5,
    )
    ctx.buff_manager.apply_buff(caster, counter_burn, target.id)
    # caster = 공격자, target = 반격 시전자
```

발동 순서:
```
공격자 → 반격자 피격
    │
    ├─ take_damage() 처리
    ├─ ON_HIT 트리거 평가
    └─ counter_burn_active 버프 존재 확인
           └─ 공격자에게 화상(5% maxHP DoT, 1턴, 최대5스택) 부여
```

### 14.3 ON_HIT 트리거 기반 반격

`TriggerSystem.evaluate_on_hit()`으로 Normal 스킬을 자동 발동하는 패시브 반격도 가능:

```python
# 발동 조건 예시:
TriggerData(
    event=TriggerEvent.ON_HIT,
    condition=None,                  # 무조건 발동
    skill_id="normal_skill_id",      # 기본 공격 자동 발동
    once_per_battle=True,            # 전투당 1회만
)
```

### 14.4 무한 루프 방지

- `once_per_battle=True`: 전투당 1회만 발동 (`_triggered_once` 집합으로 추적)
- `MAX_EXTRA_TURNS=100`: Extra Turn 최대 횟수 제한
- 화상반격은 Extra Turn 없이 즉시 버프만 부여 (추가 행동 없음)

---

## 15. 속성 상성 테이블

> 소스: `src/battle/damage_calc.py`

```python
ELEMENT_TABLE: dict[tuple, float] = {
    # Win (유리 상성): +20%
    (Element.WATER,  Element.FIRE):   1.2,
    (Element.FIRE,   Element.FOREST): 1.2,
    (Element.FOREST, Element.WATER):  1.2,
    (Element.LIGHT,  Element.DARK):   1.2,
    (Element.DARK,   Element.LIGHT):  1.2,
    # Lose (불리 상성): -20%
    (Element.FIRE,   Element.WATER):  0.8,
    (Element.FOREST, Element.FIRE):   0.8,
    (Element.WATER,  Element.FOREST): 0.8,
}
```

| 공격 \ 방어 | 화(FIRE) | 수(WATER) | 목(FOREST) | 광(LIGHT) | 암(DARK) | 무(NONE) |
|------------|---------|---------|---------|---------|---------|---------|
| **화(FIRE)** | 1.0 | 0.8 | **1.2** | 1.0 | 1.0 | 1.0 |
| **수(WATER)** | **1.2** | 1.0 | 0.8 | 1.0 | 1.0 | 1.0 |
| **목(FOREST)** | 0.8 | **1.2** | 1.0 | 1.0 | 1.0 | 1.0 |
| **광(LIGHT)** | 1.0 | 1.0 | 1.0 | 1.0 | **1.2** | 1.0 |
| **암(DARK)** | 1.0 | 1.0 | 1.0 | **1.2** | 1.0 | 1.0 |
| **무(NONE)** | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 |

**순환 상성 (삼각 관계)**:
```
화(FIRE) → 목(FOREST) → 수(WATER) → 화(FIRE)
  (화가 목에게 유리)  (목이 수에게 유리)  (수가 화에게 유리)
```

**광·암 상성 (양방향 하이리스크·하이리턴)**:
```
광(LIGHT) ↔ 암(DARK): 양쪽 모두 서로에게 1.2x
```

광·암은 서로 공격할 때 항상 유리 상성이 적용된다.
불리 상성(0.8x)은 화↔수↔목 삼각 관계에서만 발생하며, 광·암에는 불리 상성이 없다.

**실전 적용 예시**:
- 이브(수속성, ATK=800) → 카라라트리(화속성): `elem_mult = 1.2` (수가 화에게 유리)
- 카라라트리(화속성) → 이브(수속성): `elem_mult = 0.8` (화가 수에게 불리)
- 광속성 캐릭터 → 암속성 적: `elem_mult = 1.2` (항상 유리)

---

## 부록: 역할별 기본 스탯 (rules.py 기준)

| 역할 | ATK | DEF | HP | SPD | SP 비용 |
|------|-----|-----|-----|-----|--------|
| ATTACKER | 420 | 120 | 5100 | 80 | 6 |
| MAGICIAN | 341 | 108 | 4743 | 100 | 4 |
| SUPPORTER | 198 | 142 | 5909 | 120 | 4 |
| DEFENDER | 252 | 240 | 8650 | 110 | 3 |
| HEALER | 168 | 151 | 6475 | 90 | 3 |

> 개별 캐릭터는 역할 기본값에서 ±조정된 고유 스탯을 보유할 수 있다.
> 등급별 스케일링: 3.5성=1.15, 3성=1.00, 2성=0.75, 1성=0.50

## 부록: 주요 캐릭터 데이터

### 카라라트리 (c445)
- 속성: 화 / 역할: ATTACKER / 등급: 3.5
- ATK=800, DEF=400, HP=4000, SPD=80, SP비용=6
- **기본공격 "무기법"**: ENEMY_NEAR, DMG 3.00x + burn_bonus 30%/스택
- **액티브 "무루의 고통"**: ENEMY_NEAR_ROW, DMG 3.60x + 화상 15% 2턴
- **얼티밋 "출세간의 선법"**: ALL_ENEMY, DMG 2.60x + DEF -20% 2턴

### 이브 (c124)
- 속성: 수 / 역할: ATTACKER / 등급: 3.5
- ATK=800, DEF=400, HP=4000, SPD=80, SP비용=6
- **기본공격 "다크 미스트"**: ENEMY_NEAR, DMG 3.60x
- **액티브 "레인 드랍"**: ENEMY_LOWEST_HP, DMG 4.00x + DMG 3.00x (HP<25% 처형)
- **얼티밋 "실낙원"**: ENEMY_LOWEST_HP, DMG 5.00x + DMG 2.00x (HP<25% 처형)

---

## 16. 원본 기획 로직 전체 명세 (Buff.xlsx + LogicFormula.xlsx + Notion)

> **출처**: LogicFormula.xlsx (XML 공식), Buff.xlsx (버프/디버프 목록), Notion "로직" 페이지
> **목적**: 원본 게임 기획 전체 로직을 문서화. 시뮬레이터 미구현 항목 포함.
> **스케일 주의**: 원본 게임은 정수 기반 ×0.00001 스케일 사용. 시뮬레이터는 실수 기반.

---

### 16.1 데미지 계산 원본 공식 (LogicFormula.xlsx)

#### LogicDamage (일반 대미지)

```
최종대미지 =
  ATK
  × (1 - max(DEF - Penetration, 0) / (ATK + max(DEF - Penetration, 0)))
  × (LogicValue × 0.00001)
  × DamageMultiplier
  × BattleDmgRatio
  × max(1 + SkillDmgRatio×0.00001   - SkillDmgReduceRatio×0.00001,   0)
  × max(1 + BossDmgRatio×0.00001    - BossDmgReduceRatio×0.00001,    0)
  × max(1 + MonsterDmgRatio×0.00001 - MonsterDmgReduceRatio×0.00001, 0)
  × max(1 + PvPDmgRatio×0.00001     - PvPDmgReduceRatio×0.00001,     0)
  × max(ElementUpper, 0) × 0.00001
  × HittedDmgRatio
```

**DamageMultiplier 분기:**
| 스킬 종류 | 적용 비율 |
|-----------|-----------|
| Normal (기본공격) | NormalDamageRatio |
| Active (액티브) | ActiveDamageRatio |
| Ultimate (얼티밋) | UltimateDamageRatio |

- **CRI 체크**: O (크리티컬 발동 가능)
- **회피 체크**: O
- **무적 적용**: 무적 상태 대상은 HP 미감소, "무적" 표기

---

#### LogicDamagePenetration (방어 무시 대미지)

```
최종대미지 =
  ATK
  × (LogicValue × 0.00001)
  × DamageMultiplier
  × BattleDmgRatio
  × max(1 + SkillDmgRatio×0.00001   - SkillDmgReduceRatio×0.00001,   0)
  × max(1 + BossDmgRatio×0.00001    - BossDmgReduceRatio×0.00001,    0)
  × max(1 + MonsterDmgRatio×0.00001 - MonsterDmgReduceRatio×0.00001, 0)
  × max(1 + PvPDmgRatio×0.00001     - PvPDmgReduceRatio×0.00001,     0)
  × max(ElementUpper, 0) × 0.00001
  × HittedDmgRatio
```

- DEF 공식 항목 없음 (방어력 완전 무시)
- **CRI 체크**: O
- **회피 체크**: O

---

#### LogicDamageHpRatio (HP 비례 대미지)

```
최종대미지 =
  Target.HP
  × (LogicValue × 0.00001)
  × DamageMultiplier
  × BattleDmgRatio
  × (동일 비율 스탯 체인 ...)
  × HittedDmgRatio
```

- **CRI 체크**: X (크리티컬 발동 불가)
- **회피 체크**: O
- 현재 HP 기준 비율 적용

---

#### LogicCriDamage (강제 크리티컬 대미지)

- LogicDamage 공식과 동일
- 크리티컬 확률 계산 없이 **무조건 크리티컬** 적용
- **CRI 체크**: 강제 (확률 무관)
- **회피 체크**: O

---

#### LogicHeal (ATK 비례 회복)

```
회복량 =
  Caster.ATK
  × (LogicValue × 0.00001)
  × (1 + HealingReceived × 0.00001)
  × (1 + HealingDoneRatio × 0.00001)
```

- **CRI 체크**: O (크리티컬 힐 가능)
- 보호막(Barrier)은 회복되지 않음
- HealingReceived: 대상의 받는 힐량 증가 스탯
- HealingDoneRatio: 시전자의 주는 힐량 증가 스탯

---

#### LogicHealRatio (HP 비례 회복)

```
회복량 =
  Target.HP
  × (LogicValue × 0.00001)
  × (1 + HealingReceived × 0.00001)
  × (1 + HealingDoneRatio × 0.00001)
```

- 대상의 현재 HP 기준 비율 회복
- **CRI 체크**: O

---

#### LogicBarrier (ATK 비례 보호막)

```
보호막량 = Caster.ATK × (LogicValue × 0.00001)
```

---

#### LogicBarrierRatio (HP 비례 보호막)

```
보호막량 = Target.HP × (LogicValue × 0.00001)
```

---

#### LogicRevive (부활)

```
부활 HP = Target.MaxHP × (LogicValue × 0.00001)
```

- 배치 시작 위치에 부활
- 해당 위치가 빈칸이 아닐 경우 부활 취소

---

#### LogicDot (지속 효과)

```
매 배틀턴 종료 시 발동량 = Caster.ATK × (LogicValue × 0.00001)
```

- Tag: `Dmg` (지속 대미지) / `Heal` (지속 회복) 구분

---

#### LogicStatChange (스탯 증감)

```
적용 수치 = LogicValue0 (직접 수치)
대상 스탯 = LogicValue1 (스탯 Enum ID)
```

- ×0.00001 스케일링 없음. 직접 수치 적용.

---

### 16.2 전체 로직 타입 명세 (Notion 기준)

#### 즉시 발동형

| 로직 타입 | 설명 | CRI | 회피 | 비고 |
|-----------|------|-----|------|------|
| **LogicDamage** | 대상에게 대미지 | O | O | 무적 시 "무적" 표기 |
| **LogicDamageHpRatio** | 대상 현재 HP 비례 대미지 | X | O | |
| **LogicDamagePenetration** | 방어력 무시 대미지 | O | O | DEF 계산 스킵 |
| **LogicCriDamage** | 무조건 크리티컬 대미지 | 강제 | O | 크리 확률 무관 |
| **LogicHeal** | 시전자 ATK 비례 회복 | O | - | 보호막 미회복 |
| **LogicHealRatio** | 대상 HP 비례 회복 | O | - | |
| **LogicRemoveBuffCount** | 버프/디버프 제거 | - | - | LogicValue개만큼 최근 순서대로 제거 |
| **LogicRevive** | 부활 | - | - | 배치 시작 위치, 빈칸 아닐 시 취소 |
| **UseSkill** | 스킬 발동 | - | - | LogicValue=스킬 ID |
| **LogicDamageBuffScale** | 시전자 보유 버프 수 비례 대미지 | O | O | Limit 값 존재 |
| **LogicDamageBuffScaleTarget** | 타겟 보유 버프 수 비례 대미지 | O | O | |
| **LogicDamageDebuffScaleTarget** | 타겟 보유 디버프 수 비례 대미지 | O | O | |
| **LogicSpSteal** | SP 강탈 | - | - | 타겟 SP 감소 → 시전자 SP 증가. 부족 시 현재값만 |
| **LogicSpIncrease** | SP 즉시 충전 | - | - | 최대값 초과 불가 |
| **LogicBuffTurnIncrease** | 현재 버프 Max턴 증가 | - | - | |
| **LogicDeBuffTurnIncrease** | 현재 디버프 Max턴 증가 | - | - | |
| **LogicHealLossScaleHp** | 잃은 HP의 Value% 회복 | - | - | (MaxHP - CurHP) × Value% |
| **LogicAllyScaleHeal** | 배치 아군 직업/속성 수 비례 회복 | - | - | 아군 구성에 따라 회복량 변동 |

---

#### 상태 변경형 (버프/디버프)

| 로직 타입 | 설명 | 분류 | 비고 |
|-----------|------|------|------|
| **LogicStatChange** | 스탯 증감 | 버프/디버프 | LogicValue0=수치, LogicValue1=스탯 Enum |
| **LogicBarrier** | ATK 비례 보호막 부여 | 버프 | 초과 대미지 → HP 감소, 중첩 규칙 있음 |
| **LogicBarrierRatio** | HP 비례 보호막 부여 | 버프 | LogicBarrier와 동일 중첩 규칙 |
| **LogicDot** | 지속 효과 | 버프/디버프 | 배틀턴 종료마다 발동. Tag: Dmg/Heal |

---

#### CC (행동 불가) 상태이상

| 로직 타입 | 설명 | 해제 조건 | 비고 |
|-----------|------|-----------|------|
| **LogicStun** | 행동불가 | 턴 만료 | 전용 애니메이션/VFX |
| **LogicSleep** | 행동불가 | 턴 만료 또는 피격 | 피격 시 즉시 해제 |
| **LogicFreeze** | 행동불가 + 정지 | 피격 시 Value% 확률 해제 | 모션 정지 포함 |
| **LogicStone** | 행동불가 + 정지 | 피격 시 Value% 확률 해제 | 모션 정지 포함 |
| **LogicElectricshock** | 30% 확률 스킬 취소 | 턴 만료 | 스킬 시전 시 확률 체크 |
| **LogicPanic** | 30% 확률 스킬 취소 | 턴 만료 | LogicElectricshock과 동일 작동 |
| **LogicAbnormalSkill** | 스킬 사용 불가 | 턴 만료 | Normal 포함 전체 스킬 봉인 |
| **LogicConfused** | 혼란 | 턴 만료 | Normal 타겟 무작위, Active 사용 불가, Ultimate 정상 |
| **LogicBlind** | 실명 | 턴 만료 | 적중 0 고정, 적중 스탯 변화 무시 |
| **LogicSilence** | 침묵 | 턴 만료 | Normal 스킬만 사용 가능 |

---

#### 특수 효과

| 로직 타입 | 설명 | 비고 |
|-----------|------|------|
| **LogicTaunt** | 도발 - 타겟 강제 변경 | 이후 도발이 덮어쓰기 |
| **LogicSpLock** | SP 충전량 0 고정 | |
| **LogicInvincibility** | 무적 - HP 미감소 | "무적" 표기 출력 |
| **LogicUndying** | 불사 - HP 1 미만 불가 | |
| **LogicDebuffImmune** | 디버프 면역 | 추가 디버프 무시, 기존 유지, 버프 제거 효과도 무시 |
| **LogicCounterUnavailable** | 반격 확률 0 고정 | |
| **LogicCriUnavailable** | 크리 확률 0 고정 | |
| **LogicStop** | 정지 - 애니메이션 정지 | 해제 시 idle 상태로 복귀 |

---

#### 반격 무시 효과

| 로직 타입 | 설명 |
|-----------|------|
| **LogicNormalIgnoreCounter** | Normal 공격 시 반격 확률 0 |
| **LogicActiveIgnoreCounter** | Active 공격 시 반격 확률 0 |
| **LogicUltimateIgnoreCounter** | Ultimate 공격 시 반격 확률 0 |

---

#### 고급 스탯 / 조건부 효과

| 로직 타입 | 설명 | 비고 |
|-----------|------|------|
| **LogicAllyScaleStatusChange** | 아군 직업/속성 수 비례 스탯 변화 | 파티 구성에 따라 증폭 |
| **LogicStatusChangeApplyAnotherStatusRate** | 다른 스탯의 N% 만큼 스탯 증가 | 예: 방어력의 10% 만큼 공격력 증가 |
| **LogicActiveSkillTurnChangeOnce** | 액티브 쿨타임 즉시 변경 | 1회성 |
| **LogicSpdTwist** | 전체 캐릭터 속도 반전 | 빠른 캐릭터가 느려지고 느린 캐릭터가 빨라짐 |
| **LogicDamageCriApplyDebuff** | 특정 Tag 보유 대상에게 무조건 크리 | Tag 조건 충족 시에만 강제 크리 |
| **LogicStatusChangeEveryTurn** | 매 턴 종료 시 Tag 수 기준 스탯 변경 | |
| **LogicStatusChangeElementCount** | 아군 속성 종류 수 비례 스탯 변경 | 속성 다양성에 따라 증폭 |
| **LogicStatusChangeRemainingHpPercent** | HP 비율 높을수록 스탯 증가 | 풀피에 가까울수록 강함 |
| **LogicStatusChangeMissingHpPercent** | HP 비율 낮을수록 스탯 증가 | 빈사에 가까울수록 강함 |
| **LogicHealTargetCount** | 적중 대상 수 비례 회복 | 다수 타겟일수록 힐량 증가 |
| **LogicIgnoreElementUpper** | 속성 상성 무시 | ElementUpper 100000(=1.0) 고정 |

---

#### 삭제 / 미사용 로직 타입

> 원본 기획에서 취소선(~~삭제~~) 처리된 항목. 게임에 미구현 또는 제거됨.

| 로직 타입 | 비고 |
|-----------|------|
| ~~LogicWeather~~ | 삭제/미사용 |
| ~~LogicIgnoreDmg~~ | 삭제/미사용 |
| ~~LogicAbnormalMove~~ | 삭제/미사용 |
| ~~LogicPause~~ | 삭제/미사용 |
| ~~LogicSpawn~~ | 삭제/미사용 |
| ~~LogicSkillGaugeChargeRatio~~ | 삭제/미사용 |
| ~~LogicHpDrain~~ | 삭제/미사용 |
| ~~LogicStatSteal~~ | 삭제/미사용 |
| ~~LogicKnockback~~ | 삭제/미사용 |
| ~~LogicWarp~~ | 삭제/미사용 |
| ~~LogicJump~~ | 삭제/미사용 |
| ~~LogicDash1~~ | 삭제/미사용 |
| ~~LogicDash2~~ | 삭제/미사용 |
| ~~LogicSwap~~ | 삭제/미사용 |
| ~~LogicExecution~~ | 삭제/미사용 |
| ~~LogicDamageDelay~~ | 삭제/미사용 |
| ~~LogicDamageGating~~ | 삭제/미사용 |
| ~~LogicBarrierScaleDamage~~ | 삭제/미사용 |
| ~~LogicSpSwap~~ | 삭제/미사용 |

---

### 16.3 시뮬레이터 구현 GAP 분석

| 원본 로직 타입 | 시뮬레이터 구현 | 상태 | 비고 |
|----------------|----------------|------|------|
| LogicDamage | `apply_damage()` | **완전 구현** | DEF 감소 공식, 속성 상성 포함 |
| LogicDamagePenetration | `apply_damage(penetration=True)` | **완전 구현** | DEF 스킵 처리 |
| LogicDamageHpRatio | `apply_damage_hp_ratio()` | **완전 구현** | 현재 HP 비율 적용 |
| LogicCriDamage | `apply_damage(force_crit=True)` | **완전 구현** | 강제 크리 플래그 |
| LogicHeal | `apply_heal()` | **완전 구현** | ATK 비례, 크리 힐 포함 |
| LogicHealRatio | `apply_heal_ratio()` | **완전 구현** | HP 비례 힐 |
| LogicStatChange | `apply_stat_change()` | **완전 구현** | ATK/DEF/HP/SPD 모두 |
| LogicBarrier | `apply_barrier()` | **완전 구현** | 중첩 규칙 포함 |
| LogicDot | `apply_dot()` | **완전 구현** | Dmg/Heal Tag 구분 |
| LogicStun | `apply_cc(STUN)` | **완전 구현** | |
| LogicSleep | `apply_cc(SLEEP)` | **완전 구현** | 피격 해제 포함 |
| LogicFreeze | `apply_cc(FREEZE)` | **완전 구현** | 확률 해제 포함 |
| LogicInvincibility | `apply_buff(INVINCIBLE)` | **완전 구현** | |
| LogicUndying | `apply_buff(UNDYING)` | **완전 구현** | |
| LogicTaunt | `apply_taunt()` | **완전 구현** | |
| LogicRevive | `apply_revive()` | **부분 구현** | 빈칸 체크 미구현 |
| LogicBarrierRatio | - | **미구현** | HP 비례 보호막 |
| LogicRemoveBuffCount | - | **미구현** | 버프/디버프 수량 제거 |
| UseSkill | - | **미구현** | 스킬 체인 발동 |
| LogicDamageBuffScale | - | **미구현** | 버프 수 비례 대미지 |
| LogicDamageBuffScaleTarget | - | **미구현** | 타겟 버프 수 비례 대미지 |
| LogicDamageDebuffScaleTarget | - | **미구현** | 타겟 디버프 수 비례 대미지 |
| LogicSpSteal | - | **미구현** | SP 강탈 |
| LogicSpIncrease | - | **미구현** | SP 즉시 충전 |
| LogicBuffTurnIncrease | - | **미구현** | 버프 턴 연장 |
| LogicDeBuffTurnIncrease | - | **미구현** | 디버프 턴 연장 |
| LogicHealLossScaleHp | - | **미구현** | 잃은 HP 비례 힐 |
| LogicAllyScaleHeal | - | **미구현** | 파티 구성 비례 힐 |
| LogicStone | - | **미구현** | Freeze와 유사 |
| LogicElectricshock | - | **미구현** | 30% 스킬 취소 |
| LogicPanic | - | **미구현** | 30% 스킬 취소 |
| LogicAbnormalSkill | - | **미구현** | 전체 스킬 봉인 |
| LogicConfused | - | **미구현** | 혼란 상태 |
| LogicBlind | - | **미구현** | 실명 (적중 0) |
| LogicSilence | - | **미구현** | Normal 스킬만 허용 |
| LogicSpLock | - | **미구현** | SP 충전 봉인 |
| LogicDebuffImmune | - | **미구현** | 디버프 면역 |
| LogicCounterUnavailable | - | **미구현** | 반격 확률 0 고정 |
| LogicCriUnavailable | - | **미구현** | 크리 확률 0 고정 |
| LogicStop | - | **미구현** | 애니 정지 |
| LogicNormalIgnoreCounter | - | **미구현** | Normal 반격 무시 |
| LogicActiveIgnoreCounter | - | **미구현** | Active 반격 무시 |
| LogicUltimateIgnoreCounter | - | **미구현** | Ultimate 반격 무시 |
| LogicAllyScaleStatusChange | - | **미구현** | 파티 비례 스탯 |
| LogicStatusChangeApplyAnotherStatusRate | - | **미구현** | 타 스탯 비율 적용 |
| LogicActiveSkillTurnChangeOnce | - | **미구현** | 쿨타임 즉시 변경 |
| LogicSpdTwist | - | **미구현** | 전체 속도 반전 |
| LogicDamageCriApplyDebuff | - | **미구현** | Tag 조건 강제 크리 |
| LogicStatusChangeEveryTurn | - | **미구현** | 매 턴 스탯 변경 |
| LogicStatusChangeElementCount | - | **미구현** | 속성 수 비례 스탯 |
| LogicStatusChangeRemainingHpPercent | - | **미구현** | HP 높을수록 강화 |
| LogicStatusChangeMissingHpPercent | - | **미구현** | HP 낮을수록 강화 |
| LogicHealTargetCount | - | **미구현** | 타겟 수 비례 힐 |
| LogicIgnoreElementUpper | - | **미구현** | 속성 상성 무시 |

> **요약**: 완전 구현 15종 / 부분 구현 1종 / 미구현 40종

---

### 16.4 보호막 중첩 규칙 (원본)

원본 Notion 페이지 기준 보호막 동작 명세:

**기본 규칙:**
- 보호막이 존재할 때 대미지를 받으면 보호막이 먼저 흡수
- 보호막을 초과하는 대미지는 HP에 적용
  - 예: 보호막 3000, 대미지 5000 → 보호막 소멸, HP 2000 감소

**중첩 규칙 (보호막 2개 이상 보유 시):**
- 각 보호막은 독립적으로 존재하며 앞선(먼저 부여된) 보호막부터 소모
- 앞 보호막 만료 시: 남은 보호막 = min(총 보호막 합산, 현재 남은 뒤 보호막)
  - 예: 앞 3000 / 뒤 2000 → 총합 4000 → 앞 보호막 만료 시 뒤 보호막 2000으로 유지

**현재 시뮬레이터 구현 상태:**
- `apply_barrier()`: 단일 보호막 흡수 및 초과 대미지 처리 구현됨
- 다중 보호막 스택 처리: 부분 구현 (선입선출 방식)

---

### 16.5 LogicValue 스케일링 비교

원본 게임과 시뮬레이터 간 스케일링 방식 차이:

| LogicValue (원본) | 의미 | 시뮬레이터 multiplier |
|-------------------|------|-----------------------|
| 100000 | 1.0× (100%) | 1.0 |
| 150000 | 1.5× (150%) | 1.5 |
| 200000 | 2.0× (200%) | 2.0 |
| 300000 | 3.0× (300%) | 3.0 |
| 50000  | 0.5× (50%)  | 0.5 |
| 20000  | 0.2× (20%)  | 0.2 |

**원본 게임 방식:**
- 모든 수치는 정수로 저장
- 공식 적용 시 `× 0.00001` 변환으로 실수 비율 획득
- 예: `LogicValue=300000` → `300000 × 0.00001 = 3.0`

**시뮬레이터 방식:**
- 직접 실수 비율 사용 (multiplier=3.0)
- 기획 데이터를 파싱할 때 `÷ 100000` 변환 필요
- `src/fixtures/test_data.py` 내 스킬 데이터는 이미 변환된 실수값 사용

**변환 공식:**
```python
# 원본 LogicValue → 시뮬레이터 multiplier
multiplier = logic_value / 100000

# 시뮬레이터 multiplier → 원본 LogicValue
logic_value = int(multiplier * 100000)
```
