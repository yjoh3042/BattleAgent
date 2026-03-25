"""BattleUnit - 전투 중 캐릭터의 런타임 상태 관리"""
from __future__ import annotations
from typing import Dict, List, Optional, TYPE_CHECKING
from dataclasses import dataclass, field

from battle.enums import CCType, LogicType, StatType
from battle.models import CharacterData, BuffData

if TYPE_CHECKING:
    pass


@dataclass
class ActiveBuff:
    """현재 적용 중인 버프/디버프 인스턴스"""
    buff_data: BuffData
    remaining_turns: int
    stack_count: int = 1           # DoT 계열 스택 수
    source_unit_id: Optional[str] = None

    @property
    def id(self) -> str:
        return self.buff_data.id

    @property
    def source_skill_id(self) -> str:
        return self.buff_data.source_skill_id


class BattleUnit:
    """전투 중 캐릭터의 모든 런타임 상태"""

    def __init__(self, data: CharacterData):
        self.data = data
        self.id = data.id
        self.name = data.name
        self.side = data.side

        # HP
        self.max_hp: float = data.stats.hp
        self.current_hp: float = data.stats.hp
        self.barrier_hp: float = 0.0   # 보호막

        # 스킬 상태
        self.active_skill_cooldown: int = 0    # 0이면 사용 가능
        self.ultimate_cooldown: int = 0        # 얼티밋 쿨타임 (0이면 사용 가능)
        self.used_ultimate_this_round: bool = False

        # 상태이상
        self.hard_cc: Optional[CCType] = None   # 현재 Hard CC 타입
        self.hard_cc_duration: int = 0
        self.soft_cc: Optional[CCType] = None
        self.soft_cc_duration: int = 0

        # 버프/디버프 목록
        self.active_buffs: List[ActiveBuff] = []

        # 태그 (화상 스택, 도발 등 메타 데이터)
        self._tags: Dict[str, int] = {}   # tag_name -> count

        # 도발 중인 캐릭터 ID
        self.taunted_by: Optional[str] = None
        self.taunted_turns: int = 0

        # ── 상태 플래그 (마커 버프로 관리) ──────────────────────────
        self.is_invincible: bool = False       # 무적
        self.is_undying: bool = False          # 불사 (HP 1 미만 불가)
        self.is_debuff_immune: bool = False    # 디버프 면역
        self.is_sp_locked: bool = False        # SP 충전 잠금
        self.is_cri_unavailable: bool = False  # 크리 불가
        self.is_counter_unavailable: bool = False  # 반격 불가
        self.is_confused: bool = False         # 혼란
        self.is_silenced: bool = False         # 침묵
        self.ignore_element: bool = False      # 속성 상성 무시

        # ── 3대 RPG 확장 상태 플래그 ─────────────────────────────
        self.is_stealthed: bool = False         # 스텔스 (타겟 불가)
        self.is_heal_blocked: bool = False      # 회복 불가
        self.is_cursed: bool = False            # 저주 (회복→피해)
        self.is_doomed: bool = False            # 파멸
        self.is_buff_blocked: bool = False      # 버프 적용 불가
        self.is_passive_sealed: bool = False    # 패시브 봉인
        self.is_revive_sealed: bool = False     # 부활 봉인
        self.is_banished: bool = False          # 추방 (전투 제외)
        self.is_marked: bool = False            # 표적/낙인
        self.is_transformed: bool = False       # 변신 상태
        self.is_reflecting: bool = False        # 반사 상태
        self.protect_target_id: Optional[str] = None  # 보호 대상 ID
        self.protected_by_id: Optional[str] = None    # 보호자 ID

        # ── 게이지/리소스 시스템 ─────────────────────────────────
        self.energy: float = 0.0                # 에너지 게이지 (궁극기)
        self.max_energy: float = 100.0          # 최대 에너지
        self.fighting_spirit: float = 0.0       # 투지 게이지
        self.max_fighting_spirit: float = 100.0
        self.focus: int = 0                     # 집중 스택
        self.max_focus: int = 5
        self.soul_stacks: int = 0               # 영혼 수집 스택
        self.toughness: float = 100.0           # 터프니스 (격파 게이지)
        self.max_toughness: float = 100.0
        self.atb_gauge: float = 0.0             # ATB 게이지 (0~100)

        # ── 전투 내 추적 카운터 ──────────────────────────────────
        self.kill_count: int = 0                # 이번 전투 처치 수
        self.survival_turns: int = 0            # 생존 턴 수
        self.damage_accumulated: float = 0.0    # 받은 피해 축적 (카운터용)
        self.consecutive_hits_this_turn: int = 0  # 이번 턴 피격 횟수
        self.first_attack_used: bool = False    # 첫 공격 사용 여부

        # ── 보스 전용 ────────────────────────────────────────────
        self.boss_phase: int = 0                # 보스 페이즈
        self.enrage_stacks: int = 0             # 광폭화 스택
        self.countdown: int = -1                # 카운트다운 (-1=비활성)
        self.parts: Dict[str, float] = {}       # 부위별 HP

        # ── 반사/피해감소 수치 ───────────────────────────────────
        self.reflect_ratio: float = 0.0         # 반사 비율
        self.damage_cap_value: float = 0.0      # 피해 상한
        self.damage_share_ratio: float = 0.0    # 분산 비율
        self.heal_reduce_ratio: float = 0.0     # 회복 감소 비율
        self.consecutive_hit_reduce_ratio: float = 0.0  # 연속 피격 감소율

        # ── 변신 백업 ────────────────────────────────────────────
        self._original_skills: Optional[dict] = None  # 변신 전 스킬 백업

        # 전투당 트리거 발동 기록
        self._triggered_once: set = set()

        # 스탯 캐시 무효화 플래그
        self._stat_cache: Dict[str, float] = {}
        self._cache_valid: bool = False

    # ─── 생사 판정 ───────────────────────────────────────────────
    @property
    def is_alive(self) -> bool:
        return self.current_hp > 0

    # ─── 타일 포지션 (3×3 그리드) ────────────────────────────────
    @property
    def tile_pos(self) -> tuple:
        return self.data.tile_pos

    @property
    def tile_row(self) -> int:
        """행(row): 0=전열, 1=중열, 2=후열"""
        return self.data.tile_pos[0]

    @property
    def tile_col(self) -> int:
        """열(col): 0=좌, 1=중, 2=우"""
        return self.data.tile_pos[1]

    # ─── 스탯 (버프 합산) ─────────────────────────────────────────
    def _get_buff_delta(self, stat: str) -> float:
        """해당 스탯에 걸린 모든 버프/디버프의 합산값 반환"""
        total = 0.0
        base = getattr(self.data.stats, stat, 0.0)
        for ab in self.active_buffs:
            bd = ab.buff_data
            if bd.logic_type == LogicType.STAT_CHANGE and bd.stat == stat:
                if bd.is_ratio:
                    total += base * bd.value * ab.stack_count
                else:
                    total += bd.value * ab.stack_count
        return total

    @property
    def atk(self) -> float:
        return max(1.0, self.data.stats.atk + self._get_buff_delta("atk"))

    @property
    def def_(self) -> float:
        return max(0.0, self.data.stats.def_ + self._get_buff_delta("def_"))

    @property
    def spd(self) -> float:
        return max(25.0, self.data.stats.spd + self._get_buff_delta("spd"))

    @property
    def cri_ratio(self) -> float:
        return min(1.0, max(0.0, self.data.stats.cri_ratio + self._get_buff_delta("cri_ratio")))

    @property
    def cri_dmg_ratio(self) -> float:
        return max(1.0, self.data.stats.cri_dmg_ratio + self._get_buff_delta("cri_dmg_ratio"))

    @property
    def cri_resist(self) -> float:
        return max(0.0, self.data.stats.cri_resist + self._get_buff_delta("cri_resist"))

    @property
    def penetration(self) -> float:
        return max(0.0, self.data.stats.penetration + self._get_buff_delta("penetration"))

    @property
    def acc(self) -> float:
        return max(0.0, self.data.stats.acc + self._get_buff_delta("acc"))

    @property
    def dodge(self) -> float:
        return max(0.0, self.data.stats.dodge + self._get_buff_delta("dodge"))

    # ─── HP 조작 ──────────────────────────────────────────────────
    def take_damage(self, amount: float, pierce_barrier: bool = False) -> float:
        """피해 적용. 무적/불사/보호막/피해상한/반사 우선 처리. 실제 HP 감소량 반환."""
        if amount <= 0:
            return 0.0
        # 추방 상태: 피해 무효
        if self.is_banished:
            return 0.0
        # 무적: 모든 피해 무효
        if self.is_invincible:
            return 0.0
        # 피해 상한 적용
        if self.damage_cap_value > 0:
            amount = min(amount, self.damage_cap_value)
        # 연속 피격 감소
        if self.consecutive_hit_reduce_ratio > 0 and self.consecutive_hits_this_turn > 0:
            reduction = min(0.7, self.consecutive_hit_reduce_ratio * self.consecutive_hits_this_turn)
            amount *= (1.0 - reduction)
        self.consecutive_hits_this_turn += 1
        actual = amount
        # 보호막 관통
        if not pierce_barrier and self.barrier_hp > 0:
            absorbed = min(self.barrier_hp, amount)
            self.barrier_hp -= absorbed
            actual = amount - absorbed
        self.current_hp = max(0.0, self.current_hp - actual)
        # 불사: HP 1 미만 불가
        if self.is_undying and self.current_hp < 1.0 and actual > 0:
            self.current_hp = 1.0
        # 피해 축적 (카운터용)
        self.damage_accumulated += actual
        return actual

    def heal(self, amount: float, ignore_block: bool = False) -> float:
        """힐 적용. 회복 불가/저주/파멸/회복 감소 처리. 실제 회복량 반환."""
        if amount <= 0 or not self.is_alive:
            return 0.0
        # 회복 불가
        if self.is_heal_blocked and not ignore_block:
            return 0.0
        # 저주: 회복 → 피해로 전환
        if self.is_cursed:
            self.take_damage(amount)
            return -amount
        # 파멸: 회복 불가 + 회복 시도 시 피해
        if self.is_doomed:
            self.take_damage(amount * 0.5)
            return -amount * 0.5
        # 회복 효율 감소
        if self.heal_reduce_ratio > 0:
            amount *= (1.0 - self.heal_reduce_ratio)
        old = self.current_hp
        self.current_hp = min(self.max_hp, self.current_hp + amount)
        return self.current_hp - old

    def heal_with_overheal(self, amount: float) -> tuple:
        """힐 적용 + 초과 회복분 반환. (실제회복량, 초과량) 튜플."""
        if amount <= 0 or not self.is_alive:
            return 0.0, 0.0
        if self.is_heal_blocked:
            return 0.0, 0.0
        if self.is_cursed:
            self.take_damage(amount)
            return -amount, 0.0
        old = self.current_hp
        self.current_hp = min(self.max_hp, self.current_hp + amount)
        actual = self.current_hp - old
        overheal = max(0.0, amount - actual)
        return actual, overheal

    def add_barrier(self, amount: float):
        """보호막 추가"""
        self.barrier_hp += amount

    def revive(self, hp_ratio: float = 0.3):
        """부활. HP를 최대 HP의 일정 비율로 회복."""
        self.current_hp = self.max_hp * hp_ratio
        self.hard_cc = None
        self.hard_cc_duration = 0

    # ─── 버프 관리 ────────────────────────────────────────────────
    def apply_buff(self, buff_data: BuffData, source_unit_id: Optional[str] = None) -> bool:
        """
        버프/디버프 적용.
        - 동일 source_skill_id → 기존 버프 refresh (남은 턴 2로 갱신)
        - 다른 source_skill_id → 새 스택으로 추가 (무한 중첩)
        - DoT 계열은 스택 카운트 증가
        반환: True면 새로 추가, False면 갱신
        """
        is_dot = buff_data.logic_type in (LogicType.DOT, LogicType.DOT_HEAL_HP_RATIO)

        for ab in self.active_buffs:
            if ab.buff_data.source_skill_id == buff_data.source_skill_id and ab.buff_data.id == buff_data.id:
                if is_dot:
                    # DoT는 스택 증가 (max_stacks 제한)
                    if ab.stack_count < buff_data.max_stacks:
                        ab.stack_count += 1
                    ab.remaining_turns = buff_data.duration
                else:
                    # 동일 출처: 남은 턴 2로 갱신
                    ab.remaining_turns = buff_data.duration
                return False

        # 새 버프 추가
        self.active_buffs.append(ActiveBuff(
            buff_data=buff_data,
            remaining_turns=buff_data.duration,
            stack_count=1,
            source_unit_id=source_unit_id
        ))
        return True

    def remove_buffs(self, is_debuff: bool):
        """버프 또는 디버프 전체 제거"""
        self.active_buffs = [ab for ab in self.active_buffs if ab.buff_data.is_debuff != is_debuff]

    def get_buffs_by_logic(self, logic_type: LogicType) -> List[ActiveBuff]:
        return [ab for ab in self.active_buffs if ab.buff_data.logic_type == logic_type]

    # ─── 태그 시스템 ──────────────────────────────────────────────
    def add_tag(self, tag: str, count: int = 1):
        self._tags[tag] = self._tags.get(tag, 0) + count

    def get_tag_count(self, tag: str) -> int:
        return self._tags.get(tag, 0)

    def remove_tag(self, tag: str):
        self._tags.pop(tag, None)

    def has_tag(self, tag: str) -> bool:
        return self._tags.get(tag, 0) > 0

    # ─── 도발 ─────────────────────────────────────────────────────
    def apply_taunt(self, taunter_id: str, duration: int = 2):
        self.taunted_by = taunter_id
        self.taunted_turns = duration

    def tick_taunt(self):
        if self.taunted_turns > 0:
            self.taunted_turns -= 1
            if self.taunted_turns <= 0:
                self.taunted_by = None

    # ─── CC 관리 ──────────────────────────────────────────────────
    def apply_cc(self, cc_type: CCType, duration: int = 1):
        """상태이상 부여"""
        hard_cc_types = {CCType.STUN, CCType.SLEEP, CCType.FREEZE, CCType.STONE, CCType.ABNORMAL_SKILL}
        if cc_type in hard_cc_types:
            self.hard_cc = cc_type
            self.hard_cc_duration = max(self.hard_cc_duration, duration)
        else:
            self.soft_cc = cc_type
            self.soft_cc_duration = max(self.soft_cc_duration, duration)
        # 상태 플래그 설정
        if cc_type == CCType.CONFUSED:
            self.is_confused = True
        elif cc_type == CCType.SILENCE:
            self.is_silenced = True

    def tick_cc(self):
        """CC 지속 턴 감소"""
        if self.hard_cc_duration > 0:
            self.hard_cc_duration -= 1
            if self.hard_cc_duration <= 0:
                self.hard_cc = None
        if self.soft_cc_duration > 0:
            self.soft_cc_duration -= 1
            if self.soft_cc_duration <= 0:
                # 소프트 CC 만료 시 상태 플래그 해제
                if self.soft_cc == CCType.CONFUSED:
                    self.is_confused = False
                elif self.soft_cc == CCType.SILENCE:
                    self.is_silenced = False
                self.soft_cc = None

    # ─── 스킬 쿨타임 ──────────────────────────────────────────────
    def use_active_skill(self):
        """액티브 스킬 사용 → 2턴 쿨타임 시작"""
        self.active_skill_cooldown = self.data.active_skill.cooldown_turns or 2

    def use_ultimate_skill(self):
        """얼티밋 사용 → 쿨타임 시작 (전 직업 공통 4턴, 자기 턴 기준 감소)"""
        from battle.rules import ULT_COOLDOWN
        cd = self.data.ultimate_skill.cooldown_turns
        if cd <= 0:
            cd = ULT_COOLDOWN  # 전 직업 공통 4턴
        self.ultimate_cooldown = cd

    def tick_cooldown(self):
        """쿨타임 1 감소 (액티브 + 얼티밋)"""
        if self.active_skill_cooldown > 0:
            self.active_skill_cooldown -= 1
        if self.ultimate_cooldown > 0:
            self.ultimate_cooldown -= 1

    def can_use_active(self) -> bool:
        return self.active_skill_cooldown <= 0

    def can_use_ultimate(self) -> bool:
        """얼티밋 사용 가능 여부 (쿨타임 + 라운드 제한)"""
        return self.ultimate_cooldown <= 0 and not self.used_ultimate_this_round

    # ─── 턴 처리 ──────────────────────────────────────────────────
    def on_turn_start_tick(self) -> List[dict]:
        """
        턴 시작 시 처리 (CharacterTurnStart 버프):
        - DoT/HoT 등 틱 발동 후 해당 버프의 remaining_turns -1
        반환: 만료된 버프 목록
        """
        expired = []
        new_buffs = []
        for ab in self.active_buffs:
            if ab.buff_data.buff_turn_reduce_timing == "CharacterTurnStart":
                ab.remaining_turns -= 1
                if ab.remaining_turns <= 0:
                    expired.append({'buff': ab, 'stat': ab.buff_data.stat})
                else:
                    new_buffs.append(ab)
            else:
                new_buffs.append(ab)
        self.active_buffs = new_buffs
        # 마커 버프 만료 시 상태 플래그 동기화
        if expired:
            self.sync_marker_flags()
        return expired

    def on_turn_end(self) -> List[dict]:
        """
        턴 종료 시 처리 (CharacterTurnEnd 버프):
        1. CharacterTurnEnd 버프 remaining_turns -1 (만료 제거)
        2. CC 틱
        3. 쿨타임 틱
        4. 도발 틱
        반환: 만료된 버프 목록 (SPD 변화 감지용)
        """
        expired = []
        new_buffs = []
        for ab in self.active_buffs:
            if ab.buff_data.buff_turn_reduce_timing == "CharacterTurnEnd":
                ab.remaining_turns -= 1
                if ab.remaining_turns <= 0:
                    expired.append({'buff': ab, 'stat': ab.buff_data.stat})
                else:
                    new_buffs.append(ab)
            else:
                new_buffs.append(ab)
        self.active_buffs = new_buffs
        # 마커 버프 만료 시 상태 플래그 동기화
        if expired:
            self.sync_marker_flags()

        self.tick_cc()
        self.tick_cooldown()
        self.tick_taunt()

        return expired

    # ─── 마커 버프 → 상태 플래그 동기화 ────────────────────────
    def sync_marker_flags(self):
        """마커 버프 존재 여부에 따라 상태 플래그 동기화.
        버프 만료 후 호출하여 플래그를 정리한다."""
        buff_ids = {ab.buff_data.id for ab in self.active_buffs}
        buff_tags = set()
        for ab in self.active_buffs:
            buff_tags.update(ab.buff_data.tags)

        self.is_invincible = "invincibility_marker" in buff_ids or "invincibility" in buff_tags
        self.is_undying = "undying_marker" in buff_ids or "undying" in buff_tags
        self.is_debuff_immune = "debuff_immune_marker" in buff_ids or "debuff_immune" in buff_tags
        self.is_sp_locked = "sp_lock_marker" in buff_ids or "sp_lock" in buff_tags
        self.is_cri_unavailable = "cri_unavailable_marker" in buff_ids or "cri_unavailable" in buff_tags
        self.is_counter_unavailable = "counter_unavailable_marker" in buff_ids or "counter_unavailable" in buff_tags
        self.ignore_element = "ignore_element_marker" in buff_ids or "ignore_element" in buff_tags
        # ── 3대 RPG 확장 플래그 동기화 ───────────────────────────
        self.is_stealthed = "stealth" in buff_tags
        self.is_heal_blocked = "heal_block" in buff_tags
        self.is_cursed = "cursed" in buff_tags
        self.is_doomed = "doomed" in buff_tags
        self.is_buff_blocked = "buff_blocked" in buff_tags
        self.is_passive_sealed = "passive_sealed" in buff_tags
        self.is_revive_sealed = "revive_sealed" in buff_tags
        self.is_banished = "banished" in buff_tags
        self.is_marked = "marked" in buff_tags
        self.is_reflecting = "reflecting" in buff_tags
        # 수치형 마커 동기화
        self.reflect_ratio = 0.0
        self.damage_cap_value = 0.0
        self.damage_share_ratio = 0.0
        self.heal_reduce_ratio = 0.0
        self.consecutive_hit_reduce_ratio = 0.0
        for ab in self.active_buffs:
            t = ab.buff_data.tags or []
            if "reflect_ratio" in t:
                self.reflect_ratio = max(self.reflect_ratio, ab.buff_data.value)
            if "damage_cap" in t:
                self.damage_cap_value = max(self.damage_cap_value, ab.buff_data.value)
            if "damage_share" in t:
                self.damage_share_ratio = max(self.damage_share_ratio, ab.buff_data.value)
            if "heal_reduce" in t:
                self.heal_reduce_ratio = max(self.heal_reduce_ratio, ab.buff_data.value)
            if "consec_hit_reduce" in t:
                self.consecutive_hit_reduce_ratio = max(
                    self.consecutive_hit_reduce_ratio, ab.buff_data.value)

    # ─── 트리거 중복 방지 ─────────────────────────────────────────
    def mark_triggered(self, trigger_id: str):
        self._triggered_once.add(trigger_id)

    def was_triggered(self, trigger_id: str) -> bool:
        return trigger_id in self._triggered_once

    # ─── 표시용 ───────────────────────────────────────────────────
    @property
    def hp_ratio(self) -> float:
        return self.current_hp / self.max_hp if self.max_hp > 0 else 0.0

    # ─── 게이지/리소스 메서드 ──────────────────────────────────────
    def add_energy(self, amount: float) -> float:
        """에너지 추가. 실제 추가량 반환."""
        old = self.energy
        self.energy = min(self.max_energy, self.energy + amount)
        return self.energy - old

    def spend_energy(self, amount: float) -> bool:
        """에너지 소모. 성공 시 True."""
        if self.energy < amount:
            return False
        self.energy -= amount
        return True

    def add_fighting_spirit(self, amount: float) -> float:
        """투지 게이지 추가."""
        old = self.fighting_spirit
        self.fighting_spirit = min(self.max_fighting_spirit, self.fighting_spirit + amount)
        return self.fighting_spirit - old

    def spend_fighting_spirit(self, amount: float) -> bool:
        """투지 게이지 소모."""
        if self.fighting_spirit < amount:
            return False
        self.fighting_spirit -= amount
        return True

    def add_focus(self, amount: int = 1) -> int:
        """집중 스택 추가."""
        old = self.focus
        self.focus = min(self.max_focus, self.focus + amount)
        return self.focus - old

    def spend_focus(self, amount: int = 1) -> bool:
        """집중 스택 소모."""
        if self.focus < amount:
            return False
        self.focus -= amount
        return True

    def add_toughness_damage(self, amount: float) -> bool:
        """터프니스 피해. 격파 시 True 반환."""
        self.toughness = max(0.0, self.toughness - amount)
        return self.toughness <= 0.0

    def reset_toughness(self):
        """터프니스 복구."""
        self.toughness = self.max_toughness

    # ─── 변신 ───────────────────────────────────────────────────
    def transform(self, new_normal=None, new_active=None, new_ultimate=None):
        """변신: 현재 스킬 백업 후 교체."""
        if not self.is_transformed:
            self._original_skills = {
                'normal': self.data.normal_skill,
                'active': self.data.active_skill,
                'ultimate': self.data.ultimate_skill,
            }
            self.is_transformed = True
        if new_normal:
            self.data.normal_skill = new_normal
        if new_active:
            self.data.active_skill = new_active
        if new_ultimate:
            self.data.ultimate_skill = new_ultimate

    def revert_transform(self):
        """변신 해제: 원래 스킬 복원."""
        if self.is_transformed and self._original_skills:
            self.data.normal_skill = self._original_skills['normal']
            self.data.active_skill = self._original_skills['active']
            self.data.ultimate_skill = self._original_skills['ultimate']
            self._original_skills = None
            self.is_transformed = False

    # ─── 카운트다운 ─────────────────────────────────────────────
    def tick_countdown(self) -> bool:
        """카운트다운 1 감소. 0에 도달하면 True (즉사기 발동)."""
        if self.countdown > 0:
            self.countdown -= 1
            return self.countdown <= 0
        return False

    # ─── 턴 시작 리셋 ───────────────────────────────────────────
    def on_new_turn_reset(self):
        """자기 턴 시작 시 리셋할 카운터들."""
        self.consecutive_hits_this_turn = 0
        self.survival_turns += 1

    # ─── 최저 스탯 조회 (약점 탐지) ─────────────────────────────
    @property
    def lowest_stat(self) -> float:
        """ATK, DEF 중 최저값 반환 (약점 탐지용)."""
        return min(self.atk, self.def_)

    # ─── 버프/디버프 카운트 ──────────────────────────────────────
    @property
    def buff_count(self) -> int:
        return len([ab for ab in self.active_buffs if not ab.buff_data.is_debuff])

    @property
    def debuff_count(self) -> int:
        return len([ab for ab in self.active_buffs if ab.buff_data.is_debuff])

    def __repr__(self) -> str:
        return (f"BattleUnit({self.name}, HP={self.current_hp:.0f}/{self.max_hp:.0f}, "
                f"SPD={self.spd:.0f}, alive={self.is_alive})")
