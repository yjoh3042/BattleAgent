"""BuffManager - 버프/디버프 적용, 틱, DoT 처리
스택 규칙: 동일 출처 → 2턴 갱신, 다른 출처 → 무한 중첩
"""
from __future__ import annotations
from typing import List, Optional, TYPE_CHECKING

from battle.enums import LogicType, CCType
from battle.models import BuffData
from battle.damage_calc import calc_dot_damage

if TYPE_CHECKING:
    from battle.battle_unit import BattleUnit
    from battle.turn_manager import TurnManager


class BuffManager:
    """버프/디버프 생명주기 관리"""

    def __init__(self, turn_manager: Optional[TurnManager] = None):
        self._turn_manager = turn_manager
        self._log: List[str] = []

    def set_turn_manager(self, tm: TurnManager):
        self._turn_manager = tm

    # ─── 버프 적용 ────────────────────────────────────────────────
    def apply_buff(
        self,
        unit: BattleUnit,
        buff_data: BuffData,
        source_unit_id: Optional[str] = None,
    ) -> bool:
        """
        버프 적용 후 SPD 변화 감지 시 TurnManager에 알림.
        반환: True=새로 추가, False=갱신
        """
        # 디버프 면역 체크: 대상이 디버프 면역 상태이고 디버프인 경우 차단
        if buff_data.is_debuff and getattr(unit, 'is_debuff_immune', False):
            self._log.append(f"  → {unit.name} 디버프 면역! {buff_data.name or buff_data.id} 차단")
            return False
        # 버프 적용 불가 체크: 대상이 buff_blocked 상태이고 버프인 경우 차단
        if not buff_data.is_debuff and getattr(unit, 'is_buff_blocked', False):
            self._log.append(f"  → {unit.name} 버프 적용 불가! {buff_data.name or buff_data.id} 차단")
            return False
        # 추방 상태: 모든 버프/디버프 차단
        if getattr(unit, 'is_banished', False):
            self._log.append(f"  → {unit.name} 추방 상태! {buff_data.name or buff_data.id} 차단")
            return False

        # SPD 변화 감지를 위해 이전 SPD 기록
        old_spd = unit.spd if buff_data.stat == "spd" else None

        is_new = unit.apply_buff(buff_data, source_unit_id)

        # CC 처리
        if buff_data.logic_type == LogicType.CC and buff_data.cc_type:
            unit.apply_cc(buff_data.cc_type, buff_data.duration)
            self._log.append(f"  → {unit.name}에게 {buff_data.cc_type.value} 부여 ({buff_data.duration}턴)")

        # DoT 태그 (화상 스택)
        if buff_data.logic_type == LogicType.DOT and buff_data.dot_type == "burn":
            unit.add_tag("burn", 1)
            self._log.append(f"  → {unit.name} 화상 스택 +1 (현재: {unit.get_tag_count('burn')})")

        # SPD 변화 시 TurnManager 업데이트
        if old_spd is not None and self._turn_manager:
            new_spd = unit.spd
            if abs(new_spd - old_spd) > 0.001:
                self._turn_manager.on_spd_change(unit, old_spd)
                self._log.append(f"  → {unit.name} SPD {old_spd:.0f} → {new_spd:.0f} (턴 재계산)")

        action = "추가" if is_new else "갱신"
        buff_name = buff_data.name or buff_data.id
        self._log.append(f"  → {unit.name} 버프 {action}: {buff_name} ({buff_data.remaining_turns if hasattr(buff_data, 'remaining_turns') else buff_data.duration}턴)")
        return is_new

    # ─── 버프 틱 (턴 시작: CharacterTurnStart) ───────────────────
    def tick_turn_start(self, unit: BattleUnit):
        """
        턴 시작 시 (CharacterTurnStart 버프):
        1. DoT/HoT 틱 효과 발동 (버프가 살아있을 때 먼저)
        2. CharacterTurnStart 버프 remaining_turns -1, 만료 처리
        """
        self._apply_dots(unit)
        old_spd = unit.spd
        expired = unit.on_turn_start_tick()
        self._handle_expired(unit, expired, old_spd, timing_label="턴시작")

    # ─── 버프 틱 (턴 종료: CharacterTurnEnd) ─────────────────────
    def tick_turn_end(self, unit: BattleUnit):
        """
        턴 종료 시 (CharacterTurnEnd 버프):
        1. CharacterTurnEnd 버프 remaining_turns -1, 만료 처리
        2. CC / 쿨타임 / 도발 틱
        """
        old_spd = unit.spd
        expired = unit.on_turn_end()
        self._handle_expired(unit, expired, old_spd, timing_label="턴종료")

    def _handle_expired(self, unit: BattleUnit, expired: list, old_spd: float, timing_label: str = ""):
        """만료 버프 공통 후처리: SPD 재계산 + DoT 태그 정리"""
        spd_expired = any(e.get('stat') == 'spd' for e in expired)
        if spd_expired and self._turn_manager:
            new_spd = unit.spd
            if abs(new_spd - old_spd) > 0.001:
                self._turn_manager.on_spd_change(unit, old_spd)
                self._log.append(f"  → {unit.name} SPD 버프 만료({timing_label}): {old_spd:.0f} → {new_spd:.0f}")

        for e in expired:
            buff = e.get('buff')
            if not buff:
                continue
            bl = buff.buff_data.logic_type
            # 화상 만료
            if bl == LogicType.DOT and buff.buff_data.dot_type == "burn":
                for _ in range(buff.stack_count):
                    unit.remove_tag("burn")
                self._log.append(f"  → {unit.name} 화상 만료 (스택 {buff.stack_count})")
            # 출혈 만료
            elif bl == LogicType.DOT_BLEED:
                unit.remove_tag("bleed")
                self._log.append(f"  → {unit.name} 출혈 만료")
            # 감전 만료
            elif bl == LogicType.DOT_SHOCK:
                unit.remove_tag("shock")
                self._log.append(f"  → {unit.name} 감전 만료")
            # 풍화 만료
            elif bl == LogicType.DOT_WIND_SHEAR:
                unit.remove_tag("wind_shear")
                self._log.append(f"  → {unit.name} 풍화 만료")
            # 폭탄 만료 (타이머 아직 남은 채 강제 제거 시)
            elif bl == LogicType.BOMB:
                self._log.append(f"  → {unit.name} 폭탄 해제")
            # 마커 버프 만료 시 플래그 동기화는 sync_marker_flags에서 처리

    def _apply_dots(self, unit: BattleUnit):
        """DoT 효과 발동 (화상, 독, 출혈, 감전, 풍화, 폭탄 등)"""
        import math
        bombs_to_explode = []
        for ab in unit.active_buffs:
            bd = ab.buff_data
            if bd.logic_type == LogicType.DOT:
                dmg = calc_dot_damage(unit.max_hp, bd.value, ab.stack_count, unit.def_)
                unit.take_damage(dmg)
                dot_label = bd.dot_type or 'DoT'
                self._log.append(
                    f"  → {unit.name} {dot_label} 피해 {dmg} "
                    f"(스택 {ab.stack_count}, HP {unit.current_hp:.0f}/{unit.max_hp:.0f})"
                )
            elif bd.logic_type == LogicType.DOT_HEAL_HP_RATIO:
                heal = unit.max_hp * bd.value
                actual = unit.heal(heal)
                self._log.append(f"  → {unit.name} DoT 회복 {actual:.0f}")
            # ── 출혈 DOT (ATK 비례) ──────────────────────────────
            elif bd.logic_type == LogicType.DOT_BLEED:
                # 출혈: 시전자 ATK 비례 (value = ATK 배율)
                dmg = max(1, math.floor(bd.value * ab.stack_count * (1.0 - unit.def_ / (unit.def_ + 300.0))))
                unit.take_damage(dmg)
                self._log.append(
                    f"  → {unit.name} 출혈 피해 {dmg} (스택 {ab.stack_count})")
            # ── 감전 DOT + 인접 확산 ─────────────────────────────
            elif bd.logic_type == LogicType.DOT_SHOCK:
                dmg = calc_dot_damage(unit.max_hp, bd.value, ab.stack_count, unit.def_)
                unit.take_damage(dmg)
                self._log.append(
                    f"  → {unit.name} 감전 피해 {dmg} (인접 확산)")
                # 확산은 TriggerSystem에서 ON_DEBUFF_APPLIED로 처리
            # ── 풍화 DOT (중첩형, 최대 5스택) ────────────────────
            elif bd.logic_type == LogicType.DOT_WIND_SHEAR:
                dmg = calc_dot_damage(unit.max_hp, bd.value, ab.stack_count, unit.def_)
                unit.take_damage(dmg)
                self._log.append(
                    f"  → {unit.name} 풍화 피해 {dmg} (스택 {ab.stack_count}/5)")
            # ── 폭탄 틱 (시한 체크) ──────────────────────────────
            elif bd.logic_type == LogicType.BOMB:
                if ab.remaining_turns <= 1:
                    bombs_to_explode.append(ab)
        # 폭탄 폭발 처리
        for bomb_ab in bombs_to_explode:
            bomb_dmg = max(1, math.floor(unit.max_hp * bomb_ab.buff_data.value))
            unit.take_damage(bomb_dmg)
            self._log.append(
                f"  → 💣 {unit.name} 폭탄 폭발! {bomb_dmg} 피해 "
                f"(HP {unit.current_hp:.0f}/{unit.max_hp:.0f})"
            )

    # ─── 버프 제거 ────────────────────────────────────────────────
    def remove_debuffs(self, unit: BattleUnit):
        """모든 디버프 제거"""
        unit.remove_buffs(is_debuff=True)
        self._log.append(f"  → {unit.name} 디버프 전체 제거")

    def remove_buffs(self, unit: BattleUnit):
        """모든 버프 제거"""
        unit.remove_buffs(is_debuff=False)
        self._log.append(f"  → {unit.name} 버프 전체 제거")

    # ─── 로그 ─────────────────────────────────────────────────────
    def flush_log(self) -> List[str]:
        logs = self._log[:]
        self._log.clear()
        return logs
