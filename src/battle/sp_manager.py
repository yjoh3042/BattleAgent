"""SPManager - 공용 SP (Special Point) 관리
아군/적군 각각 독립된 SP 풀. 매 턴 시작 +1, 배틀 라운드 전환 시 0으로 초기화.
"""
from __future__ import annotations


class SPManager:
    """
    공용 SP 관리자.
    - ally_sp: 아군 SP (최대 MAX_SP)
    - enemy_sp: 적군 SP (최대 MAX_SP)
    - 누군가의 턴 시작마다 양 진영 SP +1
    - 배틀 라운드 전환(10 단위 시간) 시 양쪽 0으로 초기화
    """

    MAX_SP: int = 10

    def __init__(self):
        self.ally_sp: int = 0
        self.enemy_sp: int = 0

    # ─── 충전 ─────────────────────────────────────────────────────
    def charge_on_turn_start(self):
        """
        턴 시작 시 양 진영 SP +1.
        (기획: 피아 구분 없이 누군가의 턴이 시작될 때마다 양측 +1)
        """
        self.ally_sp = min(self.MAX_SP, self.ally_sp + 1)
        self.enemy_sp = min(self.MAX_SP, self.enemy_sp + 1)

    # ─── 조회 ─────────────────────────────────────────────────────
    def get_sp(self, side: str) -> int:
        """'ally' 또는 'enemy' 진영의 현재 SP 반환"""
        return self.ally_sp if side == "ally" else self.enemy_sp

    def can_spend(self, side: str, amount: int) -> bool:
        """해당 진영이 amount만큼 SP를 소모할 수 있는지 확인"""
        return self.get_sp(side) >= amount

    # ─── 소모 ─────────────────────────────────────────────────────
    def spend(self, side: str, amount: int) -> bool:
        """
        SP 소모. 성공 시 True, 부족 시 False.
        """
        if not self.can_spend(side, amount):
            return False
        if side == "ally":
            self.ally_sp -= amount
        else:
            self.enemy_sp -= amount
        return True

    def refund(self, side: str, amount: int):
        """SP 환불 (수동 얼티밋 대기 취소 등)"""
        if side == "ally":
            self.ally_sp = min(self.MAX_SP, self.ally_sp + amount)
        else:
            self.enemy_sp = min(self.MAX_SP, self.enemy_sp + amount)

    # ─── 강제 변경 ────────────────────────────────────────────────
    def add_sp(self, side: str, amount: int):
        """SP 직접 증가 (스킬 효과로 인한 SP 증가)"""
        if side == "ally":
            self.ally_sp = min(self.MAX_SP, self.ally_sp + amount)
        else:
            self.enemy_sp = min(self.MAX_SP, self.enemy_sp + amount)

    # ─── 라운드 리셋 ──────────────────────────────────────────────
    def reset(self):
        """배틀 라운드 전환 시 양쪽 SP 0으로 초기화"""
        self.ally_sp = 0
        self.enemy_sp = 0

    def __repr__(self) -> str:
        return f"SPManager(ally={self.ally_sp}/{self.MAX_SP}, enemy={self.enemy_sp}/{self.MAX_SP})"
