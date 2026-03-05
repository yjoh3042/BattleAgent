"""SPManager 단위 테스트"""
import pytest
from battle.sp_manager import SPManager


class TestCharge:
    def test_charge_increments_both(self):
        """충전 시 양 진영 +1"""
        sp = SPManager()
        sp.charge_on_turn_start()
        assert sp.ally_sp == 1
        assert sp.enemy_sp == 1

    def test_charge_multiple(self):
        """3회 충전 → 양쪽 3"""
        sp = SPManager()
        for _ in range(3):
            sp.charge_on_turn_start()
        assert sp.ally_sp == 3
        assert sp.enemy_sp == 3


class TestMaxCap:
    def test_cap_at_10(self):
        """최대 10 캡"""
        sp = SPManager()
        for _ in range(15):
            sp.charge_on_turn_start()
        assert sp.ally_sp == 10
        assert sp.enemy_sp == 10


class TestSpendAndRefund:
    def test_spend_success(self):
        """SP 충분 시 소모 성공"""
        sp = SPManager()
        sp.ally_sp = 5
        assert sp.spend("ally", 3) is True
        assert sp.ally_sp == 2

    def test_spend_fail(self):
        """SP 부족 시 소모 실패"""
        sp = SPManager()
        sp.ally_sp = 2
        assert sp.spend("ally", 5) is False
        assert sp.ally_sp == 2  # 변화 없음

    def test_refund(self):
        """환불"""
        sp = SPManager()
        sp.ally_sp = 3
        sp.refund("ally", 4)
        assert sp.ally_sp == 7

    def test_refund_capped(self):
        """환불 시 최대치 초과 불가"""
        sp = SPManager()
        sp.ally_sp = 8
        sp.refund("ally", 5)
        assert sp.ally_sp == 10

    def test_add_sp(self):
        """스킬 효과 SP 증가"""
        sp = SPManager()
        sp.add_sp("enemy", 3)
        assert sp.enemy_sp == 3


class TestReset:
    def test_reset_zeroes(self):
        """라운드 리셋 시 0"""
        sp = SPManager()
        sp.ally_sp = 7
        sp.enemy_sp = 5
        sp.reset()
        assert sp.ally_sp == 0
        assert sp.enemy_sp == 0
