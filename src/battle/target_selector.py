"""TargetSelector - 스킬 타겟 선택 로직
도발(Taunt) 처리, 다양한 타겟 전략 지원
"""
from __future__ import annotations
import random
from typing import List, Optional, TYPE_CHECKING

from battle.enums import TargetType, Role

if TYPE_CHECKING:
    from battle.battle_unit import BattleUnit


class TargetSelector:
    """스킬의 TargetType에 따라 타겟 유닛 목록 선택"""

    def select(
        self,
        caster: BattleUnit,
        target_type: TargetType,
        allies: List[BattleUnit],       # 전체 아군 (사망 포함)
        enemies: List[BattleUnit],      # 전체 적군 (사망 포함)
    ) -> List[BattleUnit]:
        """
        타겟 선택 후 반환.
        도발이 걸린 경우 강제 타겟팅 적용.
        """
        alive_allies = [u for u in allies if u.is_alive]
        alive_enemies = [u for u in enemies if u.is_alive]

        # 부활 타겟은 사망자만 필요
        if target_type == TargetType.ALLY_DEAD_RANDOM:
            dead_allies = [u for u in allies if not u.is_alive]
            return [random.choice(dead_allies)] if dead_allies else []

        if not alive_enemies and target_type in (
            TargetType.ENEMY_LOWEST_HP, TargetType.ENEMY_HIGHEST_HP,
            TargetType.ENEMY_HIGHEST_SPD, TargetType.ENEMY_RANDOM,
            TargetType.ALL_ENEMY, TargetType.ENEMY_RANDOM_2, TargetType.ENEMY_RANDOM_3,
        ):
            return []

        selected = self._select_by_type(caster, target_type, alive_allies, alive_enemies)

        # 도발 처리: 적을 대상으로 하는 스킬에 도발 강제 포함
        selected = self._apply_taunt(caster, selected, alive_enemies, target_type)

        return selected

    def _select_by_type(
        self,
        caster: BattleUnit,
        target_type: TargetType,
        alive_allies: List[BattleUnit],
        alive_enemies: List[BattleUnit],
    ) -> List[BattleUnit]:
        """TargetType별 타겟 선택 로직"""

        if target_type == TargetType.SELF:
            return [caster]

        elif target_type == TargetType.ALLY_LOWEST_HP:
            return [min(alive_allies, key=lambda u: u.hp_ratio)] if alive_allies else []

        elif target_type == TargetType.ALLY_HIGHEST_ATK:
            return [max(alive_allies, key=lambda u: u.atk)] if alive_allies else []

        elif target_type == TargetType.ALL_ALLY:
            return list(alive_allies)

        elif target_type == TargetType.ENEMY_LOWEST_HP:
            return [min(alive_enemies, key=lambda u: u.current_hp)] if alive_enemies else []

        elif target_type == TargetType.ENEMY_HIGHEST_HP:
            return [max(alive_enemies, key=lambda u: u.current_hp)] if alive_enemies else []

        elif target_type == TargetType.ENEMY_HIGHEST_SPD:
            return [max(alive_enemies, key=lambda u: u.spd)] if alive_enemies else []

        elif target_type == TargetType.ENEMY_RANDOM:
            return [random.choice(alive_enemies)] if alive_enemies else []

        elif target_type == TargetType.ALL_ENEMY:
            return list(alive_enemies)

        elif target_type == TargetType.ENEMY_RANDOM_2:
            count = min(2, len(alive_enemies))
            return random.sample(alive_enemies, count) if alive_enemies else []

        elif target_type == TargetType.ENEMY_RANDOM_3:
            count = min(3, len(alive_enemies))
            return random.sample(alive_enemies, count) if alive_enemies else []

        elif target_type == TargetType.ALLY_LOWEST_HP_2:
            sorted_allies = sorted(alive_allies, key=lambda u: u.hp_ratio)
            return sorted_allies[:2] if alive_allies else []

        elif target_type == TargetType.ALLY_ROLE_ATTACKER:
            attackers = [u for u in alive_allies if u.data.role == Role.ATTACKER]
            return attackers if attackers else list(alive_allies)  # 공격형 없으면 전체 아군

        return []

    def _apply_taunt(
        self,
        caster: BattleUnit,
        selected: List[BattleUnit],
        alive_enemies: List[BattleUnit],
        target_type: TargetType,
    ) -> List[BattleUnit]:
        """
        도발 처리:
        - 시전자가 도발을 받은 경우 (caster.taunted_by != None):
          → 단일 타겟: 도발자로 강제 변경
          → 다중 타겟: 도발자 반드시 포함
        """
        if not caster.taunted_by:
            return selected

        # 도발자 찾기
        taunter = next((u for u in alive_enemies if u.id == caster.taunted_by), None)
        if taunter is None:
            # 도발자가 이미 죽었으면 도발 해제
            caster.taunted_by = None
            return selected

        # 아군 타겟 스킬은 도발 무시
        if target_type in (
            TargetType.SELF, TargetType.ALLY_LOWEST_HP, TargetType.ALLY_HIGHEST_ATK,
            TargetType.ALL_ALLY, TargetType.ALLY_DEAD_RANDOM,
            TargetType.ALLY_LOWEST_HP_2, TargetType.ALLY_ROLE_ATTACKER,
        ):
            return selected

        # 단일 타겟인 경우 강제 교체
        if target_type in (
            TargetType.ENEMY_LOWEST_HP, TargetType.ENEMY_HIGHEST_HP,
            TargetType.ENEMY_HIGHEST_SPD, TargetType.ENEMY_RANDOM,
        ):
            return [taunter]

        # 다중 타겟인 경우 반드시 포함
        if taunter not in selected:
            selected = list(selected) + [taunter]

        return selected

    # ─── 도발 설정 ────────────────────────────────────────────────
    @staticmethod
    def apply_taunt_to_enemies(
        taunter: BattleUnit,
        enemies: List[BattleUnit],
        duration: int = 2,
    ):
        """적군 전체에 도발 부여"""
        for enemy in enemies:
            if enemy.is_alive:
                enemy.apply_taunt(taunter.id, duration)
