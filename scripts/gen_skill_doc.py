#!/usr/bin/env python3
"""엑셀 데이터 기반 캐릭터별 스킬 상세 구조 문서 생성."""
import sys, re, json, openpyxl
from collections import defaultdict, OrderedDict

sys.stdout.reconfigure(encoding='utf-8')

# ═══════════════════════════════════════════════════════════
# 1. Load all reference tables
# ═══════════════════════════════════════════════════════════
wb_skill = openpyxl.load_workbook('data/Skill.xlsx', data_only=True)
wb_buff  = openpyxl.load_workbook('data/Buff.xlsx', data_only=True)

# ── Target ──
ws = wb_skill['Target']
targets = {}
for r in range(4, ws.max_row+1):
    tid = ws.cell(r,1).value
    if tid is None: continue
    targets[tid] = (ws.cell(r,2).value or '').strip()

# ── Logic ──
ws = wb_buff['Logic']
logics = {}
for r in range(4, ws.max_row+1):
    lid = ws.cell(r,1).value
    if lid is None: continue
    logics[lid] = {
        'type': ws.cell(r,2).value,
        'cat': ws.cell(r,6).value,
    }

# ── Buff ──
ws = wb_buff['Buff']
buffs = {}
for r in range(4, ws.max_row+1):
    bid = ws.cell(r,1).value
    if bid is None: continue
    logic_list = []
    for base in [19, 22, 25]:
        lg = ws.cell(r, base).value
        lt = ws.cell(r, base+1).value
        lv = ws.cell(r, base+2).value
        if lg and lg != 0:
            logic_list.append({'id': lg, 'type': lt, 'value': lv})
    buffs[bid] = {
        'name': ws.cell(r,5).value or ws.cell(r,4).value or '',
        'buff_type': ws.cell(r,9).value,
        'sub_type': ws.cell(r,10).value,
        'add_tag': ws.cell(r,15).value,
        'overlap': ws.cell(r,17).value,
        'logics': logic_list,
    }

# ── Trigger ──
ws = wb_skill['Trigger']
triggers = {}
for r in range(4, ws.max_row+1):
    tid = ws.cell(r,1).value
    if tid is None: continue
    triggers[tid] = {
        'trigger': ws.cell(r,4).value,
        'equal': ws.cell(r,5).value,
        'tag': ws.cell(r,6).value,
        'value': ws.cell(r,7).value,
        'add1': ws.cell(r,8).value,
    }

# ── BuffValue<Child> ──
ws = wb_skill['BuffValue<Child>']
buffvalues = {}
for r in range(4, ws.max_row+1):
    bvid = ws.cell(r,1).value
    if bvid is None: continue
    buff_id = ws.cell(r,5).value
    trig_id = ws.cell(r,7).value
    lv = []
    for s in [11, 14, 17]:
        lv.append([ws.cell(r,s+i).value or 0 for i in range(3)])
    buffvalues[bvid] = {
        'buff_id': buff_id,
        'buff_desc': ws.cell(r,6).value or '',
        'trigger_id': trig_id,
        'req_tag1': ws.cell(r,8).value,
        'req_tag2': ws.cell(r,9).value,
        'rate': ws.cell(r,10).value or 0,
        'values': lv,
        'turn': ws.cell(r,20).value,
    }

# ── Skill<Child> ──
ws = wb_skill['Skill<Child>']
char_skills = OrderedDict()
for r in range(4, ws.max_row+1):
    sid = ws.cell(r,1).value
    if sid is None: continue
    cname = ws.cell(r,2).value
    if cname not in char_skills:
        char_skills[cname] = {
            'element': ws.cell(r,13).value,
            'role': ws.cell(r,14).value,
            'skills': [],
        }
    actions = []
    for cols in [(20,21,22,23,24),(25,26,27,28,29),(30,31,32,33,34),(35,36,37,38,39)]:
        tgt = ws.cell(r,cols[3]).value
        bv  = ws.cell(r,cols[4]).value
        if tgt or bv:
            actions.append({
                'act_trigger': ws.cell(r,cols[0]).value,
                'rem_trigger': ws.cell(r,cols[1]).value,
                'target_id': tgt,
                'buffvalue_id': bv,
            })
    char_skills[cname]['skills'].append({
        'id': sid,
        'name': ws.cell(r,3).value or '',
        'desc': ws.cell(r,4).value or '',
        'type': ws.cell(r,15).value,
        'cooltime': ws.cell(r,16).value or 0,
        'casting': ws.cell(r,18).value,
        'actions': actions,
    })

# ═══════════════════════════════════════════════════════════
# 2. Helper functions
# ═══════════════════════════════════════════════════════════
ELEM_KR = {'Fire':'화','Water':'수','Forest':'목','Light':'광','Dark':'암'}
ROLE_KR = {'Attacker':'공격','Magician':'마법','Defender':'방어','Healer':'힐러','Supporter':'서포터'}
TYPE_KR = {'Normal':'일반','Active':'액티브','Ultimate':'얼티밋','Passive':'패시브'}


def pct(v):
    """100000 기준값 -> 퍼센트 문자열"""
    if v is None or v == 0:
        return '0%'
    return f'{v/1000:.1f}%'


def val_str(v):
    """100000 기준값 -> 배수/퍼센트 표기"""
    if v is None or v == 0:
        return '0'
    if v >= 100000:
        return f'{v/100000:.1f}x'
    else:
        return f'{v/1000:.1f}%'


def turn_str(t):
    if t is None or t == 0:
        return '즉시'
    if t == -1:
        return '영구'
    return f'{t}턴'


def rate_str(r):
    if r is None or r == 0:
        return '0%'
    if r >= 100000:
        return '100%'
    return f'{r/1000:.1f}%'


# ── 전투 스탯 ID → 한글 매핑 (Enum.xlsx Stat 시트 기준) ──
STAT_NAMES = {
    1000:'공격력', 1001:'공격력%', 1002:'방어력', 1003:'방어력%',
    1004:'체력', 1005:'체력%', 1006:'관통력', 1007:'관통력%',
    1008:'속도', 1009:'치명확률%', 1010:'치명피해%', 1011:'치명저항%',
    1012:'치명피해방어%', 1013:'회피', 1014:'적중', 1015:'반격확률%',
    1016:'SP감소', 1017:'시작SP', 1018:'SP회복', 1019:'자연치유',
    1020:'자연치유%', 1021:'속성DMG%', 1022:'화속성DMG%', 1023:'수속성DMG%',
    1024:'목속성DMG%', 1025:'광속성DMG%', 1026:'암속성DMG%',
    1027:'스킬피해%', 1028:'스킬피해방어%', 1029:'치유량증가%',
    1030:'보스DMG%', 1031:'보스DMG방어%', 1032:'몬스터DMG%', 1033:'몬스터DMG방어%',
    1034:'노멀DMG%', 1035:'액티브DMG%', 1036:'얼티밋DMG%',
    1037:'PvP DMG%', 1038:'PvP DMG방어%',
    1039:'CC중 적DMG%', 1040:'DoT중 적DMG%', 1041:'디버프중 DMG%',
    1042:'보호막중 DMG%', 1043:'회복중 DMG%', 1044:'CC보유중 회피',
    1048:'적 디버프중 DMG%', 1049:'화상중 적DMG%', 1050:'출혈중 적DMG%',
    1051:'맹독중 적DMG%', 1052:'기절중 적DMG%', 1053:'약점피해방어%',
    1054:'열위 주는피해%', 1055:'열위 받는피해%', 1056:'받는 회복량%',
    1057:'버프중 DMG%', 1058:'받는 DMG%', 1059:'ATK증가(추가)', 1060:'DEF증가(추가)',
}


def _stat_ref(v):
    """v2/v3 값이 스탯 참조인 경우 설명 추가."""
    if not v or v == 0:
        return ''
    name = STAT_NAMES.get(v)
    if name:
        return f' (참조: {name})'
    return ''


def describe_logic(logic_id, logic_entry, values_slot):
    """Logic ID + Buff logic entry + BuffValue slot -> 한글 효과 설명"""
    lg = logics.get(logic_id, {})
    ltype = lg.get('type', '')
    cat = lg.get('cat', '')
    v1, v2, v3 = values_slot

    if not ltype:
        return f'(Logic {logic_id})'

    # ── Damage types ──
    if ltype == 'LogicDamage':
        extra = _stat_ref(v2) if v2 else ''
        cri = ' (강제 치명타)' if cat == 'ForceCri' else ''
        return f'대미지 {val_str(v1)}{cri}{extra}'
    if ltype == 'LogicDamagePenetration':
        extra = _stat_ref(v2) if v2 else ''
        return f'방어관통 대미지 {val_str(v1)}{extra}'
    if ltype == 'LogicDamageHpRatio':
        return f'체력비례 대미지 {val_str(v1)}'
    if ltype == 'LogicDamageBuffScale':
        return f'버프 스케일 대미지 {val_str(v1)}'
    if ltype == 'LogicDamageBuffScaleTarget':
        return f'대상 버프 스케일 대미지 {val_str(v1)}'
    if ltype == 'LogicDamageDebuffScaleTarget':
        return f'대상 디버프 스케일 대미지 {val_str(v1)}'
    if ltype == 'LogicDamageCriApplyDebuff':
        return f'치명타 시 디버프 부여 대미지 {val_str(v1)}'

    # ── Heal types ──
    if ltype == 'LogicHeal':
        return f'HP 회복 {val_str(v1)}'
    if ltype == 'LogicHealRatio':
        return f'HP비율 회복 {pct(v1)}'
    if ltype == 'LogicHealLossScaleHp':
        return f'손실체력비례 회복 {pct(v1)}'
    if ltype == 'LogicHealTargetCount':
        return f'대상수 비례 회복 {val_str(v1)}'
    if ltype == 'LogicAllyScaleHeal':
        return f'아군수 비례 회복 {val_str(v1)}'

    # ── Barrier / Shield ──
    if ltype == 'LogicBarrier':
        return f'배리어 {val_str(v1)}'
    if ltype == 'LogicBarrierRatio':
        return f'배리어(비율) {pct(v1)}'

    # ── Stat changes ──
    if ltype == 'LogicStatChange':
        stat_name = STAT_NAMES.get(v2, f'stat_{v2}') if v2 else '?'
        sign = '+' if v1 and v1 > 0 else ''
        return f'{stat_name} {sign}{pct(v1)}'
    if ltype == 'LogicAllyScaleStatusChange':
        return f'아군수 비례 스탯변경 {pct(v1)}'
    if ltype == 'LogicStatusChangeEveryTurn':
        return f'매턴 스탯변경 {pct(v1)}'
    if ltype == 'LogicStatusChangeElementCount':
        return f'속성수 비례 스탯변경 {pct(v1)}'
    if ltype == 'LogicStatusChangeRemainingHpPercent':
        return f'잔여체력비례 스탯변경 {pct(v1)}'
    if ltype == 'LogicStatusChangeMissingHpPercent':
        return f'손실체력비례 스탯변경 {pct(v1)}'
    if ltype == 'LogicStatusChangeDeadAlly':
        return f'죽은아군수 비례 스탯변경 {pct(v1)}'
    if ltype == 'LogicStatusChangeEveryTurnDeadAlly':
        return f'매턴 죽은아군 비례 스탯변경 {pct(v1)}'
    if ltype == 'LogicStatusChangeEveryTurnUnTag':
        return f'매턴 스탯변경(태그없음) {pct(v1)}'
    if ltype == 'LogicStatusChangeEveryTurnTag':
        return f'매턴 스탯변경(태그) {pct(v1)}'
    if ltype == 'LogicAllyScaleStatusChangeEveryTurn':
        return f'매턴 아군수 비례 스탯변경 {pct(v1)}'
    if ltype == 'LogicStatusChangeApplyAnotherStatusRate':
        return f'다른스탯비례 스탯변경 {pct(v1)}'

    # ── DOT ──
    if ltype == 'LogicDot':
        if cat == 'Dmg':
            return f'DoT 대미지 {pct(v1)}'
        if cat == 'Heal':
            return f'DoT 회복 {pct(v1)}'
        return f'DoT {pct(v1)}'
    if ltype == 'LogicDotDamage':
        return f'DoT 고정대미지 {v1}'
    if ltype == 'LogicDotHeal':
        return f'DoT 고정회복 {v1}'
    if ltype == 'LogicDotHealLossScaleHp':
        return f'DoT 손실체력비례 회복 {pct(v1)}'
    if ltype == 'LogicDotHealHpRatio':
        return f'DoT HP비율 회복 {pct(v1)}'
    if ltype == 'LogicDotDamageHpRatio':
        return f'DoT 체력비례 대미지 {pct(v1)}'

    # ── CC ──
    if ltype == 'LogicStun': return '기절'
    if ltype == 'LogicSleep': return '수면'
    if ltype == 'LogicFreeze': return '빙결'
    if ltype == 'LogicStone': return '석화'
    if ltype == 'LogicElectricshock': return '감전'
    if ltype == 'LogicPanic': return '공포'
    if ltype == 'LogicBlind': return '실명'
    if ltype == 'LogicConfused': return '혼란'
    if ltype == 'LogicKnockback': return '넉백'
    if ltype == 'LogicStop': return '행동불능(Stop)'
    if ltype == 'LogicPause': return '일시정지(Pause)'
    if ltype == 'LogicStunTag': return '기절(태그조건)'
    if ltype == 'LogicAbnormalSkill': return '이상상태 스킬'

    # ── Utility ──
    if ltype == 'LogicRevive':
        return f'부활 {pct(v1)}'
    if ltype == 'LogicTaunt':
        return '도발'
    if ltype == 'LogicSpIncrease':
        return f'SP +{v1/1000 if v1 else 0:.0f}'
    if ltype == 'LogicSpIncreaseEveryTurn':
        return '매턴 SP 증가'
    if ltype == 'LogicSkillGuageChargeRatio':
        return f'스킬게이지 충전 {pct(v1)}'
    if ltype == 'LogicSpLock':
        return 'SP 잠금'
    if ltype == 'LogicSpSteal':
        return 'SP 탈취'
    if ltype == 'LogicCooltimeChange':
        if cat == 'ActiveSkill':
            return f'액티브 쿨타임 변경 {v1}'
        if cat == 'ReactionSkill':
            return f'반격 쿨타임 변경 {v1}'
        return f'쿨타임 변경 {v1}'

    # ── Remove/Immune ──
    if ltype == 'LogicRemoveBuffCount':
        if cat == 'Buff':
            return f'버프 제거 {v1 or 1}개'
        if cat == 'Debuff':
            return f'디버프 해제 {v1 or 1}개'
        return '버프/디버프 제거'
    if ltype == 'LogicDebuffImmune':
        return '디버프 면역'
    if ltype == 'LogicRestriction':
        if cat == 'Heal':
            return '회복 금지'
        return f'제한({cat})'

    # ── Counter/Ignore ──
    if ltype == 'LogicUseSkill':
        return '추가 스킬 사용'
    if ltype == 'CounterUseSkill':
        return '반격 스킬 사용'
    if ltype == 'LogicCounterUnavailable':
        return '반격 불가'
    if ltype == 'LogicNormalIgnoreCounter':
        return '일반공격 반격무시'
    if ltype == 'LogicActiveIgnoreCounter':
        return '액티브 반격무시'
    if ltype == 'LogicUltimateIgnoreCounter':
        return '얼티밋 반격무시'
    if ltype == 'LogicActiveSkillTurnChangeOnce':
        return '액티브 턴 변경(1회)'
    if ltype == 'LogicSpdTwist':
        return '속도 왜곡'
    if ltype == 'LogicCriUnavailable':
        return '치명타 불가'
    if ltype == 'LogicInvincibility':
        return '무적'
    if ltype == 'LogicUndying':
        return '불사'
    if ltype == 'LogicBuffTurnIncrease':
        return '버프 턴 증가'
    if ltype == 'LogicDebuffTurnIncrease':
        return '디버프 턴 증가'
    if ltype == 'LogicUseSkillEveryTurn':
        return '매턴 추가 스킬'

    # ── Weather ──
    if 'LogicWeather' in ltype:
        return f'날씨변경: {cat}'

    return f'{ltype}({cat}) val={v1}'


def describe_trigger(trig_id):
    """BuffTrigger -> 조건 설명"""
    if not trig_id or trig_id == 0:
        return ''
    trig = triggers.get(trig_id, {})
    if not trig:
        return f'[조건:{trig_id}]'
    t = trig.get('trigger','')
    eq = trig.get('equal','')
    tag = trig.get('tag','')
    val = trig.get('value',0)

    if t == 'Hp':
        op_map = {
            'GreaterEqual': '>=', 'LessEqual': '<=',
            'Less': '<', 'Greater': '>',
        }
        op = op_map.get(eq, eq)
        return f'HP{op}{pct(val)}'
    if t == 'TagCount':
        op_map = {'Equal': '=', 'GreaterEqual': '>=', 'Less': '<', 'Greater': '>'}
        op = op_map.get(eq, eq)
        tag_kr = {
            'HitCriOnce': '치명타 적중', 'Burn': '화상', 'Poison': '중독',
            'Stun': '기절', 'Sleep': '수면', 'Freeze': '빙결',
            'HpMoreEqual': 'HP이상', 'HpLess': 'HP미만',
        }.get(tag, tag)
        return f'{tag_kr}{op}{val}'
    if t == 'Dead':
        return '사망 시'
    if t == 'Kill':
        return '처치 시'
    if t == 'Hit':
        return '피격 시'
    if t == 'Attacked':
        return '공격받을 때'
    if t == 'TurnStart':
        return '턴 시작 시'
    if t == 'TurnEnd':
        return '턴 종료 시'
    return f'[{t} {eq} {tag}{val}]'


def describe_buffvalue(bv_id):
    """BuffValue ID -> 효과 상세 설명"""
    bv = buffvalues.get(bv_id)
    if not bv:
        return '(데이터 없음)'

    buff_id = bv['buff_id']
    buff = buffs.get(buff_id, {})
    buff_name = buff.get('name', bv['buff_desc'])
    buff_type = buff.get('buff_type', '')
    overlap = buff.get('overlap', '')
    buff_logics = buff.get('logics', [])

    parts = []

    # Trigger condition
    trig_desc = describe_trigger(bv['trigger_id'])
    if trig_desc:
        parts.append(f'조건: {trig_desc}')

    # Require tags
    for tag in [bv.get('req_tag1'), bv.get('req_tag2')]:
        if tag and tag != 'None':
            parts.append(f'필요태그: {tag}')

    # Rate
    rate = bv.get('rate', 100000)
    if rate < 100000:
        parts.append(f'확률: {rate_str(rate)}')

    # Logic effects (빈 로직 슬롯 필터링: type이 0/None이면 스킵)
    for i, bl in enumerate(buff_logics):
        lid = bl.get('id', 0)
        ltype = bl.get('type')
        if not lid or (not ltype or ltype == 0):
            continue
        vals = bv['values'][i] if i < len(bv['values']) else [0,0,0]
        # 값이 전부 0이면 스킵
        if vals == [0, 0, 0]:
            continue
        effect = describe_logic(lid, bl, vals)
        parts.append(effect)

    # Duration
    turn = bv.get('turn')
    if turn and turn != 0:
        parts.append(f'지속: {turn_str(turn)}')

    # Overlap
    if overlap and overlap != 'None':
        overlap_kr = {
            'StackAll':'중첩', 'Replace':'교체',
            'StackCount':'스택', 'StackTurn':'턴갱신',
        }.get(overlap, overlap)
        parts.append(f'[{overlap_kr}]')

    return ' / '.join(parts) if parts else buff_name


# ═══════════════════════════════════════════════════════════
# 3. Generate Markdown
# ═══════════════════════════════════════════════════════════
lines = []
L = lines.append

L('# 캐릭터별 스킬 상세 구조')
L('')
L('> **출처**: `data/Skill.xlsx` (Skill<Child>, BuffValue<Child>) + `data/Buff.xlsx` (Buff, Logic)')
L('> **생성일**: 2026-03-13')
L(f'> **캐릭터 수**: {len(char_skills)}명 / **스킬 수**: {sum(len(v["skills"]) for v in char_skills.values())}개')
L('')

# 속성/역할 순서
elem_order = {'Fire':0,'Water':1,'Forest':2,'Light':3,'Dark':4}
role_order = {'Attacker':0,'Magician':1,'Defender':2,'Healer':3,'Supporter':4}

sorted_chars = sorted(
    char_skills.items(),
    key=lambda x: (
        elem_order.get(x[1]['element'], 9),
        role_order.get(x[1]['role'], 9),
        x[0],
    ),
)

# ── TOC ──
L('## 목차')
L('')
for cname, cdata in sorted_chars:
    ek = ELEM_KR.get(cdata['element'], '?')
    rk = ROLE_KR.get(cdata['role'], '?')
    anchor = cname.replace(' ', '-')
    L(f'- [{cname} ({ek}/{rk})](#캐릭터-{anchor})')
L('')
L('---')
L('')

# ── Character sections ──
for cname, cdata in sorted_chars:
    ek = ELEM_KR.get(cdata['element'], '?')
    rk = ROLE_KR.get(cdata['role'], '?')

    L(f'## 캐릭터: {cname}')
    L('')
    L(f'| 속성 | 역할 |')
    L(f'|:----:|:----:|')
    L(f'| {cdata["element"]} ({ek}) | {cdata["role"]} ({rk}) |')
    L('')

    # Group skills by type
    type_order = ['Normal', 'Active', 'Ultimate', 'Passive']
    type_groups = defaultdict(list)
    for sk in cdata['skills']:
        type_groups[sk['type']].append(sk)

    for stype in type_order:
        sklist = type_groups.get(stype, [])
        if not sklist:
            continue

        type_label = TYPE_KR.get(stype, stype)
        L(f'### {type_label} 스킬')
        L('')

        for idx, sk in enumerate(sklist):
            if len(sklist) > 1 and stype in ('Active', 'Ultimate'):
                suffix = f' (변형 {idx+1})'
            else:
                suffix = ''
            L(f'**{sk["name"]}**{suffix}')
            L('')

            # Clean desc (remove color tags and template tokens)
            desc_clean = re.sub(r'</?color[^>]*>', '', sk['desc'])
            desc_clean = re.sub(r'\{buff:[^}]*\}_?\{?[^}]*\}?', 'N', desc_clean)
            desc_clean = desc_clean.replace('__', ' ').strip()
            L(f'> {desc_clean}')
            L('')

            meta_parts = [f'ID: `{sk["id"]}`']
            if sk['cooltime']:
                meta_parts.append(f'쿨타임: {sk["cooltime"]}턴')
            if sk['casting']:
                meta_parts.append(f'시전: {sk["casting"]}')
            L(' | '.join(meta_parts))
            L('')

            if sk['actions']:
                L('| # | 타이밍 | 대상 | 효과 상세 |')
                L('|:-:|:------:|:----:|:----------|')
                for ai, act in enumerate(sk['actions'], 1):
                    tgt_desc = targets.get(
                        act['target_id'],
                        f'Target#{act["target_id"]}',
                    ) if act['target_id'] else '-'
                    timing = act.get('act_trigger', '-')
                    bv_desc = (
                        describe_buffvalue(act['buffvalue_id'])
                        if act['buffvalue_id']
                        else '-'
                    )
                    L(f'| {ai} | {timing} | {tgt_desc} | {bv_desc} |')
                L('')
            else:
                L('*(액션 데이터 없음)*')
                L('')

    L('---')
    L('')

# ═══════════════════════════════════════════════════════════
# 4. Write output
# ═══════════════════════════════════════════════════════════
output_path = 'docs/캐릭터별_스킬_상세_구조.md'
with open(output_path, 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))

print(f'Generated: {output_path}')
print(f'  Characters: {len(char_skills)}')
print(f'  Total lines: {len(lines)}')
