"""TurnManager - ATB/CTB 턴 관리 시스템

ATB 기획(게이지 충전)을 CTB(heapq 행동 예약)로 동일하게 시뮬레이션.
행동 간격 = BATTLE_LENGTH / SPD, heapq 기반 우선순위 큐, Extra Turn 끼어들기 지원.
라운드 전환(ROUND_INTERVAL 단위)마다 전원 행동게이지를 현재 SPD 기준으로 재계산.
"""
from __future__ import annotations
import heapq
from dataclasses import dataclass, field
from typing import Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from battle.battle_unit import BattleUnit

from battle.rules import BATTLE_LENGTH, MAX_TURN_TIME

TURN_LENGTH: float = float(BATTLE_LENGTH)     # 기본 행동 거리 (= BattleLength)
ROUND_INTERVAL: float = float(MAX_TURN_TIME)  # 배틀 라운드 전환 간격 (= Max Turn Time)
MAX_EXTRA_TURNS: int = 100     # 엑스트라 턴 최대 횟수 (무한 루프 방지)
EXTRA_TURN_EPSILON: float = 1e-6  # 끼어들기 시 현재 시간보다 약간 앞 배치


@dataclass(order=True)
class TurnEntry:
    """턴 큐의 엔트리. action_time 기준 정렬."""
    action_time: float
    sequence: int                          # 동일 시간 타이브레이커
    unit_id: str = field(compare=False)
    is_extra: bool = field(compare=False, default=False)


class TurnManager:
    """
    CTB 턴 관리자.
    - heapq로 next_action_time이 가장 작은 유닛이 먼저 행동
    - 속도 버프/디버프 즉시 반영 (동적 재정렬)
    - 10 단위 시간마다 배틀 라운드 전환
    - Ultimate 사용 시 current_time - ε 로 끼어들기
    """

    def __init__(self):
        self._heap: List[TurnEntry] = []
        self._sequence: int = 0
        self.current_time: float = 0.0
        self.battle_round: int = 0          # 현재 배틀 라운드 번호
        self._extra_turn_count: int = 0
        # 유닛별 마지막 등록된 next_action_time (중복 pop 방지)
        self._unit_next_time: Dict[str, float] = {}

    # ─── 초기화 ───────────────────────────────────────────────────
    def initialize(self, units: List[BattleUnit]):
        """전투 시작 시 모든 유닛의 첫 행동 시간 계산"""
        self._heap.clear()
        self._unit_next_time.clear()
        for unit in units:
            t = TURN_LENGTH / unit.spd
            self._push(t, unit.id, is_extra=False)

    # ─── heapq 조작 ───────────────────────────────────────────────
    def _push(self, action_time: float, unit_id: str, is_extra: bool = False):
        self._sequence += 1
        entry = TurnEntry(action_time, self._sequence, unit_id, is_extra)
        heapq.heappush(self._heap, entry)
        if not is_extra:
            self._unit_next_time[unit_id] = action_time

    def peek_next(self) -> Optional[TurnEntry]:
        """다음 행동 유닛을 팝하지 않고 확인"""
        while self._heap:
            top = self._heap[0]
            # 무효화된 엔트리 스킵 (reschedule로 덮어쓴 경우)
            if not top.is_extra and self._unit_next_time.get(top.unit_id) != top.action_time:
                heapq.heappop(self._heap)
                continue
            return top
        return None

    def pop_next(self) -> Optional[TurnEntry]:
        """다음 행동 유닛 팝"""
        while self._heap:
            entry = heapq.heappop(self._heap)
            # 무효화된 일반 턴 엔트리 스킵
            if not entry.is_extra:
                if self._unit_next_time.get(entry.unit_id) != entry.action_time:
                    continue
            self.current_time = entry.action_time
            return entry
        return None

    # ─── 재스케줄 (일반 턴) ───────────────────────────────────────
    def reschedule_unit(self, unit: BattleUnit):
        """일반 행동 후 다음 행동 시간 등록"""
        next_time = self.current_time + TURN_LENGTH / unit.spd
        self._push(next_time, unit.id, is_extra=False)

    # ─── 엑스트라 턴 (Ultimate/Counter) ──────────────────────────
    def add_extra_turn(self, unit: BattleUnit) -> bool:
        """
        Ultimate 또는 카운터 발동 시 끼어들기 턴 등록.
        현재 시간보다 약간 앞에 배치해 최우선 실행.
        """
        if self._extra_turn_count >= MAX_EXTRA_TURNS:
            return False
        extra_time = self.current_time - EXTRA_TURN_EPSILON * (self._extra_turn_count + 1)
        self._sequence += 1
        entry = TurnEntry(extra_time, self._sequence, unit.id, is_extra=True)
        heapq.heappush(self._heap, entry)
        self._extra_turn_count += 1
        return True

    # ─── 속도 변화 즉시 반영 ──────────────────────────────────────
    def on_spd_change(self, unit: BattleUnit, old_spd: float):
        """
        속도 버프/디버프 즉시 반영:
        남은 거리 = (등록된 next_time - current_time) * old_spd
        새 next_time = current_time + 남은 거리 / new_spd
        """
        old_next = self._unit_next_time.get(unit.id)
        if old_next is None:
            return
        if old_next <= self.current_time:
            # 이미 지나간 턴은 재계산 불필요
            return
        remaining_distance = (old_next - self.current_time) * old_spd
        new_next = self.current_time + remaining_distance / unit.spd
        # 기존 엔트리는 무효화되고 새 엔트리 추가
        self._push(new_next, unit.id, is_extra=False)

    # ─── 배틀 라운드 전환 체크 ────────────────────────────────────
    def check_battle_round(self) -> bool:
        """
        현재 시간이 새 배틀 라운드 경계를 넘었는지 확인.
        10 단위마다 라운드 증가. True면 라운드 전환 발생.
        """
        new_round = int(self.current_time // ROUND_INTERVAL)
        if new_round > self.battle_round:
            self.battle_round = new_round
            return True
        return False

    # ─── 라운드 전환 시 전원 행동큐 재계산 ─────────────────────────
    def recalculate_all(self, units: list[BattleUnit]):
        """
        라운드 전환 시 전원 행동게이지를 현재 SPD 기준으로 재계산.
        라운드 경계 시점(battle_round * ROUND_INTERVAL)으로부터
        TURN_LENGTH / SPD 만큼 뒤에 행동 시간을 재배치한다.
        기존 엔트리는 _unit_next_time 덮어쓰기로 자동 무효화.
        """
        round_boundary = self.battle_round * ROUND_INTERVAL
        for unit in units:
            if unit.is_alive:
                next_time = round_boundary + TURN_LENGTH / unit.spd
                self._push(next_time, unit.id, is_extra=False)

    # ─── 유닛 제거 (사망) ─────────────────────────────────────────
    def remove_unit(self, unit_id: str):
        """사망한 유닛을 큐에서 논리적으로 제거 (무효화)"""
        self._unit_next_time.pop(unit_id, None)
        # heap 엔트리는 pop 시 무효화 처리로 자동 스킵됨

    # ─── 상태 정보 ────────────────────────────────────────────────
    def get_turn_order_preview(self, units: Dict[str, BattleUnit], count: int = 8) -> List[str]:
        """다음 N개 행동 순서 미리보기 (디버그용, 힙 수정 없음)"""
        snapshot = sorted(self._heap)
        result = []
        seen_extra = set()
        for entry in snapshot:
            if len(result) >= count:
                break
            unit = units.get(entry.unit_id)
            if unit and unit.is_alive:
                label = f"[Extra]" if entry.is_extra else ""
                result.append(f"t={entry.action_time:.2f} {entry.unit_id}{label}")
        return result

    def __repr__(self) -> str:
        return f"TurnManager(time={self.current_time:.2f}, round={self.battle_round}, queue_size={len(self._heap)})"
