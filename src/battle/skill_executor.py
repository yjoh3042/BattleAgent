"""SkillExecutor - 스킬 효과 실행 (LogicType별 분기 처리)"""
from __future__ import annotations
import random
from typing import List, Dict, Any, Optional, TYPE_CHECKING

from battle.enums import LogicType, TargetType, CCType
from battle.models import SkillData, SkillEffect, BuffData
from battle.damage_calc import (
    compute_damage, calc_heal,
    compute_damage_penetration, compute_damage_hp_ratio,
    compute_damage_guaranteed_crit, compute_damage_buff_scale,
    compute_damage_spd_scale, compute_damage_def_scale,
    compute_damage_dual_scale, compute_damage_weakpoint,
    compute_damage_fixed, compute_damage_chain,
    compute_damage_counter_bonus, compute_damage_position_scale,
)
from battle.rules import (
    KNOCKBACK_ROWS, KNOCKBACK_WALL_DAMAGE_RATIO,
)
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
            # 혼란 상태: 적군 타겟을 랜덤으로 변경
            effective_target_type = effect.target_type
            if getattr(caster, 'is_confused', False) and effect.target_type not in (
                TargetType.SELF, TargetType.ALL_ALLY, TargetType.ALLY_LOWEST_HP,
                TargetType.ALLY_HIGHEST_ATK, TargetType.ALLY_DEAD_RANDOM,
                TargetType.ALLY_LOWEST_HP_2, TargetType.ALLY_ROLE_ATTACKER,
                TargetType.ALLY_ROLE_DEFENDER, TargetType.ALLY_SAME_ROW,
                TargetType.ALLY_BEHIND,
            ):
                effective_target_type = TargetType.ENEMY_RANDOM
            targets = self._selector.select(
                caster, effective_target_type, caster_allies, caster_enemies,
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
            # ─── ON_CRITICAL_HIT 트리거 ──────────────────────────
            if is_crit and caster.is_alive and ctx.trigger_system:
                ctx.trigger_system.evaluate_on_critical_hit(caster, target, ctx)
            if not target.is_alive:
                self._killed_this_skill.append(target)
                ctx.log.append(f"    💀 {target.name} 사망!")
            # ─── 무적 로그 ────────────────────────────────────────
            if target.is_alive and getattr(target, 'is_invincible', False) and actual == 0:
                ctx.log.append(f"    {target.name}: 무적으로 피해 무효!")
            # ─── 화상반격 체크 ──────────────────────────────────
            elif target.is_alive and not getattr(target, 'is_counter_unavailable', False) and any(
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
                # ON_BUFF_GAINED 트리거 (버프만, 디버프 제외)
                if not effect.buff_data.is_debuff and target.is_alive and ctx.trigger_system:
                    ctx.trigger_system.evaluate_on_buff_gained(target, effect.buff_data, ctx)

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

        # ─── DEF 무시 대미지 ─────────────────────────────────────────
        elif logic == LogicType.DAMAGE_PENETRATION:
            dmg, is_crit, is_dodged = compute_damage_penetration(caster, target, effect.multiplier)
            if is_dodged:
                ctx.log.append(f"    {caster.name} → {target.name}: {skill.name} 회피!")
                return
            actual = target.take_damage(dmg)
            crit_str = " [크리티컬!]" if is_crit else ""
            ctx.log.append(
                f"    {caster.name} → {target.name}: {skill.name} {actual:.0f} 관통피해{crit_str} "
                f"(HP {target.current_hp:.0f}/{target.max_hp:.0f})"
            )
            if target.is_alive and ctx.trigger_system:
                ctx.trigger_system.evaluate_on_hit(target, caster, int(actual), ctx)
            if not target.is_alive:
                self._killed_this_skill.append(target)
                ctx.log.append(f"    💀 {target.name} 사망!")

        # ─── HP% 대미지 ─────────────────────────────────────────────
        elif logic == LogicType.DAMAGE_HP_RATIO:
            dmg = compute_damage_hp_ratio(target, effect.value)
            actual = target.take_damage(dmg)
            ctx.log.append(
                f"    {caster.name} → {target.name}: {skill.name} HP {effect.value*100:.0f}% 피해 {actual:.0f} "
                f"(HP {target.current_hp:.0f}/{target.max_hp:.0f})"
            )
            if target.is_alive and ctx.trigger_system:
                ctx.trigger_system.evaluate_on_hit(target, caster, int(actual), ctx)
            if not target.is_alive:
                self._killed_this_skill.append(target)
                ctx.log.append(f"    💀 {target.name} 사망!")

        # ─── 무조건 크리 대미지 ──────────────────────────────────────
        elif logic == LogicType.DAMAGE_CRI:
            dmg, is_crit, is_dodged = compute_damage_guaranteed_crit(caster, target, effect.multiplier)
            if is_dodged:
                ctx.log.append(f"    {caster.name} → {target.name}: {skill.name} 회피!")
                return
            actual = target.take_damage(dmg)
            ctx.log.append(
                f"    {caster.name} → {target.name}: {skill.name} {actual:.0f} 피해 [확정 크리티컬!] "
                f"(HP {target.current_hp:.0f}/{target.max_hp:.0f})"
            )
            if target.is_alive and ctx.trigger_system:
                ctx.trigger_system.evaluate_on_hit(target, caster, int(actual), ctx)
            if not target.is_alive:
                self._killed_this_skill.append(target)
                ctx.log.append(f"    💀 {target.name} 사망!")

        # ─── 시전자 버프 수 비례 대미지 ──────────────────────────────
        elif logic == LogicType.DAMAGE_BUFF_SCALE:
            buff_count = len([ab for ab in caster.active_buffs if not ab.buff_data.is_debuff])
            scale = effect.value if effect.value else 0.1
            dmg, is_crit, is_dodged = compute_damage_buff_scale(
                caster, target, effect.multiplier, buff_count, scale
            )
            if is_dodged:
                ctx.log.append(f"    {caster.name} → {target.name}: {skill.name} 회피!")
                return
            actual = target.take_damage(dmg)
            crit_str = " [크리티컬!]" if is_crit else ""
            ctx.log.append(
                f"    {caster.name} → {target.name}: {skill.name} {actual:.0f} 피해{crit_str} "
                f"(버프 {buff_count}개 비례, HP {target.current_hp:.0f}/{target.max_hp:.0f})"
            )
            if target.is_alive and ctx.trigger_system:
                ctx.trigger_system.evaluate_on_hit(target, caster, int(actual), ctx)
            if not target.is_alive:
                self._killed_this_skill.append(target)
                ctx.log.append(f"    💀 {target.name} 사망!")

        # ─── 타겟 버프 수 비례 대미지 ────────────────────────────────
        elif logic == LogicType.DAMAGE_BUFF_SCALE_TARGET:
            buff_count = len([ab for ab in target.active_buffs if not ab.buff_data.is_debuff])
            scale = effect.value if effect.value else 0.1
            dmg, is_crit, is_dodged = compute_damage_buff_scale(
                caster, target, effect.multiplier, buff_count, scale
            )
            if is_dodged:
                ctx.log.append(f"    {caster.name} → {target.name}: {skill.name} 회피!")
                return
            actual = target.take_damage(dmg)
            crit_str = " [크리티컬!]" if is_crit else ""
            ctx.log.append(
                f"    {caster.name} → {target.name}: {skill.name} {actual:.0f} 피해{crit_str} "
                f"(타겟 버프 {buff_count}개 비례, HP {target.current_hp:.0f}/{target.max_hp:.0f})"
            )
            if target.is_alive and ctx.trigger_system:
                ctx.trigger_system.evaluate_on_hit(target, caster, int(actual), ctx)
            if not target.is_alive:
                self._killed_this_skill.append(target)
                ctx.log.append(f"    💀 {target.name} 사망!")

        # ─── 타겟 디버프 수 비례 대미지 ──────────────────────────────
        elif logic == LogicType.DAMAGE_DEBUFF_SCALE_TARGET:
            debuff_count = len([ab for ab in target.active_buffs if ab.buff_data.is_debuff])
            scale = effect.value if effect.value else 0.1
            dmg, is_crit, is_dodged = compute_damage_buff_scale(
                caster, target, effect.multiplier, debuff_count, scale
            )
            if is_dodged:
                ctx.log.append(f"    {caster.name} → {target.name}: {skill.name} 회피!")
                return
            actual = target.take_damage(dmg)
            crit_str = " [크리티컬!]" if is_crit else ""
            ctx.log.append(
                f"    {caster.name} → {target.name}: {skill.name} {actual:.0f} 피해{crit_str} "
                f"(타겟 디버프 {debuff_count}개 비례, HP {target.current_hp:.0f}/{target.max_hp:.0f})"
            )
            if target.is_alive and ctx.trigger_system:
                ctx.trigger_system.evaluate_on_hit(target, caster, int(actual), ctx)
            if not target.is_alive:
                self._killed_this_skill.append(target)
                ctx.log.append(f"    💀 {target.name} 사망!")

        # ─── 잃은 HP 비례 회복 ───────────────────────────────────────
        elif logic == LogicType.HEAL_LOSS_SCALE:
            lost_hp = target.max_hp - target.current_hp
            amount = lost_hp * effect.value
            actual = target.heal(amount)
            ctx.log.append(
                f"    {caster.name} → {target.name}: {skill.name} 잃은HP {effect.value*100:.0f}% 회복 "
                f"({actual:.0f}, HP {target.current_hp:.0f}/{target.max_hp:.0f})"
            )

        # ─── 대상 HP% 보호막 ────────────────────────────────────────
        elif logic == LogicType.BARRIER_RATIO:
            barrier_amount = target.max_hp * effect.value
            target.add_barrier(barrier_amount)
            ctx.log.append(
                f"    {caster.name} → {target.name}: HP {effect.value*100:.0f}% 보호막 {barrier_amount:.0f}"
            )

        # ─── 무적 ───────────────────────────────────────────────────
        elif logic == LogicType.INVINCIBILITY:
            duration = int(effect.value) if effect.value else 1
            marker = BuffData(
                id="invincibility_marker",
                name="무적",
                source_skill_id=skill.id,
                logic_type=LogicType.STAT_CHANGE,
                stat="def_",
                value=0,
                duration=duration,
                is_debuff=False,
                tags=["invincibility"],
            )
            ctx.buff_manager.apply_buff(target, marker, caster.id)
            target.is_invincible = True
            ctx.log.append(f"    {caster.name} → {target.name}: 무적 부여 ({duration}턴)")

        # ─── 불사 ───────────────────────────────────────────────────
        elif logic == LogicType.UNDYING:
            duration = int(effect.value) if effect.value else 1
            marker = BuffData(
                id="undying_marker",
                name="불사",
                source_skill_id=skill.id,
                logic_type=LogicType.STAT_CHANGE,
                stat="def_",
                value=0,
                duration=duration,
                is_debuff=False,
                tags=["undying"],
            )
            ctx.buff_manager.apply_buff(target, marker, caster.id)
            target.is_undying = True
            ctx.log.append(f"    {caster.name} → {target.name}: 불사 부여 ({duration}턴)")

        # ─── 디버프 면역 ─────────────────────────────────────────────
        elif logic == LogicType.DEBUFF_IMMUNE:
            duration = int(effect.value) if effect.value else 2
            marker = BuffData(
                id="debuff_immune_marker",
                name="디버프 면역",
                source_skill_id=skill.id,
                logic_type=LogicType.STAT_CHANGE,
                stat="def_",
                value=0,
                duration=duration,
                is_debuff=False,
                tags=["debuff_immune"],
            )
            ctx.buff_manager.apply_buff(target, marker, caster.id)
            target.is_debuff_immune = True
            ctx.log.append(f"    {caster.name} → {target.name}: 디버프 면역 부여 ({duration}턴)")

        # ─── SP 강탈 ─────────────────────────────────────────────────
        elif logic == LogicType.SP_STEAL:
            amount = int(effect.value)
            target_side = target.side
            caster_side = caster.side
            # 타겟 진영에서 SP 차감
            current_target_sp = ctx.sp_manager.get_sp(target_side)
            stolen = min(amount, current_target_sp)
            ctx.sp_manager.add_sp(target_side, -stolen)
            ctx.sp_manager.add_sp(caster_side, stolen)
            ctx.log.append(
                f"    {caster.name} → {target.name}: SP {stolen} 강탈! "
                f"(아군 SP {ctx.sp_manager.get_sp(caster_side)}, 적 SP {ctx.sp_manager.get_sp(target_side)})"
            )

        # ─── SP 충전 잠금 ────────────────────────────────────────────
        elif logic == LogicType.SP_LOCK:
            duration = int(effect.value) if effect.value else 2
            marker = BuffData(
                id="sp_lock_marker",
                name="SP 잠금",
                source_skill_id=skill.id,
                logic_type=LogicType.STAT_CHANGE,
                stat="def_",
                value=0,
                duration=duration,
                is_debuff=True,
                tags=["sp_lock"],
            )
            ctx.buff_manager.apply_buff(target, marker, caster.id)
            target.is_sp_locked = True
            ctx.log.append(f"    {caster.name} → {target.name}: SP 충전 잠금 ({duration}턴)")

        # ─── 버프 턴 증가 ────────────────────────────────────────────
        elif logic == LogicType.BUFF_TURN_INCREASE:
            amount = int(effect.value) if effect.value else 1
            count = 0
            for ab in target.active_buffs:
                if not ab.buff_data.is_debuff:
                    ab.remaining_turns += amount
                    count += 1
            ctx.log.append(
                f"    {caster.name} → {target.name}: 버프 {count}개 턴 +{amount}"
            )

        # ─── 디버프 턴 증가 ──────────────────────────────────────────
        elif logic == LogicType.DEBUFF_TURN_INCREASE:
            amount = int(effect.value) if effect.value else 1
            count = 0
            for ab in target.active_buffs:
                if ab.buff_data.is_debuff:
                    ab.remaining_turns += amount
                    count += 1
            ctx.log.append(
                f"    {caster.name} → {target.name}: 디버프 {count}개 턴 +{amount}"
            )

        # ─── 크리 불가 ───────────────────────────────────────────────
        elif logic == LogicType.CRI_UNAVAILABLE:
            duration = int(effect.value) if effect.value else 2
            marker = BuffData(
                id="cri_unavailable_marker",
                name="크리 불가",
                source_skill_id=skill.id,
                logic_type=LogicType.STAT_CHANGE,
                stat="cri_ratio",
                value=0,
                duration=duration,
                is_debuff=True,
                tags=["cri_unavailable"],
            )
            ctx.buff_manager.apply_buff(target, marker, caster.id)
            target.is_cri_unavailable = True
            ctx.log.append(f"    {caster.name} → {target.name}: 크리 불가 ({duration}턴)")

        # ─── 반격 불가 ───────────────────────────────────────────────
        elif logic == LogicType.COUNTER_UNAVAILABLE:
            duration = int(effect.value) if effect.value else 2
            marker = BuffData(
                id="counter_unavailable_marker",
                name="반격 불가",
                source_skill_id=skill.id,
                logic_type=LogicType.STAT_CHANGE,
                stat="def_",
                value=0,
                duration=duration,
                is_debuff=True,
                tags=["counter_unavailable"],
            )
            ctx.buff_manager.apply_buff(target, marker, caster.id)
            target.is_counter_unavailable = True
            ctx.log.append(f"    {caster.name} → {target.name}: 반격 불가 ({duration}턴)")

        # ─── 스킬 발동 ───────────────────────────────────────────────
        elif logic == LogicType.USE_SKILL:
            # effect.condition에서 skill_id 참조
            skill_id = None
            if effect.condition and 'skill_id' in effect.condition:
                skill_id = effect.condition['skill_id']
            if skill_id:
                # 시전자의 스킬에서 해당 ID 찾기
                target_skill = None
                for sk in [caster.data.normal_skill, caster.data.active_skill, caster.data.ultimate_skill, caster.data.passive_skill]:
                    if sk and sk.id == skill_id:
                        target_skill = sk
                        break
                if target_skill:
                    ctx.log.append(f"    {caster.name}: 스킬 발동 → {target_skill.name}")
                    sub_killed = self.execute(caster, target_skill, ctx)
                    self._killed_this_skill.extend(sub_killed)
                else:
                    ctx.log.append(f"    {caster.name}: 스킬 ID {skill_id} 미발견")

        # ─── 속성 상성 무시 ──────────────────────────────────────────
        elif logic == LogicType.IGNORE_ELEMENT:
            duration = int(effect.value) if effect.value else 2
            marker = BuffData(
                id="ignore_element_marker",
                name="속성 무시",
                source_skill_id=skill.id,
                logic_type=LogicType.STAT_CHANGE,
                stat="def_",
                value=0,
                duration=duration,
                is_debuff=False,
                tags=["ignore_element"],
            )
            ctx.buff_manager.apply_buff(target, marker, caster.id)
            target.ignore_element = True
            ctx.log.append(f"    {caster.name} → {target.name}: 속성 상성 무시 ({duration}턴)")

        # ─── 액티브 쿨타임 변경 ──────────────────────────────────────
        elif logic == LogicType.ACTIVE_CD_CHANGE:
            change = int(effect.value)
            old_cd = target.active_skill_cooldown
            target.active_skill_cooldown = max(0, target.active_skill_cooldown + change)
            ctx.log.append(
                f"    {caster.name} → {target.name}: 액티브 쿨타임 {old_cd} → {target.active_skill_cooldown} ({change:+d})"
            )

        # ─── 화상 대상 2배 + 강제 크리 ──────────────────────────────
        elif logic == LogicType.DAMAGE_BURN_BONUS:
            has_burn = target.get_tag_count('burn') > 0
            if has_burn:
                dmg, _, is_dodged = compute_damage_guaranteed_crit(
                    caster, target, effect.multiplier * 2.0)
            else:
                dmg, _, is_dodged = compute_damage(caster, target, effect.multiplier)
            if is_dodged:
                ctx.log.append(f"    {caster.name} → {target.name}: {skill.name} 회피!")
                return
            actual = target.take_damage(dmg)
            burn_str = " [화상 2배 크리!]" if has_burn else ""
            ctx.log.append(
                f"    {caster.name} → {target.name}: {skill.name} {actual:.0f} 피해{burn_str} "
                f"(HP {target.current_hp:.0f}/{target.max_hp:.0f})"
            )
            if target.is_alive and ctx.trigger_system:
                ctx.trigger_system.evaluate_on_hit(target, caster, int(actual), ctx)
            if not target.is_alive:
                self._killed_this_skill.append(target)
                ctx.log.append(f"    💀 {target.name} 사망!")

        # ─── 사용 횟수 비례 피해 증가 ──────────────────────────────
        elif logic == LogicType.DAMAGE_ESCALATE:
            tag_key = f"escalate_{skill.id}"
            count = caster.get_tag_count(tag_key)
            caster.add_tag(tag_key)
            multiplier = effect.multiplier * (1.0 + 0.2 * count)
            dmg, is_crit, is_dodged = compute_damage(caster, target, multiplier)
            if is_dodged:
                ctx.log.append(f"    {caster.name} → {target.name}: {skill.name} 회피!")
                return
            actual = target.take_damage(dmg)
            crit_str = " [크리티컬!]" if is_crit else ""
            ctx.log.append(
                f"    {caster.name} → {target.name}: {skill.name} {actual:.0f} 피해{crit_str} "
                f"(누적 {count+1}회, HP {target.current_hp:.0f}/{target.max_hp:.0f})"
            )
            if target.is_alive and ctx.trigger_system:
                ctx.trigger_system.evaluate_on_hit(target, caster, int(actual), ctx)
            if not target.is_alive:
                self._killed_this_skill.append(target)
                ctx.log.append(f"    💀 {target.name} 사망!")

        # ─── 같은 적 반복공격 시 피해 증가 ─────────────────────────
        elif logic == LogicType.DAMAGE_REPEAT_TARGET:
            tag_key = f"repeat_{skill.id}"
            last_id = getattr(caster, '_last_repeat_target', None)
            if last_id == target.id:
                repeat_n = caster.get_tag_count(tag_key)
                caster.add_tag(tag_key)
            else:
                # 타겟 바뀜 → 리셋
                caster.remove_tag(tag_key)
                caster.add_tag(tag_key)
                repeat_n = 0
            caster._last_repeat_target = target.id
            multiplier = effect.multiplier * (1.0 + 0.3 * repeat_n)
            dmg, is_crit, is_dodged = compute_damage(caster, target, multiplier)
            if is_dodged:
                ctx.log.append(f"    {caster.name} → {target.name}: {skill.name} 회피!")
                return
            actual = target.take_damage(dmg)
            crit_str = " [크리티컬!]" if is_crit else ""
            ctx.log.append(
                f"    {caster.name} → {target.name}: {skill.name} {actual:.0f} 피해{crit_str} "
                f"(반복 {repeat_n+1}회, HP {target.current_hp:.0f}/{target.max_hp:.0f})"
            )
            if target.is_alive and ctx.trigger_system:
                ctx.trigger_system.evaluate_on_hit(target, caster, int(actual), ctx)
            if not target.is_alive:
                self._killed_this_skill.append(target)
                ctx.log.append(f"    💀 {target.name} 사망!")

        # ─── 시전자 잃은 HP 비례 피해 증가 ─────────────────────────
        elif logic == LogicType.DAMAGE_MISSING_HP_SCALE:
            scale = effect.value if effect.value else 1.0
            multiplier = effect.multiplier * (1.0 + (1.0 - caster.hp_ratio) * scale)
            dmg, is_crit, is_dodged = compute_damage(caster, target, multiplier)
            if is_dodged:
                ctx.log.append(f"    {caster.name} → {target.name}: {skill.name} 회피!")
                return
            actual = target.take_damage(dmg)
            crit_str = " [크리티컬!]" if is_crit else ""
            ctx.log.append(
                f"    {caster.name} → {target.name}: {skill.name} {actual:.0f} 피해{crit_str} "
                f"(잃은HP {(1-caster.hp_ratio)*100:.0f}% 비례, HP {target.current_hp:.0f}/{target.max_hp:.0f})"
            )
            if target.is_alive and ctx.trigger_system:
                ctx.trigger_system.evaluate_on_hit(target, caster, int(actual), ctx)
            if not target.is_alive:
                self._killed_this_skill.append(target)
                ctx.log.append(f"    💀 {target.name} 사망!")

        # ─── 적중 수만큼 아군 회복 ─────────────────────────────────
        elif logic == LogicType.HEAL_PER_HIT:
            # target은 적 — 피해 적용
            dmg, is_crit, is_dodged = compute_damage(caster, target, effect.multiplier)
            if is_dodged:
                ctx.log.append(f"    {caster.name} → {target.name}: {skill.name} 회피!")
                return
            actual = target.take_damage(dmg)
            crit_str = " [크리티컬!]" if is_crit else ""
            ctx.log.append(
                f"    {caster.name} → {target.name}: {skill.name} {actual:.0f} 피해{crit_str} "
                f"(HP {target.current_hp:.0f}/{target.max_hp:.0f})"
            )
            if not target.is_alive:
                self._killed_this_skill.append(target)
                ctx.log.append(f"    💀 {target.name} 사망!")
            # 적중 성공 → 아군 최저HP 1명 회복
            if actual > 0:
                heal_val = effect.value if effect.value else 0.1
                allies = ctx.get_allies_of(caster)
                if allies:
                    heal_target = min(allies, key=lambda u: u.hp_ratio)
                    heal_amount = heal_target.max_hp * heal_val
                    healed = heal_target.heal(heal_amount)
                    ctx.log.append(
                        f"    → {heal_target.name}: 적중 회복 {healed:.0f} "
                        f"(HP {heal_target.current_hp:.0f}/{heal_target.max_hp:.0f})"
                    )

        # ─── 현재 HP 높을수록 회복량 증가 ──────────────────────────
        elif logic == LogicType.HEAL_CURRENT_HP_SCALE:
            base_heal = calc_heal(caster.atk, target.max_hp, effect.multiplier)
            scaled_heal = base_heal * caster.hp_ratio
            actual = target.heal(scaled_heal)
            ctx.log.append(
                f"    {caster.name} → {target.name}: {skill.name} {actual:.0f} 회복 "
                f"(시전자 HP {caster.hp_ratio*100:.0f}% 비례, HP {target.current_hp:.0f}/{target.max_hp:.0f})"
            )

        # ─── 스탯 빼앗기 ───────────────────────────────────────────
        elif logic == LogicType.STAT_STEAL:
            if effect.buff_data:
                stat_name = effect.buff_data.stat or "def_"
                steal_amount = abs(effect.buff_data.value)
                # 적에게 디버프 (스탯 감소)
                debuff = BuffData(
                    id=f"stat_steal_debuff_{skill.id}",
                    name=f"{stat_name} 강탈",
                    source_skill_id=skill.id,
                    logic_type=LogicType.STAT_CHANGE,
                    stat=stat_name,
                    value=-steal_amount,
                    duration=effect.buff_data.duration,
                    is_debuff=True,
                )
                ctx.buff_manager.apply_buff(target, debuff, caster.id)
                # 자신에게 버프 (스탯 증가)
                buff = BuffData(
                    id=f"stat_steal_buff_{skill.id}",
                    name=f"{stat_name} 흡수",
                    source_skill_id=skill.id,
                    logic_type=LogicType.STAT_CHANGE,
                    stat=stat_name,
                    value=steal_amount,
                    duration=effect.buff_data.duration,
                    is_debuff=False,
                )
                ctx.buff_manager.apply_buff(caster, buff, caster.id)
                ctx.log.append(
                    f"    {caster.name} → {target.name}: {stat_name} {steal_amount:.0f} 강탈!"
                )

        # ─── 디버프 십자 전이 ───────────────────────────────────────
        elif logic == LogicType.DEBUFF_SPREAD:
            # 대상의 디버프를 주변 십자 패턴 적에게 복제
            debuffs_to_spread = [
                ab.buff_data for ab in target.active_buffs if ab.buff_data.is_debuff
            ]
            if not debuffs_to_spread:
                ctx.log.append(f"    {caster.name} → {target.name}: 전이할 디버프 없음")
            else:
                tr, tc = target.tile_row, target.tile_col
                enemies = ctx.get_enemies_of(caster)
                adjacent = [
                    u for u in enemies
                    if u.id != target.id and u.is_alive
                    and ((abs(u.tile_row - tr) == 1 and u.tile_col == tc) or
                         (u.tile_row == tr and abs(u.tile_col - tc) == 1))
                ]
                spread_count = 0
                for adj_unit in adjacent:
                    for bd in debuffs_to_spread:
                        import copy
                        spread_bd = copy.deepcopy(bd)
                        spread_bd.id = f"{bd.id}_spread"
                        ctx.buff_manager.apply_buff(adj_unit, spread_bd, caster.id)
                        spread_count += 1
                ctx.log.append(
                    f"    {caster.name}: {target.name}의 디버프 {len(debuffs_to_spread)}개 → "
                    f"인접 {len(adjacent)}명에게 전이 ({spread_count}건)"
                )

        # ─── 자신 HP 소모 ──────────────────────────────────────────
        elif logic == LogicType.SELF_DAMAGE:
            cost = effect.value if effect.value else 0.1
            if cost < 1.0:
                # 비율 기반
                hp_cost = caster.max_hp * cost
            else:
                hp_cost = cost
            caster.current_hp = max(1, caster.current_hp - hp_cost)
            ctx.log.append(
                f"    {caster.name}: 자해 {hp_cost:.0f} (HP {caster.current_hp:.0f}/{caster.max_hp:.0f})"
            )

        # ─── 추가 행동 획득 ────────────────────────────────────────
        elif logic == LogicType.EXTRA_TURN:
            ctx.turn_manager.add_extra_turn(caster)
            ctx.log.append(f"    {caster.name}: 추가 행동 획득!")

        # ─── 속도 반전 필드 (트릭룸) ───────────────────────────────
        elif logic == LogicType.TRICK_ROOM:
            duration = int(effect.value) if effect.value else 3
            all_living = [u for u in list(ctx.allies) + list(ctx.enemies) if u.is_alive]
            if all_living:
                spd_values = [u.spd for u in all_living]
                spd_max, spd_min = max(spd_values), min(spd_values)
                for u in all_living:
                    old_spd = u.spd
                    new_spd = max(1, spd_max + spd_min - old_spd)
                    diff = new_spd - old_spd
                    trick_buff = BuffData(
                        id=f"trick_room_{u.id}",
                        name="트릭룸",
                        source_skill_id=skill.id,
                        logic_type=LogicType.STAT_CHANGE,
                        stat="spd",
                        value=diff,
                        duration=duration,
                        is_debuff=(diff < 0),
                        tags=["trick_room"],
                    )
                    ctx.buff_manager.apply_buff(u, trick_buff, caster.id)
                ctx.log.append(
                    f"    {caster.name}: 트릭룸 발동! 속도 반전 ({duration}턴, "
                    f"범위 {spd_min}~{spd_max})"
                )

        # ─── 연결 아군 버프 공유 ───────────────────────────────────
        elif logic == LogicType.LINK_BUFF:
            # target = 연결 대상 (ALLY_BEHIND 등으로 선택됨)
            # 시전자의 버프를 타겟에게 복제
            buffs_to_share = [
                ab.buff_data for ab in caster.active_buffs
                if not ab.buff_data.is_debuff
                and 'link_buff' not in (ab.buff_data.tags or [])
            ]
            if not buffs_to_share:
                ctx.log.append(f"    {caster.name} → {target.name}: 공유할 버프 없음")
            else:
                import copy
                for bd in buffs_to_share:
                    shared_bd = copy.deepcopy(bd)
                    shared_bd.id = f"{bd.id}_linked"
                    shared_bd.tags = list(shared_bd.tags or []) + ["link_buff"]
                    ctx.buff_manager.apply_buff(target, shared_bd, caster.id)
                ctx.log.append(
                    f"    {caster.name} → {target.name}: 버프 {len(buffs_to_share)}개 공유 (링크)"
                )

        # ─── DAMAGE_SPD_SCALE ────────────────────────────────────────
        elif logic == LogicType.DAMAGE_SPD_SCALE:
            dmg, is_crit, is_dodged = compute_damage_spd_scale(caster, target, effect.multiplier)
            if is_dodged:
                ctx.log.append(f"    {caster.name} → {target.name}: {skill.name} 회피!")
                return
            actual = target.take_damage(dmg)
            crit_str = " [크리티컬!]" if is_crit else ""
            ctx.log.append(
                f"    {caster.name} → {target.name}: {skill.name} {actual:.0f} SPD비례 피해{crit_str} "
                f"(HP {target.current_hp:.0f}/{target.max_hp:.0f})"
            )
            if target.is_alive and ctx.trigger_system:
                ctx.trigger_system.evaluate_on_hit(target, caster, int(actual), ctx)
            if not target.is_alive:
                self._killed_this_skill.append(target)
                ctx.log.append(f"    💀 {target.name} 사망!")

        # ─── DAMAGE_DEF_SCALE ────────────────────────────────────────
        elif logic == LogicType.DAMAGE_DEF_SCALE:
            dmg, is_crit, is_dodged = compute_damage_def_scale(caster, target, effect.multiplier)
            if is_dodged:
                ctx.log.append(f"    {caster.name} → {target.name}: {skill.name} 회피!")
                return
            actual = target.take_damage(dmg)
            crit_str = " [크리티컬!]" if is_crit else ""
            ctx.log.append(
                f"    {caster.name} → {target.name}: {skill.name} {actual:.0f} DEF비례 피해{crit_str} "
                f"(HP {target.current_hp:.0f}/{target.max_hp:.0f})"
            )
            if target.is_alive and ctx.trigger_system:
                ctx.trigger_system.evaluate_on_hit(target, caster, int(actual), ctx)
            if not target.is_alive:
                self._killed_this_skill.append(target)
                ctx.log.append(f"    💀 {target.name} 사망!")

        # ─── DAMAGE_DUAL_SCALE ───────────────────────────────────────
        elif logic == LogicType.DAMAGE_DUAL_SCALE:
            dmg, is_crit, is_dodged = compute_damage_dual_scale(caster, target, effect.multiplier)
            if is_dodged:
                ctx.log.append(f"    {caster.name} → {target.name}: {skill.name} 회피!")
                return
            actual = target.take_damage(dmg)
            crit_str = " [크리티컬!]" if is_crit else ""
            ctx.log.append(
                f"    {caster.name} → {target.name}: {skill.name} {actual:.0f} ATK+SPD 이중스케일 피해{crit_str} "
                f"(HP {target.current_hp:.0f}/{target.max_hp:.0f})"
            )
            if target.is_alive and ctx.trigger_system:
                ctx.trigger_system.evaluate_on_hit(target, caster, int(actual), ctx)
            if not target.is_alive:
                self._killed_this_skill.append(target)
                ctx.log.append(f"    💀 {target.name} 사망!")

        # ─── DAMAGE_CURRENT_HP_SCALE ─────────────────────────────────
        elif logic == LogicType.DAMAGE_CURRENT_HP_SCALE:
            multiplier = effect.multiplier * caster.hp_ratio
            dmg, is_crit, is_dodged = compute_damage(caster, target, multiplier)
            if is_dodged:
                ctx.log.append(f"    {caster.name} → {target.name}: {skill.name} 회피!")
                return
            actual = target.take_damage(dmg)
            crit_str = " [크리티컬!]" if is_crit else ""
            ctx.log.append(
                f"    {caster.name} → {target.name}: {skill.name} {actual:.0f} 현재HP비례 피해{crit_str} "
                f"(HP {target.current_hp:.0f}/{target.max_hp:.0f})"
            )
            if target.is_alive and ctx.trigger_system:
                ctx.trigger_system.evaluate_on_hit(target, caster, int(actual), ctx)
            if not target.is_alive:
                self._killed_this_skill.append(target)
                ctx.log.append(f"    💀 {target.name} 사망!")

        # ─── DAMAGE_TARGET_LOST_HP_SCALE ─────────────────────────────
        elif logic == LogicType.DAMAGE_TARGET_LOST_HP_SCALE:
            scale = effect.value if effect.value else 1.0
            multiplier = effect.multiplier * (1 + (1 - target.hp_ratio) * scale)
            dmg, is_crit, is_dodged = compute_damage(caster, target, multiplier)
            if is_dodged:
                ctx.log.append(f"    {caster.name} → {target.name}: {skill.name} 회피!")
                return
            actual = target.take_damage(dmg)
            crit_str = " [크리티컬!]" if is_crit else ""
            ctx.log.append(
                f"    {caster.name} → {target.name}: {skill.name} {actual:.0f} 적 잃은HP비례 피해{crit_str} "
                f"(HP {target.current_hp:.0f}/{target.max_hp:.0f})"
            )
            if target.is_alive and ctx.trigger_system:
                ctx.trigger_system.evaluate_on_hit(target, caster, int(actual), ctx)
            if not target.is_alive:
                self._killed_this_skill.append(target)
                ctx.log.append(f"    💀 {target.name} 사망!")

        # ─── DAMAGE_ENEMY_COUNT_SCALE ────────────────────────────────
        elif logic == LogicType.DAMAGE_ENEMY_COUNT_SCALE:
            enemy_count = len(ctx.get_enemies_of(caster))
            multiplier = effect.multiplier * (1 + 0.1 * enemy_count)
            dmg, is_crit, is_dodged = compute_damage(caster, target, multiplier)
            if is_dodged:
                ctx.log.append(f"    {caster.name} → {target.name}: {skill.name} 회피!")
                return
            actual = target.take_damage(dmg)
            crit_str = " [크리티컬!]" if is_crit else ""
            ctx.log.append(
                f"    {caster.name} → {target.name}: {skill.name} {actual:.0f} 적수비례 피해{crit_str} "
                f"(적 {enemy_count}명, HP {target.current_hp:.0f}/{target.max_hp:.0f})"
            )
            if target.is_alive and ctx.trigger_system:
                ctx.trigger_system.evaluate_on_hit(target, caster, int(actual), ctx)
            if not target.is_alive:
                self._killed_this_skill.append(target)
                ctx.log.append(f"    💀 {target.name} 사망!")

        # ─── DAMAGE_ALLY_COUNT_SCALE ─────────────────────────────────
        elif logic == LogicType.DAMAGE_ALLY_COUNT_SCALE:
            ally_count = len(ctx.get_allies_of(caster))
            multiplier = effect.multiplier * (1 + 0.15 * ally_count)
            dmg, is_crit, is_dodged = compute_damage(caster, target, multiplier)
            if is_dodged:
                ctx.log.append(f"    {caster.name} → {target.name}: {skill.name} 회피!")
                return
            actual = target.take_damage(dmg)
            crit_str = " [크리티컬!]" if is_crit else ""
            ctx.log.append(
                f"    {caster.name} → {target.name}: {skill.name} {actual:.0f} 아군수비례 피해{crit_str} "
                f"(아군 {ally_count}명, HP {target.current_hp:.0f}/{target.max_hp:.0f})"
            )
            if target.is_alive and ctx.trigger_system:
                ctx.trigger_system.evaluate_on_hit(target, caster, int(actual), ctx)
            if not target.is_alive:
                self._killed_this_skill.append(target)
                ctx.log.append(f"    💀 {target.name} 사망!")

        # ─── DAMAGE_KILL_COUNT_SCALE ─────────────────────────────────
        elif logic == LogicType.DAMAGE_KILL_COUNT_SCALE:
            kill_count = getattr(caster, 'kill_count', 0)
            multiplier = effect.multiplier * (1 + 0.2 * kill_count)
            dmg, is_crit, is_dodged = compute_damage(caster, target, multiplier)
            if is_dodged:
                ctx.log.append(f"    {caster.name} → {target.name}: {skill.name} 회피!")
                return
            actual = target.take_damage(dmg)
            crit_str = " [크리티컬!]" if is_crit else ""
            ctx.log.append(
                f"    {caster.name} → {target.name}: {skill.name} {actual:.0f} 킬카운트비례 피해{crit_str} "
                f"(킬 {kill_count}회, HP {target.current_hp:.0f}/{target.max_hp:.0f})"
            )
            if target.is_alive and ctx.trigger_system:
                ctx.trigger_system.evaluate_on_hit(target, caster, int(actual), ctx)
            if not target.is_alive:
                self._killed_this_skill.append(target)
                ctx.log.append(f"    💀 {target.name} 사망!")

        # ─── DAMAGE_SURVIVAL_TURN_SCALE ──────────────────────────────
        elif logic == LogicType.DAMAGE_SURVIVAL_TURN_SCALE:
            survival_turns = getattr(caster, 'survival_turns', 0)
            multiplier = effect.multiplier * (1 + 0.05 * survival_turns)
            dmg, is_crit, is_dodged = compute_damage(caster, target, multiplier)
            if is_dodged:
                ctx.log.append(f"    {caster.name} → {target.name}: {skill.name} 회피!")
                return
            actual = target.take_damage(dmg)
            crit_str = " [크리티컬!]" if is_crit else ""
            ctx.log.append(
                f"    {caster.name} → {target.name}: {skill.name} {actual:.0f} 생존턴비례 피해{crit_str} "
                f"(생존 {survival_turns}턴, HP {target.current_hp:.0f}/{target.max_hp:.0f})"
            )
            if target.is_alive and ctx.trigger_system:
                ctx.trigger_system.evaluate_on_hit(target, caster, int(actual), ctx)
            if not target.is_alive:
                self._killed_this_skill.append(target)
                ctx.log.append(f"    💀 {target.name} 사망!")

        # ─── DAMAGE_ACCUMULATE_COUNTER ───────────────────────────────
        elif logic == LogicType.DAMAGE_ACCUMULATE_COUNTER:
            accumulated = getattr(caster, 'damage_accumulated', 0.0)
            dmg = accumulated * (effect.value if effect.value else 1.0)
            caster.damage_accumulated = 0.0
            actual = target.take_damage(dmg)
            ctx.log.append(
                f"    {caster.name} → {target.name}: {skill.name} {actual:.0f} 축적피해 폭발 "
                f"(축적 {accumulated:.0f}, HP {target.current_hp:.0f}/{target.max_hp:.0f})"
            )
            if target.is_alive and ctx.trigger_system:
                ctx.trigger_system.evaluate_on_hit(target, caster, int(actual), ctx)
            if not target.is_alive:
                self._killed_this_skill.append(target)
                ctx.log.append(f"    💀 {target.name} 사망!")

        # ─── DAMAGE_CHAIN ────────────────────────────────────────────
        elif logic == LogicType.DAMAGE_CHAIN:
            enemies = ctx.get_enemies_of(caster)
            chain_results = compute_damage_chain(caster, target, effect.multiplier, enemies)
            for chain_target, dmg_val, is_crit_c in chain_results:
                if not chain_target.is_alive:
                    continue
                actual = chain_target.take_damage(dmg_val)
                crit_str = " [크리티컬!]" if is_crit_c else ""
                ctx.log.append(
                    f"    {caster.name} → {chain_target.name}: {skill.name} 체인 {actual:.0f} 피해{crit_str} "
                    f"(HP {chain_target.current_hp:.0f}/{chain_target.max_hp:.0f})"
                )
                if chain_target.is_alive and ctx.trigger_system:
                    ctx.trigger_system.evaluate_on_hit(chain_target, caster, int(actual), ctx)
                if not chain_target.is_alive:
                    self._killed_this_skill.append(chain_target)
                    ctx.log.append(f"    💀 {chain_target.name} 사망!")

        # ─── DAMAGE_SPLASH ───────────────────────────────────────────
        elif logic == LogicType.DAMAGE_SPLASH:
            dmg, is_crit, is_dodged = compute_damage(caster, target, effect.multiplier)
            if is_dodged:
                ctx.log.append(f"    {caster.name} → {target.name}: {skill.name} 회피!")
                return
            actual = target.take_damage(dmg)
            crit_str = " [크리티컬!]" if is_crit else ""
            ctx.log.append(
                f"    {caster.name} → {target.name}: {skill.name} {actual:.0f} 피해{crit_str} "
                f"(HP {target.current_hp:.0f}/{target.max_hp:.0f})"
            )
            if target.is_alive and ctx.trigger_system:
                ctx.trigger_system.evaluate_on_hit(target, caster, int(actual), ctx)
            if not target.is_alive:
                self._killed_this_skill.append(target)
                ctx.log.append(f"    💀 {target.name} 사망!")
            # 스플래시: 다른 적에게 secondary_value% 피해
            splash_ratio = getattr(effect, 'secondary_value', 0.3)
            splash_dmg = dmg * splash_ratio
            for other in ctx.get_enemies_of(caster):
                if other.id != target.id and other.is_alive:
                    splash_actual = other.take_damage(splash_dmg)
                    ctx.log.append(
                        f"    → {other.name}: 스플래시 {splash_actual:.0f} 피해 "
                        f"(HP {other.current_hp:.0f}/{other.max_hp:.0f})"
                    )
                    if not other.is_alive:
                        self._killed_this_skill.append(other)
                        ctx.log.append(f"    💀 {other.name} 사망!")

        # ─── DAMAGE_AOE_SPLIT ────────────────────────────────────────
        elif logic == LogicType.DAMAGE_AOE_SPLIT:
            enemies = ctx.get_enemies_of(caster)
            enemy_count = len(enemies) if enemies else 1
            total_dmg, is_crit, is_dodged = compute_damage(caster, target, effect.multiplier)
            if is_dodged:
                ctx.log.append(f"    {caster.name} → {target.name}: {skill.name} 회피!")
                return
            split_dmg = total_dmg / enemy_count
            for enemy in enemies:
                if enemy.is_alive:
                    actual = enemy.take_damage(split_dmg)
                    crit_str = " [크리티컬!]" if is_crit else ""
                    ctx.log.append(
                        f"    {caster.name} → {enemy.name}: {skill.name} {actual:.0f} 분할피해{crit_str} "
                        f"(HP {enemy.current_hp:.0f}/{enemy.max_hp:.0f})"
                    )
                    if enemy.is_alive and ctx.trigger_system:
                        ctx.trigger_system.evaluate_on_hit(enemy, caster, int(actual), ctx)
                    if not enemy.is_alive:
                        self._killed_this_skill.append(enemy)
                        ctx.log.append(f"    💀 {enemy.name} 사망!")

        # ─── DAMAGE_REFLECT ──────────────────────────────────────────
        elif logic == LogicType.DAMAGE_REFLECT:
            # 반사 버프 마커 적용 (실제 반사는 take_damage에서 처리)
            duration = int(effect.value) if effect.value else 2
            reflect_ratio = effect.multiplier if effect.multiplier else 0.3
            marker = BuffData(
                id="reflect_marker",
                name="피해 반사",
                source_skill_id=skill.id,
                logic_type=LogicType.STAT_CHANGE,
                stat="def_",
                value=reflect_ratio,
                duration=duration,
                is_debuff=False,
                tags=["reflecting", "reflect_ratio"],
            )
            ctx.buff_manager.apply_buff(target, marker, caster.id)
            ctx.log.append(f"    {caster.name} → {target.name}: 피해 반사 버프 ({reflect_ratio*100:.0f}%, {duration}턴)")

        # ─── DAMAGE_WEAKPOINT ────────────────────────────────────────
        elif logic == LogicType.DAMAGE_WEAKPOINT:
            dmg, is_crit, is_dodged = compute_damage_weakpoint(caster, target, effect.multiplier)
            if is_dodged:
                ctx.log.append(f"    {caster.name} → {target.name}: {skill.name} 회피!")
                return
            actual = target.take_damage(dmg)
            crit_str = " [크리티컬!]" if is_crit else ""
            ctx.log.append(
                f"    {caster.name} → {target.name}: {skill.name} {actual:.0f} 약점 피해{crit_str} "
                f"(HP {target.current_hp:.0f}/{target.max_hp:.0f})"
            )
            if target.is_alive and ctx.trigger_system:
                ctx.trigger_system.evaluate_on_hit(target, caster, int(actual), ctx)
            if not target.is_alive:
                self._killed_this_skill.append(target)
                ctx.log.append(f"    💀 {target.name} 사망!")

        # ─── DAMAGE_EXECUTE ──────────────────────────────────────────
        elif logic == LogicType.DAMAGE_EXECUTE:
            execute_threshold = effect.value if effect.value else 0.15
            if target.hp_ratio <= execute_threshold:
                # 즉사
                actual = target.take_damage(target.current_hp * 999)
                ctx.log.append(
                    f"    {caster.name} → {target.name}: {skill.name} 멸살! HP {target.hp_ratio*100:.0f}% ≤ {execute_threshold*100:.0f}% 즉사"
                )
            else:
                dmg, is_crit, is_dodged = compute_damage(caster, target, effect.multiplier)
                if is_dodged:
                    ctx.log.append(f"    {caster.name} → {target.name}: {skill.name} 회피!")
                    return
                actual = target.take_damage(dmg)
                crit_str = " [크리티컬!]" if is_crit else ""
                ctx.log.append(
                    f"    {caster.name} → {target.name}: {skill.name} {actual:.0f} 피해{crit_str} "
                    f"(HP {target.current_hp:.0f}/{target.max_hp:.0f})"
                )
                if target.is_alive and ctx.trigger_system:
                    ctx.trigger_system.evaluate_on_hit(target, caster, int(actual), ctx)
            if not target.is_alive:
                self._killed_this_skill.append(target)
                ctx.log.append(f"    💀 {target.name} 사망!")

        # ─── DAMAGE_BARRIER_PIERCE ───────────────────────────────────
        elif logic == LogicType.DAMAGE_BARRIER_PIERCE:
            dmg, is_crit, is_dodged = compute_damage(caster, target, effect.multiplier)
            if is_dodged:
                ctx.log.append(f"    {caster.name} → {target.name}: {skill.name} 회피!")
                return
            actual = target.take_damage(dmg, pierce_barrier=True)
            crit_str = " [크리티컬!]" if is_crit else ""
            ctx.log.append(
                f"    {caster.name} → {target.name}: {skill.name} {actual:.0f} 보호막관통 피해{crit_str} "
                f"(HP {target.current_hp:.0f}/{target.max_hp:.0f})"
            )
            if target.is_alive and ctx.trigger_system:
                ctx.trigger_system.evaluate_on_hit(target, caster, int(actual), ctx)
            if not target.is_alive:
                self._killed_this_skill.append(target)
                ctx.log.append(f"    💀 {target.name} 사망!")

        # ─── DAMAGE_KILL_SPLASH ──────────────────────────────────────
        elif logic == LogicType.DAMAGE_KILL_SPLASH:
            dmg, is_crit, is_dodged = compute_damage(caster, target, effect.multiplier)
            if is_dodged:
                ctx.log.append(f"    {caster.name} → {target.name}: {skill.name} 회피!")
                return
            actual = target.take_damage(dmg)
            crit_str = " [크리티컬!]" if is_crit else ""
            ctx.log.append(
                f"    {caster.name} → {target.name}: {skill.name} {actual:.0f} 피해{crit_str} "
                f"(HP {target.current_hp:.0f}/{target.max_hp:.0f})"
            )
            if target.is_alive and ctx.trigger_system:
                ctx.trigger_system.evaluate_on_hit(target, caster, int(actual), ctx)
            if not target.is_alive:
                self._killed_this_skill.append(target)
                ctx.log.append(f"    💀 {target.name} 사망!")
                # 잔여 피해 전파
                overflow = dmg - target.max_hp if dmg > target.max_hp else 0
                if overflow > 0:
                    for other in ctx.get_enemies_of(caster):
                        if other.is_alive:
                            splash_actual = other.take_damage(overflow)
                            ctx.log.append(
                                f"    → {other.name}: 킬 스플래시 {splash_actual:.0f} 피해 "
                                f"(HP {other.current_hp:.0f}/{other.max_hp:.0f})"
                            )
                            if not other.is_alive:
                                self._killed_this_skill.append(other)
                                ctx.log.append(f"    💀 {other.name} 사망!")

        # ─── DAMAGE_FIXED ────────────────────────────────────────────
        elif logic == LogicType.DAMAGE_FIXED:
            dmg = compute_damage_fixed(effect.value)
            actual = target.take_damage(dmg)
            ctx.log.append(
                f"    {caster.name} → {target.name}: {skill.name} {actual:.0f} 고정 피해 "
                f"(HP {target.current_hp:.0f}/{target.max_hp:.0f})"
            )
            if target.is_alive and ctx.trigger_system:
                ctx.trigger_system.evaluate_on_hit(target, caster, int(actual), ctx)
            if not target.is_alive:
                self._killed_this_skill.append(target)
                ctx.log.append(f"    💀 {target.name} 사망!")

        # ─── DAMAGE_COUNTER_SCALE ────────────────────────────────────
        elif logic == LogicType.DAMAGE_COUNTER_SCALE:
            dmg, is_crit, is_dodged = compute_damage_counter_bonus(caster, target, effect.multiplier)
            if is_dodged:
                ctx.log.append(f"    {caster.name} → {target.name}: {skill.name} 회피!")
                return
            actual = target.take_damage(dmg)
            crit_str = " [크리티컬!]" if is_crit else ""
            ctx.log.append(
                f"    {caster.name} → {target.name}: {skill.name} {actual:.0f} 반격크리 피해{crit_str} "
                f"(HP {target.current_hp:.0f}/{target.max_hp:.0f})"
            )
            if target.is_alive and ctx.trigger_system:
                ctx.trigger_system.evaluate_on_hit(target, caster, int(actual), ctx)
            if not target.is_alive:
                self._killed_this_skill.append(target)
                ctx.log.append(f"    💀 {target.name} 사망!")

        # ─── DAMAGE_REFLECT_ATK_SCALE ────────────────────────────────
        elif logic == LogicType.DAMAGE_REFLECT_ATK_SCALE:
            dmg = target.atk * (effect.multiplier if effect.multiplier else 0.5)
            actual = target.take_damage(dmg)
            ctx.log.append(
                f"    {caster.name} → {target.name}: {skill.name} {actual:.0f} ATK비례 반사 피해 "
                f"(HP {target.current_hp:.0f}/{target.max_hp:.0f})"
            )
            if target.is_alive and ctx.trigger_system:
                ctx.trigger_system.evaluate_on_hit(target, caster, int(actual), ctx)
            if not target.is_alive:
                self._killed_this_skill.append(target)
                ctx.log.append(f"    💀 {target.name} 사망!")

        # ─── HEAL_OVERHEAL_BARRIER ───────────────────────────────────
        elif logic == LogicType.HEAL_OVERHEAL_BARRIER:
            amount = calc_heal(caster.atk, target.max_hp, effect.multiplier)
            if hasattr(target, 'heal_with_overheal'):
                healed, overheal = target.heal_with_overheal(amount)
            else:
                healed = target.heal(amount)
                overheal = 0.0
            if overheal > 0:
                target.add_barrier(overheal)
            ctx.log.append(
                f"    {caster.name} → {target.name}: {skill.name} {healed:.0f} 회복, "
                f"초과 {overheal:.0f} → 보호막 (HP {target.current_hp:.0f}/{target.max_hp:.0f})"
            )

        # ─── HEAL_DEF_SCALE ──────────────────────────────────────────
        elif logic == LogicType.HEAL_DEF_SCALE:
            heal_amount = caster.def_ * (effect.multiplier if effect.multiplier else 1.0)
            actual = target.heal(heal_amount)
            ctx.log.append(
                f"    {caster.name} → {target.name}: {skill.name} {actual:.0f} DEF비례 회복 "
                f"(HP {target.current_hp:.0f}/{target.max_hp:.0f})"
            )

        # ─── HEAL_BLOCK ──────────────────────────────────────────────
        elif logic == LogicType.HEAL_BLOCK:
            duration = int(effect.value) if effect.value else 2
            marker = BuffData(
                id="heal_block_marker",
                name="회복 불가",
                source_skill_id=skill.id,
                logic_type=LogicType.STAT_CHANGE,
                stat="def_",
                value=0,
                duration=duration,
                is_debuff=True,
                tags=["heal_block"],
            )
            ctx.buff_manager.apply_buff(target, marker, caster.id)
            ctx.log.append(f"    {caster.name} → {target.name}: 회복 불가 ({duration}턴)")

        # ─── HEAL_REDUCE ─────────────────────────────────────────────
        elif logic == LogicType.HEAL_REDUCE:
            duration = int(effect.value) if effect.value else 2
            marker = BuffData(
                id="heal_reduce_marker",
                name="회복 효율 감소",
                source_skill_id=skill.id,
                logic_type=LogicType.STAT_CHANGE,
                stat="def_",
                value=0,
                duration=duration,
                is_debuff=True,
                tags=["heal_reduce"],
            )
            ctx.buff_manager.apply_buff(target, marker, caster.id)
            ctx.log.append(f"    {caster.name} → {target.name}: 회복 효율 감소 ({duration}턴)")

        # ─── HEAL_CURSE ──────────────────────────────────────────────
        elif logic == LogicType.HEAL_CURSE:
            duration = int(effect.value) if effect.value else 2
            marker = BuffData(
                id="cursed_marker",
                name="저주",
                source_skill_id=skill.id,
                logic_type=LogicType.STAT_CHANGE,
                stat="def_",
                value=0,
                duration=duration,
                is_debuff=True,
                tags=["cursed"],
            )
            ctx.buff_manager.apply_buff(target, marker, caster.id)
            ctx.log.append(f"    {caster.name} → {target.name}: 저주 부여 ({duration}턴)")

        # ─── HP_EQUALIZE ─────────────────────────────────────────────
        elif logic == LogicType.HP_EQUALIZE:
            allies = ctx.get_allies_of(caster)
            total_hp = sum(u.current_hp for u in allies)
            avg_hp_ratio = total_hp / sum(u.max_hp for u in allies) if allies else 1.0
            for ally in allies:
                ally.current_hp = min(ally.max_hp, ally.max_hp * avg_hp_ratio)
            ctx.log.append(
                f"    {caster.name}: 아군 전체 HP 균등화 (평균 {avg_hp_ratio*100:.1f}%)"
            )

        # ─── HP_SWAP ─────────────────────────────────────────────────
        elif logic == LogicType.HP_SWAP:
            caster_ratio = caster.hp_ratio
            target_ratio = target.hp_ratio
            caster.current_hp = min(caster.max_hp, caster.max_hp * target_ratio)
            target.current_hp = min(target.max_hp, target.max_hp * caster_ratio)
            ctx.log.append(
                f"    {caster.name} ↔ {target.name}: HP 비율 교환 "
                f"({caster_ratio*100:.0f}% ↔ {target_ratio*100:.0f}%)"
            )

        # ─── ATB_PUSH ────────────────────────────────────────────────
        elif logic == LogicType.ATB_PUSH:
            push_amount = effect.value if effect.value else 0.25
            target.atb_gauge = min(1.0, getattr(target, 'atb_gauge', 0.0) + push_amount)
            if hasattr(ctx.turn_manager, 'reschedule_unit'):
                ctx.turn_manager.reschedule_unit(target)
            ctx.log.append(
                f"    {caster.name} → {target.name}: ATB +{push_amount*100:.0f}%"
            )

        # ─── ATB_PULL ────────────────────────────────────────────────
        elif logic == LogicType.ATB_PULL:
            pull_amount = effect.value if effect.value else 0.25
            target.atb_gauge = max(0.0, getattr(target, 'atb_gauge', 0.0) - pull_amount)
            if hasattr(ctx.turn_manager, 'delay_unit'):
                ctx.turn_manager.delay_unit(target, pull_amount)
            ctx.log.append(
                f"    {caster.name} → {target.name}: ATB -{pull_amount*100:.0f}%"
            )

        # ─── ATB_STEAL ───────────────────────────────────────────────
        elif logic == LogicType.ATB_STEAL:
            steal_amount = effect.value if effect.value else 0.25
            stolen = min(steal_amount, getattr(target, 'atb_gauge', 0.0))
            target.atb_gauge = max(0.0, getattr(target, 'atb_gauge', 0.0) - stolen)
            caster.atb_gauge = min(1.0, getattr(caster, 'atb_gauge', 0.0) + stolen)
            if hasattr(ctx.turn_manager, 'reschedule_unit'):
                ctx.turn_manager.reschedule_unit(caster)
                ctx.turn_manager.reschedule_unit(target)
            ctx.log.append(
                f"    {caster.name} → {target.name}: ATB {stolen*100:.0f}% 흡수"
            )

        # ─── ATB_RESET ───────────────────────────────────────────────
        elif logic == LogicType.ATB_RESET:
            for enemy in ctx.get_enemies_of(caster):
                enemy.atb_gauge = 0.0
                if hasattr(ctx.turn_manager, 'reschedule_unit'):
                    ctx.turn_manager.reschedule_unit(enemy)
            ctx.log.append(f"    {caster.name}: 적 전체 ATB 리셋!")

        # ─── DAMAGE_TO_ATB ───────────────────────────────────────────
        elif logic == LogicType.DAMAGE_TO_ATB:
            duration = int(effect.value) if effect.value else 2
            marker = BuffData(
                id="damage_to_atb_marker",
                name="피해→ATB 전환",
                source_skill_id=skill.id,
                logic_type=LogicType.STAT_CHANGE,
                stat="def_",
                value=0,
                duration=duration,
                is_debuff=False,
                tags=["damage_to_atb"],
            )
            ctx.buff_manager.apply_buff(target, marker, caster.id)
            ctx.log.append(f"    {caster.name} → {target.name}: 피해→ATB 전환 마커 ({duration}턴)")

        # ─── BUFF_STEAL ──────────────────────────────────────────────
        elif logic == LogicType.BUFF_STEAL:
            import copy
            n = int(effect.value) if effect.value else 1
            target_buffs = [ab for ab in target.active_buffs if not ab.buff_data.is_debuff]
            to_steal = random.sample(target_buffs, min(n, len(target_buffs)))
            for ab in to_steal:
                target.active_buffs.remove(ab)
                stolen_bd = copy.deepcopy(ab.buff_data)
                stolen_bd.id = f"{stolen_bd.id}_stolen"
                ctx.buff_manager.apply_buff(caster, stolen_bd, caster.id)
            ctx.log.append(
                f"    {caster.name} → {target.name}: 버프 {len(to_steal)}개 탈취"
            )

        # ─── BUFF_INVERSION ──────────────────────────────────────────
        elif logic == LogicType.BUFF_INVERSION:
            buffs = [ab for ab in target.active_buffs if not ab.buff_data.is_debuff]
            for ab in buffs:
                ab.buff_data.is_debuff = True
                ab.buff_data.value = -abs(ab.buff_data.value)
            ctx.log.append(
                f"    {caster.name} → {target.name}: 버프 {len(buffs)}개 → 디버프 반전"
            )

        # ─── DEBUFF_TRANSFER ─────────────────────────────────────────
        elif logic == LogicType.DEBUFF_TRANSFER:
            import copy
            debuffs = [ab for ab in caster.active_buffs if ab.buff_data.is_debuff]
            for ab in debuffs:
                caster.active_buffs.remove(ab)
                transferred_bd = copy.deepcopy(ab.buff_data)
                transferred_bd.id = f"{transferred_bd.id}_transferred"
                ctx.buff_manager.apply_buff(target, transferred_bd, caster.id)
            ctx.log.append(
                f"    {caster.name} → {target.name}: 자신 디버프 {len(debuffs)}개 전이"
            )

        # ─── DEBUFF_DETONATE ─────────────────────────────────────────
        elif logic == LogicType.DEBUFF_DETONATE:
            debuffs = [ab for ab in target.active_buffs if ab.buff_data.is_debuff]
            debuff_count = len(debuffs)
            target.active_buffs = [ab for ab in target.active_buffs if not ab.buff_data.is_debuff]
            if debuff_count > 0:
                dmg = effect.value * debuff_count * target.max_hp
                actual = target.take_damage(dmg)
                ctx.log.append(
                    f"    {caster.name} → {target.name}: 디버프 {debuff_count}개 폭발 {actual:.0f} 피해 "
                    f"(HP {target.current_hp:.0f}/{target.max_hp:.0f})"
                )
                if target.is_alive and ctx.trigger_system:
                    ctx.trigger_system.evaluate_on_hit(target, caster, int(actual), ctx)
                if not target.is_alive:
                    self._killed_this_skill.append(target)
                    ctx.log.append(f"    💀 {target.name} 사망!")
            else:
                ctx.log.append(f"    {caster.name} → {target.name}: 폭발할 디버프 없음")

        # ─── DEBUFF_CONTAGION ────────────────────────────────────────
        elif logic == LogicType.DEBUFF_CONTAGION:
            duration = int(effect.value) if effect.value else 2
            marker = BuffData(
                id="debuff_contagion_marker",
                name="디버프 전염",
                source_skill_id=skill.id,
                logic_type=LogicType.STAT_CHANGE,
                stat="def_",
                value=0,
                duration=duration,
                is_debuff=True,
                tags=["debuff_contagion"],
            )
            ctx.buff_manager.apply_buff(target, marker, caster.id)
            ctx.log.append(f"    {caster.name} → {target.name}: 디버프 전염 마커 ({duration}턴)")

        # ─── BUFF_BLOCK ──────────────────────────────────────────────
        elif logic == LogicType.BUFF_BLOCK:
            duration = int(effect.value) if effect.value else 2
            marker = BuffData(
                id="buff_blocked_marker",
                name="버프 적용 불가",
                source_skill_id=skill.id,
                logic_type=LogicType.STAT_CHANGE,
                stat="def_",
                value=0,
                duration=duration,
                is_debuff=True,
                tags=["buff_blocked"],
            )
            ctx.buff_manager.apply_buff(target, marker, caster.id)
            ctx.log.append(f"    {caster.name} → {target.name}: 버프 적용 불가 ({duration}턴)")

        # ─── BUFF_IRREMOVABLE ────────────────────────────────────────
        elif logic == LogicType.BUFF_IRREMOVABLE:
            buffs = [ab for ab in target.active_buffs if not ab.buff_data.is_debuff]
            for ab in buffs:
                if ab.buff_data.tags is None:
                    ab.buff_data.tags = []
                if "irremovable" not in ab.buff_data.tags:
                    ab.buff_data.tags.append("irremovable")
            ctx.log.append(
                f"    {caster.name} → {target.name}: 버프 {len(buffs)}개 → 해제 불가 설정"
            )

        # ─── COOLDOWN_RESET ──────────────────────────────────────────
        elif logic == LogicType.COOLDOWN_RESET:
            target.active_skill_cooldown = 0
            target.ultimate_cooldown = 0
            ctx.log.append(f"    {caster.name} → {target.name}: 스킬 쿨타임 전체 초기화")

        # ─── PASSIVE_SEAL ────────────────────────────────────────────
        elif logic == LogicType.PASSIVE_SEAL:
            duration = int(effect.value) if effect.value else 2
            marker = BuffData(
                id="passive_sealed_marker",
                name="패시브 봉인",
                source_skill_id=skill.id,
                logic_type=LogicType.STAT_CHANGE,
                stat="def_",
                value=0,
                duration=duration,
                is_debuff=True,
                tags=["passive_sealed"],
            )
            ctx.buff_manager.apply_buff(target, marker, caster.id)
            ctx.log.append(f"    {caster.name} → {target.name}: 패시브 봉인 ({duration}턴)")

        # ─── DAMAGE_SHARE ────────────────────────────────────────────
        elif logic == LogicType.DAMAGE_SHARE:
            share_ratio = effect.value if effect.value else 0.3
            duration = int(effect.multiplier) if effect.multiplier else 2
            marker = BuffData(
                id="damage_share_marker",
                name="피해 분산",
                source_skill_id=skill.id,
                logic_type=LogicType.STAT_CHANGE,
                stat="def_",
                value=share_ratio,
                duration=duration,
                is_debuff=False,
                tags=["damage_share"],
            )
            ctx.buff_manager.apply_buff(target, marker, caster.id)
            ctx.log.append(
                f"    {caster.name} → {target.name}: 피해 분산 {share_ratio*100:.0f}% ({duration}턴)"
            )

        # ─── PROTECT_ALLY ────────────────────────────────────────────
        elif logic == LogicType.PROTECT_ALLY:
            caster.protect_target_id = target.id
            target.protected_by_id = caster.id
            ctx.log.append(
                f"    {caster.name}: {target.name} 보호 시작 (대리 피격)"
            )

        # ─── BARRIER_SHARE ───────────────────────────────────────────
        elif logic == LogicType.BARRIER_SHARE:
            caster_barrier = getattr(caster, 'barrier', 0.0)
            allies = ctx.get_allies_of(caster)
            if caster_barrier > 0 and allies:
                share_per = caster_barrier / len(allies)
                for ally in allies:
                    if ally.id != caster.id:
                        ally.add_barrier(share_per)
                ctx.log.append(
                    f"    {caster.name}: 보호막 {caster_barrier:.0f} → 아군 {len(allies)-1}명에게 분배"
                )
            else:
                ctx.log.append(f"    {caster.name}: 공유할 보호막 없음")

        # ─── DEFENSE_STANCE ──────────────────────────────────────────
        elif logic == LogicType.DEFENSE_STANCE:
            duration = int(effect.value) if effect.value else 2
            def_buff = BuffData(
                id="defense_stance_def",
                name="방어 자세 DEF",
                source_skill_id=skill.id,
                logic_type=LogicType.STAT_CHANGE,
                stat="def_",
                value=target.def_,
                duration=duration,
                is_debuff=False,
            )
            ctx.buff_manager.apply_buff(target, def_buff, caster.id)
            dmg_reduce_buff = BuffData(
                id="defense_stance_reduce",
                name="방어 자세 피해감소",
                source_skill_id=skill.id,
                logic_type=LogicType.STAT_CHANGE,
                stat="dmg_reduce",
                value=0.5,
                duration=duration,
                is_debuff=False,
                tags=["damage_reduce"],
            )
            ctx.buff_manager.apply_buff(target, dmg_reduce_buff, caster.id)
            ctx.log.append(
                f"    {caster.name} → {target.name}: 방어 자세 (DEF×2, 피해감소 50%, {duration}턴)"
            )

        # ─── STEALTH ─────────────────────────────────────────────────
        elif logic == LogicType.STEALTH:
            duration = int(effect.value) if effect.value else 2
            marker = BuffData(
                id="stealth_marker",
                name="스텔스",
                source_skill_id=skill.id,
                logic_type=LogicType.STAT_CHANGE,
                stat="def_",
                value=0,
                duration=duration,
                is_debuff=False,
                tags=["stealth"],
            )
            ctx.buff_manager.apply_buff(target, marker, caster.id)
            ctx.log.append(f"    {caster.name} → {target.name}: 스텔스 ({duration}턴)")

        # ─── CONSECUTIVE_HIT_REDUCE ──────────────────────────────────
        elif logic == LogicType.CONSECUTIVE_HIT_REDUCE:
            duration = int(effect.value) if effect.value else 2
            marker = BuffData(
                id="consec_hit_reduce_marker",
                name="연속피격 감소",
                source_skill_id=skill.id,
                logic_type=LogicType.STAT_CHANGE,
                stat="def_",
                value=0,
                duration=duration,
                is_debuff=False,
                tags=["consec_hit_reduce"],
            )
            ctx.buff_manager.apply_buff(target, marker, caster.id)
            ctx.log.append(f"    {caster.name} → {target.name}: 연속피격 감소 ({duration}턴)")

        # ─── DAMAGE_CAP ──────────────────────────────────────────────
        elif logic == LogicType.DAMAGE_CAP:
            cap_value = target.max_hp * (effect.value if effect.value else 0.3)
            duration = int(effect.multiplier) if effect.multiplier else 2
            marker = BuffData(
                id="damage_cap_marker",
                name="피해 상한",
                source_skill_id=skill.id,
                logic_type=LogicType.STAT_CHANGE,
                stat="def_",
                value=cap_value,
                duration=duration,
                is_debuff=False,
                tags=["damage_cap"],
            )
            ctx.buff_manager.apply_buff(target, marker, caster.id)
            ctx.log.append(
                f"    {caster.name} → {target.name}: 피해 상한 {cap_value:.0f} ({duration}턴)"
            )

        # ─── REVIVE_SEAL ─────────────────────────────────────────────
        elif logic == LogicType.REVIVE_SEAL:
            duration = int(effect.value) if effect.value else 2
            marker = BuffData(
                id="revive_sealed_marker",
                name="부활 봉인",
                source_skill_id=skill.id,
                logic_type=LogicType.STAT_CHANGE,
                stat="def_",
                value=0,
                duration=duration,
                is_debuff=True,
                tags=["revive_sealed"],
            )
            ctx.buff_manager.apply_buff(target, marker, caster.id)
            ctx.log.append(f"    {caster.name} → {target.name}: 부활 봉인 ({duration}턴)")

        # ─── REFLECT_BUFF ────────────────────────────────────────────
        elif logic == LogicType.REFLECT_BUFF:
            reflect_ratio = effect.value if effect.value else 0.3
            duration = int(effect.multiplier) if effect.multiplier else 2
            marker = BuffData(
                id="reflect_buff_marker",
                name="피해 반사 버프",
                source_skill_id=skill.id,
                logic_type=LogicType.STAT_CHANGE,
                stat="def_",
                value=reflect_ratio,
                duration=duration,
                is_debuff=False,
                tags=["reflecting", "reflect_ratio"],
            )
            ctx.buff_manager.apply_buff(target, marker, caster.id)
            ctx.log.append(
                f"    {caster.name} → {target.name}: 피해 반사 {reflect_ratio*100:.0f}% ({duration}턴)"
            )

        # ─── BOMB ────────────────────────────────────────────────────
        elif logic == LogicType.BOMB:
            duration = int(effect.duration) if hasattr(effect, 'duration') and effect.duration else 3
            marker = BuffData(
                id="bomb_marker",
                name="시한 폭탄",
                source_skill_id=skill.id,
                logic_type=LogicType.STAT_CHANGE,
                stat="def_",
                value=effect.value if effect.value else 0.3,
                duration=duration,
                is_debuff=True,
                tags=["bomb"],
            )
            ctx.buff_manager.apply_buff(target, marker, caster.id)
            ctx.log.append(
                f"    {caster.name} → {target.name}: 시한 폭탄 ({duration}턴 후 폭발)"
            )

        # ─── MARK ────────────────────────────────────────────────────
        elif logic == LogicType.MARK:
            duration = int(effect.value) if effect.value else 2
            marker = BuffData(
                id="marked_marker",
                name="표적",
                source_skill_id=skill.id,
                logic_type=LogicType.STAT_CHANGE,
                stat="def_",
                value=0.2,
                duration=duration,
                is_debuff=True,
                tags=["marked"],
            )
            ctx.buff_manager.apply_buff(target, marker, caster.id)
            ctx.log.append(f"    {caster.name} → {target.name}: 표적 낙인 ({duration}턴, 피해 +20%)")

        # ─── DOOM ────────────────────────────────────────────────────
        elif logic == LogicType.DOOM:
            duration = int(effect.value) if effect.value else 2
            doom_marker = BuffData(
                id="doomed_marker",
                name="파멸",
                source_skill_id=skill.id,
                logic_type=LogicType.STAT_CHANGE,
                stat="def_",
                value=0,
                duration=duration,
                is_debuff=True,
                tags=["doomed", "heal_block"],
            )
            ctx.buff_manager.apply_buff(target, doom_marker, caster.id)
            ctx.log.append(f"    {caster.name} → {target.name}: 파멸 ({duration}턴)")

        # ─── VULNERABILITY ───────────────────────────────────────────
        elif logic == LogicType.VULNERABILITY:
            amplify_ratio = effect.value if effect.value else 0.2
            duration = int(effect.multiplier) if effect.multiplier else 2
            marker = BuffData(
                id="vulnerability_marker",
                name="피해 증폭",
                source_skill_id=skill.id,
                logic_type=LogicType.STAT_CHANGE,
                stat="def_",
                value=amplify_ratio,
                duration=duration,
                is_debuff=True,
                tags=["vulnerability"],
            )
            ctx.buff_manager.apply_buff(target, marker, caster.id)
            ctx.log.append(
                f"    {caster.name} → {target.name}: 피해 증폭 {amplify_ratio*100:.0f}% ({duration}턴)"
            )

        # ─── WEAKEN ──────────────────────────────────────────────────
        elif logic == LogicType.WEAKEN:
            reduce_ratio = effect.value if effect.value else 0.2
            duration = int(effect.multiplier) if effect.multiplier else 2
            marker = BuffData(
                id="weaken_marker",
                name="가하는 피해 감소",
                source_skill_id=skill.id,
                logic_type=LogicType.STAT_CHANGE,
                stat="def_",
                value=reduce_ratio,
                duration=duration,
                is_debuff=True,
                tags=["weaken"],
            )
            ctx.buff_manager.apply_buff(target, marker, caster.id)
            ctx.log.append(
                f"    {caster.name} → {target.name}: 가하는 피해 감소 {reduce_ratio*100:.0f}% ({duration}턴)"
            )

        # ─── BANISH ──────────────────────────────────────────────────
        elif logic == LogicType.BANISH:
            duration = int(effect.value) if effect.value else 2
            target.is_banished = True
            if hasattr(ctx.turn_manager, 'remove_from_queue'):
                ctx.turn_manager.remove_from_queue(target)
            marker = BuffData(
                id="banished_marker",
                name="추방",
                source_skill_id=skill.id,
                logic_type=LogicType.STAT_CHANGE,
                stat="def_",
                value=0,
                duration=duration,
                is_debuff=True,
                tags=["banished"],
            )
            ctx.buff_manager.apply_buff(target, marker, caster.id)
            ctx.log.append(f"    {caster.name} → {target.name}: 차원 추방 ({duration}턴)")

        # ─── RESIST_IGNORE ───────────────────────────────────────────
        elif logic == LogicType.RESIST_IGNORE:
            caster._resist_ignore_active = True
            ctx.log.append(f"    {caster.name}: 효과 저항 무시 발동")

        # ─── DOT_INSTANT_TRIGGER ─────────────────────────────────────
        elif logic == LogicType.DOT_INSTANT_TRIGGER:
            dot_buffs = [
                ab for ab in target.active_buffs
                if ab.buff_data.is_debuff and ab.buff_data.logic_type == LogicType.DOT
            ]
            total_dot_dmg = 0.0
            for ab in dot_buffs:
                dot_val = ab.buff_data.value * target.max_hp if ab.buff_data.value < 1.0 else ab.buff_data.value
                total_dot_dmg += dot_val
            if total_dot_dmg > 0:
                actual = target.take_damage(total_dot_dmg)
                ctx.log.append(
                    f"    {caster.name} → {target.name}: DOT 즉시 폭발 {actual:.0f} 피해 "
                    f"({len(dot_buffs)}종, HP {target.current_hp:.0f}/{target.max_hp:.0f})"
                )
                if not target.is_alive:
                    self._killed_this_skill.append(target)
                    ctx.log.append(f"    💀 {target.name} 사망!")
            else:
                ctx.log.append(f"    {caster.name} → {target.name}: 발동할 DOT 없음")

        # ─── DOT_STACK_DETONATE ──────────────────────────────────────
        elif logic == LogicType.DOT_STACK_DETONATE:
            dot_buffs = [
                ab for ab in target.active_buffs
                if ab.buff_data.is_debuff and ab.buff_data.logic_type == LogicType.DOT
            ]
            total_dmg = sum(
                ab.buff_data.value * getattr(ab, 'stacks', 1) for ab in dot_buffs
            ) * target.max_hp
            target.active_buffs = [
                ab for ab in target.active_buffs
                if not (ab.buff_data.is_debuff and ab.buff_data.logic_type == LogicType.DOT)
            ]
            if total_dmg > 0:
                actual = target.take_damage(total_dmg)
                ctx.log.append(
                    f"    {caster.name} → {target.name}: DOT 스택 폭발 {actual:.0f} 피해 "
                    f"({len(dot_buffs)}종 제거, HP {target.current_hp:.0f}/{target.max_hp:.0f})"
                )
                if not target.is_alive:
                    self._killed_this_skill.append(target)
                    ctx.log.append(f"    💀 {target.name} 사망!")
            else:
                ctx.log.append(f"    {caster.name} → {target.name}: 폭발할 DOT 없음")

        # ─── DOT_BLEED ───────────────────────────────────────────────
        elif logic == LogicType.DOT_BLEED:
            duration = int(effect.value) if effect.value else 3
            bleed_bd = BuffData(
                id=f"bleed_{skill.id}",
                name="출혈",
                source_skill_id=skill.id,
                logic_type=LogicType.DOT,
                dot_type="bleed",
                value=effect.multiplier if effect.multiplier else 0.08,
                duration=duration,
                is_debuff=True,
                max_stacks=5,
            )
            ctx.buff_manager.apply_buff(target, bleed_bd, caster.id)
            ctx.log.append(
                f"    {caster.name} → {target.name}: 출혈 DoT ({duration}턴, "
                f"스택 {target.get_tag_count('bleed')})"
            )

        # ─── DOT_SHOCK ───────────────────────────────────────────────
        elif logic == LogicType.DOT_SHOCK:
            duration = int(effect.value) if effect.value else 2
            shock_bd = BuffData(
                id=f"shock_{skill.id}",
                name="감전",
                source_skill_id=skill.id,
                logic_type=LogicType.DOT,
                dot_type="shock",
                value=effect.multiplier if effect.multiplier else 0.06,
                duration=duration,
                is_debuff=True,
            )
            ctx.buff_manager.apply_buff(target, shock_bd, caster.id)
            ctx.log.append(f"    {caster.name} → {target.name}: 감전 DoT ({duration}턴)")
            # 인접 확산
            tr, tc = target.tile_row, target.tile_col
            enemies = ctx.get_enemies_of(caster)
            adjacent = [
                u for u in enemies
                if u.id != target.id and u.is_alive
                and ((abs(u.tile_row - tr) == 1 and u.tile_col == tc) or
                     (u.tile_row == tr and abs(u.tile_col - tc) == 1))
            ]
            for adj in adjacent:
                import copy
                spread_bd = copy.deepcopy(shock_bd)
                spread_bd.id = f"{shock_bd.id}_spread_{adj.id}"
                spread_bd.duration = max(1, duration - 1)
                ctx.buff_manager.apply_buff(adj, spread_bd, caster.id)
            if adjacent:
                ctx.log.append(f"    → 인접 {len(adjacent)}명에게 감전 확산")

        # ─── DOT_WIND_SHEAR ──────────────────────────────────────────
        elif logic == LogicType.DOT_WIND_SHEAR:
            duration = int(effect.value) if effect.value else 3
            current_stacks = target.get_tag_count('wind_shear')
            max_stacks = 5
            if current_stacks < max_stacks:
                wind_bd = BuffData(
                    id=f"wind_shear_{skill.id}_{current_stacks}",
                    name=f"풍화({current_stacks+1}스택)",
                    source_skill_id=skill.id,
                    logic_type=LogicType.DOT,
                    dot_type="wind_shear",
                    value=effect.multiplier if effect.multiplier else 0.04,
                    duration=duration,
                    is_debuff=True,
                    tags=["wind_shear"],
                )
                ctx.buff_manager.apply_buff(target, wind_bd, caster.id)
                ctx.log.append(
                    f"    {caster.name} → {target.name}: 풍화 DoT ({current_stacks+1}/{max_stacks}스택)"
                )
            else:
                ctx.log.append(
                    f"    {caster.name} → {target.name}: 풍화 최대 스택({max_stacks})"
                )

        # ─── SUMMON_CLONE ────────────────────────────────────────────
        elif logic == LogicType.SUMMON_CLONE:
            import copy
            stat_ratio = effect.value if effect.value else 0.5
            clone = copy.deepcopy(caster)
            clone.id = f"{caster.id}_clone"
            clone.name = f"{caster.name}(분신)"
            clone.atk = int(caster.atk * stat_ratio)
            clone.def_ = int(caster.def_ * stat_ratio)
            clone.max_hp = int(caster.max_hp * stat_ratio)
            clone.current_hp = clone.max_hp
            clone.active_buffs = []
            allies_list = ctx.get_allies_of(caster)
            allies_list.append(clone)
            ctx.all_units[clone.id] = clone
            if hasattr(ctx.turn_manager, 'reschedule_unit'):
                ctx.turn_manager.reschedule_unit(clone)
            ctx.log.append(
                f"    {caster.name}: 분신 소환! ({clone.name}, 스탯 {stat_ratio*100:.0f}%)"
            )

        # ─── TRANSFORM ───────────────────────────────────────────────
        elif logic == LogicType.TRANSFORM:
            if hasattr(caster, 'transform'):
                transform_skill_id = getattr(effect, 'transform_skill_id', None)
                caster.transform(transform_skill_id)
                ctx.log.append(f"    {caster.name}: 변신!")
            else:
                ctx.log.append(f"    {caster.name}: 변신 불가 (transform 메서드 없음)")

        # ─── JOINT_ATTACK ────────────────────────────────────────────
        elif logic == LogicType.JOINT_ATTACK:
            allies = [u for u in ctx.get_allies_of(caster) if u.id != caster.id and u.is_alive]
            if allies:
                strongest = max(allies, key=lambda u: u.atk)
                if strongest.data and strongest.data.normal_skill:
                    ctx.log.append(
                        f"    {caster.name} + {strongest.name}: 합체 공격 → {target.name}"
                    )
                    sub_killed = self.execute(strongest, strongest.data.normal_skill, ctx)
                    self._killed_this_skill.extend(sub_killed)
                else:
                    ctx.log.append(f"    {caster.name}: 합체 공격 대상 스킬 없음")
            else:
                ctx.log.append(f"    {caster.name}: 합체 공격 가능한 아군 없음")

        # ─── FOLLOW_UP_ATTACK ────────────────────────────────────────
        elif logic == LogicType.FOLLOW_UP_ATTACK:
            duration = int(effect.value) if effect.value else 2
            marker = BuffData(
                id="follow_up_marker",
                name="추격 공격",
                source_skill_id=skill.id,
                logic_type=LogicType.STAT_CHANGE,
                stat="def_",
                value=0,
                duration=duration,
                is_debuff=False,
                tags=["follow_up"],
            )
            ctx.buff_manager.apply_buff(caster, marker, caster.id)
            ctx.log.append(f"    {caster.name}: 추격 공격 준비 ({duration}턴)")

        # ─── DUAL_ATTACK ─────────────────────────────────────────────
        elif logic == LogicType.DUAL_ATTACK:
            allies = [u for u in ctx.get_allies_of(caster) if u.id != caster.id and u.is_alive]
            if allies:
                partner = random.choice(allies)
                if partner.data and partner.data.normal_skill:
                    ctx.log.append(
                        f"    {caster.name} + {partner.name}: 듀얼어택 → {target.name}"
                    )
                    sub_killed = self.execute(partner, partner.data.normal_skill, ctx)
                    self._killed_this_skill.extend(sub_killed)
                else:
                    ctx.log.append(f"    {caster.name}: 듀얼어택 파트너 스킬 없음")
            else:
                ctx.log.append(f"    {caster.name}: 듀얼어택 가능한 아군 없음")

        # ─── TOTEM ───────────────────────────────────────────────────
        elif logic == LogicType.TOTEM:
            import copy
            totem_hp = target.max_hp * (effect.value if effect.value else 0.2)
            totem = copy.deepcopy(caster)
            totem.id = f"{caster.id}_totem"
            totem.name = f"{caster.name}(토템)"
            totem.atk = 0
            totem.def_ = int(caster.def_ * 0.5)
            totem.max_hp = totem_hp
            totem.current_hp = totem_hp
            totem.active_buffs = []
            allies_list = ctx.get_allies_of(caster)
            allies_list.append(totem)
            ctx.all_units[totem.id] = totem
            ctx.log.append(f"    {caster.name}: 토템 설치! ({totem.name}, HP {totem_hp:.0f})")

        # ─── FIGHTING_SPIRIT ─────────────────────────────────────────
        elif logic == LogicType.FIGHTING_SPIRIT:
            amount = effect.value if effect.value else 1.0
            if hasattr(caster, 'add_fighting_spirit'):
                caster.add_fighting_spirit(amount)
                ctx.log.append(f"    {caster.name}: 투지 게이지 +{amount:.0f}")
            else:
                caster.fighting_spirit = getattr(caster, 'fighting_spirit', 0.0) + amount
                ctx.log.append(f"    {caster.name}: 투지 +{amount:.0f} (총 {caster.fighting_spirit:.0f})")

        # ─── FOCUS_STACK ─────────────────────────────────────────────
        elif logic == LogicType.FOCUS_STACK:
            amount = int(effect.value) if effect.value else 1
            if hasattr(caster, 'add_focus'):
                caster.add_focus(amount)
                ctx.log.append(f"    {caster.name}: 집중 스택 +{amount}")
            else:
                caster.focus_stacks = getattr(caster, 'focus_stacks', 0) + amount
                ctx.log.append(f"    {caster.name}: 집중 +{amount} (총 {caster.focus_stacks})")

        # ─── SOUL_COLLECT ────────────────────────────────────────────
        elif logic == LogicType.SOUL_COLLECT:
            amount = int(effect.value) if effect.value else 1
            caster.soul_stacks = getattr(caster, 'soul_stacks', 0) + amount
            ctx.log.append(f"    {caster.name}: 영혼 수집 +{amount} (총 {caster.soul_stacks})")

        # ─── SOUL_BURN ───────────────────────────────────────────────
        elif logic == LogicType.SOUL_BURN:
            soul_cost = getattr(effect, 'soul_cost', 1)
            current_souls = getattr(caster, 'soul_stacks', 0)
            if current_souls >= soul_cost:
                caster.soul_stacks = current_souls - soul_cost
                ctx.log.append(
                    f"    {caster.name}: 소울번 발동 (소울 -{soul_cost}, 남은 {caster.soul_stacks})"
                )
            else:
                ctx.log.append(
                    f"    {caster.name}: 소울번 실패 (소울 {current_souls}/{soul_cost})"
                )

        # ─── ENERGY_CHARGE ───────────────────────────────────────────
        elif logic == LogicType.ENERGY_CHARGE:
            amount = effect.value if effect.value else 20.0
            if hasattr(target, 'add_energy'):
                target.add_energy(amount)
            else:
                target.energy = min(
                    getattr(target, 'max_energy', 100),
                    getattr(target, 'energy', 0) + amount
                )
            ctx.log.append(
                f"    {caster.name} → {target.name}: 에너지 +{amount:.0f}"
            )

        # ─── ENERGY_DRAIN ────────────────────────────────────────────
        elif logic == LogicType.ENERGY_DRAIN:
            amount = effect.value if effect.value else 20.0
            target.energy = max(0, getattr(target, 'energy', 0) - amount)
            ctx.log.append(
                f"    {caster.name} → {target.name}: 에너지 -{amount:.0f} (남은 {target.energy:.0f})"
            )

        # ─── KILL_EXTRA_TURN ─────────────────────────────────────────
        elif logic == LogicType.KILL_EXTRA_TURN:
            dmg, is_crit, is_dodged = compute_damage(caster, target, effect.multiplier)
            if is_dodged:
                ctx.log.append(f"    {caster.name} → {target.name}: {skill.name} 회피!")
                return
            actual = target.take_damage(dmg)
            crit_str = " [크리티컬!]" if is_crit else ""
            ctx.log.append(
                f"    {caster.name} → {target.name}: {skill.name} {actual:.0f} 피해{crit_str} "
                f"(HP {target.current_hp:.0f}/{target.max_hp:.0f})"
            )
            if target.is_alive and ctx.trigger_system:
                ctx.trigger_system.evaluate_on_hit(target, caster, int(actual), ctx)
            if not target.is_alive:
                self._killed_this_skill.append(target)
                ctx.log.append(f"    💀 {target.name} 사망!")
                ctx.turn_manager.add_extra_turn(caster)
                ctx.log.append(f"    {caster.name}: 처치 → 추가 행동!")

        # ─── CRIT_CHAIN ──────────────────────────────────────────────
        elif logic == LogicType.CRIT_CHAIN:
            dmg, is_crit, is_dodged = compute_damage(caster, target, effect.multiplier)
            if is_dodged:
                ctx.log.append(f"    {caster.name} → {target.name}: {skill.name} 회피!")
                return
            actual = target.take_damage(dmg)
            crit_str = " [크리티컬!]" if is_crit else ""
            ctx.log.append(
                f"    {caster.name} → {target.name}: {skill.name} {actual:.0f} 피해{crit_str} "
                f"(HP {target.current_hp:.0f}/{target.max_hp:.0f})"
            )
            if target.is_alive and ctx.trigger_system:
                ctx.trigger_system.evaluate_on_hit(target, caster, int(actual), ctx)
            if not target.is_alive:
                self._killed_this_skill.append(target)
                ctx.log.append(f"    💀 {target.name} 사망!")
            if is_crit and target.is_alive:
                # 크리 시 추가 타격
                bonus_mult = effect.value if effect.value else 0.5
                dmg2, is_crit2, _ = compute_damage(caster, target, bonus_mult)
                actual2 = target.take_damage(dmg2)
                crit_str2 = " [크리티컬!]" if is_crit2 else ""
                ctx.log.append(
                    f"    → {target.name}: 크리 추가타 {actual2:.0f} 피해{crit_str2} "
                    f"(HP {target.current_hp:.0f}/{target.max_hp:.0f})"
                )
                if not target.is_alive:
                    self._killed_this_skill.append(target)
                    ctx.log.append(f"    💀 {target.name} 사망!")

        # ─── COUNTERATTACK_PASSIVE ───────────────────────────────────
        elif logic == LogicType.COUNTERATTACK_PASSIVE:
            duration = int(effect.value) if effect.value else 3
            marker = BuffData(
                id="counterattack_passive_marker",
                name="확률 반격",
                source_skill_id=skill.id,
                logic_type=LogicType.STAT_CHANGE,
                stat="def_",
                value=effect.multiplier if effect.multiplier else 0.3,
                duration=duration,
                is_debuff=False,
                tags=["counterattack"],
            )
            ctx.buff_manager.apply_buff(caster, marker, caster.id)
            ctx.log.append(f"    {caster.name}: 확률 반격 준비 ({duration}턴)")

        # ─── ALLY_DEATH_RAGE ─────────────────────────────────────────
        elif logic == LogicType.ALLY_DEATH_RAGE:
            atk_gain = effect.value if effect.value else 0.1
            spd_gain = effect.multiplier if effect.multiplier else 0.05
            perm_atk = BuffData(
                id=f"ally_death_rage_atk_{skill.id}",
                name="분노(ATK)",
                source_skill_id=skill.id,
                logic_type=LogicType.STAT_CHANGE,
                stat="atk",
                value=int(caster.atk * atk_gain),
                duration=9999,
                is_debuff=False,
            )
            perm_spd = BuffData(
                id=f"ally_death_rage_spd_{skill.id}",
                name="분노(SPD)",
                source_skill_id=skill.id,
                logic_type=LogicType.STAT_CHANGE,
                stat="spd",
                value=int(caster.spd * spd_gain),
                duration=9999,
                is_debuff=False,
            )
            ctx.buff_manager.apply_buff(caster, perm_atk, caster.id)
            ctx.buff_manager.apply_buff(caster, perm_spd, caster.id)
            ctx.log.append(
                f"    {caster.name}: 아군 사망 분노 발동! ATK+{atk_gain*100:.0f}%, SPD+{spd_gain*100:.0f}%"
            )

        # ─── FIRST_STRIKE_BONUS ──────────────────────────────────────
        elif logic == LogicType.FIRST_STRIKE_BONUS:
            if not getattr(caster, 'first_attack_used', False):
                multiplier = effect.multiplier * 2.0
                caster.first_attack_used = True
            else:
                multiplier = effect.multiplier
            dmg, is_crit, is_dodged = compute_damage(caster, target, multiplier)
            if is_dodged:
                ctx.log.append(f"    {caster.name} → {target.name}: {skill.name} 회피!")
                return
            actual = target.take_damage(dmg)
            crit_str = " [크리티컬!]" if is_crit else ""
            first_str = " [첫 타격 2배!]" if multiplier == effect.multiplier * 2.0 else ""
            ctx.log.append(
                f"    {caster.name} → {target.name}: {skill.name} {actual:.0f} 피해{crit_str}{first_str} "
                f"(HP {target.current_hp:.0f}/{target.max_hp:.0f})"
            )
            if target.is_alive and ctx.trigger_system:
                ctx.trigger_system.evaluate_on_hit(target, caster, int(actual), ctx)
            if not target.is_alive:
                self._killed_this_skill.append(target)
                ctx.log.append(f"    💀 {target.name} 사망!")

        # ─── FULL_HP_BONUS ───────────────────────────────────────────
        elif logic == LogicType.FULL_HP_BONUS:
            if caster.hp_ratio >= 1.0:
                multiplier = effect.multiplier * 1.3
                bonus_str = " [만HP 보너스!]"
            else:
                multiplier = effect.multiplier
                bonus_str = ""
            dmg, is_crit, is_dodged = compute_damage(caster, target, multiplier)
            if is_dodged:
                ctx.log.append(f"    {caster.name} → {target.name}: {skill.name} 회피!")
                return
            actual = target.take_damage(dmg)
            crit_str = " [크리티컬!]" if is_crit else ""
            ctx.log.append(
                f"    {caster.name} → {target.name}: {skill.name} {actual:.0f} 피해{crit_str}{bonus_str} "
                f"(HP {target.current_hp:.0f}/{target.max_hp:.0f})"
            )
            if target.is_alive and ctx.trigger_system:
                ctx.trigger_system.evaluate_on_hit(target, caster, int(actual), ctx)
            if not target.is_alive:
                self._killed_this_skill.append(target)
                ctx.log.append(f"    💀 {target.name} 사망!")

        # ─── LAST_STAND ──────────────────────────────────────────────
        elif logic == LogicType.LAST_STAND:
            allies = ctx.get_allies_of(caster)
            if len(allies) == 1:
                boost = 0.5
                for stat_name in ["atk", "def_", "spd"]:
                    stat_val = getattr(caster, stat_name, 0)
                    ls_buff = BuffData(
                        id=f"last_stand_{stat_name}",
                        name=f"최후의 의지({stat_name})",
                        source_skill_id=skill.id,
                        logic_type=LogicType.STAT_CHANGE,
                        stat=stat_name,
                        value=int(stat_val * boost),
                        duration=9999,
                        is_debuff=False,
                    )
                    ctx.buff_manager.apply_buff(caster, ls_buff, caster.id)
                ctx.log.append(
                    f"    {caster.name}: 최후의 의지! 전 스탯 +50% (단독 생존)"
                )
            else:
                ctx.log.append(
                    f"    {caster.name}: 최후의 의지 미발동 (아군 {len(allies)}명 생존)"
                )

        # ─── STACK_PASSIVE ───────────────────────────────────────────
        elif logic == LogicType.STACK_PASSIVE:
            tag_key = f"stack_passive_{skill.id}"
            caster.add_tag(tag_key)
            stacks = caster.get_tag_count(tag_key)
            scale = effect.value if effect.value else 0.05
            stat_name = effect.buff_data.stat if effect.buff_data and effect.buff_data.stat else "atk"
            stat_val = getattr(caster, stat_name, 0)
            stack_buff = BuffData(
                id=f"stack_passive_buff_{skill.id}_{stacks}",
                name=f"스택 패시브({stacks})",
                source_skill_id=skill.id,
                logic_type=LogicType.STAT_CHANGE,
                stat=stat_name,
                value=int(stat_val * scale),
                duration=9999,
                is_debuff=False,
            )
            ctx.buff_manager.apply_buff(caster, stack_buff, caster.id)
            ctx.log.append(
                f"    {caster.name}: 스택 패시브 {stacks}스택 ({stat_name} +{scale*100:.0f}%)"
            )

        # ─── ELEMENT_CHANGE ──────────────────────────────────────────
        elif logic == LogicType.ELEMENT_CHANGE:
            new_element = getattr(effect, 'element', None) or (
                effect.condition.get('element') if effect.condition else None
            )
            duration = int(effect.value) if effect.value else 3
            if new_element:
                caster._original_element = caster.element
                caster.element = new_element
                ctx.log.append(
                    f"    {caster.name}: 속성 변환 → {new_element} ({duration}턴)"
                )
            else:
                ctx.log.append(f"    {caster.name}: 속성 변환 대상 속성 없음")

        # ─── LEADER_SKILL ────────────────────────────────────────────
        elif logic == LogicType.LEADER_SKILL:
            if effect.buff_data:
                allies = ctx.get_allies_of(caster)
                for ally in allies:
                    perm_buff = BuffData(
                        id=f"leader_skill_{skill.id}_{ally.id}",
                        name=f"리더 스킬({effect.buff_data.stat})",
                        source_skill_id=skill.id,
                        logic_type=LogicType.STAT_CHANGE,
                        stat=effect.buff_data.stat,
                        value=effect.buff_data.value,
                        duration=9999,
                        is_debuff=False,
                    )
                    ctx.buff_manager.apply_buff(ally, perm_buff, caster.id)
                ctx.log.append(
                    f"    {caster.name}: 리더 스킬 발동 → 아군 전체 {effect.buff_data.stat} "
                    f"+{effect.buff_data.value}"
                )

        # ─── EFFECT_RES_DOWN ─────────────────────────────────────────
        elif logic == LogicType.EFFECT_RES_DOWN:
            reduce_val = effect.value if effect.value else 0.2
            duration = int(effect.multiplier) if effect.multiplier else 2
            debuff = BuffData(
                id=f"effect_res_down_{skill.id}",
                name="효과 저항 감소",
                source_skill_id=skill.id,
                logic_type=LogicType.STAT_CHANGE,
                stat="effect_res",
                value=-reduce_val,
                duration=duration,
                is_debuff=True,
            )
            ctx.buff_manager.apply_buff(target, debuff, caster.id)
            ctx.log.append(
                f"    {caster.name} → {target.name}: 효과 저항 -{reduce_val*100:.0f}% ({duration}턴)"
            )

        # ─── TOUGHNESS_BREAK ─────────────────────────────────────────
        elif logic == LogicType.TOUGHNESS_BREAK:
            tough_dmg = effect.value if effect.value else 30.0
            current_tough = getattr(target, 'toughness', 0)
            target.toughness = max(0, current_tough - tough_dmg)
            ctx.log.append(
                f"    {caster.name} → {target.name}: 터프니스 -{tough_dmg:.0f} "
                f"(남은 {target.toughness:.0f})"
            )
            if target.toughness <= 0 and current_tough > 0:
                ctx.log.append(f"    {target.name}: 약점 격파!")
                if ctx.trigger_system:
                    ctx.trigger_system.evaluate(
                        'on_toughness_break', target, caster, ctx
                    )

        # ─── BOSS_ENRAGE ─────────────────────────────────────────────
        elif logic == LogicType.BOSS_ENRAGE:
            caster.enrage_stacks = getattr(caster, 'enrage_stacks', 0) + 1
            stacks = caster.enrage_stacks
            atk_gain = effect.value if effect.value else 0.1
            enrage_buff = BuffData(
                id=f"boss_enrage_{stacks}",
                name=f"광폭화({stacks})",
                source_skill_id=skill.id,
                logic_type=LogicType.STAT_CHANGE,
                stat="atk",
                value=int(caster.atk * atk_gain),
                duration=9999,
                is_debuff=False,
            )
            ctx.buff_manager.apply_buff(caster, enrage_buff, caster.id)
            ctx.log.append(
                f"    {caster.name}: 보스 광폭화 {stacks}스택! ATK +{atk_gain*100:.0f}%"
            )

        # ─── BOSS_PHASE_ATTACK ───────────────────────────────────────
        elif logic == LogicType.BOSS_PHASE_ATTACK:
            allies = ctx.get_allies_of(caster)
            for ally in allies:
                if ally.is_alive:
                    dmg, is_crit, _ = compute_damage(caster, ally, effect.multiplier)
                    actual = ally.take_damage(dmg)
                    crit_str = " [크리티컬!]" if is_crit else ""
                    ctx.log.append(
                        f"    {caster.name} → {ally.name}: 페이즈 공격 {actual:.0f} 피해{crit_str} "
                        f"(HP {ally.current_hp:.0f}/{ally.max_hp:.0f})"
                    )
                    if not ally.is_alive:
                        self._killed_this_skill.append(ally)
                        ctx.log.append(f"    💀 {ally.name} 사망!")

        # ─── COUNTDOWN_WIPE ──────────────────────────────────────────
        elif logic == LogicType.COUNTDOWN_WIPE:
            countdown = int(effect.value) if effect.value else 3
            enemies = ctx.get_enemies_of(caster)
            for enemy in enemies:
                if enemy.is_alive:
                    marker = BuffData(
                        id=f"countdown_wipe_{enemy.id}",
                        name=f"카운트다운({countdown})",
                        source_skill_id=skill.id,
                        logic_type=LogicType.STAT_CHANGE,
                        stat="def_",
                        value=0,
                        duration=countdown,
                        is_debuff=True,
                        tags=["countdown_wipe"],
                    )
                    ctx.buff_manager.apply_buff(enemy, marker, caster.id)
            ctx.log.append(
                f"    {caster.name}: 카운트다운 즉사기 ({countdown}턴 후 전멸, {len(enemies)}명 대상)"
            )

        # ─── SHIELD_PHASE ────────────────────────────────────────────
        elif logic == LogicType.SHIELD_PHASE:
            shield_amount = caster.max_hp * (effect.value if effect.value else 0.5)
            caster.add_barrier(shield_amount)
            duration = int(effect.multiplier) if effect.multiplier else 3
            marker = BuffData(
                id="shield_phase_marker",
                name="쉴드 페이즈",
                source_skill_id=skill.id,
                logic_type=LogicType.STAT_CHANGE,
                stat="def_",
                value=0,
                duration=duration,
                is_debuff=False,
                tags=["shield_phase"],
            )
            ctx.buff_manager.apply_buff(caster, marker, caster.id)
            ctx.log.append(
                f"    {caster.name}: 쉴드 페이즈! 보호막 {shield_amount:.0f} ({duration}턴)"
            )

        # ─── PART_BREAK ──────────────────────────────────────────────
        elif logic == LogicType.PART_BREAK:
            part_name = effect.condition.get('part', 'body') if effect.condition else 'body'
            dmg = effect.value if effect.value else 100.0
            parts = getattr(target, 'parts', {})
            if part_name in parts:
                parts[part_name] = max(0, parts[part_name] - dmg)
                broken = parts[part_name] <= 0
                ctx.log.append(
                    f"    {caster.name} → {target.name}: 부위 파괴({part_name}) "
                    f"-{dmg:.0f} {'[파괴!]' if broken else ''}"
                )
            else:
                ctx.log.append(
                    f"    {caster.name} → {target.name}: 부위 파괴 ({part_name}) "
                    f"— 부위 없음, 일반 피해 적용"
                )
                actual = target.take_damage(dmg)
                if not target.is_alive:
                    self._killed_this_skill.append(target)
                    ctx.log.append(f"    💀 {target.name} 사망!")

        # ─── KNOCKBACK (넉백: 전열→후열 강제 이동) ─────────────────
        elif logic == LogicType.KNOCKBACK:
            old_row = target.tile_row
            new_row = min(2, old_row + KNOCKBACK_ROWS)
            if new_row != old_row:
                target.set_tile_pos(new_row, target.tile_col)
                row_names = {0: "전열", 1: "중열", 2: "후열"}
                ctx.log.append(
                    f"    {caster.name} → {target.name}: 넉백! "
                    f"{row_names[old_row]}→{row_names[new_row]}"
                )
                # ON_KNOCKBACK 트리거
                if ctx.trigger_system:
                    from battle.enums import TriggerEvent
                    ctx.trigger_system.evaluate(TriggerEvent.ON_KNOCKBACK, caster, ctx)
            else:
                # 이미 최후열(row 2) → 벽꿍 대미지
                wall_dmg = target.max_hp * KNOCKBACK_WALL_DAMAGE_RATIO
                actual = target.take_damage(wall_dmg)
                ctx.log.append(
                    f"    {caster.name} → {target.name}: 넉백 — 벽꿍! "
                    f"{actual:.0f} 피해 (HP {target.current_hp:.0f}/{target.max_hp:.0f})"
                )
                if not target.is_alive:
                    self._killed_this_skill.append(target)
                    ctx.log.append(f"    💀 {target.name} 사망!")

        # ─── DAMAGE_POSITION_SCALE (위치 기반 대미지) ───────────────
        elif logic == LogicType.DAMAGE_POSITION_SCALE:
            scale_value = effect.value if effect.value else 0.15
            dmg, is_crit, is_dodged = compute_damage_position_scale(
                caster, target, effect.multiplier, scale_value
            )
            if is_dodged:
                ctx.log.append(
                    f"    {caster.name} → {target.name}: {skill.name} 회피!"
                )
                return
            actual = target.take_damage(dmg)
            row_names = {0: "전열", 1: "중열", 2: "후열"}
            crit_str = " [크리티컬!]" if is_crit else ""
            ctx.log.append(
                f"    {caster.name} → {target.name}: {skill.name} {actual:.0f} 피해{crit_str} "
                f"(위치:{row_names[target.tile_row]}) "
                f"(HP {target.current_hp:.0f}/{target.max_hp:.0f})"
            )
            if is_crit and caster.is_alive and ctx.trigger_system:
                ctx.trigger_system.evaluate_on_critical_hit(caster, target, ctx)
            if not target.is_alive:
                self._killed_this_skill.append(target)
                ctx.log.append(f"    💀 {target.name} 사망!")

        # ─── DAMAGE_POISON_SCALE (중독 스택 비례 대미지) ─────────────
        elif logic == LogicType.DAMAGE_POISON_SCALE:
            poison_stacks = target.get_tag_count("poison")
            bonus = 1.0 + (effect.value if effect.value else 0.20) * poison_stacks
            dmg, is_crit, is_dodged = compute_damage(caster, target, effect.multiplier)
            if is_dodged:
                ctx.log.append(
                    f"    {caster.name} → {target.name}: {skill.name} 회피!"
                )
                return
            dmg = int(dmg * bonus)
            actual = target.take_damage(dmg)
            crit_str = " [크리티컬!]" if is_crit else ""
            ctx.log.append(
                f"    {caster.name} → {target.name}: {skill.name} {actual:.0f} 피해{crit_str} "
                f"(중독 {poison_stacks}스택, ×{bonus:.1f}) "
                f"(HP {target.current_hp:.0f}/{target.max_hp:.0f})"
            )
            if not target.is_alive:
                self._killed_this_skill.append(target)
                ctx.log.append(f"    💀 {target.name} 사망!")

        # ─── DAMAGE_STONE_BONUS (석화 대상 2배 대미지) ───────────────
        elif logic == LogicType.DAMAGE_STONE_BONUS:
            is_stoned = target.hard_cc == CCType.STONE
            bonus = 2.0 if is_stoned else 1.0
            dmg, is_crit, is_dodged = compute_damage(caster, target, effect.multiplier)
            if is_dodged:
                ctx.log.append(
                    f"    {caster.name} → {target.name}: {skill.name} 회피!"
                )
                return
            dmg = int(dmg * bonus)
            actual = target.take_damage(dmg)
            crit_str = " [크리티컬!]" if is_crit else ""
            stone_str = " [석화 보너스!]" if is_stoned else ""
            ctx.log.append(
                f"    {caster.name} → {target.name}: {skill.name} {actual:.0f} 피해{crit_str}{stone_str} "
                f"(HP {target.current_hp:.0f}/{target.max_hp:.0f})"
            )
            if not target.is_alive:
                self._killed_this_skill.append(target)
                ctx.log.append(f"    💀 {target.name} 사망!")

        # ─── INSTANT_KILL (즉사: HP% 이하 시) ──────────────────────
        elif logic == LogicType.INSTANT_KILL:
            threshold = effect.value if effect.value else 0.25
            if target.hp_ratio <= threshold:
                target.current_hp = 0
                ctx.log.append(
                    f"    {caster.name} → {target.name}: 즉사! "
                    f"(HP {target.hp_ratio*100:.0f}% ≤ {threshold*100:.0f}%)"
                )
                self._killed_this_skill.append(target)
                ctx.log.append(f"    💀 {target.name} 사망!")
            else:
                ctx.log.append(
                    f"    {caster.name} → {target.name}: 즉사 실패 "
                    f"(HP {target.hp_ratio*100:.0f}% > {threshold*100:.0f}%)"
                )

        # ─── EXECUTE (처형: 최저HP 대상 배율 증가) ───────────────────
        elif logic == LogicType.EXECUTE:
            # HP가 낮을수록 배율 증가: mult × (1 + (1 - hp_ratio) × execute_bonus)
            execute_bonus = effect.value if effect.value else 0.5
            extra_mult = 1.0 + (1.0 - target.hp_ratio) * execute_bonus
            dmg, is_crit, is_dodged = compute_damage(caster, target, effect.multiplier * extra_mult)
            if is_dodged:
                ctx.log.append(
                    f"    {caster.name} → {target.name}: {skill.name} 회피!"
                )
                return
            actual = target.take_damage(dmg)
            crit_str = " [크리티컬!]" if is_crit else ""
            ctx.log.append(
                f"    {caster.name} → {target.name}: {skill.name} {actual:.0f} 피해{crit_str} "
                f"(처형 ×{extra_mult:.2f}) "
                f"(HP {target.current_hp:.0f}/{target.max_hp:.0f})"
            )
            if not target.is_alive:
                self._killed_this_skill.append(target)
                ctx.log.append(f"    💀 {target.name} 사망!")

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
