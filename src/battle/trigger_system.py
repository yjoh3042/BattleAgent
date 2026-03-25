"""TriggerSystem - 패시브 트리거 평가 및 발동"""
from __future__ import annotations
from typing import List, Dict, Optional, TYPE_CHECKING

from battle.enums import TriggerEvent
from battle.models import TriggerData

if TYPE_CHECKING:
    from battle.battle_unit import BattleUnit
    from battle.skill_executor import EngineContext, SkillExecutor


class TriggerSystem:
    """
    전투 이벤트에 반응하는 패시브 트리거 평가.
    TriggerData.condition 구조:
      - hp_threshold: float (0.0~1.0) → HP가 이 비율 이하일 때
      - tag: str + count: int → 태그가 N 이상 스택 시
      - burn_stack_min: int → 화상 스택이 N 이상일 때
      - target_has_burn: bool → 타겟이 화상 상태일 때
      - once_per_battle: bool → 전투당 1회 제한
    """

    def __init__(self, executor: SkillExecutor):
        self._executor = executor
        self._log: List[str] = []

    def evaluate(
        self,
        event: TriggerEvent,
        unit: BattleUnit,
        ctx: EngineContext,
        extra: Optional[Dict] = None,
    ) -> List[BattleUnit]:
        """
        특정 이벤트에 대해 unit의 모든 트리거 조건 평가.
        조건 충족 시 트리거 스킬/버프 발동.
        반환: 트리거로 처치된 유닛 목록
        """
        killed = []
        if not unit.data.triggers:
            return killed

        for trigger in unit.data.triggers:
            if trigger.event != event:
                continue

            # 전투당 1회 제한
            trigger_key = f"{unit.id}_{trigger.event.value}_{trigger.skill_id}"
            if trigger.once_per_battle and unit.was_triggered(trigger_key):
                continue

            # 조건 평가
            if not self._check_condition(unit, trigger, ctx, extra):
                continue

            # 트리거 발동
            self._log.append(f"  ⚡ {unit.name} 트리거 발동: {trigger.event.value}")

            if trigger.once_per_battle:
                unit.mark_triggered(trigger_key)

            # 스킬 발동
            if trigger.skill_id:
                skill = self._find_skill(unit, trigger.skill_id)
                if skill:
                    result = self._executor.execute(unit, skill, ctx)
                    killed.extend(result)

            # 버프 직접 부여
            if trigger.buff_id:
                buff = self._find_buff(unit, trigger.buff_id)
                if buff:
                    ctx.buff_manager.apply_buff(unit, buff, unit.id)

        return killed

    def evaluate_on_kill(
        self,
        killer: BattleUnit,
        killed_unit: BattleUnit,
        ctx: EngineContext,
    ) -> List[BattleUnit]:
        """킬 발생 시 트리거"""
        return self.evaluate(TriggerEvent.ON_KILL, killer, ctx, extra={'killed': killed_unit})

    def evaluate_on_hit(
        self,
        defender: BattleUnit,
        attacker: BattleUnit,
        damage: int,
        ctx: EngineContext,
    ) -> List[BattleUnit]:
        """피격 시 트리거 (반격 포함)"""
        return self.evaluate(
            TriggerEvent.ON_HIT, defender, ctx,
            extra={'attacker': attacker, 'damage': damage}
        )

    def evaluate_battle_start(
        self,
        units: List[BattleUnit],
        ctx: EngineContext,
    ):
        """전투 시작 트리거 (초기 버프 등)"""
        for unit in units:
            if unit.is_alive:
                self.evaluate(TriggerEvent.ON_BATTLE_START, unit, ctx)

    def evaluate_round_start(
        self,
        units: List[BattleUnit],
        ctx: EngineContext,
    ):
        """배틀 라운드 시작 트리거"""
        for unit in units:
            if unit.is_alive:
                self.evaluate(TriggerEvent.ON_ROUND_START, unit, ctx)

    def evaluate_on_critical_hit(
        self,
        attacker: BattleUnit,
        target: BattleUnit,
        ctx: EngineContext,
    ) -> List[BattleUnit]:
        """치명타 적중 시 트리거"""
        return self.evaluate(
            TriggerEvent.ON_CRITICAL_HIT, attacker, ctx,
            extra={'target': target}
        )

    def evaluate_on_ultimate_used(
        self,
        caster: BattleUnit,
        ctx: EngineContext,
    ) -> List[BattleUnit]:
        """얼티밋 스킬 사용 후 트리거"""
        return self.evaluate(TriggerEvent.ON_ULTIMATE_USED, caster, ctx)

    def evaluate_on_buff_gained(
        self,
        unit: BattleUnit,
        buff_data,
        ctx: EngineContext,
    ) -> List[BattleUnit]:
        """버프 획득 시 트리거"""
        return self.evaluate(
            TriggerEvent.ON_BUFF_GAINED, unit, ctx,
            extra={'buff': buff_data}
        )

    # ══════════════════════════════════════════════════════════════
    # 3대 RPG 확장 트리거 이벤트 핸들러
    # ══════════════════════════════════════════════════════════════

    def evaluate_on_ally_death(
        self,
        survivor: BattleUnit,
        dead_ally: BattleUnit,
        ctx: EngineContext,
    ) -> List[BattleUnit]:
        """아군 사망 시 트리거 (분노 버프, 각성 등)"""
        return self.evaluate(
            TriggerEvent.ON_ALLY_DEATH, survivor, ctx,
            extra={'dead_ally': dead_ally}
        )

    def evaluate_on_enemy_death(
        self,
        dead_enemy: BattleUnit,
        killer: BattleUnit,
        ctx: EngineContext,
    ) -> List[BattleUnit]:
        """적 사망 시 트리거 (디버프 전염 등)"""
        return self.evaluate(
            TriggerEvent.ON_ENEMY_DEATH, dead_enemy, ctx,
            extra={'killer': killer}
        )

    def evaluate_on_ally_attack(
        self,
        ally: BattleUnit,
        attacker: BattleUnit,
        target: BattleUnit,
        ctx: EngineContext,
    ) -> List[BattleUnit]:
        """아군 공격 시 트리거 (추격 공격, 듀얼어택)"""
        return self.evaluate(
            TriggerEvent.ON_ALLY_ATTACK, ally, ctx,
            extra={'attacker': attacker, 'target': target}
        )

    def evaluate_on_debuff_applied(
        self,
        unit: BattleUnit,
        debuff_data,
        ctx: EngineContext,
    ) -> List[BattleUnit]:
        """디버프 부여 시 트리거"""
        return self.evaluate(
            TriggerEvent.ON_DEBUFF_APPLIED, unit, ctx,
            extra={'debuff': debuff_data}
        )

    def evaluate_on_barrier_break(
        self,
        unit: BattleUnit,
        ctx: EngineContext,
    ) -> List[BattleUnit]:
        """보호막 파괴 시 트리거"""
        return self.evaluate(TriggerEvent.ON_BARRIER_BREAK, unit, ctx)

    def evaluate_on_revive(
        self,
        unit: BattleUnit,
        ctx: EngineContext,
    ) -> List[BattleUnit]:
        """부활 시 트리거"""
        return self.evaluate(TriggerEvent.ON_REVIVE, unit, ctx)

    def evaluate_on_heal(
        self,
        unit: BattleUnit,
        heal_amount: float,
        ctx: EngineContext,
    ) -> List[BattleUnit]:
        """회복 시 트리거"""
        return self.evaluate(
            TriggerEvent.ON_HEAL, unit, ctx,
            extra={'heal_amount': heal_amount}
        )

    def evaluate_on_counter(
        self,
        counter_unit: BattleUnit,
        target: BattleUnit,
        ctx: EngineContext,
    ) -> List[BattleUnit]:
        """반격 발동 시 트리거"""
        return self.evaluate(
            TriggerEvent.ON_COUNTER, counter_unit, ctx,
            extra={'target': target}
        )

    def evaluate_on_dodge(
        self,
        dodger: BattleUnit,
        attacker: BattleUnit,
        ctx: EngineContext,
    ) -> List[BattleUnit]:
        """회피 성공 시 트리거"""
        return self.evaluate(
            TriggerEvent.ON_DODGE, dodger, ctx,
            extra={'attacker': attacker}
        )

    def evaluate_on_bomb_explode(
        self,
        unit: BattleUnit,
        damage: int,
        ctx: EngineContext,
    ) -> List[BattleUnit]:
        """폭탄 폭발 시 트리거"""
        return self.evaluate(
            TriggerEvent.ON_BOMB_EXPLODE, unit, ctx,
            extra={'damage': damage}
        )

    def evaluate_on_toughness_break(
        self,
        unit: BattleUnit,
        attacker: BattleUnit,
        ctx: EngineContext,
    ) -> List[BattleUnit]:
        """터프니스 격파 시 트리거"""
        return self.evaluate(
            TriggerEvent.ON_TOUGHNESS_BREAK, unit, ctx,
            extra={'attacker': attacker}
        )

    def evaluate_on_energy_full(
        self,
        unit: BattleUnit,
        ctx: EngineContext,
    ) -> List[BattleUnit]:
        """에너지 만충 시 트리거"""
        return self.evaluate(TriggerEvent.ON_ENERGY_FULL, unit, ctx)

    # ─── 조건 평가 ────────────────────────────────────────────────
    def _check_condition(
        self,
        unit: BattleUnit,
        trigger: TriggerData,
        ctx: EngineContext,
        extra: Optional[Dict],
    ) -> bool:
        cond = trigger.condition
        if not cond:
            return True

        # HP 임계값
        if 'hp_threshold' in cond:
            if unit.hp_ratio > cond['hp_threshold']:
                return False

        # 태그 스택
        if 'tag' in cond:
            tag = cond['tag']
            min_count = cond.get('count', 1)
            if unit.get_tag_count(tag) < min_count:
                return False

        # 화상 스택 (타겟 기준)
        if 'burn_stack_min' in cond:
            enemies = ctx.get_enemies_of(unit)
            max_burn = max((e.get_tag_count('burn') for e in enemies), default=0)
            if max_burn < cond['burn_stack_min']:
                return False

        # 타겟이 화상 상태
        if cond.get('target_has_burn') and extra:
            target = extra.get('killed') or extra.get('attacker')
            if target and target.get_tag_count('burn') == 0:
                return False

        # ── 3대 RPG 확장 조건 ────────────────────────────────────
        # HP 상한 (HP가 이 비율 이상일 때)
        if 'hp_above' in cond:
            if unit.hp_ratio < cond['hp_above']:
                return False

        # 특정 디버프 보유 여부
        if 'has_debuff_type' in cond:
            required = cond['has_debuff_type']
            has_it = any(
                ab.buff_data.dot_type == required or
                (ab.buff_data.cc_type and ab.buff_data.cc_type.value == required)
                for ab in unit.active_buffs if ab.buff_data.is_debuff
            )
            if not has_it:
                return False

        # 특정 버프 보유 여부
        if 'has_buff_tag' in cond:
            tag = cond['has_buff_tag']
            has_it = any(
                tag in (ab.buff_data.tags or [])
                for ab in unit.active_buffs
            )
            if not has_it:
                return False

        # 아군 수 조건
        if 'ally_count_max' in cond:
            allies = ctx.get_allies_of(unit)
            if len(allies) > cond['ally_count_max']:
                return False

        # 에너지 임계값
        if 'energy_threshold' in cond:
            if unit.energy < cond['energy_threshold']:
                return False

        # 투지 게이지 임계값
        if 'fighting_spirit_threshold' in cond:
            if unit.fighting_spirit < cond['fighting_spirit_threshold']:
                return False

        # 집중 스택 조건
        if 'focus_min' in cond:
            if unit.focus < cond['focus_min']:
                return False

        # 킬 카운트 조건
        if 'kill_count_min' in cond:
            if unit.kill_count < cond['kill_count_min']:
                return False

        # 변신 상태 조건
        if 'is_transformed' in cond:
            if unit.is_transformed != cond['is_transformed']:
                return False

        # 확률 기반 트리거
        if 'probability' in cond:
            import random
            if random.random() > cond['probability']:
                return False

        return True

    # ─── 스킬/버프 조회 ───────────────────────────────────────────
    def _find_skill(self, unit: BattleUnit, skill_id: str):
        """유닛의 스킬 중 ID로 검색"""
        for skill in (unit.data.normal_skill, unit.data.active_skill, unit.data.ultimate_skill, unit.data.passive_skill):
            if skill and skill.id == skill_id:
                return skill
        return None

    def _find_buff(self, unit: BattleUnit, buff_id: str):
        """유닛의 스킬 효과 중 버프 ID로 검색"""
        for skill in (unit.data.normal_skill, unit.data.active_skill, unit.data.ultimate_skill, unit.data.passive_skill):
            if not skill:
                continue
            for effect in skill.effects:
                if effect.buff_data and effect.buff_data.id == buff_id:
                    return effect.buff_data
        return None

    def flush_log(self) -> List[str]:
        logs = self._log[:]
        self._log.clear()
        return logs
