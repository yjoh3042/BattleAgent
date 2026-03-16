"""BattleEngine - 전투 메인 루프 오케스트레이터

ATB(Active Time Battle) 기획을 CTB(Conditional Turn-Based) heapq 큐로 구현.
두 방식은 행동 간격 = BATTLE_LENGTH / SPD 공식이 동일하여 결과가 같다.
SP 관리, 스킬 실행, 트리거 처리를 통합 관리한다.
"""
from __future__ import annotations
import random
from typing import List, Dict, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from battle.battle_recorder import BattleRecorder

from battle.enums import BattleResult, SkillType, CCType, TriggerEvent
from battle.models import CharacterData
from battle.battle_unit import BattleUnit
from battle.turn_manager import TurnManager
from battle.sp_manager import SPManager
from battle.buff_manager import BuffManager
from battle.skill_executor import SkillExecutor, EngineContext
from battle.trigger_system import TriggerSystem
from battle.rules import BATTLE_LENGTH

MAX_TURNS: int = 500                    # 무한 루프 방지 턴 한계
MAX_TIME: float = float(BATTLE_LENGTH)  # 최대 전투 시간 (타임오버)


class BattleEngine:
    """
    ATB/CTB 전투 엔진.
    ATB 기획(게이지 충전)을 CTB(heapq 행동 예약)로 동일하게 시뮬레이션.
    - TurnManager: heapq 기반 행동 순서 (행동 간격 = BATTLE_LENGTH / SPD)
    - SPManager: 공용 SP 관리
    - BuffManager: 버프 적용/틱
    - SkillExecutor: 스킬 효과 실행
    - TriggerSystem: 패시브 트리거
    """

    def __init__(
        self,
        ally_units: List[CharacterData],
        enemy_units: List[CharacterData],
        battle_type: str = "annihilation",   # 전멸전
        allow_active: bool = True,           # 액티브 스킬 허용 여부
        allow_ultimate: bool = True,         # 얼티밋 허용 여부
        ultimate_mode: str = "auto",         # 'auto', 'manual_ordered'
        ultimate_order: Optional[List[str]] = None,  # 지정 발동 순서 (ID)
        recorder: Optional["BattleRecorder"] = None,  # 시각화용 레코더
        seed: Optional[int] = None,                    # 랜덤 시드 (재현용)
    ):
        self.seed = seed

        # 유닛 초기화
        self.allies: List[BattleUnit] = [BattleUnit(d) for d in ally_units]
        self.enemies: List[BattleUnit] = [BattleUnit(d) for d in enemy_units]
        self.all_units: Dict[str, BattleUnit] = {
            u.id: u for u in self.allies + self.enemies
        }

        self.battle_type = battle_type
        self.allow_active = allow_active
        self.allow_ultimate = allow_ultimate
        self.ultimate_mode = ultimate_mode
        # 지정 순서 발동: 해당 ID 순서대로 얼티밋 시도
        self.ultimate_order: List[str] = ultimate_order or []
        self._ultimate_order_idx: int = 0

        # 시스템 초기화
        self.turn_manager = TurnManager()
        self.sp_manager = SPManager()
        self.buff_manager = BuffManager(self.turn_manager)
        self.executor = SkillExecutor()
        self.trigger_system = TriggerSystem(self.executor)

        # 레코더 (선택적)
        self.recorder = recorder

        # 로그
        self._log: List[str] = []
        self.turn_count: int = 0
        self.result: Optional[BattleResult] = None

    # ─── 메인 전투 루프 ───────────────────────────────────────────
    def run(self) -> BattleResult:
        """전투 실행. 종료 조건 만족 시 BattleResult 반환."""
        if self.seed is not None:
            random.seed(self.seed)

        self._log.append("=" * 60)
        self._log.append("⚔️  전투 시작!")
        self._log.append("=" * 60)

        # 유닛 큐 초기화
        self.turn_manager.initialize(list(self.all_units.values()))

        # 전투 시작 트리거
        ctx = self._make_ctx()
        self.trigger_system.evaluate_battle_start(list(self.all_units.values()), ctx)

        # 메인 루프
        while self.turn_count < MAX_TURNS:
            entry = self.turn_manager.pop_next()
            if entry is None:
                break

            unit = self.all_units.get(entry.unit_id)
            if unit is None or not unit.is_alive:
                continue

            self.turn_count += 1

            # 타임오버 체크
            if self.turn_manager.current_time > MAX_TIME:
                self._log.append(f"\n⏰ 타임오버 ({self.turn_manager.current_time:.2f})")
                self.result = BattleResult.TIME_OVER
                return BattleResult.TIME_OVER

            # ─── 배틀 라운드 전환 체크 ────────────────────────────
            if self.turn_manager.check_battle_round():
                round_num = self.turn_manager.battle_round
                self._log.append(f"\n{'─'*40}")
                self._log.append(f"🔔 배틀 라운드 {round_num} 시작! SP 초기화")
                self._log.append(f"{'─'*40}")
                self.sp_manager.reset()
                # 라운드 전환 시 얼티밋 사용 플래그 리셋
                for u in self.all_units.values():
                    u.used_ultimate_this_round = False
                # 라운드 전환 시 전원 행동큐 재계산 (현재 SPD 기준)
                alive_units = [u for u in self.all_units.values() if u.is_alive]
                self.turn_manager.recalculate_all(alive_units)
                ctx = self._make_ctx()
                self.trigger_system.evaluate_round_start(alive_units, ctx)

            # ─── 엑스트라 턴은 SP 충전 없음 ──────────────────────
            if not entry.is_extra:
                self.sp_manager.charge_on_turn_start()

            ctx = self._make_ctx()

            # ─── 턴 헤더 로그 ─────────────────────────────────────
            extra_label = " [Extra Turn]" if entry.is_extra else ""
            sp_ally = self.sp_manager.ally_sp
            sp_enemy = self.sp_manager.enemy_sp
            self._log.append(
                f"\n[T{self.turn_count}] t={self.turn_manager.current_time:.2f}{extra_label} "
                f"| {unit.name} ({unit.side}) "
                f"| HP {unit.current_hp:.0f}/{unit.max_hp:.0f} "
                f"| SP 아군:{sp_ally} 적:{sp_enemy}"
            )

            # ─── [RECORDER] 턴 시작 스냅샷 ───────────────────────
            if self.recorder:
                self.recorder.begin_turn(
                    self.turn_count, self.turn_manager.current_time,
                    self.turn_manager.battle_round, unit, entry.is_extra,
                    sp_ally, sp_enemy, self.all_units, len(self._log),
                )

            # ─── Hard CC 처리 ──────────────────────────────────────
            if unit.hard_cc:
                self._log.append(f"  ⛔ {unit.name} {unit.hard_cc.value}로 행동 불가")
                self.buff_manager.tick_turn_start(unit)  # 틱 효과 발동 (DoT 등)
                self._flush_buff_log()
                self.buff_manager.tick_turn_end(unit)    # 버프 지속시간 감소
                self._flush_buff_log()
                if not entry.is_extra:
                    self.turn_manager.reschedule_unit(unit)
                result = self._check_victory()
                if self.recorder:
                    self.recorder.set_skill("CC 행동불가", "cc_skip")
                    self.recorder.end_turn(self._log, result.value if result else None)
                if result:
                    return result
                continue

            # ─── Soft CC (확률적) ──────────────────────────────────
            if unit.soft_cc:
                if random.random() < 0.3:
                    self._log.append(f"  ⛔ {unit.name} {unit.soft_cc.value}로 행동 실패 (30%)")
                    self.buff_manager.tick_turn_start(unit)  # 틱 효과 발동 (DoT 등)
                    self._flush_buff_log()
                    self.buff_manager.tick_turn_end(unit)    # 버프 지속시간 감소
                    self._flush_buff_log()
                    if not entry.is_extra:
                        self.turn_manager.reschedule_unit(unit)
                    if self.recorder:
                        self.recorder.set_skill("CC 행동실패", "cc_skip")
                        self.recorder.end_turn(self._log, None)
                    continue

            # ─── 턴 시작 틱 (CharacterTurnStart: DoT 등) ──────────
            if not entry.is_extra:
                self.buff_manager.tick_turn_start(unit)
                self._flush_buff_log()

            # ─── 얼티밋 우선 체크 (끼어들기) ─────────────────────
            if not entry.is_extra:
                self._try_ultimate(unit, ctx)

            # ─── 스킬 결정 (엑스트라 턴: 얼티밋 실행) ───────────
            if entry.is_extra:
                skill = unit.data.ultimate_skill
                unit.use_ultimate_skill()   # 얼티밋 쿨타임 시작
                self._log.append(f"  💥 {unit.name} 얼티밋: {skill.name}")
            else:
                skill = self._decide_skill(unit)
                self._log.append(f"  🗡️  {unit.name} → {skill.name} ({skill.skill_type.value})")
                if skill.skill_type == SkillType.ACTIVE:
                    unit.use_active_skill()

            # ─── [RECORDER] 사용 스킬 기록 ───────────────────────
            if self.recorder:
                self.recorder.set_skill(skill.name, skill.skill_type.value)

            # ─── 스킬 실행 ────────────────────────────────────────
            killed = self.executor.execute(unit, skill, ctx)
            self._flush_buff_log()

            # ─── 킬 트리거 ────────────────────────────────────────
            for dead in killed:
                self.turn_manager.remove_unit(dead.id)
                self.trigger_system.evaluate_on_kill(unit, dead, ctx)
                if self.recorder:
                    self.recorder.add_event('death', dead.id, dead.id, 0, f'{dead.name} 사망')

            # ─── 턴 종료 버프 틱 ──────────────────────────────────
            # Extra Turn은 턴 종료 처리 없음 (쿨타임 감소 없음)
            if not entry.is_extra:
                self.buff_manager.tick_turn_end(unit)
                self._flush_buff_log()

                # 턴 종료 트리거
                self.trigger_system.evaluate(TriggerEvent.ON_TURN_END, unit, ctx)

                # 일반 턴만 재스케줄
                self.turn_manager.reschedule_unit(unit)

            # ─── 승리/패배 판정 ───────────────────────────────────
            result = self._check_victory()
            if self.recorder:
                self.recorder.end_turn(self._log, result.value if result else None)
            if result:
                return result

        # 턴 한계 초과
        self._log.append(f"\n⏰ 최대 턴({MAX_TURNS}) 초과 → 타임오버")
        self.result = BattleResult.TIME_OVER
        return BattleResult.TIME_OVER

    # ─── 얼티밋 시도 ──────────────────────────────────────────────
    def _try_ultimate(self, unit: BattleUnit, ctx: EngineContext):
        """
        SP가 충분하고, 이번 라운드 얼티밋 미사용 시 엑스트라 턴 등록.
        ultimate_mode:
          - 'auto': SP 충족 즉시 발동
          - 'manual_ordered': 지정 순서(ultimate_order)에 따라 발동
        """
        if not self.allow_ultimate:
            return
        if not unit.can_use_ultimate():
            return

        ult = unit.data.ultimate_skill
        if not self.sp_manager.can_spend(unit.side, ult.sp_cost):
            return

        should_use = False
        if self.ultimate_mode == "auto":
            should_use = True
        elif self.ultimate_mode == "manual_ordered":
            # 지정 순서 중 현재 해당 유닛 차례인지 확인
            if self.ultimate_order:
                target_id = self.ultimate_order[self._ultimate_order_idx % len(self.ultimate_order)]
                if unit.id == target_id:
                    should_use = True

        if should_use:
            if self.sp_manager.spend(unit.side, ult.sp_cost):
                unit.used_ultimate_this_round = True
                if self.ultimate_mode == "manual_ordered":
                    self._ultimate_order_idx += 1
                added = self.turn_manager.add_extra_turn(unit)
                if added:
                    self._log.append(
                        f"  ✨ {unit.name} 얼티밋 예약! SP -{ult.sp_cost} "
                        f"(남은 {self.sp_manager.get_sp(unit.side)})"
                    )

    # ─── 스킬 결정 ────────────────────────────────────────────────
    def _decide_skill(self, unit: BattleUnit):
        """Active 우선, 쿨타임 있으면 Normal. allow_active=False면 항상 Normal."""
        if self.allow_active and unit.can_use_active():
            return unit.data.active_skill
        return unit.data.normal_skill

    # ─── 승리/패배 판정 ───────────────────────────────────────────
    def _check_victory(self) -> Optional[BattleResult]:
        alive_allies = [u for u in self.allies if u.is_alive]
        alive_enemies = [u for u in self.enemies if u.is_alive]

        if not alive_enemies:
            t = self.turn_manager.current_time
            self._log.append(f"\n🏆 아군 승리! (타임라인: {t:.3f})")
            self.result = BattleResult.ALLY_WIN
            return BattleResult.ALLY_WIN
        if not alive_allies:
            t = self.turn_manager.current_time
            self._log.append(f"\n💀 아군 전멸 패배 (타임라인: {t:.3f})")
            self.result = BattleResult.ENEMY_WIN
            return BattleResult.ENEMY_WIN
        return None

    # ─── 컨텍스트 생성 ────────────────────────────────────────────
    def _make_ctx(self) -> EngineContext:
        return EngineContext(
            all_units=self.all_units,
            allies=self.allies,
            enemies=self.enemies,
            buff_manager=self.buff_manager,
            sp_manager=self.sp_manager,
            turn_manager=self.turn_manager,
            log=self._log,
            trigger_system=self.trigger_system,
        )

    # ─── 버프 로그 플러시 ─────────────────────────────────────────
    def _flush_buff_log(self):
        for line in self.buff_manager.flush_log():
            self._log.append(line)
        for line in self.trigger_system.flush_log():
            self._log.append(line)

    # ─── 로그 출력 ────────────────────────────────────────────────
    def print_log(self):
        print("\n".join(self._log))

    def get_log(self) -> List[str]:
        return self._log[:]

    # ─── 최종 상태 요약 ───────────────────────────────────────────
    def print_summary(self):
        print("\n" + "=" * 60)
        print("📊 전투 결과 요약")
        print("=" * 60)
        print(f"결과: {self.result.value if self.result else 'IN_PROGRESS'}")
        print(f"소요 턴: {self.turn_count}")
        print(f"소요 시간: {self.turn_manager.current_time:.3f}")
        print(f"배틀 라운드: {self.turn_manager.battle_round}")
        print("\n아군 생존:")
        for u in self.allies:
            status = f"HP {u.current_hp:.0f}/{u.max_hp:.0f}" if u.is_alive else "💀 사망"
            print(f"  {u.name}: {status}")
        print("\n적군 생존:")
        for u in self.enemies:
            status = f"HP {u.current_hp:.0f}/{u.max_hp:.0f}" if u.is_alive else "💀 사망"
            print(f"  {u.name}: {status}")
