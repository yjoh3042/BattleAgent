"""타이밍 기능 이전 상태로 파일 되돌리기 (초기 커밋용) + 백업 저장"""
import os, json, tempfile

ROOT = r"C:\Ai\BattleAgent"

files = [
    r"src\battle\models.py",
    r"src\battle\battle_unit.py",
    r"src\battle\buff_manager.py",
    r"src\battle\battle_engine.py",
    r"src\fixtures\test_data.py",
    r"tests\test_buff_manager.py",
]

# 현재(타이밍 적용) 버전 백업
backups = {}
for f in files:
    with open(os.path.join(ROOT, f), encoding="utf-8") as fh:
        backups[f] = fh.read()

tmp = os.path.join(tempfile.gettempdir(), "battle_timing_backup.json")
with open(tmp, "w", encoding="utf-8") as fh:
    json.dump(backups, fh, ensure_ascii=False)
print(f"타이밍 백업 저장: {tmp}")

# ── models.py ────────────────────────────────────────────────
c = backups[r"src\battle\models.py"]
c = c.replace(
    '    buff_turn_reduce_timing: str = "CharacterTurnEnd"  '
    '# "CharacterTurnStart"(틱 계열) | "CharacterTurnEnd"(스탯/CC 계열)\n',
    ""
)
with open(os.path.join(ROOT, r"src\battle\models.py"), "w", encoding="utf-8") as fh:
    fh.write(c)

# ── battle_unit.py ───────────────────────────────────────────
c = backups[r"src\battle\battle_unit.py"]
OLD_BU = (
    "    # ─── 턴 처리 ──────────────────────────────────────────────────\n"
    "    def on_turn_start_tick(self) -> List[dict]:\n"
    "        \"\"\"\n"
    "        턴 시작 시 처리 (CharacterTurnStart 버프):\n"
    "        - DoT/HoT 등 틱 발동 후 해당 버프의 remaining_turns -1\n"
    "        반환: 만료된 버프 목록\n"
    "        \"\"\"\n"
    "        expired = []\n"
    "        new_buffs = []\n"
    "        for ab in self.active_buffs:\n"
    "            if ab.buff_data.buff_turn_reduce_timing == \"CharacterTurnStart\":\n"
    "                ab.remaining_turns -= 1\n"
    "                if ab.remaining_turns <= 0:\n"
    "                    expired.append({'buff': ab, 'stat': ab.buff_data.stat})\n"
    "                else:\n"
    "                    new_buffs.append(ab)\n"
    "            else:\n"
    "                new_buffs.append(ab)\n"
    "        self.active_buffs = new_buffs\n"
    "        return expired\n"
    "\n"
    "    def on_turn_end(self) -> List[dict]:\n"
    "        \"\"\"\n"
    "        턴 종료 시 처리 (CharacterTurnEnd 버프):\n"
    "        1. CharacterTurnEnd 버프 remaining_turns -1 (만료 제거)\n"
    "        2. CC 틱\n"
    "        3. 쿨타임 틱\n"
    "        4. 도발 틱\n"
    "        반환: 만료된 버프 목록 (SPD 변화 감지용)\n"
    "        \"\"\"\n"
    "        expired = []\n"
    "        new_buffs = []\n"
    "        for ab in self.active_buffs:\n"
    "            if ab.buff_data.buff_turn_reduce_timing == \"CharacterTurnEnd\":\n"
    "                ab.remaining_turns -= 1\n"
    "                if ab.remaining_turns <= 0:\n"
    "                    expired.append({'buff': ab, 'stat': ab.buff_data.stat})\n"
    "                else:\n"
    "                    new_buffs.append(ab)\n"
    "            else:\n"
    "                new_buffs.append(ab)\n"
    "        self.active_buffs = new_buffs\n"
    "\n"
    "        self.tick_cc()\n"
    "        self.tick_cooldown()\n"
    "        self.tick_taunt()\n"
    "\n"
    "        return expired"
)
NEW_BU = (
    "    # ─── 턴 종료 처리 ─────────────────────────────────────────────\n"
    "    def on_turn_end(self) -> List[dict]:\n"
    "        \"\"\"\n"
    "        턴 종료 시 처리:\n"
    "        1. 버프 남은 턴 -1 (만료 제거)\n"
    "        2. CC 틱\n"
    "        3. 쿨타임 틱\n"
    "        4. 도발 틱\n"
    "        반환: 만료된 버프 목록 (SPD 변화 감지용)\n"
    "        \"\"\"\n"
    "        expired = []\n"
    "        new_buffs = []\n"
    "        for ab in self.active_buffs:\n"
    "            ab.remaining_turns -= 1\n"
    "            if ab.remaining_turns <= 0:\n"
    "                expired.append({'buff': ab, 'stat': ab.buff_data.stat})\n"
    "            else:\n"
    "                new_buffs.append(ab)\n"
    "        self.active_buffs = new_buffs\n"
    "\n"
    "        self.tick_cc()\n"
    "        self.tick_cooldown()\n"
    "        self.tick_taunt()\n"
    "\n"
    "        return expired"
)
assert OLD_BU in c, "battle_unit 치환 실패 - 소스 불일치"
c = c.replace(OLD_BU, NEW_BU)
with open(os.path.join(ROOT, r"src\battle\battle_unit.py"), "w", encoding="utf-8") as fh:
    fh.write(c)

# ── buff_manager.py ──────────────────────────────────────────
c = backups[r"src\battle\buff_manager.py"]
OLD_BM = (
    "    # ─── 버프 틱 (턴 시작: CharacterTurnStart) ───────────────────\n"
    "    def tick_turn_start(self, unit: BattleUnit):\n"
    "        \"\"\"\n"
    "        턴 시작 시 (CharacterTurnStart 버프):\n"
    "        1. DoT/HoT 틱 효과 발동 (버프가 살아있을 때 먼저)\n"
    "        2. CharacterTurnStart 버프 remaining_turns -1, 만료 처리\n"
    "        \"\"\"\n"
    "        self._apply_dots(unit)\n"
    "        old_spd = unit.spd\n"
    "        expired = unit.on_turn_start_tick()\n"
    "        self._handle_expired(unit, expired, old_spd, timing_label=\"턴시작\")\n"
    "\n"
    "    # ─── 버프 틱 (턴 종료: CharacterTurnEnd) ─────────────────────\n"
    "    def tick_turn_end(self, unit: BattleUnit):\n"
    "        \"\"\"\n"
    "        턴 종료 시 (CharacterTurnEnd 버프):\n"
    "        1. CharacterTurnEnd 버프 remaining_turns -1, 만료 처리\n"
    "        2. CC / 쿨타임 / 도발 틱\n"
    "        \"\"\"\n"
    "        old_spd = unit.spd\n"
    "        expired = unit.on_turn_end()\n"
    "        self._handle_expired(unit, expired, old_spd, timing_label=\"턴종료\")\n"
    "\n"
    "    def _handle_expired(self, unit: BattleUnit, expired: list, old_spd: float, timing_label: str = \"\"):\n"
    "        \"\"\"만료 버프 공통 후처리: SPD 재계산 + DoT 태그 정리\"\"\"\n"
    "        spd_expired = any(e.get('stat') == 'spd' for e in expired)\n"
    "        if spd_expired and self._turn_manager:\n"
    "            new_spd = unit.spd\n"
    "            if abs(new_spd - old_spd) > 0.001:\n"
    "                self._turn_manager.on_spd_change(unit, old_spd)\n"
    "                self._log.append(f\"  → {unit.name} SPD 버프 만료({timing_label}): {old_spd:.0f} → {new_spd:.0f}\")\n"
    "\n"
    "        for e in expired:\n"
    "            buff = e.get('buff')\n"
    "            if buff and buff.buff_data.logic_type == LogicType.DOT and buff.buff_data.dot_type == \"burn\":\n"
    "                for _ in range(buff.stack_count):\n"
    "                    unit.remove_tag(\"burn\")\n"
    "                self._log.append(f\"  → {unit.name} 화상 만료 (스택 {buff.stack_count})\")"
)
NEW_BM = (
    "    # ─── 버프 틱 (턴 종료 시) ─────────────────────────────────────\n"
    "    def tick_all_buffs(self, unit: BattleUnit):\n"
    "        \"\"\"\n"
    "        턴 종료 시:\n"
    "        1. DoT 피해/회복 발동\n"
    "        2. 버프 남은 턴 -1, 만료 제거\n"
    "        3. SPD 버프 만료 시 TurnManager 재계산\n"
    "        \"\"\"\n"
    "        # DoT 먼저 발동 (버프가 아직 살아있을 때)\n"
    "        self._apply_dots(unit)\n"
    "\n"
    "        # 버프 틱 (BattleUnit.on_turn_end 호출)\n"
    "        old_spd = unit.spd\n"
    "        expired = unit.on_turn_end()\n"
    "\n"
    "        # 만료된 SPD 버프가 있으면 TurnManager 재계산\n"
    "        spd_expired = any(e.get('stat') == 'spd' for e in expired)\n"
    "        if spd_expired and self._turn_manager:\n"
    "            new_spd = unit.spd\n"
    "            if abs(new_spd - old_spd) > 0.001:\n"
    "                self._turn_manager.on_spd_change(unit, old_spd)\n"
    "                self._log.append(f\"  → {unit.name} SPD 버프 만료: {old_spd:.0f} → {new_spd:.0f}\")\n"
    "\n"
    "        # 화상 DoT 버프 만료 시 태그 정리\n"
    "        for e in expired:\n"
    "            buff = e.get('buff')\n"
    "            if buff and buff.buff_data.logic_type == LogicType.DOT and buff.buff_data.dot_type == \"burn\":\n"
    "                # 스택 수만큼 태그 제거\n"
    "                for _ in range(buff.stack_count):\n"
    "                    unit.remove_tag(\"burn\")\n"
    "                self._log.append(f\"  → {unit.name} 화상 만료 (스택 {buff.stack_count})\")"
)
assert OLD_BM in c, "buff_manager 치환 실패 - 소스 불일치"
c = c.replace(OLD_BM, NEW_BM)
with open(os.path.join(ROOT, r"src\battle\buff_manager.py"), "w", encoding="utf-8") as fh:
    fh.write(c)

# ── battle_engine.py ─────────────────────────────────────────
c = backups[r"src\battle\battle_engine.py"]
# Hard CC
c = c.replace(
    "                self.buff_manager.tick_turn_start(unit)  # 틱 효과 발동 (DoT 등)\n"
    "                self._flush_buff_log()\n"
    "                self.buff_manager.tick_turn_end(unit)    # 버프 지속시간 감소\n"
    "                self._flush_buff_log()",
    "                self.buff_manager.tick_all_buffs(unit)\n"
    "                self._flush_buff_log()"
)
# Soft CC
c = c.replace(
    "                    self.buff_manager.tick_turn_start(unit)  # 틱 효과 발동 (DoT 등)\n"
    "                    self._flush_buff_log()\n"
    "                    self.buff_manager.tick_turn_end(unit)    # 버프 지속시간 감소\n"
    "                    self._flush_buff_log()",
    "                    self.buff_manager.tick_all_buffs(unit)\n"
    "                    self._flush_buff_log()"
)
# 턴 시작 블록 제거
c = c.replace(
    "            # ─── 턴 시작 틱 (CharacterTurnStart: DoT 등) ──────────\n"
    "            if not entry.is_extra:\n"
    "                self.buff_manager.tick_turn_start(unit)\n"
    "                self._flush_buff_log()\n"
    "\n"
    "            # ─── 얼티밋 우선 체크 (끼어들기) ─────────────────────",
    "            # ─── 얼티밋 우선 체크 (끼어들기) ─────────────────────"
)
# 턴 종료
c = c.replace(
    "            # ─── 턴 종료 버프 틱 ──────────────────────────────────\n"
    "            # Extra Turn은 턴 종료 처리 없음 (쿨타임 감소 없음)\n"
    "            if not entry.is_extra:\n"
    "                self.buff_manager.tick_turn_end(unit)",
    "            # ─── 턴 종료 버프 틱 ──────────────────────────────────\n"
    "            # Extra Turn은 턴 종료 처리 없음 (DoT 틱, 쿨타임 감소 없음)\n"
    "            if not entry.is_extra:\n"
    "                self.buff_manager.tick_all_buffs(unit)"
)
with open(os.path.join(ROOT, r"src\battle\battle_engine.py"), "w", encoding="utf-8") as fh:
    fh.write(c)

# ── test_data.py ─────────────────────────────────────────────
c = backups[r"src\fixtures\test_data.py"]
c = c.replace(
    "        buff_turn_reduce_timing=\"CharacterTurnStart\",  # 틱 발동 후 턴 시작에 감소\n",
    ""
)
with open(os.path.join(ROOT, r"src\fixtures\test_data.py"), "w", encoding="utf-8") as fh:
    fh.write(c)

# ── test_buff_manager.py ─────────────────────────────────────
c = backups[r"tests\test_buff_manager.py"]
OLD_TB = (
    "class TestDotTick:\n"
    "    def test_dot_deals_damage(self, make_simple_unit):\n"
    "        \"\"\"DoT 턴 시작 시 피해 발동 (CharacterTurnStart)\"\"\"\n"
    "        u = make_simple_unit(name=\"피격자\", hp=5000)\n"
    "        bm = BuffManager()\n"
    "        burn = BuffData(\n"
    "            id=\"burn_dot\", name=\"화상\",\n"
    "            source_skill_id=\"fire_skill\", logic_type=LogicType.DOT,\n"
    "            dot_type=\"burn\", value=0.05, duration=2,\n"
    "            is_debuff=True, max_stacks=5,\n"
    "            buff_turn_reduce_timing=\"CharacterTurnStart\",\n"
    "        )\n"
    "        bm.apply_buff(u, burn, \"attacker\")\n"
    "        hp_before = u.current_hp\n"
    "        bm.tick_turn_start(u)   # 턴 시작: DoT 발동\n"
    "        assert u.current_hp < hp_before  # DoT 피해 발생"
)
NEW_TB = (
    "class TestDotTick:\n"
    "    def test_dot_deals_damage(self, make_simple_unit):\n"
    "        \"\"\"DoT 턴 종료 시 피해 발동\"\"\"\n"
    "        u = make_simple_unit(name=\"피격자\", hp=5000)\n"
    "        bm = BuffManager()\n"
    "        burn = BuffData(\n"
    "            id=\"burn_dot\", name=\"화상\",\n"
    "            source_skill_id=\"fire_skill\", logic_type=LogicType.DOT,\n"
    "            dot_type=\"burn\", value=0.05, duration=2,\n"
    "            is_debuff=True, max_stacks=5,\n"
    "        )\n"
    "        bm.apply_buff(u, burn, \"attacker\")\n"
    "        hp_before = u.current_hp\n"
    "        bm.tick_all_buffs(u)\n"
    "        assert u.current_hp < hp_before  # DoT 피해 발생"
)
c = c.replace(OLD_TB, NEW_TB)
with open(os.path.join(ROOT, r"tests\test_buff_manager.py"), "w", encoding="utf-8") as fh:
    fh.write(c)

print("✅ pre-timing 복원 완료")
