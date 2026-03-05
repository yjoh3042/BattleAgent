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

    # ─── 버프 틱 (턴 종료 시) ─────────────────────────────────────
    def tick_all_buffs(self, unit: BattleUnit):
        """
        턴 종료 시:
        1. DoT 피해/회복 발동
        2. 버프 남은 턴 -1, 만료 제거
        3. SPD 버프 만료 시 TurnManager 재계산
        """
        # DoT 먼저 발동 (버프가 아직 살아있을 때)
        self._apply_dots(unit)

        # 버프 틱 (BattleUnit.on_turn_end 호출)
        old_spd = unit.spd
        expired = unit.on_turn_end()

        # 만료된 SPD 버프가 있으면 TurnManager 재계산
        spd_expired = any(e.get('stat') == 'spd' for e in expired)
        if spd_expired and self._turn_manager:
            new_spd = unit.spd
            if abs(new_spd - old_spd) > 0.001:
                self._turn_manager.on_spd_change(unit, old_spd)
                self._log.append(f"  → {unit.name} SPD 버프 만료: {old_spd:.0f} → {new_spd:.0f}")

        # 화상 DoT 버프 만료 시 태그 정리
        for e in expired:
            buff = e.get('buff')
            if buff and buff.buff_data.logic_type == LogicType.DOT and buff.buff_data.dot_type == "burn":
                # 스택 수만큼 태그 제거
                for _ in range(buff.stack_count):
                    unit.remove_tag("burn")
                self._log.append(f"  → {unit.name} 화상 만료 (스택 {buff.stack_count})")

    def _apply_dots(self, unit: BattleUnit):
        """DoT 효과 발동 (화상, 독 등)"""
        for ab in unit.active_buffs:
            bd = ab.buff_data
            if bd.logic_type == LogicType.DOT:
                dmg = calc_dot_damage(unit.max_hp, bd.value, ab.stack_count)
                unit.take_damage(dmg)
                self._log.append(
                    f"  → {unit.name} {bd.dot_type or 'DoT'} 피해 {dmg} "
                    f"(스택 {ab.stack_count}, HP {unit.current_hp:.0f}/{unit.max_hp:.0f})"
                )
            elif bd.logic_type == LogicType.DOT_HEAL_HP_RATIO:
                heal = unit.max_hp * bd.value
                actual = unit.heal(heal)
                self._log.append(f"  → {unit.name} DoT 회복 {actual:.0f}")

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
