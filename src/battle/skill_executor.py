"""SkillExecutor - 스킬 효과 실행 (LogicType별 분기 처리)"""
from __future__ import annotations
import random
from typing import List, Dict, Any, Optional, TYPE_CHECKING

from battle.enums import LogicType, TargetType, CCType
from battle.models import SkillData, SkillEffect, BuffData
from battle.damage_calc import compute_damage, calc_heal
from battle.target_selector import TargetSelector

if TYPE_CHECKING:
    from battle.battle_unit import BattleUnit
    from battle.buff_manager import BuffManager
    from battle.sp_manager import SPManager
    from battle.turn_manager import TurnManager
    from battle.trigger_system import TriggerSystem


class EngineContext:
    """스킬 실행 시 필요한 엔진 상태 참조 묶음"""
    def __init__(
        self,
        all_units: Dict[str, BattleUnit],
        allies: List[BattleUnit],
        enemies: List[BattleUnit],
        buff_manager: BuffManager,
        sp_manager: SPManager,
        turn_manager: TurnManager,
        log: List[str],
        trigger_system: Optional['TriggerSystem'] = None,
    ):
        self.all_units = all_units
        self.allies = allies
        self.enemies = enemies
        self.buff_manager = buff_manager
        self.sp_manager = sp_manager
        self.turn_manager = turn_manager
        self.log = log
        self.trigger_system = trigger_system

    def get_enemies_of(self, unit: BattleUnit) -> List[BattleUnit]:
        """해당 유닛의 적군 목록"""
        if unit.side == "ally":
            return [u for u in self.enemies if u.is_alive]
        return [u for u in self.allies if u.is_alive]

    def get_allies_of(self, unit: BattleUnit) -> List[BattleUnit]:
        """해당 유닛의 아군 목록 (자신 포함)"""
        if unit.side == "ally":
            return [u for u in self.allies if u.is_alive]
        return [u for u in self.enemies if u.is_alive]


class SkillExecutor:
    """스킬 데이터를 받아 각 Effect를 순서대로 실행"""

    def __init__(self):
        self._selector = TargetSelector()
        self._killed_this_skill: List[BattleUnit] = []

    def execute(
        self,
        caster: BattleUnit,
        skill: SkillData,
        ctx: EngineContext,
    ) -> List[BattleUnit]:
        """
        스킬의 모든 Effect 실행.
        반환: 이 스킬로 처치된 유닛 목록
        """
        self._killed_this_skill = []
        caster_allies = ctx.get_allies_of(caster)
        caster_enemies = ctx.get_enemies_of(caster)

        for effect in skill.effects:
            # 조건 체크
            if not self._check_condition(caster, effect.condition, ctx):
                continue

            # 타겟 선택 (is_melee는 스킬 단위로 적용 — 전열 보호)
            targets = self._selector.select(
                caster, effect.target_type, caster_allies, caster_enemies,
            )
            if not targets and effect.target_type not in (TargetType.SELF,):
                continue

            # 다단 히트
            for _ in range(effect.hit_count):
                for target in targets:
                    if not target.is_alive and effect.logic_type != LogicType.REVIVE:
                        continue
                    self._apply_effect(caster, target, effect, skill, ctx)

        return self._killed_this_skill

    def _apply_effect(
        self,
        caster: BattleUnit,
        target: BattleUnit,
        effect: SkillEffect,
        skill: SkillData,
        ctx: EngineContext,
    ):
        """단일 Effect를 단일 타겟에 적용"""
        logic = effect.logic_type

        # ─── 데미지 ───────────────────────────────────────────────
        if logic == LogicType.DAMAGE:
            burn_bonus = getattr(effect, 'burn_bonus_per_stack', 0.0)
            # SkillEffect에 burn_bonus_per_stack 속성이 있으면 사용
            if hasattr(effect, 'condition') and effect.condition:
                burn_bonus = effect.condition.get('burn_bonus_per_stack', 0.0)
                # 타겟 HP 조건 체크 (처형 보너스 등)
                if 'target_hp_below' in effect.condition:
                    if target.hp_ratio > effect.condition['target_hp_below']:
                        return  # 타겟 HP 조건 미달 → 스킵

            dmg, is_crit, is_dodged = compute_damage(caster, target, effect.multiplier, burn_bonus)
            if is_dodged:
                ctx.log.append(
                    f"    {caster.name} → {target.name}: {skill.name} 회피!"
                )
                return
            actual = target.take_damage(dmg)
            crit_str = " [크리티컬!]" if is_crit else ""
            ctx.log.append(
                f"    {caster.name} → {target.name}: {skill.name} {actual:.0f} 피해{crit_str} "
                f"(HP {target.current_hp:.0f}/{target.max_hp:.0f})"
            )
            # ─── ON_HIT 트리거 (피격 패시브) ──────────────────────
            if target.is_alive and ctx.trigger_system:
                ctx.trigger_system.evaluate_on_hit(target, caster, int(actual), ctx)
            if not target.is_alive:
                self._killed_this_skill.append(target)
                ctx.log.append(f"    💀 {target.name} 사망!")
            # ─── 화상반격 체크 ──────────────────────────────────
            elif target.is_alive and any(
                ab.buff_data.id == "counter_burn_active" for ab in target.active_buffs
            ):
                counter_burn = BuffData(
                    id="counter_burn_proc",
                    name="화상(반격)",
                    source_skill_id="counter_proc",
                    logic_type=LogicType.DOT,
                    dot_type="burn",
                    value=0.05,
                    duration=1,
                    is_debuff=True,
                    max_stacks=5,
                )
                ctx.buff_manager.apply_buff(caster, counter_burn, target.id)
                ctx.log.append(
                    f"    🔥 {target.name} 화상반격! → {caster.name}에게 화상"
                )

        # ─── 힐 ───────────────────────────────────────────────────
        elif logic == LogicType.HEAL:
            amount = calc_heal(caster.atk, target.max_hp, effect.multiplier)
            actual = target.heal(amount)
            ctx.log.append(
                f"    {caster.name} → {target.name}: {skill.name} {actual:.0f} 회복 "
                f"(HP {target.current_hp:.0f}/{target.max_hp:.0f})"
            )

        elif logic == LogicType.HEAL_HP_RATIO:
            amount = calc_heal(caster.atk, target.max_hp, hp_ratio=effect.value)
            actual = target.heal(amount)
            ctx.log.append(
                f"    {caster.name} → {target.name}: {skill.name} HP {effect.value*100:.0f}% 회복 "
                f"({actual:.0f}, HP {target.current_hp:.0f}/{target.max_hp:.0f})"
            )

        # ─── 스탯 버프/디버프 ─────────────────────────────────────
        elif logic == LogicType.STAT_CHANGE:
            if effect.buff_data:
                ctx.buff_manager.apply_buff(target, effect.buff_data, caster.id)
                sign = "+" if effect.buff_data.value >= 0 else ""
                ctx.log.append(
                    f"    {caster.name} → {target.name}: "
                    f"{effect.buff_data.stat} {sign}{effect.buff_data.value:.0f} 버프 ({effect.buff_data.duration}턴)"
                )

        # ─── DoT (화상, 독) ───────────────────────────────────────
        elif logic == LogicType.DOT:
            if effect.buff_data:
                ctx.buff_manager.apply_buff(target, effect.buff_data, caster.id)
                ctx.log.append(
                    f"    {caster.name} → {target.name}: "
                    f"{effect.buff_data.dot_type or 'DoT'} 부여 (스택 {target.get_tag_count('burn')})"
                )

        # ─── 도발 ─────────────────────────────────────────────────
        elif logic == LogicType.TAUNT:
            duration = int(effect.value) if effect.value else 2
            TargetSelector.apply_taunt_to_enemies(caster, ctx.get_enemies_of(caster), duration)
            ctx.log.append(f"    {caster.name}: 도발 발동 ({duration}턴, 적 전체)")

        # ─── 보호막 ───────────────────────────────────────────────
        elif logic == LogicType.BARRIER:
            barrier_amount = caster.atk * effect.multiplier if effect.multiplier else effect.value
            target.add_barrier(barrier_amount)
            ctx.log.append(
                f"    {caster.name} → {target.name}: 보호막 {barrier_amount:.0f}"
            )

        # ─── 부활 ─────────────────────────────────────────────────
        elif logic == LogicType.REVIVE:
            if not target.is_alive:
                hp_ratio = effect.value if effect.value else 0.3
                target.revive(hp_ratio)
                ctx.turn_manager.reschedule_unit(target)
                ctx.log.append(
                    f"    {caster.name} → {target.name}: 부활! (HP {target.current_hp:.0f})"
                )

        # ─── SP 증가 ──────────────────────────────────────────────
        elif logic == LogicType.SP_INCREASE:
            amount = int(effect.value)
            ctx.sp_manager.add_sp(caster.side, amount)
            ctx.log.append(
                f"    {caster.name}: 아군 SP +{amount} "
                f"(현재 {ctx.sp_manager.get_sp(caster.side)})"
            )

        # ─── CC 부여 ──────────────────────────────────────────────
        elif logic == LogicType.CC:
            if effect.buff_data and effect.buff_data.cc_type:
                # target 조건 체크 (화상 스택 등)
                if effect.condition:
                    burn_min = effect.condition.get('target_burn_min', 0)
                    if burn_min > 0 and target.get_tag_count('burn') < burn_min:
                        ctx.log.append(
                            f"    {target.name}: 화상 {target.get_tag_count('burn')}/{burn_min} 부족 → {effect.buff_data.cc_type.value} 미발동"
                        )
                        return
                ctx.buff_manager.apply_buff(target, effect.buff_data, caster.id)
                ctx.log.append(
                    f"    {caster.name} → {target.name}: "
                    f"{effect.buff_data.cc_type.value} 부여 ({effect.buff_data.duration}턴)"
                )

        # ─── 화상반격 준비 (COUNTER) ──────────────────────────────
        elif logic == LogicType.COUNTER:
            duration = int(effect.value) if effect.value else 2
            counter_marker = BuffData(
                id="counter_burn_active",
                name="화상반격",
                source_skill_id=skill.id,
                logic_type=LogicType.STAT_CHANGE,
                stat="def_",
                value=0,          # 실제 스탯 변화 없음 (마커 역할)
                duration=duration,
                is_debuff=False,
            )
            ctx.buff_manager.apply_buff(target, counter_marker, caster.id)
            ctx.log.append(
                f"    {caster.name}: 화상반격 준비 ({duration}턴, 피격 시 반격)"
            )

        # ─── 버프/디버프 제거 ─────────────────────────────────────
        elif logic == LogicType.REMOVE_BUFF:
            ctx.buff_manager.remove_buffs(target)
            ctx.log.append(f"    {caster.name} → {target.name}: 버프 제거")

        elif logic == LogicType.REMOVE_DEBUFF:
            ctx.buff_manager.remove_debuffs(target)
            ctx.log.append(f"    {caster.name} → {target.name}: 디버프 제거")

    # ─── 조건 체크 ────────────────────────────────────────────────
    def _check_condition(
        self,
        caster: BattleUnit,
        condition: dict | None,
        ctx: EngineContext,
    ) -> bool:
        """스킬 Effect 발동 조건 체크"""
        if not condition:
            return True

        # HP 임계값
        if 'hp_threshold' in condition:
            if caster.hp_ratio > condition['hp_threshold']:
                return False

        # 화상 스택 보유 여부
        if 'requires_burn' in condition:
            enemies = ctx.get_enemies_of(caster)
            has_burn = any(e.get_tag_count('burn') > 0 for e in enemies)
            if condition['requires_burn'] and not has_burn:
                return False

        # 태그 보유 여부
        if 'requires_tag' in condition:
            tag = condition['requires_tag']
            min_count = condition.get('tag_min_count', 1)
            if caster.get_tag_count(tag) < min_count:
                return False

        return True
