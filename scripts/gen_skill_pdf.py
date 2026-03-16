"""c600 루미나 / c601 에레보스 스킬 상세 기획서 PDF 생성"""
import sys, os
sys.stdout.reconfigure(encoding='utf-8')

from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm, cm
from reportlab.lib.colors import HexColor, white, black
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, KeepTogether
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# === Font Setup (한글) ===
font_paths = [
    ('C:/Windows/Fonts/malgun.ttf', 'Malgun'),
    ('C:/Windows/Fonts/malgunbd.ttf', 'MalgunBold'),
]
for fp, fname in font_paths:
    if os.path.exists(fp):
        pdfmetrics.registerFont(TTFont(fname, fp))
FONT = 'Malgun'
FONT_B = 'MalgunBold'

# === Colors ===
C_LIGHT = HexColor('#FFF8E1')   # 루미나 (광/서포터) 배경
C_DARK  = HexColor('#E8F5E9')   # 에레보스 (목/공격자) 배경
C_HDR   = HexColor('#1565C0')   # 헤더 파란색
C_HDR2  = HexColor('#2E7D32')   # 에레보스 헤더 초록
C_SUB   = HexColor('#E3F2FD')   # 서브헤더
C_GOLD  = HexColor('#FF8F00')   # 강조 골드
C_GRAY  = HexColor('#F5F5F5')
C_BORDER = HexColor('#BDBDBD')

# === Styles ===
styles = getSampleStyleSheet()

def ps(name, font=FONT, size=9, color=black, align=TA_LEFT, leading=None, bold=False):
    return ParagraphStyle(
        name, fontName=FONT_B if bold else font, fontSize=size,
        textColor=color, alignment=align, leading=leading or size+3,
        wordWrap='CJK', splitLongWords=True,
    )

S_TITLE = ps('Title2', size=22, color=C_HDR, align=TA_CENTER, bold=True, leading=28)
S_SUBTITLE = ps('Sub', size=12, color=HexColor('#555555'), align=TA_CENTER)
S_H1 = ps('H1', size=16, color=C_HDR, bold=True, leading=22)
S_H2 = ps('H2', size=13, color=HexColor('#1B5E20'), bold=True, leading=18)
S_H3 = ps('H3', size=11, color=HexColor('#333333'), bold=True, leading=15)
S_BODY = ps('Body2', size=9, leading=13)
S_BODYC = ps('BodyC', size=9, align=TA_CENTER, leading=13)
S_BODYB = ps('BodyB', size=9, bold=True, leading=13)
S_BODYBC = ps('BodyBC', size=9, bold=True, align=TA_CENTER, leading=13)
S_SMALL = ps('Small', size=7.5, color=HexColor('#666666'), leading=10)
S_SMALLC = ps('SmallC', size=7.5, color=HexColor('#666666'), align=TA_CENTER, leading=10)
S_OP = ps('OP', size=10, color=HexColor('#D84315'), bold=True, leading=14)
S_STAT = ps('Stat', size=10, align=TA_CENTER, leading=14)
S_STAT_B = ps('StatB', size=10, align=TA_CENTER, bold=True, leading=14)

def p(text, style=S_BODY):
    return Paragraph(str(text), style)

def header_table(data, col_widths, hdr_color=C_HDR, alt1=C_LIGHT, alt2=white):
    t = Table(data, colWidths=col_widths, repeatRows=1)
    style_cmds = [
        ('BACKGROUND', (0,0), (-1,0), hdr_color),
        ('TEXTCOLOR', (0,0), (-1,0), white),
        ('FONTNAME', (0,0), (-1,0), FONT_B),
        ('FONTSIZE', (0,0), (-1,0), 9),
        ('FONTNAME', (0,1), (-1,-1), FONT),
        ('FONTSIZE', (0,1), (-1,-1), 8.5),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('GRID', (0,0), (-1,-1), 0.5, C_BORDER),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
    ]
    for i in range(1, len(data)):
        bg = alt1 if i % 2 == 1 else alt2
        style_cmds.append(('BACKGROUND', (0,i), (-1,i), bg))
    t.setStyle(TableStyle(style_cmds))
    return t

# === Build PDF ===
out_path = 'data/Skill_c600_c601_기획서.pdf'
doc = SimpleDocTemplate(
    out_path, pagesize=A4,
    leftMargin=15*mm, rightMargin=15*mm,
    topMargin=18*mm, bottomMargin=18*mm,
    title='c600 루미나 / c601 에레보스 스킬 상세 기획서',
    author='BattleAgent Design Team',
)

story = []
W = doc.width  # usable width

# ============================================================
# PAGE 1: 표지
# ============================================================
story.append(Spacer(1, 40*mm))
story.append(p('신규 캐릭터 스킬 상세 기획서', S_TITLE))
story.append(Spacer(1, 8*mm))
story.append(p('c600 루미나 (광/서포터)  ×  c601 에레보스 (목/공격자)', S_SUBTITLE))
story.append(Spacer(1, 15*mm))

# 요약 박스
cover_data = [
    [p('항목', S_BODYBC), p('c600 루미나', S_BODYBC), p('c601 에레보스', S_BODYBC)],
    [p('속성 / 역할', S_BODYC), p('광 (Light) / 서포터', S_BODYC), p('목 (Forest) / 공격자', S_BODYC)],
    [p('설계 의도', S_BODYC), p('시트리+엘리시온+브라우니 통합\n최상위 서포터', S_BODYC), p('이브+쿠바바+아르테미스 통합\n최상위 딜러', S_BODYC)],
    [p('핵심 OP', S_BODYC), p('Active 전체버프+정화\nUlt 힐+ATK+CriDmg+SP', S_BODYC), p('ATK 530 + CRI 35% + PEN 20%\nNormal 2연타 / Active 처형', S_BODYC)],
    [p('OP 등급', S_BODYBC), p('SS+', S_BODYBC), p('SS+', S_BODYBC)],
]
cw = [W*0.22, W*0.39, W*0.39]
t = Table(cover_data, colWidths=cw)
t.setStyle(TableStyle([
    ('BACKGROUND', (0,0), (-1,0), C_HDR),
    ('TEXTCOLOR', (0,0), (-1,0), white),
    ('BACKGROUND', (1,1), (1,-1), C_LIGHT),
    ('BACKGROUND', (2,1), (2,-1), C_DARK),
    ('BACKGROUND', (0,1), (0,-1), C_SUB),
    ('GRID', (0,0), (-1,-1), 0.7, C_BORDER),
    ('ALIGN', (0,0), (-1,-1), 'CENTER'),
    ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ('FONTNAME', (0,0), (-1,-1), FONT),
    ('FONTSIZE', (0,0), (-1,-1), 10),
    ('TOPPADDING', (0,0), (-1,-1), 6),
    ('BOTTOMPADDING', (0,0), (-1,-1), 6),
]))
story.append(t)
story.append(Spacer(1, 20*mm))
story.append(p('BattleAgent Design Team  |  2026.03', ps('footer', size=10, color=HexColor('#999999'), align=TA_CENTER)))

# ============================================================
# PAGE 2: 캐릭터 기본 스탯
# ============================================================
story.append(PageBreak())
story.append(p('1. 캐릭터 기본 스탯', S_H1))
story.append(Spacer(1, 4*mm))

stat_data = [
    [p('스탯', S_BODYBC), p('c600 루미나', S_BODYBC), p('비고', S_BODYBC),
     p('스탯', S_BODYBC), p('c601 에레보스', S_BODYBC), p('비고', S_BODYBC)],
    [p('ATK', S_BODYC), p('230', S_STAT), p('서포터 최고', S_SMALLC),
     p('ATK', S_BODYC), p('530', S_STAT_B), p('게임 내 최고', S_SMALLC)],
    [p('DEF', S_BODYC), p('160', S_STAT), p('서포터 최고', S_SMALLC),
     p('DEF', S_BODYC), p('135', S_STAT), p('공격자 평균+', S_SMALLC)],
    [p('HP', S_BODYC), p('6800', S_STAT), p('서포터 최고', S_SMALLC),
     p('HP', S_BODYC), p('5500', S_STAT), p('공격자 상위', S_SMALLC)],
    [p('SPD', S_BODYC), p('120', S_STAT_B), p('서포터 룰 준수', S_SMALLC),
     p('SPD', S_BODYC), p('80', S_STAT), p('공격자 중 최고', S_SMALLC)],
    [p('CRI', S_BODYC), p('5%', S_STAT), p('기본값', S_SMALLC),
     p('CRI', S_BODYC), p('35%', S_STAT_B), p('게임 내 최고', S_SMALLC)],
    [p('PEN', S_BODYC), p('0%', S_STAT), p('기본값', S_SMALLC),
     p('PEN', S_BODYC), p('20%', S_STAT_B), p('게임 내 최고', S_SMALLC)],
    [p('MaxSP', S_BODYC), p('4', S_STAT), p('', S_SMALLC),
     p('MaxSP', S_BODYC), p('6', S_STAT), p('', S_SMALLC)],
    [p('UseSP', S_BODYC), p('3', S_STAT_B), p('저렴!', S_SMALLC),
     p('UseSP', S_BODYC), p('5', S_STAT), p('표준', S_SMALLC)],
    [p('ID', S_BODYC), p('10000600', S_STAT), p('', S_SMALLC),
     p('ID', S_BODYC), p('10000601', S_STAT), p('', S_SMALLC)],
]
cw2 = [W*0.1, W*0.14, W*0.14, W*0.1, W*0.14, W*0.14]  # widths won't exceed page
# Adjust proportionally
total_r = sum([0.1, 0.14, 0.14, 0.1, 0.14, 0.14])
cw2 = [W*(x/total_r)*0.76 for x in [0.1, 0.14, 0.14, 0.1, 0.14, 0.14]]
# Add gap
cw2_with_gap = [W*0.12, W*0.16, W*0.16, W*0.04, W*0.12, W*0.16, W*0.16]

# Rebuild with gap column
stat_data2 = []
for row in stat_data:
    stat_data2.append(row[:3] + [p('', S_BODYC)] + row[3:])

t2 = Table(stat_data2, colWidths=cw2_with_gap)
style2 = [
    ('BACKGROUND', (0,0), (2,0), C_HDR),
    ('BACKGROUND', (4,0), (6,0), C_HDR2),
    ('TEXTCOLOR', (0,0), (2,0), white),
    ('TEXTCOLOR', (4,0), (6,0), white),
    ('BACKGROUND', (3,0), (3,-1), white),
    ('GRID', (0,0), (2,-1), 0.5, C_BORDER),
    ('GRID', (4,0), (6,-1), 0.5, C_BORDER),
    ('ALIGN', (0,0), (-1,-1), 'CENTER'),
    ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ('FONTNAME', (0,0), (-1,-1), FONT),
    ('FONTSIZE', (0,0), (-1,-1), 9),
    ('TOPPADDING', (0,0), (-1,-1), 3),
    ('BOTTOMPADDING', (0,0), (-1,-1), 3),
]
for i in range(1, len(stat_data2)):
    style2.append(('BACKGROUND', (0,i), (0,i), C_SUB))
    style2.append(('BACKGROUND', (4,i), (4,i), C_SUB))
    bg_l = C_LIGHT if i%2==1 else white
    bg_r = C_DARK if i%2==1 else white
    style2.append(('BACKGROUND', (1,i), (2,i), bg_l))
    style2.append(('BACKGROUND', (5,i), (6,i), bg_r))
t2.setStyle(TableStyle(style2))
story.append(t2)

# OP 포인트 요약
story.append(Spacer(1, 6*mm))
story.append(p('OP 설계 포인트', S_H3))
story.append(Spacer(1, 2*mm))

op_data = [
    [p('', S_BODYBC), p('루미나 (c600)', S_BODYBC), p('에레보스 (c601)', S_BODYBC)],
    [p('OP 1', S_BODYBC),
     p('Active: 전체 아군 ATK+30%, SPD+20, 디버프 제거를 한 스킬에 통합', S_BODY),
     p('ATK 530 + CRI 35% + PEN 20% = 기본 스탯만으로 최강 딜러', S_BODY)],
    [p('OP 2', S_BODYBC),
     p('Ult: 힐35% + ATK+35% + CriDmg+50% + SP+1을 SP3에 시전', S_BODY),
     p('Normal 2연타 (250%x2) = 크리 기회 2배, 실질 500%', S_BODY)],
    [p('OP 3', S_BODYBC),
     p('패시브: 전투 시작 DEF+15% 영구 + 피격시 확률 회복', S_BODY),
     p('Active 처형: HP<50% 시 추가 300% (총 800%) + DEF-25%', S_BODY)],
    [p('OP 4', S_BODYBC),
     p('SP3 = 모든 궁극기 중 가장 저렴', S_BODY),
     p('Ult AoE 350% + DEF-30% + 출혈DoT = 후속 딜러 시너지', S_BODY)],
]
cw_op = [W*0.08, W*0.46, W*0.46]
t_op = Table(op_data, colWidths=cw_op)
t_op.setStyle(TableStyle([
    ('BACKGROUND', (0,0), (-1,0), HexColor('#37474F')),
    ('TEXTCOLOR', (0,0), (-1,0), white),
    ('BACKGROUND', (0,1), (0,-1), HexColor('#ECEFF1')),
    ('BACKGROUND', (1,1), (1,-1), HexColor('#FFFDE7')),
    ('BACKGROUND', (2,1), (2,-1), HexColor('#F1F8E9')),
    ('GRID', (0,0), (-1,-1), 0.5, C_BORDER),
    ('ALIGN', (0,0), (0,-1), 'CENTER'),
    ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ('FONTNAME', (0,0), (-1,-1), FONT),
    ('FONTSIZE', (0,0), (-1,-1), 8.5),
    ('TOPPADDING', (0,0), (-1,-1), 4),
    ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ('LEFTPADDING', (0,0), (-1,-1), 5),
]))
story.append(t_op)

# ============================================================
# PAGE 3: 루미나 스킬 상세
# ============================================================
story.append(PageBreak())
story.append(p('2. c600 루미나 — 스킬 상세', S_H1))
story.append(Spacer(1, 3*mm))

def skill_block(name, stype, desc, target, details, notes, level='—'):
    """단일 스킬 블록 생성"""
    data = [
        [p(f'{stype}', S_BODYBC), p(name, ps('sn', size=11, bold=True, color=C_HDR)), p(f'Lv.{level}', S_BODYBC), p(target, S_BODYC)],
        [p('효과', S_BODYBC), p(desc, S_BODY), '', ''],
        [p('수치', S_BODYBC), p(details, S_BODY), '', ''],
        [p('비고', S_BODYBC), p(notes, S_SMALL), '', ''],
    ]
    cw_s = [W*0.1, W*0.5, W*0.1, W*0.2]
    t = Table(data, colWidths=cw_s)
    t.setStyle(TableStyle([
        ('SPAN', (1,1), (3,1)),
        ('SPAN', (1,2), (3,2)),
        ('SPAN', (1,3), (3,3)),
        ('BACKGROUND', (0,0), (-1,0), C_HDR),
        ('TEXTCOLOR', (0,0), (-1,0), white),
        ('BACKGROUND', (0,1), (0,-1), C_SUB),
        ('BACKGROUND', (1,1), (-1,-1), C_LIGHT),
        ('GRID', (0,0), (-1,-1), 0.5, C_BORDER),
        ('ALIGN', (0,0), (-1,0), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('FONTNAME', (0,0), (-1,-1), FONT),
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
    ]))
    return t

def skill_block_dark(name, stype, desc, target, details, notes, level='—'):
    """에레보스 스킬 블록"""
    data = [
        [p(f'{stype}', S_BODYBC), p(name, ps('snd', size=11, bold=True, color=C_HDR2)), p(f'Lv.{level}', S_BODYBC), p(target, S_BODYC)],
        [p('효과', S_BODYBC), p(desc, S_BODY), '', ''],
        [p('수치', S_BODYBC), p(details, S_BODY), '', ''],
        [p('비고', S_BODYBC), p(notes, S_SMALL), '', ''],
    ]
    cw_s = [W*0.1, W*0.5, W*0.1, W*0.2]
    t = Table(data, colWidths=cw_s)
    t.setStyle(TableStyle([
        ('SPAN', (1,1), (3,1)),
        ('SPAN', (1,2), (3,2)),
        ('SPAN', (1,3), (3,3)),
        ('BACKGROUND', (0,0), (-1,0), C_HDR2),
        ('TEXTCOLOR', (0,0), (-1,0), white),
        ('BACKGROUND', (0,1), (0,-1), C_SUB),
        ('BACKGROUND', (1,1), (-1,-1), C_DARK),
        ('GRID', (0,0), (-1,-1), 0.5, C_BORDER),
        ('ALIGN', (0,0), (-1,0), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('FONTNAME', (0,0), (-1,-1), FONT),
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
    ]))
    return t

# --- 루미나 Normal ---
story.append(skill_block(
    '성광의 채찍', 'Normal',
    '신성한 빛으로 적 1명을 공격',
    '적 근접 1명',
    'ATK x 120%  |  BuffValue: 1000001 (공용대미지)',
    'SkillID: 1544601  |  CastingType: Move  |  Trigger: SignalHit',
))
story.append(Spacer(1, 3*mm))

# --- 루미나 Active ---
story.append(p('Active — 빛의 축복 (쿨타임: 3턴)', S_H3))
story.append(Spacer(1, 2*mm))

act_data = [
    [p('Lv', S_BODYBC), p('ATK 버프', S_BODYBC), p('SPD 버프', S_BODYBC), p('디버프 제거', S_BODYBC), p('SkillID', S_BODYBC)],
    [p('1', S_BODYC), p('ATK +30% (3턴)', S_BODYC), p('SPD +20 (3턴)', S_BODYC), p('전체 정화', S_BODYC), p('2544601', S_SMALLC)],
    [p('2', S_BODYC), p('ATK +35% (3턴)', S_BODYC), p('SPD +25 (3턴)', S_BODYC), p('전체 정화', S_BODYC), p('2544602', S_SMALLC)],
]
story.append(header_table(act_data, [W*0.06, W*0.24, W*0.24, W*0.22, W*0.14]))
story.append(Spacer(1, 1*mm))
story.append(p('대상: 아군 전체 (1000000)  |  CastingType: Static  |  Trigger: Immediately', S_SMALL))
story.append(Spacer(1, 3*mm))

# --- 루미나 Ultimate ---
story.append(p('Ultimate — 성역의 은총 (SP 소모: 3)', S_H3))
story.append(Spacer(1, 2*mm))

ult_data = [
    [p('Lv', S_BODYBC), p('HP 회복', S_BODYBC), p('ATK 버프', S_BODYBC), p('CriDmg 버프', S_BODYBC), p('SP 회복', S_BODYBC), p('SkillID', S_BODYBC)],
    [p('1', S_BODYC), p('35%', S_BODYC), p('+35% (3턴)', S_BODYC), p('+50% (3턴)', S_BODYC), p('+1', S_BODYC), p('3544601', S_SMALLC)],
    [p('2', S_BODYC), p('40%', S_BODYC), p('+40% (3턴)', S_BODYC), p('+55% (3턴)', S_BODYC), p('+1', S_BODYC), p('3544602', S_SMALLC)],
    [p('3', S_BODYC), p('45%', S_BODYC), p('+45% (3턴)', S_BODYC), p('+60% (3턴)', S_BODYC), p('+2', S_BODYC), p('3544603', S_SMALLC)],
]
story.append(header_table(ult_data, [W*0.06, W*0.14, W*0.18, W*0.2, W*0.12, W*0.14]))
story.append(Spacer(1, 1*mm))
story.append(p('대상: 아군 전체 (1000000)  |  CastingType: Static  |  Trigger: Immediately  |  회복 BuffID: 9900003', S_SMALL))
story.append(Spacer(1, 3*mm))

# --- 루미나 Passive ---
story.append(p('Passive', S_H3))
story.append(Spacer(1, 2*mm))

pass_data = [
    [p('패시브', S_BODYBC), p('이름', S_BODYBC), p('대상', S_BODYBC), p('효과', S_BODYBC), p('지속', S_BODYBC), p('트리거', S_BODYBC)],
    [p('1', S_BODYC), p('빛의 가호', S_BODYC), p('아군 전체', S_BODYC), p('DEF +15%', S_BODYC), p('영구', S_BODYC), p('BattleStart', S_SMALLC)],
    [p('2', S_BODYC), p('성스러운 빛', S_BODYC), p('피격 아군', S_BODYC), p('HP 10% 회복', S_BODYC), p('즉시', S_BODYC), p('OnAllyDamaged\n(5% 확률)', S_SMALLC)],
]
story.append(header_table(pass_data, [W*0.08, W*0.16, W*0.14, W*0.2, W*0.12, W*0.2]))

# ============================================================
# PAGE 4: 에레보스 스킬 상세
# ============================================================
story.append(PageBreak())
story.append(p('3. c601 에레보스 — 스킬 상세', S_H1))
story.append(Spacer(1, 3*mm))

# --- 에레보스 Normal ---
story.append(skill_block_dark(
    '심연의 쌍격', 'Normal',
    '암흑의 힘으로 적 1명을 2회 연속 공격 (크리 기회 2배)',
    '적 근접 1명',
    'ATK x 250% x 2타  |  실질 500%  |  BuffValue: 1000001 x2',
    'SkillID: 1531601  |  CastingType: Move  |  Trigger: SignalHit x2',
))
story.append(Spacer(1, 3*mm))

# --- 에레보스 Active ---
story.append(p('Active — 종결자의 일격 (쿨타임: 4턴)', S_H3))
story.append(Spacer(1, 2*mm))

act2_data = [
    [p('Lv', S_BODYBC), p('기본 대미지', S_BODYBC), p('처형 추가\n(HP<50%)', S_BODYBC), p('DEF 감소', S_BODYBC), p('합산 배율', S_BODYBC), p('SkillID', S_BODYBC)],
    [p('1', S_BODYC), p('500%', S_BODYC), p('+300%', S_BODYC), p('-25% (2턴)', S_BODYC), p('800%', S_BODYBC), p('2531601', S_SMALLC)],
    [p('2', S_BODYC), p('600%', S_BODYC), p('+350%', S_BODYC), p('-30% (2턴)', S_BODYC), p('950%', S_BODYBC), p('2531602', S_SMALLC)],
]
t_act2 = header_table(act2_data, [W*0.06, W*0.16, W*0.18, W*0.18, W*0.16, W*0.14], hdr_color=C_HDR2, alt1=C_DARK)
story.append(t_act2)
story.append(Spacer(1, 1*mm))
story.append(p('대상: 적 최저HP (2000012)  |  CastingType: Move  |  처형 조건: RequireTag1=10201, RequireTag2=50000 (HP<50%)', S_SMALL))
story.append(Spacer(1, 1*mm))
story.append(p('Trigger: 기본=SignalHit / 처형=SignalHit(조건부) / DEF감소=AttackEnd  |  처형 BuffID: 1000015', S_SMALL))
story.append(Spacer(1, 3*mm))

# --- 에레보스 Ultimate ---
story.append(p('Ultimate — 심판의 심연 (SP 소모: 5)', S_H3))
story.append(Spacer(1, 2*mm))

ult2_data = [
    [p('Lv', S_BODYBC), p('AoE 대미지', S_BODYBC), p('DEF 감소', S_BODYBC), p('출혈 DoT', S_BODYBC), p('SkillID', S_BODYBC)],
    [p('1', S_BODYC), p('350%', S_BODYC), p('-30% (2턴)', S_BODYC), p('ATK 20% (3턴)', S_BODYC), p('3531601', S_SMALLC)],
    [p('2', S_BODYC), p('400%', S_BODYC), p('-35% (2턴)', S_BODYC), p('ATK 25% (3턴)', S_BODYC), p('3531602', S_SMALLC)],
    [p('3', S_BODYC), p('450%', S_BODYC), p('-40% (2턴)', S_BODYC), p('ATK 30% (3턴)', S_BODYC), p('3531603', S_SMALLC)],
]
t_ult2 = header_table(ult2_data, [W*0.06, W*0.2, W*0.22, W*0.24, W*0.14], hdr_color=C_HDR2, alt1=C_DARK)
story.append(t_ult2)
story.append(Spacer(1, 1*mm))
story.append(p('대상: 적 전체 (920001)  |  CastingType: NonTargetMove  |  Trigger: 대미지=SignalHit / 디버프,DoT=AttackEnd', S_SMALL))
story.append(Spacer(1, 1*mm))
story.append(p('출혈 BuffID: 3002306 (에레보스 전용)  |  DEF감소 BuffID: 3000201', S_SMALL))
story.append(Spacer(1, 3*mm))

# --- 에레보스 Passive ---
story.append(p('Passive', S_H3))
story.append(Spacer(1, 2*mm))

pass2_data = [
    [p('패시브', S_BODYBC), p('이름', S_BODYBC), p('대상', S_BODYBC), p('효과', S_BODYBC), p('지속', S_BODYBC), p('트리거', S_BODYBC)],
    [p('1', S_BODYC), p('심연의 힘', S_BODYC), p('자신', S_BODYC), p('ATK +20%\nPEN +10%', S_BODYC), p('영구', S_BODYC), p('BattleStart', S_SMALLC)],
    [p('2', S_BODYC), p('처형자의 본능', S_BODYC), p('자신', S_BODYC), p('ATK +15%', S_BODYC), p('2턴', S_BODYC), p('OnKill', S_SMALLC)],
]
t_pass2 = header_table(pass2_data, [W*0.08, W*0.16, W*0.1, W*0.22, W*0.1, W*0.2], hdr_color=C_HDR2, alt1=C_DARK)
story.append(t_pass2)

# ============================================================
# PAGE 5: BuffValue 상세 매핑
# ============================================================
story.append(PageBreak())
story.append(p('4. BuffValue 상세 매핑', S_H1))
story.append(Spacer(1, 3*mm))

story.append(p('4-1. 루미나 (c600) — 21개 BuffValue', S_H2))
story.append(Spacer(1, 2*mm))

bv600_data = [
    [p('ID', S_BODYBC), p('스킬', S_BODYBC), p('설명', S_BODYBC), p('Buff', S_BODYBC), p('V1', S_BODYBC), p('V2\n(Stat)', S_BODYBC), p('Turn', S_BODYBC), p('Rate', S_BODYBC)],
    [p('15446011', S_SMALLC), p('Normal', S_SMALLC), p('성광채찍 대미지', S_SMALL), p('1000001', S_SMALLC), p('120000', S_SMALLC), p('—', S_SMALLC), p('0', S_SMALLC), p('100%', S_SMALLC)],
    [p('25446011', S_SMALLC), p('Active1', S_SMALLC), p('빛의축복 ATK', S_SMALL), p('2000101', S_SMALLC), p('30000', S_SMALLC), p('1001', S_SMALLC), p('3', S_SMALLC), p('100%', S_SMALLC)],
    [p('25446012', S_SMALLC), p('Active1', S_SMALLC), p('빛의축복 SPD', S_SMALL), p('2001001', S_SMALLC), p('20000', S_SMALLC), p('1010', S_SMALLC), p('3', S_SMALLC), p('100%', S_SMALLC)],
    [p('25446013', S_SMALLC), p('Active1', S_SMALLC), p('빛의축복 정화', S_SMALL), p('4000101', S_SMALLC), p('1', S_SMALLC), p('—', S_SMALLC), p('0', S_SMALLC), p('100%', S_SMALLC)],
    [p('25446021', S_SMALLC), p('Active2', S_SMALLC), p('빛의축복+ ATK', S_SMALL), p('2000101', S_SMALLC), p('35000', S_SMALLC), p('1001', S_SMALLC), p('3', S_SMALLC), p('100%', S_SMALLC)],
    [p('25446022', S_SMALLC), p('Active2', S_SMALLC), p('빛의축복+ SPD', S_SMALL), p('2001001', S_SMALLC), p('25000', S_SMALLC), p('1010', S_SMALLC), p('3', S_SMALLC), p('100%', S_SMALLC)],
    [p('25446023', S_SMALLC), p('Active2', S_SMALLC), p('빛의축복+ 정화', S_SMALL), p('4000101', S_SMALLC), p('1', S_SMALLC), p('—', S_SMALLC), p('0', S_SMALLC), p('100%', S_SMALLC)],
    [p('35446011', S_SMALLC), p('Ult1', S_SMALLC), p('성역은총 힐', S_SMALL), p('9900003', S_SMALLC), p('35000', S_SMALLC), p('—', S_SMALLC), p('0', S_SMALLC), p('100%', S_SMALLC)],
    [p('35446012', S_SMALLC), p('Ult1', S_SMALLC), p('성역은총 ATK', S_SMALL), p('2000101', S_SMALLC), p('35000', S_SMALLC), p('1001', S_SMALLC), p('3', S_SMALLC), p('100%', S_SMALLC)],
    [p('35446013', S_SMALLC), p('Ult1', S_SMALLC), p('성역은총 CriDmg', S_SMALL), p('2000501', S_SMALLC), p('50000', S_SMALLC), p('1005', S_SMALLC), p('3', S_SMALLC), p('100%', S_SMALLC)],
    [p('35446014', S_SMALLC), p('Ult1', S_SMALLC), p('성역은총 SP', S_SMALL), p('2003001', S_SMALLC), p('1', S_SMALLC), p('—', S_SMALLC), p('0', S_SMALLC), p('100%', S_SMALLC)],
    [p('35446021', S_SMALLC), p('Ult2', S_SMALLC), p('성역은총+ 힐', S_SMALL), p('9900003', S_SMALLC), p('40000', S_SMALLC), p('—', S_SMALLC), p('0', S_SMALLC), p('100%', S_SMALLC)],
    [p('35446022', S_SMALLC), p('Ult2', S_SMALLC), p('성역은총+ ATK', S_SMALL), p('2000101', S_SMALLC), p('40000', S_SMALLC), p('1001', S_SMALLC), p('3', S_SMALLC), p('100%', S_SMALLC)],
    [p('35446023', S_SMALLC), p('Ult2', S_SMALLC), p('성역은총+ CriDmg', S_SMALL), p('2000501', S_SMALLC), p('55000', S_SMALLC), p('1005', S_SMALLC), p('3', S_SMALLC), p('100%', S_SMALLC)],
    [p('35446024', S_SMALLC), p('Ult2', S_SMALLC), p('성역은총+ SP', S_SMALL), p('2003001', S_SMALLC), p('1', S_SMALLC), p('—', S_SMALLC), p('0', S_SMALLC), p('100%', S_SMALLC)],
    [p('35446031', S_SMALLC), p('Ult3', S_SMALLC), p('성역은총++ 힐', S_SMALL), p('9900003', S_SMALLC), p('45000', S_SMALLC), p('—', S_SMALLC), p('0', S_SMALLC), p('100%', S_SMALLC)],
    [p('35446032', S_SMALLC), p('Ult3', S_SMALLC), p('성역은총++ ATK', S_SMALL), p('2000101', S_SMALLC), p('45000', S_SMALLC), p('1001', S_SMALLC), p('3', S_SMALLC), p('100%', S_SMALLC)],
    [p('35446033', S_SMALLC), p('Ult3', S_SMALLC), p('성역은총++ CriDmg', S_SMALL), p('2000501', S_SMALLC), p('60000', S_SMALLC), p('1005', S_SMALLC), p('3', S_SMALLC), p('100%', S_SMALLC)],
    [p('35446034', S_SMALLC), p('Ult3', S_SMALLC), p('성역은총++ SP', S_SMALL), p('2003001', S_SMALLC), p('2', S_SMALLC), p('—', S_SMALLC), p('0', S_SMALLC), p('100%', S_SMALLC)],
    [p('45446011', S_SMALLC), p('Passive1', S_SMALLC), p('빛의가호 DEF', S_SMALL), p('2000201', S_SMALLC), p('15000', S_SMALLC), p('1003', S_SMALLC), p('-1', S_SMALLC), p('100%', S_SMALLC)],
    [p('45446021', S_SMALLC), p('Passive2', S_SMALLC), p('성스러운빛 힐', S_SMALL), p('9900003', S_SMALLC), p('10000', S_SMALLC), p('—', S_SMALLC), p('0', S_SMALLC), p('5%', S_SMALLC)],
]
cw_bv = [W*0.11, W*0.1, W*0.22, W*0.1, W*0.1, W*0.1, W*0.07, W*0.08]
story.append(header_table(bv600_data, cw_bv))

story.append(Spacer(1, 5*mm))
story.append(p('4-2. 에레보스 (c601) — 20개 BuffValue', S_H2))
story.append(Spacer(1, 2*mm))

bv601_data = [
    [p('ID', S_BODYBC), p('스킬', S_BODYBC), p('설명', S_BODYBC), p('Buff', S_BODYBC), p('V1', S_BODYBC), p('V2\n(Stat)', S_BODYBC), p('Turn', S_BODYBC), p('Rate', S_BODYBC)],
    [p('15316011', S_SMALLC), p('Normal', S_SMALLC), p('심연쌍격 1타', S_SMALL), p('1000001', S_SMALLC), p('250000', S_SMALLC), p('—', S_SMALLC), p('0', S_SMALLC), p('100%', S_SMALLC)],
    [p('15316012', S_SMALLC), p('Normal', S_SMALLC), p('심연쌍격 2타', S_SMALL), p('1000001', S_SMALLC), p('250000', S_SMALLC), p('—', S_SMALLC), p('0', S_SMALLC), p('100%', S_SMALLC)],
    [p('25316011', S_SMALLC), p('Active1', S_SMALLC), p('종결자일격 메인', S_SMALL), p('1000002', S_SMALLC), p('500000', S_SMALLC), p('—', S_SMALLC), p('0', S_SMALLC), p('100%', S_SMALLC)],
    [p('25316012', S_SMALLC), p('Active1', S_SMALLC), p('종결자일격 처형', S_SMALL), p('1000015', S_SMALLC), p('300000', S_SMALLC), p('—', S_SMALLC), p('0', S_SMALLC), p('100%', S_SMALLC)],
    [p('25316013', S_SMALLC), p('Active1', S_SMALLC), p('종결자일격 DEF감소', S_SMALL), p('3000201', S_SMALLC), p('-25000', S_SMALLC), p('1003', S_SMALLC), p('2', S_SMALLC), p('100%', S_SMALLC)],
    [p('25316021', S_SMALLC), p('Active2', S_SMALLC), p('종결자일격+ 메인', S_SMALL), p('1000002', S_SMALLC), p('600000', S_SMALLC), p('—', S_SMALLC), p('0', S_SMALLC), p('100%', S_SMALLC)],
    [p('25316022', S_SMALLC), p('Active2', S_SMALLC), p('종결자일격+ 처형', S_SMALL), p('1000015', S_SMALLC), p('350000', S_SMALLC), p('—', S_SMALLC), p('0', S_SMALLC), p('100%', S_SMALLC)],
    [p('25316023', S_SMALLC), p('Active2', S_SMALLC), p('종결자일격+ DEF감소', S_SMALL), p('3000201', S_SMALLC), p('-30000', S_SMALLC), p('1003', S_SMALLC), p('2', S_SMALLC), p('100%', S_SMALLC)],
    [p('35316011', S_SMALLC), p('Ult1', S_SMALLC), p('심판심연 대미지', S_SMALL), p('1000003', S_SMALLC), p('350000', S_SMALLC), p('—', S_SMALLC), p('0', S_SMALLC), p('100%', S_SMALLC)],
    [p('35316012', S_SMALLC), p('Ult1', S_SMALLC), p('심판심연 DEF감소', S_SMALL), p('3000201', S_SMALLC), p('-30000', S_SMALLC), p('1003', S_SMALLC), p('2', S_SMALLC), p('100%', S_SMALLC)],
    [p('35316013', S_SMALLC), p('Ult1', S_SMALLC), p('심판심연 출혈', S_SMALL), p('3002306', S_SMALLC), p('20000', S_SMALLC), p('—', S_SMALLC), p('3', S_SMALLC), p('100%', S_SMALLC)],
    [p('35316021', S_SMALLC), p('Ult2', S_SMALLC), p('심판심연+ 대미지', S_SMALL), p('1000003', S_SMALLC), p('400000', S_SMALLC), p('—', S_SMALLC), p('0', S_SMALLC), p('100%', S_SMALLC)],
    [p('35316022', S_SMALLC), p('Ult2', S_SMALLC), p('심판심연+ DEF감소', S_SMALL), p('3000201', S_SMALLC), p('-35000', S_SMALLC), p('1003', S_SMALLC), p('2', S_SMALLC), p('100%', S_SMALLC)],
    [p('35316023', S_SMALLC), p('Ult2', S_SMALLC), p('심판심연+ 출혈', S_SMALL), p('3002306', S_SMALLC), p('25000', S_SMALLC), p('—', S_SMALLC), p('3', S_SMALLC), p('100%', S_SMALLC)],
    [p('35316031', S_SMALLC), p('Ult3', S_SMALLC), p('심판심연++ 대미지', S_SMALL), p('1000003', S_SMALLC), p('450000', S_SMALLC), p('—', S_SMALLC), p('0', S_SMALLC), p('100%', S_SMALLC)],
    [p('35316032', S_SMALLC), p('Ult3', S_SMALLC), p('심판심연++ DEF감소', S_SMALL), p('3000201', S_SMALLC), p('-40000', S_SMALLC), p('1003', S_SMALLC), p('2', S_SMALLC), p('100%', S_SMALLC)],
    [p('35316033', S_SMALLC), p('Ult3', S_SMALLC), p('심판심연++ 출혈', S_SMALL), p('3002306', S_SMALLC), p('30000', S_SMALLC), p('—', S_SMALLC), p('3', S_SMALLC), p('100%', S_SMALLC)],
    [p('45316011', S_SMALLC), p('Passive1', S_SMALLC), p('심연의힘 ATK', S_SMALL), p('2000101', S_SMALLC), p('20000', S_SMALLC), p('1001', S_SMALLC), p('-1', S_SMALLC), p('100%', S_SMALLC)],
    [p('45316012', S_SMALLC), p('Passive1', S_SMALLC), p('심연의힘 PEN', S_SMALL), p('2009001', S_SMALLC), p('10000', S_SMALLC), p('—', S_SMALLC), p('-1', S_SMALLC), p('100%', S_SMALLC)],
    [p('45316021', S_SMALLC), p('Passive2', S_SMALLC), p('처형자본능 ATK', S_SMALL), p('2000101', S_SMALLC), p('15000', S_SMALLC), p('1001', S_SMALLC), p('2', S_SMALLC), p('100%', S_SMALLC)],
]
story.append(header_table(bv601_data, cw_bv, hdr_color=C_HDR2, alt1=C_DARK))

# ============================================================
# PAGE 6: 신규 Buff 정의 + 밸런스 비교
# ============================================================
story.append(PageBreak())
story.append(p('5. 신규 Buff 정의', S_H1))
story.append(Spacer(1, 3*mm))

nbuf_data = [
    [p('BuffID', S_BODYBC), p('이름', S_BODYBC), p('설명', S_BODYBC), p('카테고리', S_BODYBC), p('비고', S_BODYBC)],
    [p('9900003', S_BODYC), p('루미나 전용 회복', S_BODYC), p('HP% 비례 회복', S_BODYC), p('회복', S_BODYC), p('기존 9900001/2 패턴', S_SMALL)],
    [p('4000101', S_BODYC), p('디버프 제거', S_BODYC), p('대상의 모든 디버프 제거', S_BODYC), p('정화', S_BODYC), p('신규 카테고리', S_SMALL)],
    [p('3002306', S_BODYC), p('에레보스 전용 출혈', S_BODYC), p('ATK% 비례 DoT (매턴)', S_BODYC), p('DoT', S_BODYC), p('기존 3002301~5 패턴', S_SMALL)],
    [p('2009001', S_BODYC), p('관통력 증가', S_BODYC), p('관통력 수치 증가', S_BODYC), p('버프', S_BODYC), p('신규 스탯 버프', S_SMALL)],
    [p('1000015', S_BODYC), p('조건부 대미지', S_BODYC), p('HP조건 충족시 추가 대미지', S_BODYC), p('대미지', S_BODYC), p('이브 처형 패턴 확장', S_SMALL)],
]
story.append(header_table(nbuf_data, [W*0.12, W*0.18, W*0.28, W*0.12, W*0.22]))

story.append(Spacer(1, 8*mm))
story.append(p('6. 밸런스 비교 (기존 메타 캐릭터 대비)', S_H1))
story.append(Spacer(1, 3*mm))

# 서포터 비교
story.append(p('6-1. 서포터 비교', S_H3))
story.append(Spacer(1, 2*mm))
sup_data = [
    [p('', S_BODYBC), p('루미나\n(c600)', S_BODYBC), p('시트리', S_BODYBC), p('엘리시온', S_BODYBC), p('브라우니', S_BODYBC)],
    [p('ATK', S_BODYBC), p('230', S_BODYBC), p('210', S_BODYC), p('185', S_BODYC), p('195', S_BODYC)],
    [p('DEF', S_BODYBC), p('160', S_BODYBC), p('140', S_BODYC), p('145', S_BODYC), p('150', S_BODYC)],
    [p('HP', S_BODYBC), p('6800', S_BODYBC), p('5600', S_BODYC), p('5800', S_BODYC), p('5400', S_BODYC)],
    [p('SPD', S_BODYBC), p('120', S_BODYBC), p('110', S_BODYC), p('115', S_BODYC), p('118', S_BODYC)],
    [p('SP소모', S_BODYBC), p('3', S_BODYBC), p('4', S_BODYC), p('4', S_BODYC), p('3', S_BODYC)],
    [p('Active\n(최대)', S_BODYBC), p('ATK+35%\nSPD+25\n정화', S_BODY), p('ATK+25%', S_BODYC), p('SPD+15', S_BODYC), p('DEF+20%\n정화', S_BODYC)],
    [p('Ultimate\n(최대)', S_BODYBC), p('힐45%\nATK+45%\nCriDmg+60%\nSP+2', S_BODY), p('ATK+30%\nCriDmg+30%', S_BODYC), p('힐30%\nSP+1', S_BODYC), p('DEF+25%\n힐20%', S_BODYC)],
    [p('등급', S_BODYBC), p('SS+', S_BODYBC), p('S', S_BODYC), p('A+', S_BODYC), p('A', S_BODYC)],
]
cw_bal = [W*0.14, W*0.22, W*0.22, W*0.22, W*0.2]
t_sup = Table(sup_data, colWidths=cw_bal)
t_sup.setStyle(TableStyle([
    ('BACKGROUND', (0,0), (-1,0), C_HDR),
    ('TEXTCOLOR', (0,0), (-1,0), white),
    ('BACKGROUND', (0,1), (0,-1), HexColor('#E3F2FD')),
    ('BACKGROUND', (1,1), (1,-1), HexColor('#FFF8E1')),
    ('GRID', (0,0), (-1,-1), 0.5, C_BORDER),
    ('ALIGN', (0,0), (-1,-1), 'CENTER'),
    ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ('FONTNAME', (0,0), (-1,-1), FONT),
    ('FONTSIZE', (0,0), (-1,-1), 8.5),
    ('TOPPADDING', (0,0), (-1,-1), 3),
    ('BOTTOMPADDING', (0,0), (-1,-1), 3),
]))
story.append(t_sup)

story.append(Spacer(1, 5*mm))

# 딜러 비교
story.append(p('6-2. 딜러 비교', S_H3))
story.append(Spacer(1, 2*mm))
dps_data = [
    [p('', S_BODYBC), p('에레보스\n(c601)', S_BODYBC), p('이브', S_BODYBC), p('쿠바바', S_BODYBC), p('아르테미스', S_BODYBC)],
    [p('ATK', S_BODYBC), p('530', S_BODYBC), p('490', S_BODYC), p('430', S_BODYC), p('400', S_BODYC)],
    [p('CRI', S_BODYBC), p('35%', S_BODYBC), p('30%', S_BODYC), p('25%', S_BODYC), p('20%', S_BODYC)],
    [p('PEN', S_BODYBC), p('20%', S_BODYBC), p('15%', S_BODYC), p('10%', S_BODYC), p('5%', S_BODYC)],
    [p('SPD', S_BODYBC), p('80', S_BODYBC), p('75', S_BODYC), p('70', S_BODYC), p('78', S_BODYC)],
    [p('SP소모', S_BODYBC), p('5', S_BODYC), p('5', S_BODYC), p('6', S_BODYC), p('5', S_BODYC)],
    [p('Normal', S_BODYBC), p('250%x2\n(500%)', S_BODY), p('200%', S_BODYC), p('220%', S_BODYC), p('180%x2', S_BODYC)],
    [p('Active\n(최대)', S_BODYBC), p('600%+350%\n+DEF-30%', S_BODY), p('400%\n+HP30%처형', S_BODYC), p('450%', S_BODYC), p('350%x2', S_BODYC)],
    [p('Ultimate\n(최대)', S_BODYBC), p('AoE 450%\n+DEF-40%\n+출혈30%', S_BODY), p('AoE 280%', S_BODYC), p('AoE 350%', S_BODYC), p('AoE 300%\n+CRI', S_BODYC)],
    [p('등급', S_BODYBC), p('SS+', S_BODYBC), p('S+', S_BODYC), p('S', S_BODYC), p('A+', S_BODYC)],
]
t_dps = Table(dps_data, colWidths=cw_bal)
t_dps.setStyle(TableStyle([
    ('BACKGROUND', (0,0), (-1,0), C_HDR2),
    ('TEXTCOLOR', (0,0), (-1,0), white),
    ('BACKGROUND', (0,1), (0,-1), HexColor('#E3F2FD')),
    ('BACKGROUND', (1,1), (1,-1), HexColor('#E8F5E9')),
    ('GRID', (0,0), (-1,-1), 0.5, C_BORDER),
    ('ALIGN', (0,0), (-1,-1), 'CENTER'),
    ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ('FONTNAME', (0,0), (-1,-1), FONT),
    ('FONTSIZE', (0,0), (-1,-1), 8.5),
    ('TOPPADDING', (0,0), (-1,-1), 3),
    ('BOTTOMPADDING', (0,0), (-1,-1), 3),
]))
story.append(t_dps)

# ============================================================
# PAGE 7: ID 규칙 + 값 환산 가이드
# ============================================================
story.append(PageBreak())
story.append(p('7. ID 규칙 및 값 환산 가이드', S_H1))
story.append(Spacer(1, 4*mm))

story.append(p('7-1. Skill ID 구조', S_H3))
story.append(Spacer(1, 2*mm))
id_data = [
    [p('자리', S_BODYBC), p('1', S_BODYBC), p('2', S_BODYBC), p('3', S_BODYBC), p('4', S_BODYBC), p('5-6', S_BODYBC), p('7', S_BODYBC)],
    [p('의미', S_BODYC), p('SkillType', S_BODYC), p('GradeCode', S_BODYC), p('ElementCode', S_BODYC), p('RoleCode', S_BODYC), p('CharNum', S_BODYC), p('Variant', S_BODYC)],
    [p('루미나', S_BODYC), p('1~4', S_BODYC), p('5 (5성)', S_BODYC), p('4 (광)', S_BODYC), p('4 (서포터)', S_BODYC), p('60', S_BODYC), p('1~3', S_BODYC)],
    [p('에레보스', S_BODYC), p('1~4', S_BODYC), p('5 (5성)', S_BODYC), p('3 (목)', S_BODYC), p('1 (공격자)', S_BODYC), p('60', S_BODYC), p('1~3', S_BODYC)],
]
story.append(header_table(id_data, [W*0.1, W*0.14, W*0.14, W*0.14, W*0.14, W*0.14, W*0.14]))
story.append(Spacer(1, 1*mm))
story.append(p('SkillType: 1=Normal, 2=Active, 3=Ultimate, 4=Passive  |  Variant: 스킬 레벨 (1=Lv1, 2=Lv2, 3=Lv3)', S_SMALL))

story.append(Spacer(1, 5*mm))
story.append(p('7-2. BuffValue 값 환산', S_H3))
story.append(Spacer(1, 2*mm))
conv_data = [
    [p('항목', S_BODYBC), p('내부 값', S_BODYBC), p('실제 의미', S_BODYBC), p('예시', S_BODYBC)],
    [p('대미지 배율', S_BODYC), p('V1 x 1/1000', S_BODYC), p('ATK 대비 %', S_BODYC), p('120000 = 120%', S_BODYC)],
    [p('스탯 버프 (%)', S_BODYC), p('V1 x 1/1000', S_BODYC), p('기본 스탯 대비 %', S_BODYC), p('30000 = 30%', S_BODYC)],
    [p('스탯 버프 (고정)', S_BODYC), p('V1 x 1/1000', S_BODYC), p('고정 수치', S_BODYC), p('20000 = +20', S_BODYC)],
    [p('BuffRate', S_BODYC), p('100000 = 100%', S_BODYC), p('발동 확률', S_BODYC), p('5000 = 5%', S_BODYC)],
    [p('BuffTurn', S_BODYC), p('0 = 즉시', S_BODYC), p('지속 턴 수', S_BODYC), p('-1 = 영구', S_BODYC)],
    [p('V2 (Stat Code)', S_BODYC), p('1001~1010', S_BODYC), p('대상 스탯', S_BODYC), p('1001=ATK, 1003=DEF\n1005=CriDmg, 1010=SPD', S_BODYC)],
]
story.append(header_table(conv_data, [W*0.18, W*0.22, W*0.24, W*0.3]))

story.append(Spacer(1, 5*mm))
story.append(p('7-3. Target ID', S_H3))
story.append(Spacer(1, 2*mm))
tgt_data = [
    [p('Target ID', S_BODYBC), p('설명', S_BODYBC), p('사용처', S_BODYBC)],
    [p('2000011', S_BODYC), p('적 근접 1명', S_BODYC), p('Normal 공격', S_BODYC)],
    [p('2000012', S_BODYC), p('적 최저 HP', S_BODYC), p('에레보스 Active (처형)', S_BODYC)],
    [p('920001', S_BODYC), p('적 전체', S_BODYC), p('에레보스 Ultimate (AoE)', S_BODYC)],
    [p('1000000', S_BODYC), p('아군 전체', S_BODYC), p('루미나 Active/Ultimate', S_BODYC)],
    [p('1100000', S_BODYC), p('자신', S_BODYC), p('에레보스 Passive', S_BODYC)],
    [p('1200001', S_BODYC), p('피격 아군', S_BODYC), p('루미나 Passive2', S_BODYC)],
]
story.append(header_table(tgt_data, [W*0.18, W*0.35, W*0.4]))

story.append(Spacer(1, 5*mm))
story.append(p('7-4. ActionTriggerType', S_H3))
story.append(Spacer(1, 2*mm))
trg_data = [
    [p('Trigger', S_BODYBC), p('발동 시점', S_BODYBC), p('사용처', S_BODYBC)],
    [p('SignalHit', S_BODYC), p('타격 시 (대미지 적용)', S_BODYC), p('Normal/Active 공격', S_BODYC)],
    [p('Immediately', S_BODYC), p('즉시 (스킬 시전과 동시)', S_BODYC), p('루미나 Active/Ult 버프', S_BODYC)],
    [p('AttackEnd', S_BODYC), p('공격 종료 후', S_BODYC), p('에레보스 Active DEF감소, Ult 디버프', S_BODYC)],
    [p('BattleStart', S_BODYC), p('전투 시작 시', S_BODYC), p('양 캐릭터 Passive1', S_BODYC)],
    [p('OnKill', S_BODYC), p('적 처치 시', S_BODYC), p('에레보스 Passive2', S_BODYC)],
    [p('OnAllyDamaged', S_BODYC), p('아군 피격 시', S_BODYC), p('루미나 Passive2', S_BODYC)],
]
story.append(header_table(trg_data, [W*0.2, W*0.35, W*0.38]))

# === Build ===
doc.build(story)
print(f'PDF saved: {out_path}')
print('DONE')
