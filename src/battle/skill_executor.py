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
