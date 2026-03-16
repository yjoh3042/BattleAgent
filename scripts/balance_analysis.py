"""밸런스 분석 리포트 생성기.

사용법: PYTHONUTF8=1 python scripts/balance_analysis.py
출력: docs/밸런스_분석_리포트.md
"""
import json, re, sys
from collections import Counter, defaultdict
from pathlib import Path
from datetime import date

ROOT = Path(__file__).resolve().parent.parent
OUT  = ROOT / 'docs' / '밸런스_분석_리포트.md'

# ── 데이터 로드 ──────────────────────────────────────────────
with open(ROOT / 'data' / '_all_chars.json', encoding='utf-8') as f:
    chars = json.load(f)

# ── 상수 ─────────────────────────────────────────────────────
ELEM_ORDER = ['FIRE', 'WATER', 'FOREST', 'LIGHT', 'DARK']
ROLE_ORDER = ['ATTACKER', 'MAGICIAN', 'DEFENDER', 'HEALER', 'SUPPORTER']
ELEM_KR = {'FIRE': '화', 'WATER': '수', 'FOREST': '목', 'LIGHT': '광', 'DARK': '암'}
ROLE_KR = {
    'ATTACKER': '공격수', 'MAGICIAN': '마법사',
    'DEFENDER': '방어수', 'HEALER': '힐러', 'SUPPORTER': '서포터',
}
BATTLE_LENGTH = 300
TODAY = date.today().isoformat()

# ── 파싱 유틸 ────────────────────────────────────────────────
def parse_dmg(eff: str) -> float:
    """DMG X.XXx * xNhit 총 배율."""
    mults = [float(m) for m in re.findall(r'DMG (\d+\.\d+)x', eff)]
    if not mults:
        return 0.0
    hits_m = re.search(r'x(\d+)hit', eff)
    hits = int(hits_m.group(1)) if hits_m else 1
    return mults[0] * hits + sum(mults[1:])

def parse_heal(eff: str) -> int:
    m = re.search(r'HEAL (\d+)%', eff)
    return int(m.group(1)) if m else 0

def parse_buffs(eff: str):
    """Return list of (stat, sign, value, is_pct, duration)."""
    result = []
    for m in re.finditer(r'(\w+)([+-])(\d+\.?\d*)(%?)\((\d+)T\)', eff):
        stat, sign, val, pct, dur = m.groups()
        result.append((stat, sign, float(val), bool(pct), int(dur)))
    return result

def parse_cc(eff: str):
    return [(m.group(1), int(m.group(2))) for m in re.finditer(r'CC:(\w+)\((\d+)T\)', eff)]

def parse_dot(eff: str):
    return [(m.group(1), int(m.group(2)), int(m.group(3)))
            for m in re.finditer(r'(burn|bleed|poison) (\d+)%\((\d+)T\)', eff)]

def parse_debuffs(eff: str):
    result = []
    for m in re.finditer(r'(\w+)-(\d+\.?\d*)(%?)\((\d+)T\)', eff):
        stat, val, pct, dur = m.groups()
        result.append((stat, float(val), bool(pct), int(dur)))
    return result

# ── 마크다운 빌더 ────────────────────────────────────────────
lines = []

def h(level: int, text: str):
    lines.append(f"{'#' * level} {text}")

def blank():
    lines.append('')

def text(s: str = ''):
    lines.append(s)

def table(headers: list, rows: list):
    """headers: list[str], rows: list[list]"""
    sep_row = ['---'] * len(headers)
    lines.append('| ' + ' | '.join(headers) + ' |')
    lines.append('| ' + ' | '.join(sep_row) + ' |')
    for row in rows:
        lines.append('| ' + ' | '.join(str(c) for c in row) + ' |')

# ═══════════════════════════════════════════════════════════
# 헤더
# ═══════════════════════════════════════════════════════════
h(1, 'BattleAgent 밸런스 분석 리포트')
blank()
text(f'> 분석 대상: {len(chars)}명 캐릭터 | 데이터: `_all_chars.json`')
text(f'> 생성일: {TODAY}')
blank()

# ═══════════════════════════════════════════════════════════
# 1. 역할 × 속성 분포
# ═══════════════════════════════════════════════════════════
h(2, '1. 역할 × 속성 분포')
blank()

role_elem: dict[str, dict[str, list]] = {r: {e: [] for e in ELEM_ORDER} for r in ROLE_ORDER}
for c in chars:
    role_elem[c['role']][c['element']].append(c['name'])

elem_kr_list = [ELEM_KR[e] for e in ELEM_ORDER]
headers = ['역할'] + elem_kr_list + ['합계']
rows = []
col_totals = {e: 0 for e in ELEM_ORDER}
for role in ROLE_ORDER:
    row = [ROLE_KR[role]]
    total = 0
    for elem in ELEM_ORDER:
        cnt = len(role_elem[role][elem])
        row.append(str(cnt))
        col_totals[elem] += cnt
        total += cnt
    row.append(f'**{total}**')
    rows.append(row)
rows.append(['**합계**'] + [f'**{col_totals[e]}**' for e in ELEM_ORDER] + [f'**{len(chars)}**'])
table(headers, rows)
blank()

# 공백 슬롯
gaps = [(ELEM_KR[e], ROLE_KR[r])
        for r in ROLE_ORDER for e in ELEM_ORDER if not role_elem[r][e]]
if gaps:
    text('**공백 슬롯** (해당 역할×속성 조합에 캐릭터 없음):')
    blank()
    for elem_kr, role_kr in gaps:
        text(f'- {elem_kr}/{role_kr}')
else:
    text('모든 역할×속성 조합에 캐릭터가 존재합니다.')
blank()

# 불균형 분석
text('**역할별 인원 불균형:**')
blank()
role_counts = {r: sum(len(role_elem[r][e]) for e in ELEM_ORDER) for r in ROLE_ORDER}
avg_role = len(chars) / len(ROLE_ORDER)
for role in ROLE_ORDER:
    cnt = role_counts[role]
    delta = cnt - avg_role
    flag = ' ← 과다' if delta > 3 else (' ← 부족' if delta < -3 else '')
    text(f'- {ROLE_KR[role]}: {cnt}명 (평균 대비 {delta:+.1f}){flag}')
blank()

# ═══════════════════════════════════════════════════════════
# 2. 성급별 분포
# ═══════════════════════════════════════════════════════════
h(2, '2. 성급별 분포')
blank()
text('> `_all_chars.json` 현재 버전에는 `star` 필드가 포함되지 않습니다.')
text('> 아래는 속성별/역할별 인원 분포입니다.')
blank()

# 속성별 분포 table
elem_role_rows = []
for elem in ELEM_ORDER:
    row = [ELEM_KR[elem]]
    total = 0
    for role in ROLE_ORDER:
        cnt = len(role_elem[role][elem])
        row.append(str(cnt))
        total += cnt
    row.append(f'**{total}**')
    elem_role_rows.append(row)

table(['속성'] + [ROLE_KR[r] for r in ROLE_ORDER] + ['합계'], elem_role_rows)
blank()

# ═══════════════════════════════════════════════════════════
# 3. 역할별 스탯 범위 분석
# ═══════════════════════════════════════════════════════════
h(2, '3. 역할별 스탯 범위 분석')
blank()

stat_fields = ['atk', 'def', 'hp', 'spd', 'sp']
stat_kr = {'atk': 'ATK', 'def': 'DEF', 'hp': 'HP', 'spd': 'SPD', 'sp': 'SP'}

# chars with stat data (atk > 0) — all 70 have it
stat_chars = [c for c in chars if c.get('atk', 0) > 0]
text(f'스탯 데이터 보유 캐릭터: {len(stat_chars)}명 / {len(chars)}명')
blank()

for role in ROLE_ORDER:
    rc = [c for c in stat_chars if c['role'] == role]
    if not rc:
        continue
    h(3, f'{ROLE_KR[role]} ({len(rc)}명)')
    blank()
    stat_rows = []
    for sf in stat_fields:
        vals = [c[sf] for c in rc]
        mn, mx, avg = min(vals), max(vals), sum(vals)/len(vals)
        stat_rows.append([stat_kr[sf], str(mn), str(mx), f'{avg:.1f}'])
    table(['스탯', '최소', '최대', '평균'], stat_rows)
    blank()

# ═══════════════════════════════════════════════════════════
# 4. 대미지 출력 분석
# ═══════════════════════════════════════════════════════════
h(2, '4. 대미지 출력 분석')
blank()

# 수집
all_skill_entries = []
for c in chars:
    for stype in ['normal', 'active', 'ultimate']:
        sk = c[stype]
        eff = sk['effects']
        mult = parse_dmg(eff)
        if mult > 0:
            all_skill_entries.append({
                'name': c['name'], 'role': c['role'], 'element': c['element'],
                'skill_type': stype, 'skill_name': sk['name'],
                'target': sk.get('target', ''),
                'multiplier': mult, 'raw_dmg': mult * c['atk'],
                'effects': eff,
            })

h(3, '4-1. 역할별 스킬 배율 평균')
blank()

avg_rows = []
for role in ROLE_ORDER:
    entries = [e for e in all_skill_entries if e['role'] == role]
    by_type = defaultdict(list)
    for e in entries:
        by_type[e['skill_type']].append(e['multiplier'])
    def avg_of(lst): return f'{sum(lst)/len(lst):.2f}' if lst else '-'
    avg_rows.append([
        ROLE_KR[role],
        avg_of(by_type['normal']),
        avg_of(by_type['active']),
        avg_of(by_type['ultimate']),
    ])
table(['역할', '일반(평균)', '액티브(평균)', '궁극기(평균)'], avg_rows)
blank()

h(3, '4-2. Top 10 단일 스킬 배율')
blank()

top10 = sorted(all_skill_entries, key=lambda x: x['multiplier'], reverse=True)[:10]
top10_rows = []
for i, e in enumerate(top10, 1):
    stype_kr = {'normal': '일반', 'active': '액티브', 'ultimate': '궁극기'}[e['skill_type']]
    top10_rows.append([str(i), e['name'], ROLE_KR[e['role']], e['skill_name'],
                       stype_kr, f'{e["multiplier"]:.2f}x', e['target']])
table(['#', '캐릭터', '역할', '스킬명', '타입', '배율', '대상'], top10_rows)
blank()

h(3, '4-3. Top AoE 궁극기 배율')
blank()

aoe_ults = sorted(
    [e for e in all_skill_entries
     if e['skill_type'] == 'ultimate' and 'ALL_ENEMY' in e['target']],
    key=lambda x: x['multiplier'], reverse=True
)
if aoe_ults:
    aoe_rows = []
    for i, e in enumerate(aoe_ults[:10], 1):
        extras = [p.strip() for p in e['effects'].split('|') if 'DMG' not in p]
        extra_str = ', '.join(extras) if extras else '-'
        aoe_rows.append([str(i), e['name'], ROLE_KR[e['role']], e['skill_name'],
                         f'{e["multiplier"]:.2f}x', extra_str])
    table(['#', '캐릭터', '역할', '스킬명', '배율', '부가효과'], aoe_rows)
else:
    text('AoE 궁극기 없음')
blank()

# ═══════════════════════════════════════════════════════════
# 5. 턴 이코노미
# ═══════════════════════════════════════════════════════════
h(2, '5. 턴 이코노미')
blank()
text(f'> BATTLE_LENGTH = {BATTLE_LENGTH} | 턴 간격 = {BATTLE_LENGTH} / SPD | 궁극기 충전 시간 = SP × (턴 간격)')
blank()

h(3, '5-1. 역할별 행동 사이클 (역할 대표값)')
blank()

# 역할별 평균 SPD/SP 계산
role_spd_avg: dict[str, float] = {}
role_sp_avg: dict[str, float] = {}
for role in ROLE_ORDER:
    rc = [c for c in chars if c['role'] == role]
    role_spd_avg[role] = sum(c['spd'] for c in rc) / len(rc)
    role_sp_avg[role]  = sum(c['sp']  for c in rc) / len(rc)

cycle_rows = []
for role in ROLE_ORDER:
    spd = role_spd_avg[role]
    sp  = role_sp_avg[role]
    interval = BATTLE_LENGTH / spd
    actions_per_10 = 10 / interval
    ult_charge = sp * interval
    cycle_rows.append([
        ROLE_KR[role],
        f'{spd:.0f}',
        f'{interval:.2f}',
        f'{actions_per_10:.2f}',
        f'{sp:.1f}',
        f'{ult_charge:.2f}',
    ])
table(['역할', '평균 SPD', '턴 간격', '10턴당 행동', '평균 SP', '궁극기 충전시간'], cycle_rows)
blank()

h(3, '5-2. 캐릭터별 추정 DPS (일반공격 기준 Top 15)')
blank()

dps_list = []
for c in chars:
    mult = parse_dmg(c['normal']['effects'])
    if mult > 0:
        interval = BATTLE_LENGTH / c['spd']
        dps_list.append({
            'name': c['name'], 'role': c['role'],
            'atk': c['atk'], 'spd': c['spd'],
            'mult': mult, 'dps': mult * c['atk'] / interval,
        })

dps_list.sort(key=lambda x: x['dps'], reverse=True)
dps_rows = []
for i, e in enumerate(dps_list[:15], 1):
    dps_rows.append([str(i), e['name'], ROLE_KR[e['role']],
                     str(e['atk']), str(e['spd']),
                     f'{e["mult"]:.2f}x', f'{e["dps"]:.1f}'])
table(['#', '캐릭터', '역할', 'ATK', 'SPD', '일반 배율', '추정 DPS'], dps_rows)
blank()

# ═══════════════════════════════════════════════════════════
# 6. 힐러 비교
# ═══════════════════════════════════════════════════════════
h(2, '6. 힐러 비교')
blank()

healers = [c for c in chars if c['role'] == 'HEALER']
heal_rows = []
for c in healers:
    a_heal = parse_heal(c['active']['effects'])
    u_heal = parse_heal(c['ultimate']['effects'])
    u_extras = [p.strip() for p in c['ultimate']['effects'].split('|') if 'HEAL' not in p]
    a_extras = [p.strip() for p in c['active']['effects'].split('|') if 'HEAL' not in p]
    extras = ', '.join(u_extras + a_extras) or '-'
    u_tgt = c['ultimate'].get('target', '')
    tgt_kr = '전체 아군' if 'ALL_ALLY' in u_tgt else '단일 아군'
    heal_rows.append([c['name'], ELEM_KR[c['element']],
                      f'{a_heal}%' if a_heal else '-',
                      f'{u_heal}%', tgt_kr, extras])

table(['캐릭터', '속성', '액티브 힐%', '궁극기 힐%', '궁극기 대상', '부가효과'], heal_rows)
blank()

# 팀 총 힐량 추정
text('**궁극기 팀 총 힐량 추정** (파티 평균 HP = 5,800, 4인 파티 기준):')
blank()
avg_hp = 5800
team_rows = []
for c in healers:
    u_heal = parse_heal(c['ultimate']['effects'])
    tgt = c['ultimate'].get('target', '')
    multiplier = 4 if 'ALL_ALLY' in tgt else 1
    total = u_heal / 100 * avg_hp * multiplier
    team_rows.append([c['name'], f'{u_heal}%',
                      '전체 아군' if multiplier == 4 else '단일 아군',
                      f'{total:,.0f}'])
table(['캐릭터', '힐%', '대상', '팀 총 힐량(추정)'], team_rows)
blank()

# ═══════════════════════════════════════════════════════════
# 7. 서포터 버프 강도 비교
# ═══════════════════════════════════════════════════════════
h(2, '7. 서포터 버프 강도 비교')
blank()
text('> 점수 = Σ(버프값 × 지속턴) + CLEANSE +20 + HEAL×0.5 + SP_INCREASE +30')
blank()

supporters = [c for c in chars if c['role'] == 'SUPPORTER']
sup_scores = []
for c in supporters:
    score = 0.0
    for stype in ['active', 'ultimate']:
        eff = c[stype]['effects']
        for stat, sign, val, is_pct, dur in parse_buffs(eff):
            if sign == '+':
                score += val * dur
        if 'CLEANSE' in eff: score += 20
        if 'HEAL' in eff:
            score += parse_heal(eff) * 0.5
        if 'SP_INCREASE' in eff: score += 30
    sup_scores.append({'name': c['name'], 'element': c['element'], 'score': score,
                       'a_eff': c['active']['effects'], 'u_eff': c['ultimate']['effects']})

sup_scores.sort(key=lambda x: x['score'], reverse=True)
avg_sup = sum(s['score'] for s in sup_scores) / len(sup_scores) if sup_scores else 0

sup_rows = []
for s in sup_scores:
    delta = s['score'] - avg_sup
    flag = ' HIGH' if delta > avg_sup * 0.5 else (' LOW' if delta < -avg_sup * 0.3 else '')
    sup_rows.append([s['name'], ELEM_KR[s['element']],
                     f'{s["score"]:.0f}', f'{delta:+.0f}', flag.strip() or '-'])
table(['캐릭터', '속성', '점수', 'Δ평균', '판정'], sup_rows)
blank()
text(f'평균 버프 점수: **{avg_sup:.1f}**')
blank()

# ═══════════════════════════════════════════════════════════
# 8. CC / DoT / 디버프 커버리지
# ═══════════════════════════════════════════════════════════
h(2, '8. CC / DoT / 디버프 커버리지')
blank()

cc_all, dot_all, debuff_all = [], [], []
for c in chars:
    for stype in ['normal', 'active', 'ultimate']:
        eff = c[stype]['effects']
        tgt = c[stype].get('target', '')
        for cc_type, dur in parse_cc(eff):
            cc_all.append({'name': c['name'], 'role': c['role'], 'element': c['element'],
                           'stype': stype, 'cc_type': cc_type, 'dur': dur, 'target': tgt})
        for dot_type, val, dur in parse_dot(eff):
            dot_all.append({'name': c['name'], 'role': c['role'], 'element': c['element'],
                            'stype': stype, 'dot_type': dot_type, 'val': val, 'dur': dur})
        for stat, val, is_pct, dur in parse_debuffs(eff):
            debuff_all.append({'name': c['name'], 'role': c['role'], 'element': c['element'],
                               'stype': stype, 'stat': stat, 'val': val,
                               'is_pct': is_pct, 'dur': dur})

stype_kr = {'normal': '일반', 'active': '액티브', 'ultimate': '궁극기'}

h(3, '8-1. CC 보유 캐릭터')
blank()
if cc_all:
    cc_rows = []
    for e in sorted(cc_all, key=lambda x: x['cc_type']):
        cc_rows.append([e['name'], ROLE_KR[e['role']], e['cc_type'],
                        f'{e["dur"]}T', stype_kr[e['stype']], e['target']])
    table(['캐릭터', '역할', 'CC 유형', '지속', '스킬', '대상'], cc_rows)
    blank()
    cc_count = Counter(e['cc_type'] for e in cc_all)
    text('CC 유형별 횟수: ' + ', '.join(f'{k}: {v}' for k, v in cc_count.most_common()))
else:
    text('CC 스킬 없음')
blank()

h(3, '8-2. DoT 보유 캐릭터')
blank()
if dot_all:
    dot_rows = []
    for e in sorted(dot_all, key=lambda x: x['dot_type']):
        dot_rows.append([e['name'], ROLE_KR[e['role']], e['dot_type'],
                         f'{e["val"]}%', f'{e["dur"]}T', stype_kr[e['stype']]])
    table(['캐릭터', '역할', 'DoT 유형', '비율', '지속', '스킬'], dot_rows)
    blank()
    dot_count = Counter(e['dot_type'] for e in dot_all)
    text('DoT 유형별 횟수: ' + ', '.join(f'{k}: {v}' for k, v in dot_count.most_common()))
else:
    text('DoT 스킬 없음')
blank()

h(3, '8-3. 스탯 디버프 보유 캐릭터')
blank()
if debuff_all:
    db_rows = []
    for e in sorted(debuff_all, key=lambda x: x['stat']):
        val_str = f'-{e["val"]:.0f}%' if e['is_pct'] else f'-{e["val"]:.0f}'
        db_rows.append([e['name'], ROLE_KR[e['role']], e['stat'],
                        val_str, f'{e["dur"]}T', stype_kr[e['stype']]])
    table(['캐릭터', '역할', '스탯', '감소량', '지속', '스킬'], db_rows)
else:
    text('스탯 디버프 없음')
blank()

# ═══════════════════════════════════════════════════════════
# 9. 종합 밸런스 이슈
# ═══════════════════════════════════════════════════════════
h(2, '9. 종합 밸런스 이슈')
blank()

issues = []

# (A) 궁극기 배율 이상치 (역할 내 ±1.5σ)
role_ult_entries = defaultdict(list)
for e in all_skill_entries:
    if e['skill_type'] == 'ultimate':
        role_ult_entries[e['role']].append(e)

for role in ROLE_ORDER:
    entries = role_ult_entries[role]
    if len(entries) < 2:
        continue
    mults = [e['multiplier'] for e in entries]
    avg = sum(mults) / len(mults)
    std = (sum((m - avg)**2 for m in mults) / len(mults)) ** 0.5
    if std == 0:
        continue
    for e in entries:
        dev = (e['multiplier'] - avg) / std
        if abs(dev) > 1.5:
            severity = 'HIGH' if abs(dev) > 2.0 else 'MEDIUM'
            label = '이상치(강)' if dev > 0 else '이상치(약)'
            issues.append({'severity': severity, 'type': 'ULT_OUTLIER',
                           'char': e['name'], 'role': ROLE_KR[role],
                           'detail': f'궁극기 배율 {e["multiplier"]:.2f}x (역할 평균 {avg:.2f}x, {dev:+.1f}σ) — {label}'})

# (B) 서포터 버프 이상치
for s in sup_scores:
    delta = s['score'] - avg_sup
    if delta > avg_sup * 0.5:
        issues.append({'severity': 'HIGH', 'type': 'SUPPORT_OP',
                       'char': s['name'], 'role': '서포터',
                       'detail': f'버프 점수 {s["score"]:.0f} (평균 {avg_sup:.0f}, +{delta:.0f})'})
    elif avg_sup > 0 and delta < -avg_sup * 0.3:
        issues.append({'severity': 'MEDIUM', 'type': 'SUPPORT_WEAK',
                       'char': s['name'], 'role': '서포터',
                       'detail': f'버프 점수 {s["score"]:.0f} (평균 {avg_sup:.0f}, {delta:.0f})'})

# (C) 역할 분포 불균형
for role, cnt in role_counts.items():
    delta = cnt - avg_role
    if delta > 4:
        issues.append({'severity': 'MEDIUM', 'type': 'ROLE_IMBALANCE',
                       'char': ROLE_KR[role], 'role': ROLE_KR[role],
                       'detail': f'{cnt}명 (평균 {avg_role:.1f}, +{delta:.0f}) — 과다'})
    elif delta < -4:
        issues.append({'severity': 'MEDIUM', 'type': 'ROLE_IMBALANCE',
                       'char': ROLE_KR[role], 'role': ROLE_KR[role],
                       'detail': f'{cnt}명 (평균 {avg_role:.1f}, {delta:.0f}) — 부족'})

# (D) 공백 슬롯
if gaps:
    issues.append({'severity': 'MEDIUM', 'type': 'COVERAGE_GAP',
                   'char': '구조', 'role': '전체',
                   'detail': f'역할×속성 공백 {len(gaps)}개: {", ".join(f"{e}/{r}" for e,r in gaps[:5])}{"..." if len(gaps)>5 else ""}'})

# (E) 단일/AoE 비율
for role in ['ATTACKER', 'MAGICIAN']:
    entries = role_ult_entries[role]
    single = [e for e in entries if 'ALL_ENEMY' not in e['target']]
    aoe    = [e for e in entries if 'ALL_ENEMY' in e['target']]
    if single and aoe:
        s_avg = sum(e['multiplier'] for e in single) / len(single)
        a_avg = sum(e['multiplier'] for e in aoe)    / len(aoe)
        ratio = s_avg / a_avg if a_avg else 0
        if ratio < 1.3 or ratio > 3.5:
            issues.append({'severity': 'MEDIUM', 'type': 'AOE_RATIO',
                           'char': ROLE_KR[role], 'role': ROLE_KR[role],
                           'detail': f'단일/AoE 비율 {ratio:.2f} (권장 1.5~2.5)'})

# 출력
high_issues = [i for i in issues if i['severity'] == 'HIGH']
med_issues  = [i for i in issues if i['severity'] == 'MEDIUM']

if high_issues:
    text(f'### HIGH 이슈 ({len(high_issues)}건)')
    blank()
    for i, iss in enumerate(high_issues, 1):
        text(f'{i}. **[{iss["type"]}]** {iss["char"]} ({iss["role"]}) — {iss["detail"]}')
    blank()

if med_issues:
    text(f'### MEDIUM 이슈 ({len(med_issues)}건)')
    blank()
    for i, iss in enumerate(med_issues, 1):
        text(f'{i}. **[{iss["type"]}]** {iss["char"]} ({iss["role"]}) — {iss["detail"]}')
    blank()

if not issues:
    text('현재 탐지된 주요 밸런스 이슈 없음.')
    blank()

text(f'> 총 {len(issues)}건 (HIGH={len(high_issues)}, MEDIUM={len(med_issues)})')
blank()

# ═══════════════════════════════════════════════════════════
# 10. 데이터 커버리지 현황
# ═══════════════════════════════════════════════════════════
h(2, '10. 데이터 커버리지 현황')
blank()

def is_placeholder(eff: str) -> bool:
    return not eff or eff.strip() in ('-', 'TBD', '') or re.match(r'^(없음|미정|placeholder)$', eff.strip(), re.I) is not None

full_data, partial, placeholder_only = 0, 0, 0
coverage_rows = []
for c in chars:
    effs = [c[st]['effects'] for st in ['normal', 'active', 'ultimate']]
    filled = sum(1 for e in effs if not is_placeholder(e))
    has_dmg = any(parse_dmg(e) > 0 for e in effs)
    has_heal = any(parse_heal(e) > 0 for e in effs)
    if filled == 3:
        status = '완전'
        full_data += 1
    elif filled > 0:
        status = f'부분({filled}/3)'
        partial += 1
    else:
        status = '플레이스홀더'
        placeholder_only += 1
    coverage_rows.append([c['name'], ROLE_KR[c['role']], ELEM_KR[c['element']],
                           status,
                           'Y' if has_dmg else '-',
                           'Y' if has_heal else '-'])

table(['캐릭터', '역할', '속성', '스킬 데이터', '대미지', '힐'], coverage_rows)
blank()

text(f'- **완전** (3/3 스킬 데이터): {full_data}명')
text(f'- **부분** (1~2 스킬): {partial}명')
text(f'- **플레이스홀더**: {placeholder_only}명')
text(f'- **총 대미지 스킬 보유**: {sum(1 for c in chars if any(parse_dmg(c[st]["effects"])>0 for st in ["normal","active","ultimate"]))}명')
text(f'- **총 힐 스킬 보유**: {sum(1 for c in chars if any(parse_heal(c[st]["effects"])>0 for st in ["normal","active","ultimate"]))}명')
blank()

# ── 파일 쓰기 ────────────────────────────────────────────────
OUT.parent.mkdir(parents=True, exist_ok=True)
with open(OUT, 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines) + '\n')

print(f'리포트 생성 완료: {OUT}')
print(f'총 라인 수: {len(lines)}')
