"""캐릭터 스탯 & 스킬 상세 명세서 생성 (문장형 설명)"""
import sys, inspect
sys.path.insert(0, 'src')
sys.stdout.reconfigure(encoding='utf-8')
import fixtures.test_data as td

EL_KR = {'FIRE':'화','WATER':'수','FOREST':'목','LIGHT':'광','DARK':'암'}
ROLE_KR = {'ATTACKER':'딜러','MAGICIAN':'마법사','DEFENDER':'탱커','HEALER':'힐러','SUPPORTER':'서포터'}
TGT_KR = {
    'ENEMY_NEAR':'가장 가까운 적 1명','ENEMY_NEAR_ROW':'가장 가까운 적 + 동일 행',
    'ENEMY_NEAR_CROSS':'가장 가까운 적 + 십자 범위','ALL_ENEMY':'적 전체',
    'ENEMY_RANDOM':'적 랜덤 1명','ENEMY_RANDOM_2':'적 랜덤 2명','ENEMY_RANDOM_3':'적 랜덤 3명',
    'ENEMY_LOWEST_HP':'HP가 가장 낮은 적','ENEMY_HIGHEST_HP':'HP가 가장 높은 적',
    'ENEMY_HIGHEST_SPD':'SPD가 가장 높은 적','ENEMY_BACK_ROW':'적 최후열 전체',
    'ENEMY_FRONT_ROW':'적 최전열 전체','ENEMY_SAME_COL':'시전자와 동일 열의 적(관통)',
    'ENEMY_LAST_COL':'적 최우열 전체','ENEMY_ADJACENT':'인접 타일의 적',
    'SELF':'자신','ALL_ALLY':'아군 전체','ALLY_LOWEST_HP':'HP가 가장 낮은 아군',
    'ALLY_LOWEST_HP_2':'HP가 낮은 아군 2명','ALLY_HIGHEST_ATK':'ATK가 가장 높은 아군',
    'ALLY_SAME_ROW':'동일 행 아군','ALLY_BEHIND':'뒤쪽 아군 1명',
    'ALLY_DEAD_RANDOM':'사망한 아군 1명','ALLY_ROLE_ATTACKER':'공격형 아군 전체',
    'ALLY_ROLE_DEFENDER':'방어형 아군 전체',
}
STAT_KR = {'atk':'공격력','def_':'방어력','spd':'속도','hp':'체력',
           'cri_ratio':'크리티컬 확률','cri_dmg_ratio':'크리티컬 피해','acc':'명중률',
           'cri_resist':'크리 저항'}
DOT_KR = {'burn':'화상','poison':'중독','bleed':'출혈'}
CC_KR = {'stun':'기절','sleep':'수면','freeze':'빙결','stone':'석화',
         'panic':'공포','silence':'침묵','blind':'실명','electric_shock':'감전'}
TRIGGER_KR = {
    'on_kill':'적 처치 시','on_hit':'피격 시','on_battle_start':'전투 시작 시',
    'on_round_start':'라운드 시작 시','on_turn_end':'턴 종료 시',
}


def grade_from(role, atk):
    t = {
        'ATTACKER': {920: 3.5, 800: 3, 640: 2, 480: 1},
        'MAGICIAN': {690: 3.5, 600: 3, 480: 2, 360: 1},
        'DEFENDER': {574: 3.5, 500: 3, 400: 2, 300: 1},
        'HEALER':   {460: 3.5, 400: 3, 320: 2, 240: 1},
        'SUPPORTER': {574: 3.5, 500: 3, 400: 2, 300: 1},
    }
    for v, g in sorted(t.get(role, {}).items(), reverse=True):
        if atk >= v:
            return g
    return 1


def desc_effect(e):
    lt = e.logic_type.name
    tgt = TGT_KR.get(e.target_type.name, e.target_type.name)
    cond = e.condition or {}
    hc = getattr(e, 'hit_count', 1) or 1

    if lt == 'DAMAGE':
        base = f"ATK의 {e.multiplier:.2f}배"
        if hc > 1:
            total = e.multiplier * hc
            base = f"ATK의 {e.multiplier:.2f}배로 {hc}회 연속 타격하여 총 {total:.2f}배"
        s = f"{tgt}에게 {base} 피해를 입힌다."
        if cond.get('target_hp_below'):
            pct = cond['target_hp_below']
            s = f"{tgt}의 HP가 {pct:.0%} 이하일 때, {base} 추가 피해를 입힌다. (처형 효과)"
        if cond.get('burn_bonus_per_stack'):
            bn = cond['burn_bonus_per_stack']
            s += f" 대상에게 적용된 화상 스택 1개당 +{bn:.2f}배의 추가 피해가 가산된다."
        return s
    elif lt == 'HEAL_HP_RATIO':
        return f"{tgt}의 최대 HP의 {e.value:.0%}만큼 즉시 회복시킨다."
    elif lt == 'STAT_CHANGE':
        bd = e.buff_data
        if not bd:
            return '스탯 변경 효과를 부여한다.'
        stat = STAT_KR.get(bd.stat, bd.stat)
        if bd.is_ratio:
            vstr = f"{abs(bd.value):.0%}"
        else:
            vstr = f"{abs(bd.value):.0f}"
        if bd.is_debuff:
            return f"{tgt}의 {stat}을(를) {bd.duration}턴간 {vstr} 감소시킨다."
        else:
            return f"{tgt}의 {stat}을(를) {bd.duration}턴간 {vstr} 증가시킨다."
    elif lt == 'DOT':
        bd = e.buff_data
        dt = DOT_KR.get(bd.dot_type, bd.dot_type)
        return (f"{tgt}에게 {dt} 상태를 부여한다. "
                f"매 턴 시작 시 최대 HP의 {bd.value:.0%} 피해를 {bd.duration}턴간 받는다. "
                f"(최대 {bd.max_stacks}스택까지 중첩 가능)")
    elif lt == 'CC':
        bd = e.buff_data
        cc = CC_KR.get(bd.cc_type.value, bd.cc_type.value)
        hard = bd.cc_type.value in ('stun', 'sleep', 'freeze', 'stone')
        cc_desc = "행동이 완전히 봉쇄된다." if hard else "30% 확률로 행동에 실패한다."
        return f"{tgt}에게 {cc} 상태이상을 {bd.duration}턴간 부여한다. {cc_desc}"
    elif lt == 'BARRIER':
        return (f"{tgt}에게 최대 HP의 {e.value:.0%}에 해당하는 보호막을 부여한다. "
                "보호막이 유지되는 동안 HP 대신 보호막이 먼저 소모된다.")
    elif lt == 'TAUNT':
        return f"적 전체를 {int(e.value)}턴간 도발하여 모든 공격을 자신에게 집중시킨다."
    elif lt == 'REVIVE':
        return f"{tgt}을(를) HP {e.value:.0%} 상태로 전투에 복귀시킨다. (부활)"
    elif lt == 'SP_INCREASE':
        return f"{tgt}의 SP를 {int(e.value)} 증가시킨다."
    elif lt == 'REMOVE_DEBUFF':
        return f"{tgt}에게 적용된 모든 디버프(화상, 독, 감속 등)를 즉시 제거한다."
    elif lt == 'REMOVE_BUFF':
        return f"{tgt}에게 적용된 모든 버프(공격력 증가, 보호막, 속도 증가 등)를 즉시 제거한다."
    elif lt == 'COUNTER':
        return (f"{tgt}에게 {int(e.value)}턴간 반격 준비 상태를 부여한다. "
                "피격 시 공격한 적에게 자동으로 반격한다.")
    else:
        return f"{lt} 효과를 발동한다. (값: {e.value})"


# Collect characters
chars = []
for name, func in sorted(inspect.getmembers(td, inspect.isfunction)):
    if not name.startswith('make_') or name.startswith('make_teddy'):
        continue
    try:
        chars.append(func())
    except Exception:
        pass

eo = {'FIRE': 0, 'WATER': 1, 'FOREST': 2, 'LIGHT': 3, 'DARK': 4}
ro = {'ATTACKER': 0, 'MAGICIAN': 1, 'DEFENDER': 2, 'HEALER': 3, 'SUPPORTER': 4}
chars.sort(key=lambda c: (eo.get(c.element.name, 9), ro.get(c.role.name, 9), c.id))

lines = []
lines.append('# 캐릭터 스탯 & 스킬 상세 명세서')
lines.append('')
lines.append(f'> 총 {len(chars)}캐릭터 | ATK/DEF x2 + 스킬배율 x2 적용 (v7.0)')
lines.append('> 자동 생성: test_data.py 기준')
lines.append('')
lines.append('---')

current_el = None
for c in chars:
    st = c.stats
    el = c.element.name
    role = c.role.name
    grade = grade_from(role, st.atk)

    if el != current_el:
        current_el = el
        emoji = {'FIRE': '🔥', 'WATER': '💧', 'FOREST': '🌿', 'LIGHT': '☀️', 'DARK': '🌙'}[el]
        lines.append('')
        lines.append(f'## {emoji} {EL_KR[el]}속성')
        lines.append('')

    grade_str = f'{grade}★' if grade != 3.5 else '3.5★'
    lines.append(f'### {c.name} ({c.id}) — {EL_KR[el]}/{ROLE_KR[role]} {grade_str}')
    lines.append('')
    lines.append('| 스탯 | ATK | DEF | HP | SPD | CRI | PEN | SP비용 |')
    lines.append('|:----:|:---:|:---:|:--:|:---:|:---:|:---:|:-----:|')
    lines.append(f'| 값 | {st.atk:.0f} | {st.def_:.0f} | {st.hp:.0f} | {st.spd:.0f} '
                 f'| {st.cri_ratio:.0%} | {st.penetration:.0%} | {c.ultimate_skill.sp_cost} |')
    lines.append('')

    skill_labels = [
        (c.normal_skill, '일반 공격 (Normal)',
         '쿨타임 없이 매 턴 사용할 수 있는 기본 공격이다.'),
        (c.active_skill, '액티브 스킬 (Active)',
         '사용 후 일정 턴의 쿨타임이 필요한 강화 스킬이다.'),
        (c.ultimate_skill, '궁극기 (Ultimate)',
         '공유 SP를 소모하여 엑스트라 턴으로 발동하는 필살기이다.'),
    ]
    for skill, label, intro in skill_labels:
        cd_str = f' 쿨타임 {skill.cooldown_turns}턴.' if skill.cooldown_turns > 0 else ''
        sp_str = f' SP {skill.sp_cost} 소모.' if skill.sp_cost > 0 else ''
        lines.append(f'**{label}** — 「{skill.name}」')
        lines.append('')
        lines.append(f'> {intro}{cd_str}{sp_str}')
        lines.append('')
        for i, e in enumerate(skill.effects, 1):
            desc = desc_effect(e)
            lines.append(f'{i}. {desc}')
        lines.append('')

    if c.triggers:
        lines.append('**패시브 트리거:**')
        lines.append('')
        for t in c.triggers:
            once = ' 이 효과는 전투당 1회만 발동한다.' if t.once_per_battle else ''
            ev = TRIGGER_KR.get(t.event.value, t.event.value)
            skill_desc = ''
            if t.skill_id:
                for sk in [c.normal_skill, c.active_skill, c.ultimate_skill]:
                    if sk.id == t.skill_id:
                        sk_label = {'normal': '일반 공격', 'active': '액티브 스킬',
                                    'ultimate': '궁극기'}[sk.skill_type.value]
                        skill_desc = (f" {sk_label} 「{sk.name}」이(가) "
                                      "쿨타임과 무관하게 즉시 자동 발동된다.")
            lines.append(f'- **{ev}**:{skill_desc}{once}')
        lines.append('')

    lines.append('---')

doc = '\n'.join(lines)
with open('docs/CHARACTER_SPEC.md', 'w', encoding='utf-8') as f:
    f.write(doc)
print(f'Generated: {len(chars)} characters, {len(lines)} lines')
