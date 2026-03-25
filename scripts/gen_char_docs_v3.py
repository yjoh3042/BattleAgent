"""캐릭터 스킬 컨셉 문서 자동 생성기 v3
xlsx 기반으로 docs/character/{이름}.md 를 70개 일괄 생성합니다.

읽는 컬럼: 성급, 속성, 직업, 캐릭터, 스킬타입, 스킬설명, 강화1, 강화2
"""
import sys
import pathlib
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")

XLSX_PATH = pathlib.Path(__file__).resolve().parents[1] / "data" / "스킬컨셉 NEW.xlsx"
OUT_DIR = pathlib.Path(__file__).resolve().parents[1] / "docs" / "character"

# ── 속성 상성 ──────────────────────────────────────────────────
ELEM_ADVANTAGE = {
    "Fire":   ("Forest", "Water"),
    "Water":  ("Fire",   "Forest"),
    "Forest": ("Water",  "Fire"),
    "Light":  ("Dark",   None),
    "Dark":   ("Light",  None),
}

# ── 속성 한글 매핑 ─────────────────────────────────────────────
ELEM_KR = {
    "Fire":   "화염",
    "Water":  "수",
    "Forest": "목",
    "Light":  "광",
    "Dark":   "암",
}

# ── 직업 약점 설명 ─────────────────────────────────────────────
ROLE_WEAKNESS = {
    "Attacker":  "낮은 방어력 — 집중 공격에 취약",
    "Magician":  "낮은 HP/DEF — 선공을 잡히면 위험",
    "Defender":  "낮은 화력 — 딜 기여도 낮음",
    "Healer":    "낮은 공격력 — 전투 기여는 회복에 의존",
    "Supporter": "낮은 단독 전투력 — 아군 없이 무력",
}

# ── 역할 강점 키워드 매핑 ──────────────────────────────────────
ROLE_STRENGTH_PREFIX = {
    "Attacker":  "고배율 공격",
    "Magician":  "광역 CC/디버프",
    "Defender":  "도발·반격 생존",
    "Healer":    "팀 회복·정화",
    "Supporter": "팀 버프·시너지",
}

# ── 스킬 설명에서 강점 키워드 추출 ─────────────────────────────
STRENGTH_KEYWORDS = [
    "화상", "빙결", "수면", "기절", "침묵", "중독", "출혈", "감전", "석화", "공포",
    "치명타", "크리", "관통", "속도", "방어력", "공격력", "보호막", "도발", "반격",
    "부활", "면역", "디버프 제거", "버프 제거", "SP 증가", "SP 강탈",
    "연타", "광역", "전체 대미지", "처형", "즉사",
]


def extract_strength_keywords(skill_texts: list[str]) -> str:
    found = []
    combined = " ".join(t for t in skill_texts if isinstance(t, str))
    for kw in STRENGTH_KEYWORDS:
        if kw in combined and kw not in found:
            found.append(kw)
    if not found:
        return "기본기 충실"
    return ", ".join(found[:4])


def safe(val) -> str:
    """NaN → 빈 문자열"""
    if pd.isna(val):
        return ""
    return str(val).strip()


def elem_compat(elem: str) -> tuple[str, str]:
    """유리/불리 속성 반환 (한글)"""
    adv, dis = ELEM_ADVANTAGE.get(elem, (None, None))
    adv_str = ELEM_KR.get(adv, adv) if adv else "없음"
    dis_str = ELEM_KR.get(dis, dis) if dis else "없음"
    return adv_str, dis_str


def grade_str(grade) -> str:
    try:
        g = float(grade)
        if g == int(g):
            return f"{int(g)}"
        return str(g)
    except Exception:
        return str(grade)


def build_doc(char_name: str, skills: dict, meta: dict) -> str:
    """
    skills: { '노멀': {desc, enh1, enh2}, '액티브': ..., '얼티밋': ..., '패시브': ... }
    meta:   { elem, role, grade }
    """
    elem = meta.get("elem", "")
    role = meta.get("role", "")
    grade = meta.get("grade", "")

    adv, dis = elem_compat(elem)

    skill_texts = [v.get("desc", "") for v in skills.values()]
    strength_kw = extract_strength_keywords(skill_texts)
    role_prefix = ROLE_STRENGTH_PREFIX.get(role, "")
    strength = f"{role_prefix} — {strength_kw}" if role_prefix else strength_kw
    weakness = ROLE_WEAKNESS.get(role, "역할 특성에 따른 취약점")

    lines = []
    lines.append(f"# {char_name} — 스킬 컨셉 상세 기획서\n")

    lines.append("## 캐릭터 아이덴티티")
    lines.append("| 항목 | 값 |")
    lines.append("|---|---|")
    lines.append(f"| 속성 | {elem} |")
    lines.append(f"| 직업 | {role} |")
    lines.append(f"| 성급 | {grade_str(grade)}★ |\n")

    lines.append("## 스킬 상세\n")

    for skill_type in ["노멀", "액티브", "얼티밋", "패시브"]:
        s = skills.get(skill_type, {})
        desc = s.get("desc", "—")
        enh1 = s.get("enh1", "—")
        enh2 = s.get("enh2", "—")
        lines.append(f"### {skill_type}")
        lines.append(f"- 설명: {desc if desc else '—'}")
        lines.append(f"- 강화+1: {enh1 if enh1 else '—'}")
        lines.append(f"- 강화+2: {enh2 if enh2 else '—'}\n")

    lines.append("## 속성 상성")
    lines.append(f"- 유리: {adv}속성")
    lines.append(f"- 불리: {dis}속성\n")

    lines.append("## 핵심 포인트")
    lines.append(f"- 강점: {strength}")
    lines.append(f"- 약점: {weakness}")
    lines.append("")

    return "\n".join(lines)


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    df = pd.read_excel(XLSX_PATH, header=0)
    # 컬럼 정규화
    df.columns = [str(c).strip() for c in df.columns]

    # 실제 컬럼명 확인 후 매핑
    col_map = {}
    for col in df.columns:
        lc = col.lower()
        if "성급" in col:
            col_map["grade"] = col
        elif "속성" in col:
            col_map["elem"] = col
        elif "직업" in col:
            col_map["role"] = col
        elif "캐릭터" in col:
            col_map["char"] = col
        elif "스킬타입" in col or "스킬 타입" in col:
            col_map["skill_type"] = col
        elif "스킬설명" in col or "스킬 설명" in col:
            col_map["desc"] = col
        elif "강화" in col and "+1" in col or col.endswith("1") and "강화" in col:
            col_map["enh1"] = col
        elif "강화" in col and "+2" in col or col.endswith("2") and "강화" in col:
            col_map["enh2"] = col

    # fallback: positional (성급=0, 속성=1, 직업=2, 캐릭터=3, 스킬타입=4, 스킬설명=5, 강화1=6, 강화2=7)
    cols = list(df.columns)
    if "grade" not in col_map and len(cols) > 0:
        col_map["grade"] = cols[0]
    if "elem" not in col_map and len(cols) > 1:
        col_map["elem"] = cols[1]
    if "role" not in col_map and len(cols) > 2:
        col_map["role"] = cols[2]
    if "char" not in col_map and len(cols) > 3:
        col_map["char"] = cols[3]
    if "skill_type" not in col_map and len(cols) > 4:
        col_map["skill_type"] = cols[4]
    if "desc" not in col_map and len(cols) > 5:
        col_map["desc"] = cols[5]
    if "enh1" not in col_map and len(cols) > 6:
        col_map["enh1"] = cols[6]
    if "enh2" not in col_map and len(cols) > 7:
        col_map["enh2"] = cols[7]

    print("컬럼 매핑:", col_map)

    # 캐릭터별 데이터 수집
    # key: (char_name, grade, elem, role) → skills dict
    char_data: dict[tuple, dict] = {}
    char_order: list[tuple] = []

    for _, row in df.iterrows():
        char_name = safe(row.get(col_map.get("char", ""), ""))
        if not char_name:
            continue
        grade = safe(row.get(col_map.get("grade", ""), ""))
        elem = safe(row.get(col_map.get("elem", ""), ""))
        role = safe(row.get(col_map.get("role", ""), ""))
        skill_type = safe(row.get(col_map.get("skill_type", ""), ""))
        desc = safe(row.get(col_map.get("desc", ""), ""))
        enh1 = safe(row.get(col_map.get("enh1", ""), ""))
        enh2 = safe(row.get(col_map.get("enh2", ""), ""))

        key = (char_name, grade, elem, role)
        if key not in char_data:
            char_data[key] = {}
            char_order.append(key)

        char_data[key][skill_type] = {"desc": desc, "enh1": enh1, "enh2": enh2}

    print(f"캐릭터 수: {len(char_data)}")

    # 중복 이름 처리: 같은 이름이 여러 key에 있으면 파일명 구분
    # 이름 → [key, ...] 매핑
    name_to_keys: dict[str, list] = {}
    for key in char_order:
        name = key[0]
        if name not in name_to_keys:
            name_to_keys[name] = []
        name_to_keys[name].append(key)

    # 파일명 결정
    def filename_for(key):
        name, grade, elem, role = key
        others = name_to_keys[name]
        if len(others) == 1:
            return f"{name}.md"
        # 중복: 이름 끝에 숫자 suffix 없으면 첫번째가 원본, 나머지는 이름2, 이름3
        # 또는 이미 이름에 숫자가 붙어있으면 그대로
        idx = others.index(key)
        if idx == 0:
            return f"{name}.md"
        else:
            return f"{name}{idx + 1}.md"

    generated = 0
    for key in char_order:
        name, grade, elem, role = key
        skills = char_data[key]
        meta = {"elem": elem, "role": role, "grade": grade}
        content = build_doc(name, skills, meta)
        fname = filename_for(key)
        out_path = OUT_DIR / fname
        out_path.write_text(content, encoding="utf-8")
        generated += 1
        print(f"  [{generated:02d}] {fname}")

    print(f"\n완료: {generated}개 문서 생성 → {OUT_DIR}")


if __name__ == "__main__":
    main()
