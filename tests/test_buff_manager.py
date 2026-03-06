"""BuffManager 단위 테스트"""
import pytest
from battle.enums import LogicType, CCType
from battle.models import BuffData
from battle.buff_manager import BuffManager
from battle.turn_manager import TurnManager


class TestSameSourceRefresh:
    def test_same_source_refreshes_duration(self, make_simple_unit):
        """동일 출처 버프 → 턴 갱신 (새로 추가 안 함)"""
        u = make_simple_unit(name="유닛")
        bm = BuffManager()
        buff = BuffData(
            id="atk_buff", name="공격력 증가",
            source_skill_id="skill_a", logic_type=LogicType.STAT_CHANGE,
            stat="atk", value=50, duration=2,
        )
        bm.apply_buff(u, buff, "src1")
        assert len(u.active_buffs) == 1

        # 동일 출처 재적용 → 갱신
        bm.apply_buff(u, buff, "src1")
        assert len(u.active_buffs) == 1
        assert u.active_buffs[0].remaining_turns == 2  # duration 갱신


class TestDifferentSourceStack:
    def test_different_source_adds_new(self, make_simple_unit):
        """다른 출처 → 새 스택 추가"""
        u = make_simple_unit(name="유닛")
        bm = BuffManager()
        buff_a = BuffData(
            id="atk_buff", name="공격력A",
            source_skill_id="skill_a", logic_type=LogicType.STAT_CHANGE,
            stat="atk", value=50, duration=2,
        )
        buff_b = BuffData(
            id="atk_buff", name="공격력B",
            source_skill_id="skill_b", logic_type=LogicType.STAT_CHANGE,
            stat="atk", value=30, duration=2,
        )
        bm.apply_buff(u, buff_a, "src1")
        bm.apply_buff(u, buff_b, "src2")
        assert len(u.active_buffs) == 2
        # 합산 확인: base 300 + 50 + 30 = 380
        assert abs(u.atk - 380.0) < 0.01


class TestDotTick:
    def test_dot_deals_damage(self, make_simple_unit):
        """DoT 턴 시작 시 피해 발동 (CharacterTurnStart)"""
        u = make_simple_unit(name="피격자", hp=5000)
        bm = BuffManager()
        burn = BuffData(
            id="burn_dot", name="화상",
            source_skill_id="fire_skill", logic_type=LogicType.DOT,
            dot_type="burn", value=0.05, duration=2,
            is_debuff=True, max_stacks=5,
            buff_turn_reduce_timing="CharacterTurnStart",
        )
        bm.apply_buff(u, burn, "attacker")
        hp_before = u.current_hp
        bm.tick_turn_start(u)   # 턴 시작: DoT 발동
        assert u.current_hp < hp_before  # DoT 피해 발생


class TestSpdBuffTurnRecalc:
    def test_spd_buff_triggers_reschedule(self, make_simple_unit):
        """SPD 버프 적용 시 TurnManager 재계산"""
        u = make_simple_unit(name="유닛", spd=100)
        tm = TurnManager()
        tm.initialize([u])
        bm = BuffManager(turn_manager=tm)

        old_next = tm._unit_next_time[u.id]

        spd_buff = BuffData(
            id="spd_buff", name="속도증가",
            source_skill_id="quick_skill", logic_type=LogicType.STAT_CHANGE,
            stat="spd", value=50, duration=2,
        )
        bm.apply_buff(u, spd_buff, "caster")

        new_next = tm._unit_next_time[u.id]
        assert new_next < old_next  # SPD 증가 → 다음 행동 앞당겨짐
