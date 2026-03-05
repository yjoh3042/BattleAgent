"""damage_calc 모듈 단위 테스트"""
import random
import pytest

from battle.enums import Element
from battle.damage_calc import (
    calc_base_damage, get_element_mult, roll_crit, get_crit_mult,
    calc_final_damage, get_burn_bonus_mult, compute_damage, roll_dodge,
)


class TestBaseDamage:
    def test_standard_formula(self):
        """Atk=300, Def=150 → 300*(1 - 150/450) = 200"""
        result = calc_base_damage(300, 150)
        assert abs(result - 200.0) < 0.01

    def test_zero_def(self):
        """Def=0 → Atk 그대로"""
        result = calc_base_damage(300, 0)
        assert abs(result - 300.0) < 0.01

    def test_equal_atk_def(self):
        """Atk==Def → Atk/2"""
        result = calc_base_damage(200, 200)
        assert abs(result - 100.0) < 0.01

    def test_penetration(self):
        """Def=200, Pen=50 → effective_def=150"""
        result = calc_base_damage(300, 200, penetration=50)
        expected = calc_base_damage(300, 150)
        assert abs(result - expected) < 0.01

    def test_penetration_exceeds_def(self):
        """Pen > Def → effective_def=0"""
        result = calc_base_damage(300, 100, penetration=200)
        assert abs(result - 300.0) < 0.01

    def test_zero_atk_def(self):
        result = calc_base_damage(0, 0)
        assert result == 0.0


class TestElementMultiplier:
    def test_fire_vs_forest(self):
        assert get_element_mult(Element.FIRE, Element.FOREST) == 1.2

    def test_forest_vs_water(self):
        assert get_element_mult(Element.FOREST, Element.WATER) == 1.2

    def test_water_vs_fire(self):
        assert get_element_mult(Element.WATER, Element.FIRE) == 1.2

    def test_light_vs_dark(self):
        assert get_element_mult(Element.LIGHT, Element.DARK) == 1.2

    def test_no_advantage(self):
        assert get_element_mult(Element.FIRE, Element.WATER) == 1.0

    def test_same_element(self):
        assert get_element_mult(Element.FIRE, Element.FIRE) == 1.0


class TestCritRoll:
    def test_guaranteed_crit(self):
        """크리 확률 100% → 항상 크리"""
        random.seed(99)
        assert roll_crit(1.0) is True

    def test_zero_crit(self):
        """크리 확률 0 → 항상 미크리"""
        random.seed(99)
        assert roll_crit(0.0) is False

    def test_crit_resist_cancels(self):
        """크리 저항이 크리 확률 이상 → 미크리"""
        random.seed(99)
        assert roll_crit(0.5, cri_resist=0.5) is False

    def test_seed_determinism(self):
        """시드 고정 시 동일 결과"""
        random.seed(42)
        r1 = roll_crit(0.5)
        random.seed(42)
        r2 = roll_crit(0.5)
        assert r1 == r2


class TestCritMult:
    def test_crit_applies(self):
        assert get_crit_mult(1.5, True) == 1.5

    def test_no_crit(self):
        assert get_crit_mult(1.5, False) == 1.0


class TestDodgeRoll:
    def test_zero_dodge(self):
        """회피율 0, 명중 1.0 → 항상 실패"""
        random.seed(42)
        assert roll_dodge(0.0, 1.0) is False

    def test_high_dodge(self):
        """회피율 1.0, 명중 1.0 → dodge - (1 - acc) = 1.0 → 항상 회피"""
        random.seed(42)
        assert roll_dodge(1.0, 1.0) is True

    def test_acc_counters_dodge(self):
        """명중이 높으면 회피 불가"""
        # dodge=0.3, acc=1.0 → effective=0.3 (확률적)
        # dodge=0.3, acc=0.7 → effective=0.0 → 회피 불가
        assert roll_dodge(0.3, 0.7) is False


class TestBurnBonus:
    def test_no_burn(self):
        assert get_burn_bonus_mult(0) == 1.0

    def test_one_stack(self):
        """1스택, bonus=0.5 → 1.5"""
        assert get_burn_bonus_mult(1, 0.5) == 1.5

    def test_two_stacks(self):
        """2스택, bonus=0.5 → 2.0"""
        assert get_burn_bonus_mult(2, 0.5) == 2.0


class TestComputeDamage:
    def test_returns_three_tuple(self, make_simple_unit):
        """compute_damage는 (dmg, is_crit, is_dodged) 3-튜플 반환"""
        random.seed(42)
        atk = make_simple_unit(name="공격자", side="ally", atk=300, def_=100)
        dfn = make_simple_unit(name="방어자", side="enemy", atk=100, def_=150)
        result = compute_damage(atk, dfn, 1.0)
        assert len(result) == 3

    def test_dodge_returns_zero(self, make_simple_unit):
        """회피 성공 시 데미지 0"""
        random.seed(42)
        atk = make_simple_unit(name="공격자", side="ally", atk=300, acc=1.0)
        dfn = make_simple_unit(name="방어자", side="enemy", dodge=1.0)
        dmg, is_crit, is_dodged = compute_damage(atk, dfn, 1.0)
        assert is_dodged is True
        assert dmg == 0

    def test_seed_reproducibility(self, make_simple_unit):
        """동일 시드 → 동일 결과"""
        atk = make_simple_unit(name="A", side="ally", atk=300)
        dfn = make_simple_unit(name="B", side="enemy", def_=150)
        random.seed(42)
        r1 = compute_damage(atk, dfn, 1.0)
        random.seed(42)
        r2 = compute_damage(atk, dfn, 1.0)
        assert r1 == r2
