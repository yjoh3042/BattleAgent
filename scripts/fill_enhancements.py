"""스킬컨셉 NEW.xlsx 강화+1, 강화+2 자동 채우기

강화 원칙:
  강화+1: 기존 효과의 수치 강화 또는 부가 효과 1개 추가
  강화+2: 새로운 기믹 추가 (조건부 발동, 추가 CC, 범위 확대 등)

스킬타입별 강화 방향:
  노멀:   +1 = 부가 효과 추가 (소량 회복, 소량 버프)
          +2 = 조건부 추가 효과 (확률 2타, CC 확률)
  액티브: +1 = 기존 효과 강화 (배율↑, 대상 수↑, 확률↑)
          +2 = 새 기믹 추가 (추가 CC, 버프, 연계 효과)
  얼티밋: +1 = 기존 효과 강화 (배율↑, 범위↑)
          +2 = 강력한 추가 기믹 (추가턴, 쿨초기화, 연쇄 효과)
  패시브: +1 = 발동 조건 완화 또는 효과 수치 증가
          +2 = 2차 트리거 추가 또는 팀 확장 효과
"""
import pandas as pd
import re


def detect_keywords(desc: str) -> dict:
    """스킬 설명에서 키워드를 감지하여 딕셔너리로 반환."""
    d = str(desc)
    return {
        "damage": "대미지" in d or "공격" in d,
        "heal": "회복" in d or "힐" in d,
        "burn": "화상" in d,
        "freeze": "빙결" in d,
        "bleed": "출혈" in d,
        "sleep": "수면" in d,
        "stun": "기절" in d,
        "silence": "침묵" in d,
        "confuse": "혼란" in d,
        "poison": "중독" in d or "독" in d,
        "spd": "속도" in d,
        "def": "방어력" in d,
        "atk": "공격력" in d,
        "crit": "치명타" in d or "크리" in d,
        "dodge": "회피" in d,
        "taunt": "도발" in d,
        "counter": "반격" in d,
        "shield": "보호막" in d or "쉴드" in d,
        "sp": "SP" in d or "sp" in d,
        "buff": "버프" in d,
        "debuff": "디버프" in d,
        "revive": "부활" in d,
        "immune": "면역" in d,
        "aoe": "전체" in d,
        "front": "전열" in d,
        "back": "후열" in d,
        "line": "직선" in d,
        "cross": "십자" in d,
        "multi_hit": "타 대미지" in d,
        "self_buff": "자신" in d and ("증가" in d or "버프" in d),
        "ally_buff": "아군" in d and "증가" in d,
        "cooldown": "쿨타임" in d,
        "kill": "처치" in d or "죽" in d or "사망" in d,
        "instant_kill": "즉사" in d,
        "hp_cond": "HP" in d or "체력" in d,
        "spread": "전이" in d or "확산" in d,
        "remove": "제거" in d,
        "absorb": "흡혈" in d,
        "contract": "계약" in d,
    }


# ──────────────────────────────────────────────────────────────
# 노멀 스킬 강화
# ──────────────────────────────────────────────────────────────

def enhance_normal(row, kw, elem, role):
    """노멀 스킬 강화+1, +2 생성."""
    # +1: 소량 부가 효과
    e1_options = {
        ("Fire", "Attacker"):     ("대미지 +10%", "30% 확률로 화상 부여"),
        ("Fire", "Magician"):     ("대미지 +10%", "30% 확률로 화상 부여"),
        ("Fire", "Defender"):     ("피격 시 자힐 5%", "30% 확률로 공격자에게 화상"),
        ("Fire", "Healer"):       ("대미지 +10%", "적중 시 아군 최저HP 소량 회복"),
        ("Fire", "Supporter"):    ("대미지 +10%", "적중 시 아군 1명 공격력 소폭 증가"),
        ("Water", "Attacker"):    ("대미지 +10%", "30% 확률로 속도 감소"),
        ("Water", "Magician"):    ("대미지 +10%", "30% 확률로 속도 감소"),
        ("Water", "Defender"):    ("피격 시 자힐 5%", "적중 시 자신 속도 소폭 증가"),
        ("Water", "Healer"):      ("대미지 +10%", "적중 시 아군 최저HP 소량 회복"),
        ("Water", "Supporter"):   ("대미지 +10%", "적중 시 아군 1명 속도 소폭 증가"),
        ("Forest", "Attacker"):   ("대미지 +10%", "30% 확률로 대상 방어력 감소"),
        ("Forest", "Magician"):   ("대미지 +10%", "30% 확률로 수면 부여"),
        ("Forest", "Defender"):   ("피격 시 자힐 5%", "적중 시 자신 방어력 소폭 증가"),
        ("Forest", "Healer"):     ("대미지 +10%", "적중 시 아군 최저HP 소량 회복"),
        ("Forest", "Supporter"):  ("대미지 +10%", "적중 시 아군 1명 방어력 소폭 증가"),
        ("Light", "Attacker"):    ("대미지 +10%", "30% 확률로 대상 버프 1개 제거"),
        ("Light", "Magician"):    ("대미지 +10%", "30% 확률로 대상 버프 1개 제거"),
        ("Light", "Defender"):    ("피격 시 자힐 5%", "적중 시 자신에게 소량 보호막"),
        ("Light", "Healer"):      ("대미지 +10%", "적중 시 아군 최저HP 소량 회복"),
        ("Light", "Supporter"):   ("대미지 +10%", "적중 시 아군 1명 소량 보호막"),
        ("Dark", "Attacker"):     ("대미지 +10%", "치명타 시 추가 대미지 +15%"),
        ("Dark", "Magician"):     ("대미지 +10%", "치명타 시 추가 대미지 +15%"),
        ("Dark", "Defender"):     ("피격 시 자힐 5%", "적중 시 30% 확률로 도발"),
        ("Dark", "Healer"):       ("대미지 +10%", "적중 시 아군 최저HP 소량 회복"),
        ("Dark", "Supporter"):    ("대미지 +10%", "적중 시 아군 1명 치명타 확률 소폭 증가"),
    }
    key = (elem, role)
    e1, e2 = e1_options.get(key, ("대미지 +10%", "30% 확률로 추가 효과"))
    return e1, e2


# ──────────────────────────────────────────────────────────────
# 액티브 스킬 강화
# ──────────────────────────────────────────────────────────────

def enhance_active(row, kw, elem, role):
    """액티브 스킬 강화+1, +2 생성."""
    desc = str(row['스킬설명'])

    # +1: 기존 효과 강화
    if kw["self_buff"]:
        e1 = "버프 수치 +10% 증가"
    elif kw["heal"]:
        e1 = "회복량 +15%"
    elif kw["shield"]:
        e1 = "보호막 수치 +15%"
    elif kw["multi_hit"]:
        e1 = "타격 횟수 +1"
    elif kw["damage"]:
        e1 = "대미지 +15%"
    else:
        e1 = "효과 수치 +15%"

    # +2: 새 기믹 추가 (속성+직업 기반)
    e2_map = {
        # Fire
        ("Fire", "Attacker"):     "적중 시 화상 중인 대상 추가 대미지 +20%",
        ("Fire", "Magician"):     "화상 중인 적에게 치명타 확률 +30%",
        ("Fire", "Defender"):     "사용 후 2턴간 피격 시 공격자에게 화상 부여",
        ("Fire", "Healer"):       "회복 대상에게 화상 면역 2턴 부여",
        ("Fire", "Supporter"):    "화속성 아군 추가로 공격력 +10%",
        # Water
        ("Water", "Attacker"):    "빙결 중인 적 대상 대미지 2배",
        ("Water", "Magician"):    "적중 시 50% 확률로 빙결 1턴",
        ("Water", "Defender"):    "사용 후 2턴간 자신 회피율 증가",
        ("Water", "Healer"):      "회복 대상의 속도 +15 증가 2턴",
        ("Water", "Supporter"):   "수속성 아군 추가로 속도 +10",
        # Forest
        ("Forest", "Attacker"):   "방어력 감소 중인 적 대상 추가 대미지 +20%",
        ("Forest", "Magician"):   "수면 중인 적에게 방어력 무시 대미지",
        ("Forest", "Defender"):   "사용 후 2턴간 받는 대미지 -15%",
        ("Forest", "Healer"):     "회복 대상에게 방어력 +20% 2턴 부여",
        ("Forest", "Supporter"):  "목속성 아군 추가로 방어력 +10%",
        # Light
        ("Light", "Attacker"):    "보호막이 있는 적 대상 보호막 무시 대미지",
        ("Light", "Magician"):    "적의 버프 1개당 추가 대미지 +5%",
        ("Light", "Defender"):    "사용 후 인접 아군에게 보호막 부여",
        ("Light", "Healer"):      "부활 대상 HP +20% 추가 회복",
        ("Light", "Supporter"):   "보호막 중인 아군 추가로 공격력 +10%",
        # Dark
        ("Dark", "Attacker"):     "치명타 발생 시 대상에게 출혈 부여",
        ("Dark", "Magician"):     "치명타 확률 중첩 최대치 +1 증가",
        ("Dark", "Defender"):     "반격 시 50% 확률로 대상 침묵 부여",
        ("Dark", "Healer"):       "회복 대상에게 치명타 확률 +10% 2턴 부여",
        ("Dark", "Supporter"):    "암속성 아군 추가로 치명타 대미지 +15%",
    }
    e2 = e2_map.get((elem, role), "추가 효과 부여")

    # 특수 케이스 처리
    if kw["taunt"]:
        e1 = "도발 지속 +1턴"
        e2 = "도발 중 받는 대미지 -10%"
    if kw["counter"]:
        e1 = "반격 확률 +15%"
    if kw["revive"]:
        e1 = "부활 HP +15% 증가"
        e2 = "부활 대상에게 2턴간 받는 대미지 -20%"
    if kw["cooldown"]:
        e1 = "쿨타임 감소량 +1"
    if kw["absorb"]:
        e1 = "흡혈 비율 +10%"
    if kw["contract"]:
        e1 = "계약 회복량 +15%"
        e2 = "계약 대상 방어력 추가 +10%"
    if kw["immune"]:
        e1 = "면역 지속 +1턴"
    if kw["sp"]:
        e1 = "SP 획득 조건 완화"
    if kw["spread"]:
        e1 = "전이 범위 +1명 추가"

    return e1, e2


# ──────────────────────────────────────────────────────────────
# 얼티밋 스킬 강화
# ──────────────────────────────────────────────────────────────

def enhance_ultimate(row, kw, elem, role):
    """얼티밋 스킬 강화+1, +2 생성."""
    # +1: 기존 효과 강화
    if kw["heal"]:
        e1 = "회복량 +20%"
    elif kw["shield"]:
        e1 = "보호막 수치 +20%"
    elif kw["multi_hit"]:
        e1 = "타격 횟수 +2"
    elif kw["damage"]:
        e1 = "대미지 +20%"
    else:
        e1 = "효과 수치 +20%"

    # 특수 효과 기반 +1 보정
    if kw["burn"]:
        e1 = "대미지 +20%, 화상 스택 +1 추가"
    if kw["freeze"]:
        e1 = "대미지 +20%, 빙결 확률 +20%"
    if kw["sleep"]:
        e1 = "대미지 +20%, 수면 지속 +1턴"
    if kw["bleed"]:
        e1 = "대미지 +20%, 출혈 지속 +1턴"
    if kw["stun"]:
        e1 = "대미지 +20%, 기절 확률 +20%"
    if kw["silence"]:
        e1 = "대미지 +20%, 침묵 확률 +20%"
    if kw["revive"]:
        e1 = "부활 HP +20% 증가"
    if kw["remove"]:
        e1 = "제거 개수 +1 추가"
    if kw["taunt"]:
        e1 = "도발 지속 +1턴"

    # +2: 강력한 추가 기믹 (속성+직업)
    e2_map = {
        # Fire
        ("Fire", "Attacker"):     "화상 중인 적 처치 시 SP +1",
        ("Fire", "Magician"):     "화상 중인 적 수만큼 전체 대미지 +10% 증가",
        ("Fire", "Defender"):     "사용 후 3턴간 아군 전체 받는 대미지 -10%",
        ("Fire", "Healer"):       "회복 후 아군 전체 디버프 1개 추가 제거",
        ("Fire", "Supporter"):    "화속성 아군 3턴간 공격력 +20% 추가 버프",
        # Water
        ("Water", "Attacker"):    "빙결 중인 적 대상 방어력 무시 대미지",
        ("Water", "Magician"):    "속도가 감소된 적에게 추가 대미지 +30%",
        ("Water", "Defender"):    "사용 후 아군 전체 속도 +10 증가 2턴",
        ("Water", "Healer"):      "회복 후 아군 전체 회피율 증가 2턴",
        ("Water", "Supporter"):   "사용 후 가장 빠른 아군 즉시 턴 획득",
        # Forest
        ("Forest", "Attacker"):   "수면 또는 방어력 감소 중인 적에게 추가 대미지 +30%",
        ("Forest", "Magician"):   "수면 중인 적 수만큼 전체 대미지 +15% 증가",
        ("Forest", "Defender"):   "사용 후 3턴간 아군 전체 방어력 +15%",
        ("Forest", "Healer"):     "회복 후 아군 전체 디버프 1개 추가 제거",
        ("Forest", "Supporter"):  "목속성 아군 3턴간 방어력 +20% 추가 버프",
        # Light
        ("Light", "Attacker"):    "버프가 없는 적에게 추가 대미지 +30%",
        ("Light", "Magician"):    "디버프 중인 적 수만큼 아군 보호막 강화",
        ("Light", "Defender"):    "보호막이 깨지지 않은 아군 공격력 +15% 2턴",
        ("Light", "Healer"):      "부활 대상에게 3턴간 받는 대미지 -30%",
        ("Light", "Supporter"):   "버프 중인 아군 수만큼 전체 버프 지속 +1턴",
        # Dark
        ("Dark", "Attacker"):     "적 처치 시 자신 즉시 추가턴 획득",
        ("Dark", "Magician"):     "침묵 또는 출혈 중인 적에게 추가 대미지 +30%",
        ("Dark", "Defender"):     "도발 대상 공격 시 받는 대미지 흡혈 30%",
        ("Dark", "Healer"):       "출혈 중인 적이 있으면 회복량 +30% 추가",
        ("Dark", "Supporter"):    "암속성 아군 3턴간 치명타 확률 +15% 추가 버프",
    }
    e2 = e2_map.get((elem, role), "추가 기믹 부여")

    if kw["instant_kill"]:
        e1 = "즉사 HP 기준 30% → 40%로 상향"
        e2 = "즉사 성공 시 아군 전체 공격력 +20% 3턴"
    if kw["confuse"]:
        e1 = "혼란 확률 +20%"
    if kw["ally_buff"] and kw["spd"]:
        e1 = "속도 증가 수치 +10 추가"

    return e1, e2


# ──────────────────────────────────────────────────────────────
# 패시브 스킬 강화
# ──────────────────────────────────────────────────────────────

def enhance_passive(row, kw, elem, role):
    """패시브 스킬 강화+1, +2 생성."""
    desc = str(row['스킬설명'])

    # +1: 효과 수치 증가 또는 조건 완화
    if kw["damage"]:
        e1 = "추가 대미지 수치 +15%"
    elif kw["heal"]:
        e1 = "회복량 +15%"
    elif kw["def"]:
        e1 = "방어력 증가 수치 +15%"
    elif kw["atk"]:
        e1 = "공격력 증가 수치 +15%"
    elif kw["crit"]:
        e1 = "치명타 관련 수치 +10%"
    elif kw["spd"]:
        e1 = "속도 관련 수치 +10"
    elif kw["sp"]:
        e1 = "SP 획득 확률 5% → 10%"
    elif kw["dodge"]:
        e1 = "회피 관련 수치 +10%"
    elif kw["shield"]:
        e1 = "보호막 수치 +15%"
    elif kw["remove"]:
        e1 = "제거 개수 +1 추가"
    elif kw["cooldown"]:
        e1 = "쿨타임 감소량 +1"
    elif kw["absorb"]:
        e1 = "흡혈 비율 +10%"
    elif kw["counter"]:
        e1 = "반격 대미지 +20%"
    else:
        e1 = "효과 수치 +15%"

    # 확률 기반 패시브 +1 보정
    if "확률" in desc:
        pct = re.search(r'(\d+)%', desc)
        if pct:
            old = int(pct.group(1))
            new = min(old + 15, 100)
            e1 = f"발동 확률 {old}% → {new}%"

    # 이미 채워진 니르티 케이스 보존
    if row['캐릭터'] == '니르티' and kw.get("freeze", False):
        e1 = "빙결 중인 적 대상 대미지 증가"

    # +2: 2차 트리거 또는 팀 확장
    e2_map = {
        ("Fire", "Attacker"):     "화상 중인 적 처치 시 아군 전체 공격력 +10% 2턴",
        ("Fire", "Magician"):     "화상 부여 시 30% 확률로 화상 스택 +1 추가",
        ("Fire", "Defender"):     "피격 시 20% 확률로 자힐 10%",
        ("Fire", "Healer"):       "디버프 제거 시 대상에게 공격력 +10% 2턴",
        ("Fire", "Supporter"):    "화속성 아군 버프 지속 +1턴 증가",
        ("Water", "Attacker"):    "속도 차이 클수록 치명타 확률 추가 증가",
        ("Water", "Magician"):    "빙결 부여 시 대상 속도 추가 감소",
        ("Water", "Defender"):    "속도가 높을수록 받는 대미지 추가 감소",
        ("Water", "Healer"):      "회복 시 대상 디버프 1개 추가 제거",
        ("Water", "Supporter"):   "수속성 아군 속도 +5 추가",
        ("Forest", "Attacker"):   "방어력 감소 적 처치 시 자신 방어력 +10% 2턴",
        ("Forest", "Magician"):   "수면 부여 시 대상 방어력 추가 감소",
        ("Forest", "Defender"):   "버프 1개당 받는 대미지 추가 -3%",
        ("Forest", "Healer"):     "회복 시 대상 방어력 +10% 2턴",
        ("Forest", "Supporter"):  "목속성 아군 디버프 지속 -1턴 감소",
        ("Light", "Attacker"):    "버프 제거 성공 시 자신 공격력 +10% 2턴",
        ("Light", "Magician"):    "디버프 제거 시 제거한 수만큼 자신 공격력 증가",
        ("Light", "Defender"):    "보호막 파괴 시 자신 방어력 +15% 2턴",
        ("Light", "Healer"):      "부활 아군에게 추가로 디버프 면역 2턴",
        ("Light", "Supporter"):   "보호막 아군의 버프 지속 +1턴",
        ("Dark", "Attacker"):     "치명타 적 처치 시 자신 공격력 +15% 2턴",
        ("Dark", "Magician"):     "침묵 부여 시 대상 받는 대미지 +10% 2턴",
        ("Dark", "Defender"):     "도발 대상 처치 시 자신 HP 10% 회복",
        ("Dark", "Healer"):       "출혈 적 수만큼 회복량 +5% 증가",
        ("Dark", "Supporter"):    "치명타 발생 시 해당 아군 디버프 1개 제거",
    }
    e2 = e2_map.get((elem, role), "추가 트리거 효과 부여")

    return e1, e2


# ──────────────────────────────────────────────────────────────
# 메인 실행
# ──────────────────────────────────────────────────────────────

def main():
    path = "data/스킬컨셉 NEW.xlsx"
    df = pd.read_excel(path, header=0)
    original_cols = list(df.columns)
    df.columns = ['성급', '속성', '직업', '캐릭터', '스킬타입', '스킬설명', '강화1', '강화2', '비고']

    # NaN-only 컬럼이 float64로 추론되므로 object로 변환
    df['강화1'] = df['강화1'].astype(object)
    df['강화2'] = df['강화2'].astype(object)

    filled_1 = 0
    filled_2 = 0

    for idx, row in df.iterrows():
        elem = row['속성']
        role = row['직업']
        stype = row['스킬타입']
        desc = str(row['스킬설명']) if pd.notna(row['스킬설명']) else ""
        kw = detect_keywords(desc)

        # 이미 채워진 강화+1은 보존 (니르티)
        already_e1 = pd.notna(row['강화1'])
        already_e2 = pd.notna(row['강화2'])

        if stype == '노멀':
            e1, e2 = enhance_normal(row, kw, elem, role)
        elif stype == '액티브':
            e1, e2 = enhance_active(row, kw, elem, role)
        elif stype == '얼티밋':
            e1, e2 = enhance_ultimate(row, kw, elem, role)
        elif stype == '패시브':
            e1, e2 = enhance_passive(row, kw, elem, role)
        else:
            continue

        if not already_e1:
            df.at[idx, '강화1'] = e1
            filled_1 += 1
        if not already_e2:
            df.at[idx, '강화2'] = e2
            filled_2 += 1

    df.columns = original_cols
    df.to_excel(path, index=False)

    print(f"강화+1 채운 수: {filled_1}개")
    print(f"강화+2 채운 수: {filled_2}개")

    # 검증
    df2 = pd.read_excel(path, header=0)
    e1_empty = df2.iloc[:, 6].isna().sum()
    e2_empty = df2.iloc[:, 7].isna().sum()
    print(f"\n남은 빈칸 — 강화+1: {e1_empty}, 강화+2: {e2_empty}")


if __name__ == "__main__":
    main()
