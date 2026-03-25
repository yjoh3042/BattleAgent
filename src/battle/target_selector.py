"""TargetSelector - 스킬 타겟 선택 로직
도발(Taunt) 처리, 3×3 타일 포지셔닝, Near 거리 기반 타겟 지원
"""
from __future__ import annotations
import random
from typing import List, Optional, TYPE_CHECKING

from battle.enums import TargetType, Role, Element

if TYPE_CHECKING:
    from battle.battle_unit import BattleUnit


# 아군 타겟 TargetType 집합 (도발 무시)
_ALLY_TARGET_TYPES = frozenset({
    TargetType.SELF,
    TargetType.ALLY_LOWEST_HP,
    TargetType.ALLY_HIGHEST_ATK,
    TargetType.ALL_ALLY,
    TargetType.ALLY_DEAD_RANDOM,
    TargetType.ALLY_LOWEST_HP_2,
    TargetType.ALLY_ROLE_ATTACKER,
    TargetType.ALLY_ROLE_DEFENDER,
    TargetType.ALLY_SAME_ROW,
    TargetType.ALLY_BEHIND,
    TargetType.ALLY_LOWEST_HP_3,
    TargetType.ALLY_SAME_ELEMENT,
    TargetType.ALLY_ADJACENT,
    TargetType.ALLY_FRONT,
    TargetType.ALLY_DEAD_ALL,
    TargetType.ALLY_MOST_BUFFS,
})


class TargetSelector:
    """스킬의 TargetType에 따라 타겟 유닛 목록 선택"""

    def select(
        self,
        caster: 'BattleUnit',
        target_type: TargetType,
        allies: List['BattleUnit'],       # 전체 아군 (사망 포함)
        enemies: List['BattleUnit'],      # 전체 적군 (사망 포함)
    ) -> List['BattleUnit']:
        """
        타겟 선택 후 반환.
        - 두 진영은 3×3 그리드로 서로 마주보며 배치
        - Near 계열: 타일 거리 = caster.row + target.row + |caster.col - target.col|
        - 도발이 걸린 경우 강제 타겟팅 적용
        """
        alive_allies = [u for u in allies if u.is_alive]
        alive_enemies = [u for u in enemies if u.is_alive]

        # 부활 타겟은 사망자만 필요
        if target_type == TargetType.ALLY_DEAD_RANDOM:
            dead_allies = [u for u in allies if not u.is_alive]
            return [random.choice(dead_allies)] if dead_allies else []

        if not alive_enemies and target_type not in _ALLY_TARGET_TYPES:
            return []

        selected = self._select_by_type(caster, target_type, alive_allies, alive_enemies)

        # 도발 처리: 전체 alive_enemies 에서 도발자 탐색
        selected = self._apply_taunt(caster, selected, alive_enemies, target_type)

        return selected

    # ─── 타일 거리 계산 ───────────────────────────────────────────
    @staticmethod
    def _tile_distance(caster: 'BattleUnit', target: 'BattleUnit') -> int:
        """
        두 진영이 마주보는 3×3 그리드 기준 타일 거리.
        거리 = caster.tile_row + target.tile_row + |caster.tile_col - target.tile_col|
        (row 0=전열, 2=후열; 양 진영 row 0끼리가 가장 가까움)
        """
        return caster.tile_row + target.tile_row + abs(caster.tile_col - target.tile_col)

    @classmethod
    def _nearest_enemy(cls, caster: 'BattleUnit', alive_enemies: List['BattleUnit']) -> Optional['BattleUnit']:
        """타일 거리가 가장 가까운 적 1명 (동거리 시 HP 낮은 쪽 우선)"""
        if not alive_enemies:
            return None
        return min(alive_enemies, key=lambda u: (cls._tile_distance(caster, u), u.current_hp))

    # ─── 전열/후열 유틸 ───────────────────────────────────────────
    @staticmethod
    def _get_effective_front_row(alive_units: List['BattleUnit']) -> List['BattleUnit']:
        """살아있는 유닛 중 row 값이 가장 작은(최전열) 유닛들 반환"""
        if not alive_units:
            return []
        min_row = min(u.tile_row for u in alive_units)
        return [u for u in alive_units if u.tile_row == min_row]

    @staticmethod
    def _get_effective_back_row(alive_units: List['BattleUnit']) -> List['BattleUnit']:
        """살아있는 유닛 중 row 값이 가장 큰(최후열) 유닛들 반환"""
        if not alive_units:
            return []
        max_row = max(u.tile_row for u in alive_units)
        return [u for u in alive_units if u.tile_row == max_row]

    @staticmethod
    def _get_effective_last_col(alive_units: List['BattleUnit']) -> List['BattleUnit']:
        """살아있는 유닛 중 col 값이 가장 큰(최우열) 유닛들 반환"""
        if not alive_units:
            return []
        max_col = max(u.tile_col for u in alive_units)
        return [u for u in alive_units if u.tile_col == max_col]

    # ─── TargetType별 선택 로직 ───────────────────────────────────
    def _select_by_type(
        self,
        caster: 'BattleUnit',
        target_type: TargetType,
        alive_allies: List['BattleUnit'],
        alive_enemies: List['BattleUnit'],
    ) -> List['BattleUnit']:

        # ── 아군 타겟 ──────────────────────────────────────────────
        if target_type == TargetType.SELF:
            return [caster]

        elif target_type == TargetType.ALLY_LOWEST_HP:
            return [min(alive_allies, key=lambda u: u.hp_ratio)] if alive_allies else []

        elif target_type == TargetType.ALLY_HIGHEST_ATK:
            return [max(alive_allies, key=lambda u: u.atk)] if alive_allies else []

        elif target_type == TargetType.ALL_ALLY:
            return list(alive_allies)

        elif target_type == TargetType.ALLY_LOWEST_HP_2:
            sorted_allies = sorted(alive_allies, key=lambda u: u.hp_ratio)
            return sorted_allies[:2] if alive_allies else []

        elif target_type == TargetType.ALLY_ROLE_ATTACKER:
            attackers = [u for u in alive_allies if u.data.role == Role.ATTACKER]
            return attackers if attackers else list(alive_allies)

        elif target_type == TargetType.ALLY_ROLE_DEFENDER:
            defenders = [u for u in alive_allies if u.data.role == Role.DEFENDER]
            return defenders if defenders else list(alive_allies)

        elif target_type == TargetType.ALLY_DEAD_RANDOM:
            return []  # select() 최상단에서 처리됨

        # ── 아군 타일 기반 ──────────────────────────────────────────
        elif target_type == TargetType.ALLY_SAME_ROW:
            # 시전자와 같은 행의 아군 (자신 제외)
            return [u for u in alive_allies
                    if u.tile_row == caster.tile_row and u.id != caster.id]

        elif target_type == TargetType.ALLY_BEHIND:
            # 자신 바로 뒤 1칸 (row+1, 동일 col) — 없으면 []
            behind_row = caster.tile_row + 1
            behind = [u for u in alive_allies
                      if u.tile_row == behind_row and u.tile_col == caster.tile_col
                      and u.id != caster.id]
            return behind

        elif target_type == TargetType.ALLY_LOWEST_HP_3:
            # 체력 낮은 아군 3명
            sorted_allies = sorted(alive_allies, key=lambda u: u.hp_ratio)
            return sorted_allies[:3] if alive_allies else []

        elif target_type == TargetType.ALLY_SAME_ELEMENT:
            # 같은 속성 아군 전체 (자신 포함)
            same_el = [u for u in alive_allies if u.data.element == caster.data.element]
            return same_el if same_el else list(alive_allies)

        elif target_type == TargetType.ALLY_ADJACENT:
            # 자신 양옆 아군 (같은 행 ±1열, 자신 제외)
            adj = [u for u in alive_allies
                   if u.tile_row == caster.tile_row
                   and abs(u.tile_col - caster.tile_col) == 1
                   and u.id != caster.id]
            return adj

        elif target_type == TargetType.ALLY_FRONT:
            # 자신 바로 앞 1칸 (row-1, 동일 col) — 없으면 []
            front_row = caster.tile_row - 1
            front = [u for u in alive_allies
                     if u.tile_row == front_row and u.tile_col == caster.tile_col
                     and u.id != caster.id]
            return front

        # ── 적군 Near 계열 (타일 거리 기반) ───────────────────────
        elif target_type == TargetType.ENEMY_NEAR:
            # 가장 가까운 적 1명
            near = self._nearest_enemy(caster, alive_enemies)
            return [near] if near else []

        elif target_type == TargetType.ENEMY_NEAR_ROW:
            # 가장 가까운 적 + 해당 적의 행(row) 전체
            near = self._nearest_enemy(caster, alive_enemies)
            if not near:
                return []
            return [u for u in alive_enemies if u.tile_row == near.tile_row]

        elif target_type == TargetType.ENEMY_NEAR_CROSS:
            # 가장 가까운 적 + 십자(상하좌우 인접 1칸) 형태
            near = self._nearest_enemy(caster, alive_enemies)
            if not near:
                return []
            nr, nc = near.tile_row, near.tile_col
            result = []
            seen = set()
            for u in alive_enemies:
                dr = abs(u.tile_row - nr)
                dc = abs(u.tile_col - nc)
                # 십자: 같은 행 다른 열(dr==0) 또는 같은 열 다른 행(dc==0)
                if (dr == 0 or dc == 0) and (dr + dc <= 1):
                    if u.id not in seen:
                        seen.add(u.id)
                        result.append(u)
            return result

        # ── 적군 일반 타겟 ──────────────────────────────────────────
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

        # ── 적군 타일 기반 ──────────────────────────────────────────
        elif target_type == TargetType.ENEMY_FRONT_ROW:
            return self._get_effective_front_row(alive_enemies)

        elif target_type == TargetType.ENEMY_BACK_ROW:
            return self._get_effective_back_row(alive_enemies)

        elif target_type == TargetType.ENEMY_LAST_COL:
            # 적 최우열(col 최댓값) 전체 — 920013: 논타겟 적 3열
            return self._get_effective_last_col(alive_enemies)

        elif target_type == TargetType.ENEMY_SAME_COL:
            # 시전자와 동일 열(col)의 적 — 종대 관통 공격
            same_col = [u for u in alive_enemies if u.tile_col == caster.tile_col]
            return same_col if same_col else list(alive_enemies)

        elif target_type == TargetType.ENEMY_ADJACENT:
            # 시전자 기준 ±1행·±1열 인접 타일의 적
            adjacent = [
                u for u in alive_enemies
                if abs(u.tile_row - caster.tile_row) <= 1
                and abs(u.tile_col - caster.tile_col) <= 1
            ]
            return adjacent if adjacent else list(alive_enemies)

        elif target_type == TargetType.ENEMY_ELEMENT_WEAK:
            # 상성 약점 적 우선 타겟 (없으면 ENEMY_NEAR fallback)
            weak_map = {
                Element.FIRE: Element.FOREST,
                Element.WATER: Element.FIRE,
                Element.FOREST: Element.WATER,
                Element.LIGHT: Element.DARK,
                Element.DARK: Element.LIGHT,
            }
            weak_el = weak_map.get(caster.data.element)
            if weak_el:
                weak_targets = [u for u in alive_enemies if u.data.element == weak_el]
                if weak_targets:
                    return [min(weak_targets, key=lambda u: (self._tile_distance(caster, u), u.current_hp))]
            # fallback: nearest enemy
            near = self._nearest_enemy(caster, alive_enemies)
            return [near] if near else []

        # ── 3대 RPG 확장 타겟 타입 ───────────────────────────────
        # 전체 (적+아군)
        if target_type == TargetType.ALL_UNITS:
            return alive_allies + alive_enemies

        # 사망 아군 전체
        if target_type == TargetType.ALLY_DEAD_ALL:
            dead = [u for u in allies if not u.is_alive]
            return dead

        # 표적/낙인 적 우선
        if target_type == TargetType.ENEMY_MARKED:
            marked = [u for u in alive_enemies if getattr(u, 'is_marked', False)]
            if marked:
                return [min(marked, key=lambda u: u.current_hp)]
            return [min(alive_enemies, key=lambda u: u.current_hp)] if alive_enemies else []

        # 디버프 가장 많은 적
        if target_type == TargetType.ENEMY_MOST_DEBUFFS:
            if not alive_enemies:
                return []
            return [max(alive_enemies, key=lambda u: u.debuff_count)]

        # 버프 가장 많은 적
        if target_type == TargetType.ENEMY_MOST_BUFFS:
            if not alive_enemies:
                return []
            return [max(alive_enemies, key=lambda u: u.buff_count)]

        # 버프 가장 많은 아군
        if target_type == TargetType.ALLY_MOST_BUFFS:
            if not alive_allies:
                return []
            return [max(alive_allies, key=lambda u: u.buff_count)]

        # DEF 가장 낮은 적
        if target_type == TargetType.ENEMY_LOWEST_DEF:
            if not alive_enemies:
                return []
            return [min(alive_enemies, key=lambda u: u.def_)]

        return []

    # ─── 도발 처리 ────────────────────────────────────────────────
    def _apply_taunt(
        self,
        caster: 'BattleUnit',
        selected: List['BattleUnit'],
        alive_enemies: List['BattleUnit'],
        target_type: TargetType,
    ) -> List['BattleUnit']:
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
            caster.taunted_by = None
            return selected

        # 아군 타겟 스킬은 도발 무시
        if target_type in _ALLY_TARGET_TYPES:
            return selected

        # 단일 타겟 → 도발자로 강제 교체
        if target_type in (
            TargetType.ENEMY_NEAR,
            TargetType.ENEMY_LOWEST_HP, TargetType.ENEMY_HIGHEST_HP,
            TargetType.ENEMY_HIGHEST_SPD, TargetType.ENEMY_RANDOM,
            TargetType.ENEMY_ELEMENT_WEAK,
        ):
            return [taunter]

        # 다중 타겟 → 도발자 반드시 포함
        if taunter not in selected:
            selected = list(selected) + [taunter]

        return selected

    # ─── 도발 설정 ────────────────────────────────────────────────
    @staticmethod
    def apply_taunt_to_enemies(
        taunter: 'BattleUnit',
        enemies: List['BattleUnit'],
        duration: int = 2,
    ):
        """적군 전체에 도발 부여"""
        for enemy in enemies:
            if enemy.is_alive:
                enemy.apply_taunt(taunter.id, duration)
