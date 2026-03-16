"""BattleEngine 통합 테스트 (캐릭터 비종속 – conftest make_simple_unit 사용)"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import pytest
from battle.battle_engine import BattleEngine
from battle.battle_recorder import BattleRecorder
from battle.enums import BattleResult


def _make_party(factory, n=5, side="ally", **kwargs):
    """make_simple_unit 팩토리 → CharacterData 목록 (BattleEngine 입력 형식)"""
    return [factory(name=f"유닛{i}", side=side, **kwargs).data for i in range(n)]


def _make_enemies(factory, n=3, **kwargs):
    return _make_party(factory, n=n, side="enemy", **kwargs)


class TestNormalOnly:
    def test_completes(self, make_simple_unit):
        """NormalOnly → 정상 종료"""
        eng = BattleEngine(
            ally_units=_make_party(make_simple_unit),
            enemy_units=_make_enemies(make_simple_unit),
            allow_active=False, allow_ultimate=False, seed=42,
        )
        result = eng.run()
        assert result in (BattleResult.ALLY_WIN, BattleResult.ENEMY_WIN, BattleResult.TIME_OVER)


class TestWithActiveAndUltimate:
    def test_completes(self, make_simple_unit):
        """Active+Ultimate 허용 → 정상 종료"""
        eng = BattleEngine(
            ally_units=_make_party(make_simple_unit),
            enemy_units=_make_enemies(make_simple_unit),
            allow_active=True, allow_ultimate=True,
            ultimate_mode="auto", seed=42,
        )
        result = eng.run()
        assert result in (BattleResult.ALLY_WIN, BattleResult.ENEMY_WIN, BattleResult.TIME_OVER)

    def test_stronger_ally_wins(self, make_simple_unit):
        """압도적 아군 스탯 → 아군 승리"""
        eng = BattleEngine(
            ally_units=_make_party(make_simple_unit, atk=9999, def_=9999, hp=99999),
            enemy_units=_make_enemies(make_simple_unit, atk=1, def_=1, hp=100),
            allow_active=True, allow_ultimate=True,
            ultimate_mode="auto", seed=42,
        )
        result = eng.run()
        assert result == BattleResult.ALLY_WIN


class TestSeedReproducibility:
    def test_same_seed_same_result(self, make_simple_unit):
        """동일 seed → 동일 결과 및 동일 기록 수"""
        def make_eng(recorder):
            return BattleEngine(
                ally_units=_make_party(make_simple_unit),
                enemy_units=_make_enemies(make_simple_unit),
                allow_active=True, allow_ultimate=True, seed=42, recorder=recorder,
            )

        rec1, rec2 = BattleRecorder(), BattleRecorder()
        r1 = make_eng(rec1).run()
        r2 = make_eng(rec2).run()

        assert r1 == r2
        assert len(rec1.records) == len(rec2.records)

    def test_different_seed_runs(self, make_simple_unit):
        """다른 seed → 둘 다 정상 종료"""
        def run(seed):
            return BattleEngine(
                ally_units=_make_party(make_simple_unit),
                enemy_units=_make_enemies(make_simple_unit),
                allow_active=True, allow_ultimate=True, seed=seed,
            ).run()

        r1, r2 = run(42), run(999)
        valid = (BattleResult.ALLY_WIN, BattleResult.ENEMY_WIN, BattleResult.TIME_OVER)
        assert r1 in valid
        assert r2 in valid


class TestRecorder:
    def test_recorder_captures_turns(self, make_simple_unit):
        """Recorder가 턴 기록을 수집"""
        rec = BattleRecorder()
        eng = BattleEngine(
            ally_units=_make_party(make_simple_unit),
            enemy_units=_make_enemies(make_simple_unit),
            allow_active=True, allow_ultimate=True, seed=42, recorder=rec,
        )
        eng.run()
        assert len(rec.records) > 0
        assert rec.records[0].turn_num == 1
