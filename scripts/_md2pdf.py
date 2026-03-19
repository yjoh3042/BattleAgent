"""META_GIMMICK_GUIDE.md → PDF 변환 스크립트 (reportlab + 한국어 폰트)"""
import re, sys, os
sys.stdout.reconfigure(encoding='utf-8')

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.colors import HexColor, black, white, Color
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, KeepTogether, HRFlowable
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# ── 폰트 등록 ──
FONT_DIR = "C:/Windows/Fonts"
pdfmetrics.registerFont(TTFont("Malgun", f"{FONT_DIR}/malgun.ttf"))
pdfmetrics.registerFont(TTFont("MalgunBd", f"{FONT_DIR}/malgunbd.ttf"))

FONT = "Malgun"
FONT_BD = "MalgunBd"

# ── 색상 ──
C_BG      = HexColor("#F8F9FA")
C_HEADER  = HexColor("#2C3E50")
C_ACCENT  = HexColor("#3498DB")
C_CODE_BG = HexColor("#F0F0F0")
C_TBL_HD  = HexColor("#34495E")
C_TBL_ALT = HexColor("#ECF0F1")
C_FIRE    = HexColor("#FFE0D0")
C_WATER   = HexColor("#D0E8FF")
C_FOREST  = HexColor("#D8F0D0")
C_LIGHT   = HexColor("#FFF8D0")
C_DARK    = HexColor("#E8D8F0")

# ── 이모지 제거 (폰트 미지원) ──
EMOJI_RE = re.compile(
    "[\U0001F300-\U0001F9FF\U00002600-\U000027BF\U0001FA00-\U0001FA6F"
    "\U0001FA70-\U0001FAFF\U00002702-\U000027B0\U0000FE0F]+")

def clean(text):
    """이모지 제거 + XML 이스케이프"""
    text = EMOJI_RE.sub("", text)
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return text.strip()

def bold_clean(text):
    """**bold** 마크다운 → <b> 태그 변환"""
    text = EMOJI_RE.sub("", text)
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
    text = re.sub(r'`(.+?)`', r'<font face="Courier" size="8" color="#E74C3C">\1</font>', text)
    return text.strip()

# ── 스타일 ──
styles = getSampleStyleSheet()

S_TITLE = ParagraphStyle("KTitle", fontName=FONT_BD, fontSize=22, leading=28,
                          textColor=C_HEADER, alignment=TA_CENTER, spaceAfter=4*mm)
S_SUB = ParagraphStyle("KSub", fontName=FONT, fontSize=10, leading=14,
                        textColor=HexColor("#7F8C8D"), alignment=TA_CENTER, spaceAfter=6*mm)
S_H1 = ParagraphStyle("KH1", fontName=FONT_BD, fontSize=16, leading=22,
                        textColor=C_HEADER, spaceBefore=8*mm, spaceAfter=3*mm)
S_H2 = ParagraphStyle("KH2", fontName=FONT_BD, fontSize=13, leading=18,
                        textColor=C_ACCENT, spaceBefore=5*mm, spaceAfter=2*mm)
S_H3 = ParagraphStyle("KH3", fontName=FONT_BD, fontSize=11, leading=15,
                        textColor=HexColor("#2980B9"), spaceBefore=3*mm, spaceAfter=2*mm)
S_BODY = ParagraphStyle("KBody", fontName=FONT, fontSize=9, leading=13,
                          textColor=black, spaceAfter=2*mm)
S_BODY_BD = ParagraphStyle("KBodyBd", fontName=FONT_BD, fontSize=9, leading=13,
                            textColor=black, spaceAfter=2*mm)
S_CODE = ParagraphStyle("KCode", fontName="Courier", fontSize=7.5, leading=10,
                         textColor=HexColor("#2C3E50"), backColor=C_CODE_BG,
                         leftIndent=4*mm, rightIndent=4*mm, spaceBefore=1*mm, spaceAfter=2*mm)
S_BULLET = ParagraphStyle("KBullet", fontName=FONT, fontSize=9, leading=13,
                           leftIndent=8*mm, bulletIndent=3*mm, spaceAfter=1*mm)
S_TBL_CELL = ParagraphStyle("KCell", fontName=FONT, fontSize=7.5, leading=10,
                              alignment=TA_CENTER)
S_TBL_CELL_L = ParagraphStyle("KCellL", fontName=FONT, fontSize=7.5, leading=10,
                                alignment=TA_LEFT)
S_TBL_HD_CELL = ParagraphStyle("KHdCell", fontName=FONT_BD, fontSize=7.5, leading=10,
                                 textColor=white, alignment=TA_CENTER)

# ── 마크다운 파싱 ──
def parse_md(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()
    return lines

def make_table(header, rows, col_widths=None):
    """마크다운 테이블 → reportlab Table"""
    hdr_cells = [Paragraph(bold_clean(c), S_TBL_HD_CELL) for c in header]
    data = [hdr_cells]
    for row in rows:
        data.append([Paragraph(bold_clean(c), S_TBL_CELL_L) for c in row])

    if not col_widths:
        page_w = A4[0] - 30*mm
        n = len(header)
        col_widths = [page_w / n] * n

    tbl = Table(data, colWidths=col_widths, repeatRows=1)
    style_cmds = [
        ('BACKGROUND', (0, 0), (-1, 0), C_TBL_HD),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('FONTNAME', (0, 0), (-1, 0), FONT_BD),
        ('FONTSIZE', (0, 0), (-1, -1), 7.5),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor("#BDC3C7")),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
    ]
    # 줄무늬
    for i in range(1, len(data)):
        if i % 2 == 0:
            style_cmds.append(('BACKGROUND', (0, i), (-1, i), C_TBL_ALT))
    tbl.setStyle(TableStyle(style_cmds))
    return tbl

def build_pdf(md_path, pdf_path):
    lines = parse_md(md_path)
    doc = SimpleDocTemplate(
        pdf_path, pagesize=A4,
        leftMargin=15*mm, rightMargin=15*mm,
        topMargin=15*mm, bottomMargin=15*mm
    )
    story = []

    i = 0
    in_code_block = False
    code_lines = []
    in_table = False
    table_header = []
    table_rows = []

    def flush_table():
        nonlocal in_table, table_header, table_rows
        if table_header and table_rows:
            page_w = A4[0] - 30*mm
            n = len(table_header)
            # 컬럼 수에 따라 적절한 폭 분배
            col_widths = [page_w / n] * n
            story.append(make_table(table_header, table_rows, col_widths))
            story.append(Spacer(1, 2*mm))
        in_table = False
        table_header = []
        table_rows = []

    def flush_code():
        nonlocal in_code_block, code_lines
        if code_lines:
            code_text = "<br/>".join(
                clean(l).replace(" ", "&nbsp;") for l in code_lines
            )
            story.append(Paragraph(code_text, S_CODE))
        in_code_block = False
        code_lines = []

    while i < len(lines):
        line = lines[i].rstrip("\n")

        # 코드 블록
        if line.strip().startswith("```"):
            if in_code_block:
                flush_code()
            else:
                if in_table:
                    flush_table()
                in_code_block = True
                code_lines = []
            i += 1
            continue

        if in_code_block:
            code_lines.append(line)
            i += 1
            continue

        # 테이블 행
        if "|" in line and line.strip().startswith("|"):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            # 구분자 행 (---) 스킵
            if all(re.match(r'^:?-+:?$', c) for c in cells):
                i += 1
                continue
            if not in_table:
                in_table = True
                table_header = cells
            else:
                table_rows.append(cells)
            i += 1
            continue
        else:
            if in_table:
                flush_table()

        stripped = line.strip()

        # 빈 줄
        if not stripped:
            i += 1
            continue

        # --- 구분선
        if stripped == "---" or stripped == "---\n":
            story.append(HRFlowable(width="100%", thickness=0.5, color=HexColor("#BDC3C7"),
                                     spaceBefore=3*mm, spaceAfter=3*mm))
            i += 1
            continue

        # 제목
        if stripped.startswith("# ") and not stripped.startswith("## "):
            story.append(Paragraph(bold_clean(stripped[2:]), S_TITLE))
            i += 1
            continue
        if stripped.startswith("## "):
            story.append(Paragraph(bold_clean(stripped[3:]), S_H1))
            i += 1
            continue
        if stripped.startswith("### "):
            story.append(Paragraph(bold_clean(stripped[4:]), S_H2))
            i += 1
            continue
        if stripped.startswith("#### "):
            story.append(Paragraph(bold_clean(stripped[5:]), S_H3))
            i += 1
            continue

        # 인용 (>)
        if stripped.startswith("> "):
            text = bold_clean(stripped[2:])
            s = ParagraphStyle("Quote", parent=S_BODY, textColor=HexColor("#7F8C8D"),
                               leftIndent=6*mm, fontSize=9)
            story.append(Paragraph(text, s))
            i += 1
            continue

        # 불릿
        if stripped.startswith("- ") or stripped.startswith("* "):
            text = bold_clean(stripped[2:])
            story.append(Paragraph(f"  * {text}", S_BULLET))
            i += 1
            continue

        # 번호 목록
        m = re.match(r'^(\d+)\.\s+(.+)', stripped)
        if m:
            text = bold_clean(m.group(2))
            story.append(Paragraph(f"  {m.group(1)}. {text}", S_BULLET))
            i += 1
            continue

        # 일반 텍스트
        story.append(Paragraph(bold_clean(stripped), S_BODY))
        i += 1

    # flush remaining
    if in_code_block:
        flush_code()
    if in_table:
        flush_table()

    # 빌드
    doc.build(story)
    print(f"PDF 생성 완료: {pdf_path}")
    print(f"  페이지 수: {len(story)} flowables")

if __name__ == "__main__":
    md_path = r"C:\Ai\BattleAgent\docs\META_GIMMICK_GUIDE.md"
    pdf_path = r"C:\Ai\BattleAgent\docs\META_GIMMICK_GUIDE.pdf"
    build_pdf(md_path, pdf_path)
