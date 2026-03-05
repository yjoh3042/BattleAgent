"""BattleRecorder - 턴별 구조화 데이터 수집 (HTML 시각화용)"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from battle.battle_unit import BattleUnit


@dataclass
class UnitSnapshot:
    """단일 유닛의 특정 시점 상태 스냅샷"""
    id: str
    name: str
    side: str
    role: str
    element: str
    hp: float
    max_hp: float
    barrier_hp: float
    is_alive: bool
    burn_stacks: int
    has_hard_cc: bool
    soft_cc: bool
    active_skill_cd: int
    used_ult: bool
    buffs: List[dict]   # [{name, remaining, is_debuff}]

    @property
    def hp_ratio(self) -> float:
        return self.hp / self.max_hp if self.max_hp > 0 else 0.0


@dataclass
class TurnRecord:
    """한 턴의 완전한 기록"""
    turn_num: int
    time: float
    battle_round: int
    active_unit_id: str
    is_extra: bool
    skill_name: str
    skill_type: str          # 'normal' | 'active' | 'ultimate' | 'cc_skip' | 'round_start'
    ally_sp: int
    enemy_sp: int
    units: Dict[str, UnitSnapshot]   # 턴 시작 시 스냅샷 (active 전)
    events: List[dict]               # {type, src, dst, value, label, is_crit}
    log_lines: List[str]             # 이 턴의 텍스트 로그 라인들
    result: Optional[str] = None     # 'ally_win' | 'enemy_win' | None


class BattleRecorder:
    """BattleEngine에 주입되어 턴별 데이터를 수집"""

    def __init__(self):
        self.records: List[TurnRecord] = []
        self.scenario_label: str = ""
        self._current: Optional[TurnRecord] = None
        self._log_start_idx: int = 0

    # ─── 턴 생명주기 ──────────────────────────────────────────────
    def begin_turn(
        self,
        turn_num: int,
        time: float,
        battle_round: int,
        active_unit: "BattleUnit",
        is_extra: bool,
        ally_sp: int,
        enemy_sp: int,
        all_units: Dict[str, "BattleUnit"],
        log_len: int,
    ):
        """턴 시작 시 스냅샷 수집"""
        units_snap = {uid: self._snap(u) for uid, u in all_units.items()}
        self._current = TurnRecord(
            turn_num=turn_num,
            time=round(time, 4),
            battle_round=battle_round,
            active_unit_id=active_unit.id,
            is_extra=is_extra,
            skill_name="",
            skill_type="normal",
            ally_sp=ally_sp,
            enemy_sp=enemy_sp,
            units=units_snap,
            events=[],
            log_lines=[],
        )
        self._log_start_idx = log_len

    def set_skill(self, skill_name: str, skill_type: str):
        """사용 스킬 정보 설정"""
        if self._current:
            self._current.skill_name = skill_name
            self._current.skill_type = skill_type

    def add_event(
        self,
        event_type: str,    # 'damage'|'heal'|'buff'|'debuff'|'death'|'revive'|'sp'|'ultimate'|'taunt'
        src_id: str,
        dst_id: str,
        value: float,
        label: str,
        is_crit: bool = False,
    ):
        """이벤트 기록 (스킬 실행 중 호출)"""
        if self._current:
            self._current.events.append({
                "type": event_type,
                "src": src_id,
                "dst": dst_id,
                "value": round(value),
                "label": label,
                "is_crit": is_crit,
            })

    def end_turn(self, full_log: List[str], result: Optional[str] = None):
        """턴 종료 시 로그 슬라이스 저장 후 records에 추가"""
        if self._current:
            self._current.log_lines = full_log[self._log_start_idx:]
            self._current.result = result
            self.records.append(self._current)
            self._current = None

    # ─── 스냅샷 생성 ──────────────────────────────────────────────
    @staticmethod
    def _snap(unit: "BattleUnit") -> UnitSnapshot:
        buffs = []
        for ab in unit.active_buffs:
            buffs.append({
                "name": ab.buff_data.name or ab.buff_data.id,
                "remaining": ab.remaining_turns,
                "is_debuff": ab.buff_data.is_debuff,
                "stack": ab.stack_count,
            })
        return UnitSnapshot(
            id=unit.id,
            name=unit.name,
            side=unit.side,
            role=unit.data.role.value,
            element=unit.data.element.value,
            hp=round(unit.current_hp, 1),
            max_hp=round(unit.max_hp, 1),
            barrier_hp=round(unit.barrier_hp, 1),
            is_alive=unit.is_alive,
            burn_stacks=unit.get_tag_count("burn"),
            has_hard_cc=(unit.hard_cc is not None),
            soft_cc=(unit.soft_cc is not None),
            active_skill_cd=unit.active_skill_cooldown,
            used_ult=unit.used_ultimate_this_round,
            buffs=buffs,
        )

    # ─── JSON 직렬화 ──────────────────────────────────────────────
    def to_dict(self) -> dict:
        """HTML 임베딩용 JSON 직렬화"""
        turns = []
        for r in self.records:
            units_data = {}
            for uid, snap in r.units.items():
                units_data[uid] = {
                    "id": snap.id,
                    "name": snap.name,
                    "side": snap.side,
                    "role": snap.role,
                    "element": snap.element,
                    "hp": snap.hp,
                    "max_hp": snap.max_hp,
                    "barrier_hp": snap.barrier_hp,
                    "is_alive": snap.is_alive,
                    "burn": snap.burn_stacks,
                    "cc": snap.has_hard_cc,
                    "soft_cc": snap.soft_cc,
                    "cd": snap.active_skill_cd,
                    "used_ult": snap.used_ult,
                    "buffs": snap.buffs,
                    "hp_ratio": round(snap.hp_ratio, 4),
                }
            turns.append({
                "n": r.turn_num,
                "t": r.time,
                "round": r.battle_round,
                "active": r.active_unit_id,
                "extra": r.is_extra,
                "skill": r.skill_name,
                "skill_type": r.skill_type,
                "ally_sp": r.ally_sp,
                "enemy_sp": r.enemy_sp,
                "units": units_data,
                "events": r.events,
                "log": r.log_lines,
                "result": r.result,
            })
        return {
            "scenario": self.scenario_label,
            "total_turns": len(self.records),
            "turns": turns,
        }
