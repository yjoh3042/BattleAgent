"""TurnManager 단위 테스트"""
import pytest
from battle.turn_manager import TurnManager, TURN_LENGTH, ROUND_INTERVAL


class TestCTBOrdering:
    def test_faster_unit_acts_first(self, make_simple_unit):
        """SPD 100 vs SPD 50 → SPD 100이 먼저 행동"""
        fast = make_simple_unit(name="빠름", spd=100)
        slow = make_simple_unit(name="느림", spd=50)
        tm = TurnManager()
        tm.initialize([fast, slow])
        entry = tm.pop_next()
        assert entry.unit_id == fast.id  # 300/100=3.0 < 300/50=6.0

    def test_same_spd_uses_sequence(self, make_simple_unit):
        """동일 SPD → 등록 순서대로"""
        u1 = make_simple_unit(name="유닛1", spd=100)
        u2 = make_simple_unit(name="유닛2", spd=100)
        tm = TurnManager()
        tm.initialize([u1, u2])
        entry = tm.pop_next()
        assert entry.unit_id == u1.id


class TestExtraTurn:
    def test_extra_turn_inserted_before_current(self, make_simple_unit):
        """Extra turn은 현재 시간보다 앞에 배치"""
        u1 = make_simple_unit(name="유닛1", spd=100)
        u2 = make_simple_unit(name="유닛2", spd=50)
        tm = TurnManager()
        tm.initialize([u1, u2])
        tm.pop_next()  # u1 행동 (t=3.0)
        tm.reschedule_unit(u1)  # u1 next at t=6.0
        # u2는 t=6.0에 행동 예정
        tm.add_extra_turn(u1)  # extra at t=3.0 - epsilon
        entry = tm.pop_next()
        assert entry.unit_id == u1.id
        assert entry.is_extra is True


class TestSpdChangeReschedule:
    def test_spd_increase_moves_forward(self, make_simple_unit):
        """SPD 증가 → 다음 행동 시간 앞당겨짐"""
        u = make_simple_unit(name="유닛", spd=100)
        tm = TurnManager()
        tm.initialize([u])
        original_next = tm._unit_next_time[u.id]  # 3.0
        tm.current_time = 0.0

        # SPD 100 → 200으로 변경 시뮬레이션
        old_spd = 100.0
        u.data.stats.spd = 200  # 직접 변경
        tm.on_spd_change(u, old_spd)

        new_next = tm._unit_next_time[u.id]
        assert new_next < original_next  # 앞당겨짐


class TestBattleRound:
    def test_round_transition(self, make_simple_unit):
        """시간이 10 넘으면 배틀 라운드 전환"""
        tm = TurnManager()
        tm.current_time = 10.5
        assert tm.check_battle_round() is True
        assert tm.battle_round == 1

    def test_no_transition_same_round(self):
        """같은 라운드 안에서는 전환 없음"""
        tm = TurnManager()
        tm.current_time = 5.0
        assert tm.check_battle_round() is False
        assert tm.battle_round == 0

    def test_multiple_rounds(self):
        """여러 라운드 진행"""
        tm = TurnManager()
        tm.current_time = 25.0
        assert tm.check_battle_round() is True
        assert tm.battle_round == 2
