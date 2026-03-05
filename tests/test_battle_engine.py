"""BattleEngine 통합 테스트"""
import sys
import os
import random

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import pytest
from battle.battle_engine import BattleEngine
from battle.battle_recorder import BattleRecorder
from battle.enums import BattleResult
from fixtures.test_data import get_party1, get_party2, get_enemies


class TestNormalOnly:
    def test_completes(self):
        """시나리오1 NormalOnly → 정상 종료"""
        eng = BattleEngine(
            ally_units=get_party1(), enemy_units=get_enemies(),
            allow_active=False, allow_ultimate=False, seed=42,
        )
        result = eng.run()
        assert result in (BattleResult.ALLY_WIN, BattleResult.ENEMY_WIN, BattleResult.TIME_OVER)


class TestSettingUltimate:
    def test_ally_wins(self):
        """시나리오4 SettingUltimate → 아군 승리"""
        eng = BattleEngine(
            ally_units=get_party1(), enemy_units=get_enemies(),
            allow_active=True, allow_ultimate=True,
            ultimate_mode="manual_ordered",
            ultimate_order=["citria", "hild", "arahan", "frey", "dana"],
            seed=42,
        )
        result = eng.run()
        assert result == BattleResult.ALLY_WIN


class TestBurnSynergyParty:
    def test_party2_wins(self):
        """시나리오6 화상 시너지 파티 → 아군 승리"""
        eng = BattleEngine(
            ally_units=get_party2(), enemy_units=get_enemies(),
            allow_active=True, allow_ultimate=True,
            ultimate_mode="manual_ordered",
            ultimate_order=["citria", "laga", "gumiho", "kara", "cain"],
            seed=42,
        )
        result = eng.run()
        assert result == BattleResult.ALLY_WIN


class TestSeedReproducibility:
    def test_same_seed_same_result(self):
        """동일 seed → 동일 결과"""
        rec1 = BattleRecorder()
        eng1 = BattleEngine(
            ally_units=get_party1(), enemy_units=get_enemies(),
            allow_active=True, allow_ultimate=True, seed=42, recorder=rec1,
        )
        r1 = eng1.run()

        rec2 = BattleRecorder()
        eng2 = BattleEngine(
            ally_units=get_party1(), enemy_units=get_enemies(),
            allow_active=True, allow_ultimate=True, seed=42, recorder=rec2,
        )
        r2 = eng2.run()

        assert r1 == r2
        assert len(rec1.records) == len(rec2.records)

    def test_different_seed_may_differ(self):
        """다른 seed → 결과가 다를 수 있음 (적어도 실행 가능)"""
        eng1 = BattleEngine(
            ally_units=get_party1(), enemy_units=get_enemies(),
            allow_active=True, allow_ultimate=True, seed=42,
        )
        eng2 = BattleEngine(
            ally_units=get_party1(), enemy_units=get_enemies(),
            allow_active=True, allow_ultimate=True, seed=999,
        )
        r1 = eng1.run()
        r2 = eng2.run()
        # 둘 다 정상 종료
        assert r1 in (BattleResult.ALLY_WIN, BattleResult.ENEMY_WIN, BattleResult.TIME_OVER)
        assert r2 in (BattleResult.ALLY_WIN, BattleResult.ENEMY_WIN, BattleResult.TIME_OVER)


class TestRecorder:
    def test_recorder_captures_turns(self):
        """Recorder가 턴 기록을 수집"""
        rec = BattleRecorder()
        eng = BattleEngine(
            ally_units=get_party1(), enemy_units=get_enemies(),
            allow_active=True, allow_ultimate=True, seed=42, recorder=rec,
        )
        eng.run()
        assert len(rec.records) > 0
        assert rec.records[0].turn_num == 1
