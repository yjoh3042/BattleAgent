"""전체 캐릭터 데이터 추출 → JSON"""
import sys, os, json, inspect
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import fixtures.test_data as td

def eff_str(e):
    lt = e.logic_type.name
    if lt == 'DAMAGE':
        hc = getattr(e, 'hit_count', 1) or 1
        cond = e.condition or {}
        s = f'DMG {e.multiplier:.2f}x'
        if hc > 1: s += f' x{hc}hit'
        if cond.get('target_hp_below'): s += f' (HP<{cond["target_hp_below"]:.0%})'
        if cond.get('burn_bonus_per_stack'): s += f' +burn{cond["burn_bonus_per_stack"]:.0%}/stk'
        return s
    elif lt == 'HEAL_HP_RATIO':
        return f'HEAL {e.value:.0%}'
    elif lt in ('STAT_BUFF', 'STAT_CHANGE'):
        bd = e.buff_data
        if bd is None: return f'{lt}(?)'
        sign = '-' if bd.is_debuff else '+'
        st = bd.stat or '?'
        if bd.is_ratio:
            vstr = f'{bd.value:.0%}'
        else:
            vstr = f'{bd.value:.0f}'
        return f'{st}{sign}{vstr}({bd.duration}T)'
    elif lt == 'DOT':
        bd = e.buff_data
        if bd is None: return 'DOT(?)'
        dt = bd.dot_type or 'dot'
        dr = getattr(bd, 'value', 0)
        return f'{dt} {dr:.0%}({bd.duration}T)'
    elif lt == 'CC':
        bd = e.buff_data
        if bd is None: return 'CC(?)'
        ct = bd.cc_type.name if bd.cc_type else '?'
        return f'CC:{ct}({bd.duration}T)'
    elif lt == 'SP_GAIN':
        return f'SP+{e.value:.0f}'
    elif lt == 'CLEANSE':
        return 'CLEANSE'
    elif lt == 'REVIVE':
        return f'REVIVE {e.value:.0%}'
    elif lt == 'SHIELD':
        return f'SHIELD {e.value:.0%}'
    elif lt == 'REMOVE_DEBUFF':
        return 'CLEANSE'
    elif lt == 'TAUNT':
        bd = e.buff_data
        dur = bd.duration if bd else '?'
        return f'TAUNT({dur}T)'
    else:
        return lt

def extract_skill(skill):
    effs = []
    for e in skill.effects:
        try:
            effs.append(eff_str(e))
        except Exception as ex:
            effs.append(f'ERR:{ex}')
    tgt = skill.effects[0].target_type.name if skill.effects else '?'
    return {'name': skill.name, 'target': tgt, 'effects': ' | '.join(effs)}

chars = []
for name, func in sorted(inspect.getmembers(td, inspect.isfunction)):
    if not name.startswith('make_') or name.startswith('make_teddy'):
        continue
    try:
        c = func()
        st = c.stats
        n_info = extract_skill(c.normal_skill)
        a_info = extract_skill(c.active_skill)
        u_info = extract_skill(c.ultimate_skill)

        chars.append({
            'id': c.id, 'name': c.name,
            'element': c.element.name, 'role': c.role.name,
            'atk': st.atk, 'def': st.def_, 'hp': st.hp, 'spd': st.spd,
            'cri': st.cri_ratio, 'pen': st.penetration,
            'sp': c.ultimate_skill.sp_cost,
            'normal': n_info, 'active': a_info, 'ultimate': u_info,
        })
    except Exception as ex:
        print(f'SKIP {name}: {ex}')

elem_order = {'FIRE':0,'WATER':1,'FOREST':2,'LIGHT':3,'DARK':4}
role_order = {'ATTACKER':0,'MAGICIAN':1,'HEALER':2,'DEFENDER':3,'SUPPORTER':4}
chars.sort(key=lambda c: (elem_order.get(c['element'],9), role_order.get(c['role'],9), c['id']))

with open('data/_all_chars.json', 'w', encoding='utf-8') as f:
    json.dump(chars, f, ensure_ascii=False, indent=1)

print(f'Total: {len(chars)} characters')
for c in chars:
    elem_kr = {'FIRE':'화','WATER':'수','FOREST':'목','LIGHT':'광','DARK':'암'}[c['element']]
    role_kr = {'ATTACKER':'공격','MAGICIAN':'마법','HEALER':'힐러','DEFENDER':'방어','SUPPORTER':'서포터'}[c['role']]
    print(f"  {c['id']:6s} {c['name']:8s} {elem_kr}/{role_kr:4s} ATK={c['atk']:3.0f} DEF={c['def']:3.0f} HP={c['hp']:4.0f} SPD={c['spd']:3.0f} CRI={c['cri']:.0%} PEN={c['pen']:.0%} SP={c['sp']}")
    print(f"         N: {c['normal']['effects']}")
    print(f"         A: {c['active']['effects']}")
    print(f"         U: {c['ultimate']['effects']}")
