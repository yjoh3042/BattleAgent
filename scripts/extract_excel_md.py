import pandas as pd
import sys
import os

sys.stdout.reconfigure(encoding='utf-8')

output_lines = []

def add(line=""):
    output_lines.append(line)

def df_to_markdown(df):
    """DataFrame을 마크다운 표로 변환"""
    if df.empty:
        return "_데이터 없음_"
    cols = [str(c) for c in df.columns]
    header = "| " + " | ".join(cols) + " |"
    sep = "| " + " | ".join(["---"] * len(cols)) + " |"
    rows = []
    for _, row in df.iterrows():
        cells = []
        for v in row:
            if pd.isna(v):
                cells.append("")
            else:
                cells.append(str(v).replace("|", "\|").replace("\n", " "))
        rows.append("| " + " | ".join(cells) + " |")
    return "\n".join([header, sep] + rows)

def process_file(path, label):
    add(f"# {label}")
    add()
    xl = pd.ExcelFile(path)
    add(f"**파일 경로:** `{path}`")
    add(f"**시트 목록:** {xl.sheet_names}")
    add()

    for sheet in xl.sheet_names:
        add(f"## 시트: `{sheet}`")
        add()
        # 헤더 없이 읽기 (raw)
        df_raw = pd.read_excel(path, sheet_name=sheet, header=None)
        add(f"**크기:** {df_raw.shape[0]}행 × {df_raw.shape[1]}열")
        add()

        # 첫 행이 헤더인지 확인 - 문자열이 많으면 헤더로 사용
        first_row = df_raw.iloc[0]
        str_count = sum(1 for v in first_row if isinstance(v, str) and not pd.isna(v))
        total = len(first_row)

        if str_count / max(total, 1) > 0.5:
            # 첫 행을 헤더로 사용
            df = pd.read_excel(path, sheet_name=sheet, header=0)
            add(df_to_markdown(df))
        else:
            # 헤더 없이 출력
            df_raw.columns = [f"Col{i}" for i in range(df_raw.shape[1])]
            add(df_to_markdown(df_raw))

        add()

# Buff.xlsx 처리
process_file("C:/Ai/BattleAgent/data/Buff.xlsx", "Buff.xlsx")

# LogicFormula.xlsx 처리
process_file("C:/Ai/BattleAgent/data/LogicFormula.xlsx", "LogicFormula.xlsx")

# 파일 저장
out_path = "C:/Ai/BattleAgent/.omc/scientist/reports/excel_extraction.md"
with open(out_path, "w", encoding="utf-8") as f:
    f.write("\n".join(output_lines))

print(f"저장 완료: {out_path}")
print(f"총 줄 수: {len(output_lines)}")
