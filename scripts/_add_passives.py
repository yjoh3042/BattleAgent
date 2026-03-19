"""test_data.py에 모든 캐릭터의 패시브 스킬을 자동 추가하는 스크립트."""
import re, sys
sys.stdout.reconfigure(encoding='utf-8')

filepath = r"src\fixtures\test_data.py"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

# ═══════════════════════════════════════════
# Step 1: _passive() 빌더 함수 추가
# ═══════════════════════════════════════════
passive_builder = """

def _passive(sid: str, name: str, effects: list) -> SkillData:
    \"\"\"패시브 스킬 (트리거 또는 전투 시작 시 자동 발동).\"\"\"
    return SkillData(id=sid, name=name, skill_type=SkillType.PASSIVE,
                     effects=effects, cooldown_turns=0)

"""

ult_marker = "                     effects=effects, sp_cost=sp)\n"
if '_passive' not in content:
    idx = content.find(ult_marker)
    if idx >= 0:
        end = idx + len(ult_marker)
        content = content[:end] + passive_builder + content[end:]
        print("✅ _passive() 빌더 추가 완료")
else:
    print("⏭️  _passive() 빌더 이미 존재")

# ═══════════════════════════════════════════
# Step 2: 캐릭터별 패시브 정의
# ═══════════════════════════════════════════
# (passive_name, effects_code, trigger_event, once_per_battle)
P = {}

# ═══ 화속성 ═══
P["c283"] = ("잔화의 추격",
    '[_dmg(TargetType.ENEMY_NEAR, 1.50), _dot_eff(TargetType.ENEMY_NEAR, _burn(f"{sid}_p", 0.10, 2))]',
    "ON_KILL", True)
P["c339"] = ("화상 확산",
    '[_dot_eff(TargetType.ALL_ENEMY, _burn(f"{sid}_p", 0.10, 2))]',
    "ON_KILL", True)
P["c417"] = ("원혼의 울음",
    '[_dmg(TargetType.ENEMY_NEAR, 1.50), _cc(CCType.PANIC, 1, f"{sid}_p", TargetType.ENEMY_NEAR)]',
    "ON_KILL", True)
P["c429"] = ("생명의 씨앗",
    '[_heal_ratio(TargetType.ALL_ALLY, 0.10), _hot_eff(TargetType.ALL_ALLY, _hot(f"{sid}_p", 0.03, 2))]',
    "ON_BATTLE_START", True)
P["c445"] = ("화염 추격자",
    '[_dmg(TargetType.ENEMY_NEAR, 2.00, burn_bonus=0.20)]',
    "ON_KILL", False)
P["c462"] = ("불꽃 반격",
    '[_dmg(TargetType.ENEMY_NEAR, 1.50), _dot_eff(TargetType.ENEMY_NEAR, _burn(f"{sid}_p", 0.10, 2))]',
    "ON_HIT", True)
P["c501"] = ("화신의 분노",
    '[_dmg(TargetType.ENEMY_NEAR, 2.50, burn_bonus=0.15)]',
    "ON_KILL", False)
P["c562"] = ("저주의 연장",
    '[_debuff_turn_inc(TargetType.ALL_ENEMY, 1), _stat_eff(TargetType.ALL_ALLY, _sb("atk", 0.10, 2, f"{sid}_p", "패시브 공격", is_ratio=True))]',
    "ON_BATTLE_START", True)
P["c354"] = ("화상 촉매",
    '[_dot_eff(TargetType.ENEMY_NEAR, _burn(f"{sid}_p", 0.10, 2)), _stat_eff(TargetType.ENEMY_NEAR, _sb("spd", 0.10, 2, f"{sid}_p", "패시브 감속", is_debuff=True, is_ratio=True))]',
    "ON_HIT", True)
P["c412"] = ("광기의 불꽃",
    '[_dmg(TargetType.ENEMY_NEAR, 2.00), _dot_eff(TargetType.ENEMY_NEAR, _burn(f"{sid}_p", 0.10, 2))]',
    "ON_KILL", True)
P["c003"] = ("화염 증폭",
    '[_dot_eff(TargetType.ENEMY_NEAR, _burn(f"{sid}_p", 0.10, 2))]',
    "ON_BATTLE_START", True)
P["c037"] = ("방화벽",
    '[_shield(TargetType.SELF, 0.10)]',
    "ON_BATTLE_START", True)
P["c083"] = ("화염 일격",
    '[_dmg(TargetType.ENEMY_NEAR, 1.50)]',
    "ON_KILL", True)
P["c286"] = ("잔불의 온기",
    '[_heal_ratio(TargetType.ALLY_LOWEST_HP, 0.15)]',
    "ON_BATTLE_START", True)

# ═══ 수속성 ═══
P["c124"] = ("처형자의 본능",
    '[_dmg(TargetType.ENEMY_LOWEST_HP, 2.00)]',
    "ON_KILL", False)
P["c167"] = ("수류 보복",
    '[_stat_eff(TargetType.ALL_ENEMY, _sb("spd", 10.0, 2, f"{sid}_p", "패시브 감속", is_debuff=True, is_ratio=False)), _sp_steal(TargetType.ENEMY_HIGHEST_SPD, 1)]',
    "ON_HIT", True)
P["c281"] = ("가속의 축복",
    '[_stat_eff(TargetType.ALL_ALLY, _sb("spd", 10.0, 2, f"{sid}_p", "패시브 속도", is_ratio=False))]',
    "ON_BATTLE_START", True)
P["c318"] = ("빙결의 기운",
    '[_cc(CCType.FREEZE, 1, f"{sid}_p", TargetType.ENEMY_NEAR), _stat_eff(TargetType.ENEMY_NEAR, _sb("spd", 0.10, 2, f"{sid}_p", "패시브 감속", is_debuff=True, is_ratio=True))]',
    "ON_BATTLE_START", True)
P["c502"] = ("급습의 한기",
    '[_dmg(TargetType.ENEMY_NEAR, 1.50), _cc(CCType.STUN, 1, f"{sid}_p", TargetType.ENEMY_NEAR)]',
    "ON_KILL", True)
P["c537"] = ("성수의 반격",
    '[_dmg(TargetType.ENEMY_NEAR, 1.50), _stat_eff(TargetType.SELF, _sb("def_", 0.10, 2, f"{sid}_p", "패시브 방어", is_ratio=True))]',
    "ON_HIT", True)
P["c442"] = ("심연의 추격",
    '[_dmg(TargetType.ENEMY_NEAR, 2.50)]',
    "ON_KILL", False)
P["c464"] = ("장풍 추격",
    '[_dmg(TargetType.ENEMY_NEAR, 2.00)]',
    "ON_KILL", True)
P["c022"] = ("빙결 카운터",
    '[_cc(CCType.FREEZE, 1, f"{sid}_p", TargetType.ENEMY_NEAR)]',
    "ON_HIT", True)
P["c437"] = ("바람의 가호",
    '[_heal_ratio(TargetType.ALLY_LOWEST_HP, 0.15), _stat_eff(TargetType.ALLY_LOWEST_HP, _sb("def_", 0.10, 2, f"{sid}_p", "패시브 방어", is_ratio=True))]',
    "ON_BATTLE_START", True)
P["c002"] = ("수정의 일격",
    '[_dmg(TargetType.ENEMY_NEAR, 1.50)]',
    "ON_KILL", True)
P["c193"] = ("집중의 일섬",
    '[_stat_eff(TargetType.SELF, _sb("atk", 0.15, 2, f"{sid}_p", "패시브 공격", is_ratio=True))]',
    "ON_KILL", True)
P["c362"] = ("수류의 힘",
    '[_stat_eff(TargetType.ALL_ALLY, _sb("def_", 0.10, 2, f"{sid}_p", "패시브 방어", is_ratio=True))]',
    "ON_BATTLE_START", True)
P["c366"] = ("해류 장벽",
    '[_shield(TargetType.SELF, 0.10)]',
    "ON_BATTLE_START", True)

# ═══ 목속성 ═══
P["c229"] = ("정보원의 선물",
    '[_hot_eff(TargetType.ALL_ALLY, _hot(f"{sid}_p", 0.03, 2)), _stat_eff(TargetType.ALL_ALLY, _sb("spd", 10.0, 2, f"{sid}_p", "패시브 속도", is_ratio=False))]',
    "ON_BATTLE_START", True)
P["c336"] = ("독의 추격",
    '[_dmg(TargetType.ENEMY_NEAR, 1.50), _dot_eff(TargetType.ENEMY_NEAR, _poison(f"{sid}_p", 0.10, 2))]',
    "ON_KILL", True)
P["c447"] = ("분노의 씨앗",
    '[_stat_eff(TargetType.SELF, _sb("atk", 0.20, 2, f"{sid}_p", "패시브 공격", is_ratio=True))]',
    "ON_BATTLE_START", True)
P["c461"] = ("숲의 각성",
    '[_stat_eff(TargetType.ALL_ALLY, _sb("atk", 0.10, 2, f"{sid}_p", "패시브 공격", is_ratio=True)), _hot_eff(TargetType.ALL_ALLY, _hot(f"{sid}_p", 0.03, 2))]',
    "ON_BATTLE_START", True)
P["c468"] = ("지혜의 가시",
    '[_dmg(TargetType.ENEMY_NEAR, 1.00), _stat_eff(TargetType.SELF, _sb("def_", 0.15, 2, f"{sid}_p", "패시브 방어", is_ratio=True))]',
    "ON_HIT", True)
P["c525"] = ("악마의 축복",
    '[_stat_eff(TargetType.ALL_ALLY, _sb("cri_ratio", 0.15, 2, f"{sid}_p", "패시브 크리", is_ratio=False)), _stat_eff(TargetType.ALL_ALLY, _sb("atk", 0.10, 2, f"{sid}_p", "패시브 공격", is_ratio=True))]',
    "ON_BATTLE_START", False)
P["c549"] = ("대지의 추격",
    '[_dmg(TargetType.ENEMY_NEAR, 2.00), _dot_eff(TargetType.ENEMY_NEAR, _poison(f"{sid}_p", 0.10, 2))]',
    "ON_KILL", True)
P["c601"] = ("심연의 추격",
    '[_dmg(TargetType.ENEMY_NEAR, 2.00), _dot_eff(TargetType.ENEMY_NEAR, _poison(f"{sid}_p", 0.15, 2))]',
    "ON_KILL", True)
P["c180"] = ("대지의 반격",
    '[_dmg(TargetType.ENEMY_NEAR, 1.50), _dot_eff(TargetType.ENEMY_NEAR, _poison(f"{sid}_p", 0.10, 2))]',
    "ON_HIT", True)
P["c132"] = ("황금의 추격",
    '[_dmg(TargetType.ENEMY_NEAR, 1.50), _stat_eff(TargetType.ENEMY_NEAR, _sb("def_", 0.10, 2, f"{sid}_p", "패시브 방깎", is_debuff=True, is_ratio=True))]',
    "ON_KILL", True)
P["c398"] = ("숲의 선물",
    '[_stat_eff(TargetType.ALL_ALLY, _sb("atk", 0.10, 2, f"{sid}_p", "패시브 공격", is_ratio=True)), _barrier_ratio(TargetType.ALL_ALLY, 0.05)]',
    "ON_BATTLE_START", True)
P["c031"] = ("자연의 치유",
    '[_heal_ratio(TargetType.ALLY_LOWEST_HP, 0.15)]',
    "ON_BATTLE_START", True)
P["c033"] = ("달빛 저주",
    '[_cc(CCType.SLEEP, 1, f"{sid}_p", TargetType.ENEMY_NEAR)]',
    "ON_HIT", True)
P["c062"] = ("넝쿨의 추격",
    '[_dmg(TargetType.ENEMY_NEAR, 1.50), _dot_eff(TargetType.ENEMY_NEAR, _poison(f"{sid}_p", 0.10, 2))]',
    "ON_KILL", True)

# ═══ 광속성 ═══
P["c194"] = ("가시의 추격",
    '[_dmg(TargetType.ENEMY_NEAR, 2.00), _barrier_ratio(TargetType.SELF, 0.05)]',
    "ON_KILL", False)
P["c364"] = ("사탕의 보호",
    '[_buff_turn_inc(TargetType.ALL_ALLY, 1)]',
    "ON_HIT", True)
P["c393"] = ("달빛 보호막",
    '[_barrier_ratio(TargetType.ALL_ALLY, 0.05), _heal_ratio(TargetType.ALLY_LOWEST_HP, 0.10)]',
    "ON_BATTLE_START", True)
P["c438"] = ("신성 보호",
    '[_barrier_ratio(TargetType.SELF, 0.08), _debuff_immune(TargetType.SELF, 1)]',
    "ON_HIT", True)
P["c455"] = ("전쟁신의 가호",
    '[_heal_ratio(TargetType.ALLY_LOWEST_HP, 0.15), _remove_debuff_eff(TargetType.ALLY_LOWEST_HP)]',
    "ON_BATTLE_START", True)
P["c473"] = ("요정의 보호",
    '[_stat_eff(TargetType.ALL_ALLY, _sb("def_", 0.10, 2, f"{sid}_p", "패시브 방어", is_ratio=True)), _debuff_immune(TargetType.SELF, 1)]',
    "ON_BATTLE_START", True)
P["c533"] = ("꿈의 잔향",
    '[_dmg(TargetType.ENEMY_NEAR, 1.50), _cc(CCType.SLEEP, 1, f"{sid}_p", TargetType.ENEMY_NEAR)]',
    "ON_KILL", True)
P["c600"] = ("성광의 반격",
    '[_heal_ratio(TargetType.ALL_ALLY, 0.08), _buff_turn_inc(TargetType.ALL_ALLY, 1)]',
    "ON_HIT", True)
P["c353"] = ("빛의 장벽",
    '[_barrier_ratio(TargetType.ALL_ALLY, 0.08)]',
    "ON_BATTLE_START", False)
P["c183"] = ("빛의 치유",
    '[_heal_ratio(TargetType.ALLY_LOWEST_HP, 0.15)]',
    "ON_BATTLE_START", True)
P["c296"] = ("발키리의 추격",
    '[_dmg(TargetType.ENEMY_NEAR, 2.00), _barrier_ratio(TargetType.SELF, 0.05)]',
    "ON_KILL", True)
P["c028"] = ("성광의 선물",
    '[_stat_eff(TargetType.ALL_ALLY, _sb("atk", 0.10, 2, f"{sid}_p", "패시브 공격", is_ratio=True))]',
    "ON_BATTLE_START", True)
P["c221"] = ("광폭의 추격",
    '[_dmg(TargetType.ENEMY_NEAR, 1.50), _barrier_ratio(TargetType.SELF, 0.05)]',
    "ON_KILL", True)
P["c227"] = ("정의의 카운터",
    '[_dmg(TargetType.ENEMY_NEAR, 1.50), _debuff_immune(TargetType.SELF, 1)]',
    "ON_HIT", True)

# ═══ 암속성 ═══
P["c486"] = ("질주의 추격",
    '[_dmg(TargetType.ENEMY_NEAR, 2.00), _remove_buff_eff(TargetType.ENEMY_NEAR)]',
    "ON_KILL", False)
P["c432"] = ("침식의 추격",
    '[_dmg(TargetType.ENEMY_NEAR, 1.50), _stat_eff(TargetType.ENEMY_NEAR, _sb("def_", 0.10, 2, f"{sid}_p", "패시브 방깎", is_debuff=True, is_ratio=True))]',
    "ON_KILL", True)
P["c532"] = ("사자의 추격",
    '[_dmg_cri(TargetType.ENEMY_LOWEST_HP, 2.00)]',
    "ON_KILL", False)
P["c051"] = ("사신의 카운터",
    '[_dmg_pen(TargetType.ENEMY_NEAR, 1.50)]',
    "ON_HIT", True)
P["c400"] = ("절규의 메아리",
    '[_dmg(TargetType.ENEMY_NEAR, 1.50, hit_count=2)]',
    "ON_KILL", True)
P["c448"] = ("흡혈의 본능",
    '[_heal_ratio(TargetType.ALLY_LOWEST_HP, 0.15), _dot_eff(TargetType.ENEMY_NEAR, _bleed(f"{sid}_p", 0.10, 2))]',
    "ON_BATTLE_START", True)
P["c485"] = ("어둠의 침식",
    '[_stat_eff(TargetType.ALL_ENEMY, _sb("spd", 10.0, 2, f"{sid}_p", "패시브 감속", is_debuff=True, is_ratio=False)), _dot_eff(TargetType.ENEMY_NEAR, _bleed(f"{sid}_p", 0.08, 2))]',
    "ON_BATTLE_START", True)
P["c156"] = ("피의 추격",
    '[_dmg_cri(TargetType.ENEMY_NEAR, 2.00)]',
    "ON_KILL", False)
P["c294"] = ("혈맹의 추격",
    '[_dmg(TargetType.ENEMY_NEAR, 1.50), _remove_buff_eff(TargetType.ENEMY_NEAR)]',
    "ON_KILL", True)
P["c514"] = ("그림자 추격",
    '[_dmg(TargetType.ENEMY_NEAR, 1.50)]',
    "ON_KILL", True)
P["c001"] = ("암흑 방벽",
    '[_shield(TargetType.SELF, 0.10), _stat_eff(TargetType.SELF, _sb("def_", 0.10, 2, f"{sid}_p", "패시브 방어", is_ratio=True))]',
    "ON_BATTLE_START", True)
P["c035"] = ("명계의 선물",
    '[_stat_eff(TargetType.ALL_ALLY, _sb("atk", 0.10, 2, f"{sid}_p", "패시브 공격", is_ratio=True))]',
    "ON_BATTLE_START", True)
P["c048"] = ("암흑 치유력",
    '[_heal_ratio(TargetType.ALLY_LOWEST_HP, 0.15), _dot_eff(TargetType.ENEMY_NEAR, _bleed(f"{sid}_p", 0.08, 2))]',
    "ON_BATTLE_START", True)
P["c064"] = ("석화의 추격",
    '[_dmg(TargetType.ENEMY_NEAR, 1.50), _cc(CCType.STONE, 1, f"{sid}_p", TargetType.ENEMY_NEAR)]',
    "ON_KILL", True)


# ═══════════════════════════════════════════
# Step 3: 적용 — 각 캐릭터 함수에 passive_skill + triggers 삽입
# ═══════════════════════════════════════════
EVENT_MAP = {
    "ON_KILL": "TriggerEvent.ON_KILL",
    "ON_HIT": "TriggerEvent.ON_HIT",
    "ON_BATTLE_START": "TriggerEvent.ON_BATTLE_START",
}

changes = 0
for sid, (pname, peffects, event, once) in P.items():
    once_str = "True" if once else "False"
    trigger_event = EVENT_MAP[event]

    # 새 passive_skill + triggers 코드
    new_block = (
        f'        passive_skill=_passive(f"{{sid}}_p", "{pname}",\n'
        f'            {peffects}),\n'
        f'        triggers=[\n'
        f'            TriggerData(event={trigger_event}, skill_id=f"{{sid}}_p",\n'
        f'                        once_per_battle={once_str}),\n'
        f'        ],'
    )

    # 해당 sid의 CharacterData 블록 찾기
    sid_marker = f'sid = "{sid}"'
    sid_idx = content.find(sid_marker)
    if sid_idx == -1:
        print(f"⚠️  {sid} 미발견, 스킵")
        continue

    # sid 이후 "tile_pos=" 찾기
    tile_idx = content.find("tile_pos=", sid_idx)
    if tile_idx == -1:
        print(f"⚠️  {sid} tile_pos 미발견, 스킵")
        continue

    # tile_pos= 줄의 시작 찾기
    line_start = content.rfind("\n", 0, tile_idx) + 1

    # 기존 triggers=[...] 블록이 있으면 제거
    # triggers= 가 tile_pos 앞에 있는지 확인
    check_region = content[sid_idx:line_start]
    trig_match = re.search(r'\n(\s*triggers=\[.*?\],\s*\n)', check_region, re.DOTALL)

    # 기존 passive_skill= 블록이 있으면 제거
    pass_match = re.search(r'\n(\s*passive_skill=.*?\],\s*\n\s*triggers=\[.*?\],\s*\n)', check_region, re.DOTALL)

    if pass_match:
        # 이미 passive_skill이 있으면 교체
        old_block = pass_match.group(1)
        old_start = sid_idx + pass_match.start(1)
        old_end = sid_idx + pass_match.end(1)
        content = content[:old_start] + "\n" + new_block + "\n" + content[old_end:]
        changes += 1
    elif trig_match:
        # triggers만 있으면 passive_skill 추가 + triggers 교체
        old_block = trig_match.group(1)
        old_start = sid_idx + trig_match.start(1)
        old_end = sid_idx + trig_match.end(1)
        content = content[:old_start] + "\n" + new_block + "\n" + content[old_end:]
        changes += 1
    else:
        # triggers도 없으면 tile_pos 앞에 삽입
        indent = "        "
        content = content[:line_start] + new_block + "\n" + indent + content[line_start:].lstrip(" ")
        changes += 1

print(f"\n✅ {changes}/{len(P)} 캐릭터 패시브 스킬 추가 완료")

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)

print("✅ 파일 저장 완료")
