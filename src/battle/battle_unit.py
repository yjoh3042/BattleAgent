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
    def take_damage(self, amount: float) -> float:
        """피해 적용. 무적/불사/보호막 우선 처리. 실제 HP 감소량 반환."""
        if amount <= 0:
            return 0.0
        # 무적: 모든 피해 무효
        if self.is_invincible:
            return 0.0
        actual = amount
        if self.barrier_hp > 0:
            absorbed = min(self.barrier_hp, amount)
            self.barrier_hp -= absorbed
            actual = amount - absorbed
        self.current_hp = max(0.0, self.current_hp - actual)
        # 불사: HP 1 미만 불가
        if self.is_undying and self.current_hp < 1.0 and actual > 0:
            self.current_hp = 1.0
        return actual

    def heal(self, amount: float) -> float:
        """힐 적용. 실제 회복량 반환."""
        if amount <= 0 or not self.is_alive:
            return 0.0
        old = self.current_hp
        self.current_hp = min(self.max_hp, self.current_hp + amount)
        return self.current_hp - old

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

    # ─── 트리거 중복 방지 ─────────────────────────────────────────
    def mark_triggered(self, trigger_id: str):
        self._triggered_once.add(trigger_id)

    def was_triggered(self, trigger_id: str) -> bool:
        return trigger_id in self._triggered_once

    # ─── 표시용 ───────────────────────────────────────────────────
    @property
    def hp_ratio(self) -> float:
        return self.current_hp / self.max_hp if self.max_hp > 0 else 0.0

    def __repr__(self) -> str:
        return (f"BattleUnit({self.name}, HP={self.current_hp:.0f}/{self.max_hp:.0f}, "
                f"SPD={self.spd:.0f}, alive={self.is_alive})")
