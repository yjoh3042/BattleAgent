"""전체 캐릭터(70명) 스킬 기획서 PDF 생성"""
import sys, os, json, re
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor, white, black
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, KeepTogether
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors

# === Font ===
for fp, fn in [('C:/Windows/Fonts/malgun.ttf','Malgun'),('C:/Windows/Fonts/malgunbd.ttf','MalgunBold')]:
    if os.path.exists(fp): pdfmetrics.registerFont(TTFont(fn, fp))
F, FB = 'Malgun', 'MalgunBold'

# === Colors per Element ===
ELEM_COLORS = {
    'FIRE':   {'hdr': '#D32F2F', 'bg': '#FFEBEE', 'bg2': '#FFCDD2', 'accent': '#F44336'},
    'WATER':  {'hdr': '#1565C0', 'bg': '#E3F2FD', 'bg2': '#BBDEFB', 'accent': '#2196F3'},
    'FOREST': {'hdr': '#2E7D32', 'bg': '#E8F5E9', 'bg2': '#C8E6C9', 'accent': '#4CAF50'},
    'LIGHT':  {'hdr': '#F9A825', 'bg': '#FFFDE7', 'bg2': '#FFF9C4', 'accent': '#FFC107'},
    'DARK':   {'hdr': '#4A148C', 'bg': '#F3E5F5', 'bg2': '#E1BEE7', 'accent': '#9C27B0'},
}
ELEM_KR = {'FIRE':'화','WATER':'수','FOREST':'목','LIGHT':'광','DARK':'암'}
ROLE_KR = {'ATTACKER':'공격자','MAGICIAN':'마법사','HEALER':'힐러','DEFENDER':'방어자','SUPPORTER':'서포터'}
ELEM_ORDER = {'FIRE':0,'WATER':1,'FOREST':2,'LIGHT':3,'DARK':4}
ROLE_ORDER = {'ATTACKER':0,'MAGICIAN':1,'HEALER':2,'DEFENDER':3,'SUPPORTER':4}

C_BORDER = HexColor('#BDBDBD')

# === Styles ===
def ps(name, sz=9, clr=black, al=TA_LEFT, bold=False, ld=None):
    return ParagraphStyle(name, fontName=FB if bold else F, fontSize=sz,
        textColor=clr, alignment=al, leading=ld or sz+3, wordWrap='CJK')

S_TITLE   = ps('T', 22, HexColor('#1565C0'), TA_CENTER, True, 28)
S_SUBTITLE= ps('ST', 11, HexColor('#555'), TA_CENTER)
S_H1      = ps('H1', 16, HexColor('#1565C0'), bold=True, ld=22)
S_H2      = ps('H2', 13, bold=True, ld=18)
S_BODY    = ps('B', 9)
S_BODYC   = ps('BC', 9, al=TA_CENTER)
S_BODYB   = ps('BB', 9, bold=True)
S_BODYBC  = ps('BBC', 9, al=TA_CENTER, bold=True)
S_SMALL   = ps('SM', 7.5, HexColor('#666'))
S_SMALLC  = ps('SMC', 7.5, HexColor('#666'), TA_CENTER)

def p(t, s=S_BODY): return Paragraph(str(t), s)

# === Load Data ===
with open('data/_all_chars.json', encoding='utf-8') as f:
    chars = json.load(f)

# Group by element
from collections import OrderedDict
by_elem = OrderedDict()
for elem in ['FIRE','WATER','FOREST','LIGHT','DARK']:
    by_elem[elem] = [c for c in chars if c['element'] == elem]

# === Build PDF ===
out = 'data/전체_캐릭터_스킬_기획서.pdf'
doc = SimpleDocTemplate(out, pagesize=A4,
    leftMargin=14*mm, rightMargin=14*mm, topMargin=16*mm, bottomMargin=16*mm,
    title='BattleAgent 전체 캐릭터 스킬 기획서', author='BattleAgent Design Team')

story = []
W = doc.width

# ============================================================
# COVER PAGE
# ============================================================
story.append(Spacer(1, 35*mm))
story.append(p('BattleAgent', ps('ct', 28, HexColor('#333'), TA_CENTER, True, 34)))
story.append(p('전체 캐릭터 스킬 기획서', S_TITLE))
story.append(Spacer(1, 8*mm))
story.append(p(f'총 {len(chars)}명  |  5속성  |  5역할', S_SUBTITLE))
story.append(Spacer(1, 12*mm))

# 속성별 요약
sum_data = [[p('속성', S_BODYBC), p('캐릭터 수', S_BODYBC), p('구성', S_BODYBC)]]
for elem, clist in by_elem.items():
    roles = {}
    for c in clist:
        rk = ROLE_KR[c['role']]
        roles[rk] = roles.get(rk, 0) + 1
    role_str = ', '.join(f'{r} {n}명' for r, n in roles.items())
    ec = ELEM_COLORS[elem]
    sum_data.append([
        p(f"{ELEM_KR[elem]} ({elem})", ps(f'e{elem}', 10, HexColor(ec['hdr']), TA_CENTER, True)),
        p(str(len(clist)), S_BODYBC),
        p(role_str, S_BODYC)
    ])
cw_sum = [W*0.25, W*0.15, W*0.5]
t_sum = Table(sum_data, colWidths=cw_sum)
t_sum_style = [
    ('BACKGROUND', (0,0), (-1,0), HexColor('#37474F')),
    ('TEXTCOLOR', (0,0), (-1,0), white),
    ('GRID', (0,0), (-1,-1), 0.5, C_BORDER),
    ('ALIGN', (0,0), (-1,-1), 'CENTER'),
    ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ('FONTNAME', (0,0), (-1,-1), F),
    ('TOPPADDING', (0,0), (-1,-1), 5),
    ('BOTTOMPADDING', (0,0), (-1,-1), 5),
]
for i, elem in enumerate(['FIRE','WATER','FOREST','LIGHT','DARK'], 1):
    t_sum_style.append(('BACKGROUND', (0,i), (-1,i), HexColor(ELEM_COLORS[elem]['bg'])))
t_sum.setStyle(TableStyle(t_sum_style))
story.append(t_sum)

story.append(Spacer(1, 15*mm))
story.append(p('BattleAgent Design Team  |  2026.03', ps('ft', 10, HexColor('#999'), TA_CENTER)))

# ============================================================
# TABLE OF CONTENTS
# ============================================================
story.append(PageBreak())
story.append(p('목차', ps('toc_h', 18, HexColor('#333'), TA_CENTER, True, 24)))
story.append(Spacer(1, 6*mm))

toc_data = [[p('No.', S_BODYBC), p('ID', S_BODYBC), p('이름', S_BODYBC),
             p('속성', S_BODYBC), p('역할', S_BODYBC), p('ATK', S_BODYBC),
             p('HP', S_BODYBC), p('SPD', S_BODYBC)]]
for i, c in enumerate(chars, 1):
    ec = ELEM_COLORS[c['element']]
    toc_data.append([
        p(str(i), S_SMALLC), p(c['id'], S_SMALLC), p(c['name'], ps(f'n{i}', 8, al=TA_CENTER, bold=True)),
        p(ELEM_KR[c['element']], ps(f'e{i}', 8, HexColor(ec['hdr']), TA_CENTER, True)),
        p(ROLE_KR[c['role']], S_SMALLC),
        p(f"{c['atk']:.0f}", S_SMALLC), p(f"{c['hp']:.0f}", S_SMALLC), p(f"{c['spd']:.0f}", S_SMALLC),
    ])
cw_toc = [W*0.06, W*0.09, W*0.15, W*0.09, W*0.12, W*0.09, W*0.09, W*0.09]
t_toc = Table(toc_data, colWidths=cw_toc, repeatRows=1)
toc_style = [
    ('BACKGROUND', (0,0), (-1,0), HexColor('#37474F')),
    ('TEXTCOLOR', (0,0), (-1,0), white),
    ('GRID', (0,0), (-1,-1), 0.4, HexColor('#E0E0E0')),
    ('ALIGN', (0,0), (-1,-1), 'CENTER'),
    ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ('FONTNAME', (0,0), (-1,-1), F),
    ('FONTSIZE', (0,0), (-1,-1), 8),
    ('TOPPADDING', (0,0), (-1,-1), 2.5),
    ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
]
for i, c in enumerate(chars, 1):
    bg = HexColor(ELEM_COLORS[c['element']]['bg']) if i%2==1 else white
    toc_style.append(('BACKGROUND', (0,i), (-1,i), bg))
t_toc.setStyle(TableStyle(toc_style))
story.append(t_toc)

# ============================================================
# ELEMENT SECTION PAGES
# ============================================================
TARGET_DESC = {
    'ENEMY_NEAR': '가장 가까운 적 1명',
    'ENEMY_LOWEST_HP': 'HP가 가장 낮은 적',
    'ENEMY_RANDOM': '무작위 적 1명',
    'ENEMY_RANDOM_2': '무작위 적 2명',
    'ENEMY_RANDOM_3': '무작위 적 3명',
    'ENEMY_NEAR_ROW': '가장 가까운 적 열',
    'ENEMY_NEAR_CROSS': '가장 가까운 적 십자 범위',
    'ENEMY_BACK_ROW': '적 후열',
    'ENEMY_SAME_COL': '같은 열 적',
    'ALL_ENEMY': '적 전체',
    'ALL_ALLY': '아군 전체',
    'ALLY_LOWEST_HP': 'HP가 가장 낮은 아군 1명',
    'ALLY_LOWEST_HP_2': 'HP가 가장 낮은 아군 2명',
    'ALLY_HIGHEST_ATK': 'ATK가 가장 높은 아군',
    'SELF': '자기 자신',
}

def describe_skill_kr(name, target, effects, skill_type):
    """스킬 효과를 한글 문장으로 변환"""
    tgt = TARGET_DESC.get(target, target)
    parts = [p_str.strip() for p_str in effects.split('|')]
    sentences = []

    for part in parts:
        part = part.strip()
        # DMG patterns
        if part.startswith('DMG '):
            rest = part[4:]
            # Multi-hit: "2.50x x3hit"
            if 'x' in rest and 'hit' in rest:
                tokens = rest.split()
                mult = tokens[0].replace('x', '')
                hits = tokens[1].replace('x', '').replace('hit', '')
                pct = int(float(mult) * 100)
                sentences.append(f'{tgt}에게 공격력의 {pct}% 대미지를 {hits}회 적중시킵니다')
            # Conditional: "3.50x (HP<30%)"
            elif '(HP<' in rest:
                tokens = rest.split('(HP<')
                base_mult = tokens[0].strip().replace('x', '')
                hp_thresh = tokens[1].replace(')', '').replace('%', '')
                pct = int(float(base_mult) * 100)
                sentences.append(f'대상 HP가 {hp_thresh}% 미만일 때 추가로 {pct}% 대미지를 가합니다')
            else:
                mult = rest.strip().replace('x', '')
                try:
                    pct = int(float(mult) * 100)
                    sentences.append(f'{tgt}에게 공격력의 {pct}% 대미지를 가합니다')
                except ValueError:
                    sentences.append(f'{tgt}에게 대미지를 가합니다')

        # HEAL
        elif part.startswith('HEAL '):
            val = part[5:].replace('%', '').strip()
            sentences.append(f'{tgt}의 HP를 {val}% 회복합니다')

        # CC patterns
        elif part.startswith('CC:'):
            cc_map = {'STUN': '기절', 'SLEEP': '수면', 'FREEZE': '빙결', 'STONE': '석화', 'PANIC': '공포'}
            m = re.match(r'CC:(\w+)\((\d+)T\)', part)
            if m:
                cc_type = cc_map.get(m.group(1), m.group(1))
                dur = m.group(2)
                sentences.append(f'{dur}턴간 {cc_type} 상태이상을 부여합니다')

        # DoT: burn/poison/bleed
        elif 'burn' in part:
            m = re.match(r'burn (\d+)%\((\d+)T\)', part)
            if m:
                sentences.append(f'{m.group(1)}% 위력의 화상을 {m.group(2)}턴간 부여합니다')

        elif 'poison' in part:
            m = re.match(r'poison (\d+)%\((\d+)T\)', part)
            if m:
                sentences.append(f'{m.group(1)}% 위력의 중독을 {m.group(2)}턴간 부여합니다')

        elif 'bleed' in part:
            m = re.match(r'bleed (\d+)%\((\d+)T\)', part)
            if m:
                sentences.append(f'{m.group(1)}% 위력의 출혈을 {m.group(2)}턴간 부여합니다')

        # Stat buffs: atk+20%(2T), def_+15%(2T), spd+15(2T)
        elif re.match(r'(atk|def_|spd|acc|cri_ratio|cri_dmg_ratio)[+-]', part):
            stat_map = {'atk': '공격력', 'def_': '방어력', 'spd': '속도', 'acc': '적중률',
                        'cri_ratio': '치명타 확률', 'cri_dmg_ratio': '치명타 피해'}
            m = re.match(r'(\w+?)([+-])(\d+)(%?)\((\d+)T\)', part)
            if m:
                stat = stat_map.get(m.group(1), m.group(1))
                sign = '증가' if m.group(2) == '+' else '감소'
                val = m.group(3)
                is_pct = m.group(4) == '%'
                dur = m.group(5)
                if val == '0':
                    sentences.append(f'{dur}턴간 {stat} 상승 효과를 부여합니다')
                elif is_pct:
                    sentences.append(f'{dur}턴간 {stat}을(를) {val}% {sign}시킵니다')
                else:
                    sentences.append(f'{dur}턴간 {stat}을(를) {val}만큼 {sign}시킵니다')

        # BARRIER
        elif part == 'BARRIER':
            sentences.append('보호막을 생성합니다')

        # TAUNT
        elif part.startswith('TAUNT'):
            sentences.append('도발 상태를 부여하여 적의 공격을 집중시킵니다')

        # COUNTER
        elif part == 'COUNTER':
            sentences.append('반격 태세를 갖춥니다')

        # CLEANSE
        elif part == 'CLEANSE':
            sentences.append('디버프를 해제합니다')

        # REVIVE
        elif part.startswith('REVIVE'):
            m = re.match(r'REVIVE (\d+)%', part)
            if m:
                sentences.append(f'쓰러진 아군을 HP {m.group(1)}%로 부활시킵니다')

        # SP_INCREASE
        elif part == 'SP_INCREASE':
            sentences.append('SP를 1 회복합니다')

    return '. '.join(sentences) + '.' if sentences else effects


def make_char_block(c, idx, total_w):
    """캐릭터 1명 상세 블록 생성"""
    ec = ELEM_COLORS[c['element']]
    hdr_c = HexColor(ec['hdr'])
    bg_c = HexColor(ec['bg'])
    bg2_c = HexColor(ec['bg2'])

    elements = []

    # --- Header bar ---
    h_style = ps(f'ch{c["id"]}', 14, white, TA_LEFT, True, 18)
    elem_str = ELEM_KR[c['element']]
    role_str = ROLE_KR[c['role']]
    hdr_data = [[
        p(f'  {c["name"]}', h_style),
        p(f'{c["id"]}', ps(f'ci{c["id"]}', 9, HexColor('#EEEEEE'), TA_CENTER)),
        p(f'{elem_str} / {role_str}', ps(f'cr{c["id"]}', 10, white, TA_CENTER, True)),
    ]]
    t_h = Table(hdr_data, colWidths=[total_w*0.4, total_w*0.2, total_w*0.4])
    t_h.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), hdr_c),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
    ]))
    elements.append(t_h)

    # --- Stats ---
    cri_str = f'{c["cri"]:.0%}' if c["cri"] != 0.15 else '15%'
    pen_str = f'{c["pen"]:.0%}' if c["pen"] > 0 else '0%'

    stat_data = [
        [p('ATK', S_BODYBC), p(f'{c["atk"]:.0f}', S_BODYBC),
         p('DEF', S_BODYBC), p(f'{c["def"]:.0f}', S_BODYBC),
         p('HP', S_BODYBC), p(f'{c["hp"]:.0f}', S_BODYBC),
         p('SPD', S_BODYBC), p(f'{c["spd"]:.0f}', S_BODYBC),
         p('CRI', S_BODYBC), p(cri_str, S_BODYBC),
         p('PEN', S_BODYBC), p(pen_str, S_BODYBC),
         p('SP', S_BODYBC), p(str(c["sp"]), S_BODYBC)],
    ]
    cw_st = [total_w*0.055]*14
    t_st = Table(stat_data, colWidths=cw_st)
    st_style = [
        ('GRID', (0,0), (-1,-1), 0.4, C_BORDER),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('FONTNAME', (0,0), (-1,-1), F),
        ('FONTSIZE', (0,0), (-1,-1), 8),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
    ]
    # label cells
    for col in range(0, 14, 2):
        st_style.append(('BACKGROUND', (col, 0), (col, 0), bg2_c))
        st_style.append(('FONTNAME', (col, 0), (col, 0), FB))
    for col in range(1, 14, 2):
        st_style.append(('BACKGROUND', (col, 0), (col, 0), bg_c))
    # Highlight exceptional stats
    atk_val = c['atk']
    if atk_val >= 450: st_style.append(('TEXTCOLOR', (1,0), (1,0), HexColor('#D32F2F')))
    if c['cri'] >= 0.25: st_style.append(('TEXTCOLOR', (9,0), (9,0), HexColor('#D32F2F')))
    if c['pen'] >= 0.15: st_style.append(('TEXTCOLOR', (11,0), (11,0), HexColor('#D32F2F')))

    t_st.setStyle(TableStyle(st_style))
    elements.append(t_st)

    # --- Skills ---
    sk_data = [
        [p('스킬', S_BODYBC), p('이름', S_BODYBC), p('대상', S_BODYBC), p('효과', S_BODYBC)],
    ]
    sk_descs = []  # 문장 설명 저장
    for stype, skey in [('Normal','normal'), ('Active','active'), ('Ultimate','ultimate')]:
        sk = c[skey]
        tgt_kr = sk['target'].replace('ENEMY_NEAR','적1').replace('ENEMY_LOWEST_HP','적최저HP') \
            .replace('ENEMY_RANDOM','적랜덤').replace('ALL_ENEMY','적전체') \
            .replace('ALL_ALLY','아군전체').replace('SELF','자신') \
            .replace('ALLY_LOWEST_HP','아군최저HP')
        eff_txt = sk['effects']
        # Make it more readable
        eff_txt = eff_txt.replace('DMG ','').replace('HEAL ','힐').replace('CLEANSE','정화') \
            .replace('SP_INCREASE','SP+1').replace('COUNTER','반격') \
            .replace('TAUNT','도발').replace('REVIVE','부활').replace('SHIELD','보호막')
        sk_data.append([
            p(stype, ps(f'sk{c["id"]}{stype}', 8, hdr_c, TA_CENTER, True)),
            p(sk['name'], ps(f'sn{c["id"]}{stype}', 8, al=TA_CENTER, bold=True)),
            p(tgt_kr, S_SMALLC),
            p(eff_txt, ps(f'se{c["id"]}{stype}', 8)),
        ])
        # 문장 설명 생성
        desc_text = describe_skill_kr(sk['name'], sk['target'], sk['effects'], stype)
        sk_descs.append((stype, desc_text))

    cw_sk = [total_w*0.1, total_w*0.2, total_w*0.12, total_w*0.58]
    t_sk = Table(sk_data, colWidths=cw_sk)
    sk_style = [
        ('BACKGROUND', (0,0), (-1,0), HexColor('#455A64')),
        ('TEXTCOLOR', (0,0), (-1,0), white),
        ('GRID', (0,0), (-1,-1), 0.4, C_BORDER),
        ('ALIGN', (0,0), (2,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('FONTNAME', (0,0), (-1,-1), F),
        ('FONTSIZE', (0,0), (-1,-1), 8),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING', (3,1), (3,-1), 5),
    ]
    for i in range(1, 4):
        bg = bg_c if i%2==1 else white
        sk_style.append(('BACKGROUND', (0,i), (-1,i), bg))
    t_sk.setStyle(TableStyle(sk_style))
    elements.append(t_sk)

    # 문장 설명 테이블 추가
    desc_data = []
    for stype, desc_text in sk_descs:
        desc_data.append([
            p(stype, ps(f'dt{c["id"]}{stype}', 7.5, HexColor('#666666'), TA_CENTER, True)),
            p(desc_text, ps(f'dd{c["id"]}{stype}', 7.5, HexColor('#333333'))),
        ])
    cw_desc = [total_w * 0.1, total_w * 0.9]
    t_desc = Table(desc_data, colWidths=cw_desc)
    desc_style_cmds = [
        ('GRID', (0,0), (-1,-1), 0.3, HexColor('#E0E0E0')),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('FONTNAME', (0,0), (-1,-1), F),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('LEFTPADDING', (1,0), (1,-1), 5),
        ('BACKGROUND', (0,0), (0,-1), HexColor('#F5F5F5')),
    ]
    for i in range(len(desc_data)):
        bg = HexColor(ELEM_COLORS[c['element']]['bg']) if i % 2 == 0 else white
        desc_style_cmds.append(('BACKGROUND', (1,i), (1,i), bg))
    t_desc.setStyle(TableStyle(desc_style_cmds))
    elements.append(t_desc)
    elements.append(Spacer(1, 4*mm))

    return KeepTogether(elements)

# Generate per-element sections
for elem, clist in by_elem.items():
    ec = ELEM_COLORS[elem]
    story.append(PageBreak())

    # Element section header
    elem_kr = ELEM_KR[elem]
    sect_style = ps(f'sect_{elem}', 20, HexColor(ec['hdr']), TA_CENTER, True, 26)
    story.append(p(f'{elem_kr} ({elem}) 속성  —  {len(clist)}명', sect_style))
    story.append(Spacer(1, 2*mm))

    # Divider line
    div_data = [['']]
    t_div = Table(div_data, colWidths=[W])
    t_div.setStyle(TableStyle([
        ('LINEABOVE', (0,0), (-1,0), 2, HexColor(ec['hdr'])),
        ('TOPPADDING', (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(t_div)
    story.append(Spacer(1, 4*mm))

    for c in clist:
        story.append(make_char_block(c, 0, W))

# ============================================================
# APPENDIX: STAT COMPARISON TABLES
# ============================================================
story.append(PageBreak())
story.append(p('부록: 전체 스탯 비교표', ps('app_h', 18, HexColor('#333'), TA_CENTER, True, 24)))
story.append(Spacer(1, 4*mm))

# ATK ranking
story.append(p('ATK 랭킹 (상위 15)', ps('rk1', 12, bold=True, ld=16)))
story.append(Spacer(1, 2*mm))

atk_sorted = sorted(chars, key=lambda c: -c['atk'])[:15]
atk_data = [[p('#', S_BODYBC), p('이름', S_BODYBC), p('속성', S_BODYBC), p('역할', S_BODYBC),
             p('ATK', S_BODYBC), p('CRI', S_BODYBC), p('PEN', S_BODYBC), p('비고', S_BODYBC)]]
for i, c in enumerate(atk_sorted, 1):
    ec = ELEM_COLORS[c['element']]
    is_op = c['id'] in ('c600','c601')
    ns = ps(f'ar{i}', 8.5, al=TA_CENTER, bold=is_op)
    atk_data.append([
        p(str(i), S_SMALLC),
        p(c['name'], ns),
        p(ELEM_KR[c['element']], ps(f'ae{i}', 8, HexColor(ec['hdr']), TA_CENTER, True)),
        p(ROLE_KR[c['role']], S_SMALLC),
        p(f"{c['atk']:.0f}", ps(f'av{i}', 9, al=TA_CENTER, bold=True)),
        p(f"{c['cri']:.0%}", S_SMALLC),
        p(f"{c['pen']:.0%}", S_SMALLC),
        p('OP' if is_op else '', ps(f'ao{i}', 8, HexColor('#D32F2F'), TA_CENTER, True)),
    ])
cw_rk = [W*0.05, W*0.13, W*0.08, W*0.12, W*0.1, W*0.08, W*0.08, W*0.08]
t_atk = Table(atk_data, colWidths=cw_rk, repeatRows=1)
atk_style = [
    ('BACKGROUND', (0,0), (-1,0), HexColor('#D32F2F')),
    ('TEXTCOLOR', (0,0), (-1,0), white),
    ('GRID', (0,0), (-1,-1), 0.4, HexColor('#E0E0E0')),
    ('ALIGN', (0,0), (-1,-1), 'CENTER'),
    ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ('FONTNAME', (0,0), (-1,-1), F),
    ('FONTSIZE', (0,0), (-1,-1), 8),
    ('TOPPADDING', (0,0), (-1,-1), 2.5),
    ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
]
for i in range(1, len(atk_data)):
    c = atk_sorted[i-1]
    bg = HexColor(ELEM_COLORS[c['element']]['bg']) if i%2==1 else white
    atk_style.append(('BACKGROUND', (0,i), (-1,i), bg))
    if c['id'] in ('c600','c601'):
        atk_style.append(('BACKGROUND', (0,i), (-1,i), HexColor('#FFF9C4')))
t_atk.setStyle(TableStyle(atk_style))
story.append(t_atk)

story.append(Spacer(1, 6*mm))

# HP ranking
story.append(p('HP 랭킹 (상위 10)', ps('rk2', 12, bold=True, ld=16)))
story.append(Spacer(1, 2*mm))

hp_sorted = sorted(chars, key=lambda c: -c['hp'])[:10]
hp_data = [[p('#', S_BODYBC), p('이름', S_BODYBC), p('속성', S_BODYBC), p('역할', S_BODYBC),
            p('HP', S_BODYBC), p('DEF', S_BODYBC), p('비고', S_BODYBC)]]
for i, c in enumerate(hp_sorted, 1):
    ec = ELEM_COLORS[c['element']]
    is_op = c['id'] in ('c600','c601')
    hp_data.append([
        p(str(i), S_SMALLC),
        p(c['name'], ps(f'hr{i}', 8.5, al=TA_CENTER, bold=is_op)),
        p(ELEM_KR[c['element']], ps(f'he{i}', 8, HexColor(ec['hdr']), TA_CENTER, True)),
        p(ROLE_KR[c['role']], S_SMALLC),
        p(f"{c['hp']:.0f}", ps(f'hv{i}', 9, al=TA_CENTER, bold=True)),
        p(f"{c['def']:.0f}", S_SMALLC),
        p('OP' if is_op else '', ps(f'ho{i}', 8, HexColor('#D32F2F'), TA_CENTER, True)),
    ])
cw_hp = [W*0.05, W*0.13, W*0.08, W*0.12, W*0.1, W*0.08, W*0.08]
t_hp = Table(hp_data, colWidths=cw_hp, repeatRows=1)
hp_style = [
    ('BACKGROUND', (0,0), (-1,0), HexColor('#2E7D32')),
    ('TEXTCOLOR', (0,0), (-1,0), white),
    ('GRID', (0,0), (-1,-1), 0.4, HexColor('#E0E0E0')),
    ('ALIGN', (0,0), (-1,-1), 'CENTER'),
    ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ('FONTNAME', (0,0), (-1,-1), F),
    ('FONTSIZE', (0,0), (-1,-1), 8),
    ('TOPPADDING', (0,0), (-1,-1), 2.5),
    ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
]
for i in range(1, len(hp_data)):
    c = hp_sorted[i-1]
    bg = HexColor(ELEM_COLORS[c['element']]['bg']) if i%2==1 else white
    hp_style.append(('BACKGROUND', (0,i), (-1,i), bg))
    if c['id'] in ('c600','c601'):
        hp_style.append(('BACKGROUND', (0,i), (-1,i), HexColor('#FFF9C4')))
t_hp.setStyle(TableStyle(hp_style))
story.append(t_hp)

# ============================================================
# APPENDIX 2: ROLE COMPARISON
# ============================================================
story.append(PageBreak())
story.append(p('부록: 역할별 비교', ps('app2', 18, HexColor('#333'), TA_CENTER, True, 24)))
story.append(Spacer(1, 4*mm))

for role_en, role_kr in [('ATTACKER','공격자'),('MAGICIAN','마법사'),('HEALER','힐러'),('DEFENDER','방어자'),('SUPPORTER','서포터')]:
    role_chars = [c for c in chars if c['role'] == role_en]
    if not role_chars: continue

    role_chars.sort(key=lambda c: -c['atk'])
    story.append(p(f'{role_kr} ({len(role_chars)}명)', ps(f'rh_{role_en}', 12, bold=True, ld=16)))
    story.append(Spacer(1, 2*mm))

    rd = [[p('이름', S_BODYBC), p('속성', S_BODYBC), p('ATK', S_BODYBC), p('DEF', S_BODYBC),
           p('HP', S_BODYBC), p('SPD', S_BODYBC), p('CRI', S_BODYBC), p('SP', S_BODYBC),
           p('Normal', S_BODYBC), p('Ultimate 핵심', S_BODYBC)]]
    for c in role_chars:
        ec = ELEM_COLORS[c['element']]
        is_op = c['id'] in ('c600','c601')
        # Shorten ult effects
        ult_short = c['ultimate']['effects']
        ult_short = ult_short.replace('DMG ','').replace('HEAL ','힐') \
            .replace('CLEANSE','정화').replace('SP_INCREASE','SP+') \
            .replace('COUNTER','반격').replace('REVIVE','부활')
        if len(ult_short) > 40: ult_short = ult_short[:38] + '..'

        norm_short = c['normal']['effects'].replace('DMG ','')
        if len(norm_short) > 20: norm_short = norm_short[:18] + '..'

        rd.append([
            p(c['name'], ps(f'rn{c["id"]}', 8.5, al=TA_CENTER, bold=is_op)),
            p(ELEM_KR[c['element']], ps(f're{c["id"]}', 8, HexColor(ec['hdr']), TA_CENTER, True)),
            p(f"{c['atk']:.0f}", S_SMALLC),
            p(f"{c['def']:.0f}", S_SMALLC),
            p(f"{c['hp']:.0f}", S_SMALLC),
            p(f"{c['spd']:.0f}", S_SMALLC),
            p(f"{c['cri']:.0%}", S_SMALLC),
            p(str(c['sp']), S_SMALLC),
            p(norm_short, ps(f'rno{c["id"]}', 7)),
            p(ult_short, ps(f'ru{c["id"]}', 7)),
        ])

    cw_r = [W*0.1, W*0.06, W*0.06, W*0.06, W*0.07, W*0.06, W*0.06, W*0.04, W*0.16, W*0.27]
    t_r = Table(rd, colWidths=cw_r, repeatRows=1)
    r_style = [
        ('BACKGROUND', (0,0), (-1,0), HexColor('#455A64')),
        ('TEXTCOLOR', (0,0), (-1,0), white),
        ('GRID', (0,0), (-1,-1), 0.3, HexColor('#E0E0E0')),
        ('ALIGN', (0,0), (7,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('FONTNAME', (0,0), (-1,-1), F),
        ('FONTSIZE', (0,0), (-1,-1), 7.5),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('LEFTPADDING', (8,1), (9,-1), 3),
    ]
    for i in range(1, len(rd)):
        c = role_chars[i-1]
        bg = HexColor(ELEM_COLORS[c['element']]['bg']) if i%2==1 else white
        r_style.append(('BACKGROUND', (0,i), (-1,i), bg))
        if c['id'] in ('c600','c601'):
            r_style.append(('BACKGROUND', (0,i), (-1,i), HexColor('#FFF9C4')))
    t_r.setStyle(TableStyle(r_style))
    story.append(t_r)
    story.append(Spacer(1, 5*mm))

# ============================================================
# BUILD
# ============================================================
doc.build(story)
print(f'PDF saved: {out}')
print(f'Characters: {len(chars)}')
print('DONE')
