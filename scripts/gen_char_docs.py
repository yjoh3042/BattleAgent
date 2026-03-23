"""캐릭터 스킬 컨셉 문서 자동 생성기 v2
docs/character/{이름}.md 형식으로 70개 캐릭터 풀 컨셉 기획서를 일괄 생성합니다.

포함 섹션:
  1. 캐릭터 아이덴티티 (스탯/속성/역할)
  2. 스킬 상세 (노말/액티브/얼티밋/패시브 + 트리거)
  3. 설계 의도 & 밸런스 히스토리
  4. 이상적 전투 흐름 (5턴 시나리오)
  5. 시너지 & 카운터 분석
  6. 메타 참여 / 속성 상성 / 핵심 포인트
"""
import sys, os, pathlib, re, textwrap
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
sys.stdout.reconfigure(encoding="utf-8")

from fixtures.test_data import *
from battle.enums import Element, Role, LogicType, TargetType, TriggerEvent, CCType

# ═══════════════════════════════════════════════════════════════
# 한글 매핑 테이블
# ═══════════════════════════════════════════════════════════════
ELEM_KR = {
    Element.FIRE: ("🔥", "화", "FIRE"),
    Element.WATER: ("💧", "수", "WATER"),
    Element.FOREST: ("🌿", "목", "FOREST"),
    Element.LIGHT: ("✨", "광", "LIGHT"),
    Element.DARK: ("🌙", "암", "DARK"),
}
ROLE_KR = {
    Role.ATTACKER: ("⚔️", "공격형", "ATTACKER"),
    Role.MAGICIAN: ("🔮", "구속형", "MAGICIAN"),
    Role.DEFENDER: ("🛡️", "방어형", "DEFENDER"),
    Role.HEALER: ("💚", "회복형", "HEALER"),
    Role.SUPPORTER: ("🌟", "서포터", "SUPPORTER"),
}
LOGIC_KR = {
    LogicType.DAMAGE: "일반 데미지",
    LogicType.DAMAGE_BURN_BONUS: "화상 보너스 데미지 (화상 대상 2배+강제크리)",
    LogicType.DAMAGE_ESCALATE: "사용횟수 비례 피해 증가",
    LogicType.DAMAGE_REPEAT_TARGET: "같은 적 반복공격 피해 증가",
    LogicType.DAMAGE_MISSING_HP_SCALE: "잃은 HP 비례 피해 증가",
    LogicType.DAMAGE_PENETRATION: "DEF 무시 관통 데미지",
    LogicType.DAMAGE_HP_RATIO: "대상 최대HP% 데미지",
    LogicType.DAMAGE_CRI: "확정 크리티컬 데미지",
    LogicType.DAMAGE_BUFF_SCALE: "시전자 버프 수 비례 데미지",
    LogicType.DAMAGE_BUFF_SCALE_TARGET: "타겟 버프 수 비례 데미지",
    LogicType.DAMAGE_DEBUFF_SCALE_TARGET: "타겟 디버프 수 비례 데미지",
    LogicType.HEAL_HP_RATIO: "최대HP 비율 회복",
    LogicType.HEAL_PER_HIT: "적중 수 비례 회복",
    LogicType.HEAL_LOSS_SCALE: "잃은 HP 비례 회복",
    LogicType.HEAL_CURRENT_HP_SCALE: "현재 HP 비례 회복",
    LogicType.STAT_CHANGE: "스탯 변경",
    LogicType.DOT: "지속 피해 (DoT)",
    LogicType.DOT_HEAL_HP_RATIO: "지속 회복 (HoT)",
    LogicType.CC: "군중 제어 (CC)",
    LogicType.TAUNT: "도발",
    LogicType.COUNTER: "반격 준비",
    LogicType.REVIVE: "부활",
    LogicType.SP_INCREASE: "SP 증가",
    LogicType.SP_STEAL: "SP 강탈",
    LogicType.SP_LOCK: "SP 충전 잠금",
    LogicType.BARRIER: "보호막",
    LogicType.BARRIER_RATIO: "HP비율 보호막",
    LogicType.INVINCIBILITY: "무적",
    LogicType.UNDYING: "불사",
    LogicType.DEBUFF_IMMUNE: "디버프 면역",
    LogicType.REMOVE_DEBUFF: "디버프 제거",
    LogicType.REMOVE_BUFF: "버프 제거 (스트립)",
    LogicType.BUFF_TURN_INCREASE: "버프 턴 증가",
    LogicType.DEBUFF_TURN_INCREASE: "디버프 턴 증가",
    LogicType.DEBUFF_SPREAD: "디버프 전이",
    LogicType.CRI_UNAVAILABLE: "크리 불가",
    LogicType.COUNTER_UNAVAILABLE: "반격 불가",
    LogicType.USE_SKILL: "스킬 체인 발동",
    LogicType.IGNORE_ELEMENT: "속성 상성 무시",
    LogicType.ACTIVE_CD_CHANGE: "액티브 쿨타임 변경",
    LogicType.SELF_DAMAGE: "자해 (자신 HP 감소)",
    LogicType.STAT_STEAL: "스탯 강탈",
    LogicType.LINK_BUFF: "연결 버프 (뒤 유닛 공유)",
}
TARGET_KR = {
    TargetType.ENEMY_NEAR: "가장 가까운 적 1체",
    TargetType.ALL_ENEMY: "적 전체",
    TargetType.ENEMY_RANDOM: "적 랜덤 1체",
    TargetType.ENEMY_RANDOM_2: "적 랜덤 2체",
    TargetType.ENEMY_RANDOM_3: "적 랜덤 3체",
    TargetType.ENEMY_NEAR_ROW: "가장 가까운 적의 열 전체",
    TargetType.ENEMY_NEAR_CROSS: "가장 가까운 적 + 십자 범위",
    TargetType.ENEMY_BACK_ROW: "적 후열 전체",
    TargetType.ENEMY_SAME_COL: "같은 열의 모든 적",
    TargetType.ENEMY_LOWEST_HP: "HP가 가장 낮은 적",
    TargetType.ENEMY_HIGHEST_SPD: "SPD가 가장 높은 적",
    TargetType.ENEMY_ELEMENT_WEAK: "속성 약점 적",
    TargetType.SELF: "자기 자신",
    TargetType.ALL_ALLY: "아군 전체",
    TargetType.ALLY_LOWEST_HP: "HP가 가장 낮은 아군",
    TargetType.ALLY_LOWEST_HP_2: "HP가 낮은 아군 2체",
    TargetType.ALLY_LOWEST_HP_3: "HP가 낮은 아군 3체",
    TargetType.ALLY_HIGHEST_ATK: "ATK가 가장 높은 아군",
    TargetType.ALLY_SAME_ROW: "같은 열 아군",
    TargetType.ALLY_SAME_ELEMENT: "같은 속성 아군",
    TargetType.ALLY_ADJACENT: "인접 아군",
    TargetType.ALLY_FRONT: "전열 아군",
    TargetType.ALLY_BEHIND: "뒤쪽 아군",
    TargetType.ALLY_DEAD_RANDOM: "사망 아군 1체",
}
TRIGGER_KR = {
    TriggerEvent.ON_BATTLE_START: "전투 시작 시",
    TriggerEvent.ON_KILL: "적 처치 시",
    TriggerEvent.ON_HIT: "피격 시",
    TriggerEvent.ON_CRITICAL_HIT: "크리티컬 적중 시",
    TriggerEvent.ON_ULTIMATE_USED: "얼티밋 사용 후",
    TriggerEvent.ON_BUFF_GAINED: "버프 획득 시",
    TriggerEvent.ON_TURN_START: "턴 시작 시",
    TriggerEvent.ON_TURN_END: "턴 종료 시",
    TriggerEvent.ON_ROUND_START: "라운드 시작 시",
    TriggerEvent.ON_ATTACK: "공격 시",
    TriggerEvent.ON_DEATH: "사망 시",
    TriggerEvent.ON_HP_THRESHOLD: "HP 임계점 도달 시",
    TriggerEvent.ON_BURN_APPLIED: "화상 부여 시",
    TriggerEvent.ON_STATUS_APPLIED: "상태이상 부여 시",
}
CC_KR = {
    CCType.STUN: "기절", CCType.FREEZE: "빙결", CCType.SLEEP: "수면",
    CCType.STONE: "석화", CCType.PANIC: "공포", CCType.SILENCE: "침묵",
    CCType.ELECTRIC_SHOCK: "감전", CCType.ABNORMAL_SKILL: "스킬 이상",
    CCType.POISON: "중독", CCType.BURN: "화상", CCType.BLIND: "실명",
}

# ═══════════════════════════════════════════════════════════════
# 메타 매핑
# ═══════════════════════════════════════════════════════════════
META_V8 = {
    "M01 화상폭발": (["카라라트리", "다비", "드미테르", "살마키스", "지바"], "DAMAGE_BURN_BONUS + DEBUFF_SPREAD로 화상 스택을 극대화하여 폭발적 딜링"),
    "M02 빙결처형": (["이브", "도계화", "마야우엘", "상아", "에우로스"], "CC 체인(FREEZE/STUN)으로 적 행동 봉쇄 + 처형 마무리"),
    "M03 독확산정원": (["에레보스", "판", "그릴라", "메티스", "브라우니"], "DEBUFF_SPREAD로 독 전이 + HoT 지속회복 소모전"),
    "M04 버프연쇄": (["아슈토레스", "루미나", "시트리", "엘리시온", "티와즈"], "ON_BUFF_GAINED + LINK_BUFF로 버프 스노우볼"),
    "M05 철벽요새": (["다누", "세멜레", "티타니아", "샤를", "다나"], "LINK_BUFF + HEAL_CURRENT_HP_SCALE 기반 절대 방어"),
    "M06 광전사": (["에르제베트", "쿠바바", "메두사", "유나", "미르칼라"], "SELF_DAMAGE → MISSING_HP_SCALE로 자해 리스크 기반 폭딜"),
    "M07 속도학살": (["이브", "니르티", "아라한", "티스베", "엘리시온"], "SPD 우위 + REPEAT_TARGET으로 턴 압도 + 처형"),
    "M08 크리연쇄": (["아누비스", "아르테미스", "그릴라", "바토리", "네반"], "ON_CRITICAL_HIT + 확정크리로 연쇄 패시브 발동"),
    "M09 암살침투": (["쿠바바", "아르테미스", "유나", "프레이", "미르칼라"], "STAT_STEAL + 관통으로 방어 무력화 + 출혈 DoT"),
    "M10 성속결속": (["아슈토레스", "오네이로이", "시트리", "모나", "티와즈"], "ALLY_SAME_ELEMENT + LINK_BUFF로 광속 단일 속성 시너지"),
}
META_V7 = {
    "M01 화상연소": ["카라라트리", "다비", "드미테르", "살마키스", "지바"],
    "M02 빙결감옥": ["바리", "도계화", "마야우엘", "상아", "에우로스"],
    "M03 독정원": ["에레보스", "판", "그릴라", "메티스", "브라우니"],
    "M04 하이퍼캐리": ["쿠바바", "루미나", "시트리", "엘리시온", "아우로라"],
    "M05 철벽요새": ["다누", "세멜레", "티타니아", "샤를", "네반"],
    "M06 반격요새": ["프레이", "데레사", "라가라자", "맘몬", "미르칼라"],
    "M07 속도처형": ["이브", "니르티", "아라한", "티스베", "엘리시온"],
    "M08 암속강공": ["아누비스", "아르테미스", "유나", "바토리", "프레이"],
    "M09 전멸폭격": ["에레보스", "라가라자", "구미호", "아우로라", "지바"],
    "M10 광전사": ["아슈토레스", "에르제베트", "카인", "그릴라", "지바"],
    "M11 광속성벽": ["아슈토레스", "시트리", "티와즈", "티타니아", "모나"],
    "M12 CC킬체인": ["오네이로이", "마프데트", "미리암", "미다스", "자청비"],
}
ELEM_ADVANTAGE = {
    Element.FIRE: (Element.FOREST, Element.WATER),
    Element.WATER: (Element.FIRE, Element.FOREST),
    Element.FOREST: (Element.WATER, Element.FIRE),
    Element.LIGHT: (Element.DARK, None),
    Element.DARK: (Element.LIGHT, None),
}

# ═══════════════════════════════════════════════════════════════
# 밸런스 히스토리 파싱 (소스코드 주석 추출)
# ═══════════════════════════════════════════════════════════════
def parse_balance_history():
    """test_data.py에서 make_* 함수별 버전 주석을 추출"""
    src = pathlib.Path(__file__).resolve().parents[1] / "src" / "fixtures" / "test_data.py"
    text = src.read_text(encoding="utf-8")

    # 함수별로 분할
    funcs = re.split(r'\ndef (make_\w+)', text)
    history = {}  # sid -> [change_note, ...]

    for i in range(1, len(funcs), 2):
        func_name = funcs[i]
        func_body = funcs[i + 1] if i + 1 < len(funcs) else ""

        # sid 추출
        sid_match = re.search(r'sid\s*=\s*"(c\w+)"', func_body)
        if not sid_match:
            continue
        sid = sid_match.group(1)

        # 버전 주석 추출 (v7.x, v8.x 패턴)
        changes = []
        for line in func_body.split("\n"):
            line = line.strip()
            # v숫자.숫자 패턴 매칭
            version_matches = re.findall(r'(v\d+\.?\d*[a-z]?)\s*[:]?\s*(.+?)(?:\)|$)', line)
            for ver, desc in version_matches:
                desc = desc.strip().rstrip(")")
                if desc and len(desc) > 3:
                    changes.append(f"**{ver}**: {desc}")
            # # v숫자 주석 형태
            comment_match = re.search(r'#\s*(v\d+\.\d+\S*)\s+(.+?)$', line)
            if comment_match:
                ver = comment_match.group(1)
                desc = comment_match.group(2).strip()
                entry = f"**{ver}**: {desc}"
                if entry not in changes:
                    changes.append(entry)

        # 중복 제거 및 정렬
        seen = set()
        unique = []
        for c in changes:
            if c not in seen:
                seen.add(c)
                unique.append(c)
        history[sid] = unique

    return history

BALANCE_HISTORY = parse_balance_history()

# ═══════════════════════════════════════════════════════════════
# 시너지 매핑 (메타 팀 기반 자동 생성)
# ═══════════════════════════════════════════════════════════════
def build_synergy_map():
    """메타 팀에서 같이 편성된 캐릭터 쌍 추출"""
    synergy = {}  # name -> {partner_name: [meta_name, ...]}
    for meta_name, (members, desc) in META_V8.items():
        for m in members:
            if m not in synergy:
                synergy[m] = {}
            for partner in members:
                if partner != m:
                    if partner not in synergy[m]:
                        synergy[m][partner] = []
                    synergy[m][partner].append(meta_name)
    return synergy

SYNERGY_MAP = build_synergy_map()

# ═══════════════════════════════════════════════════════════════
# 카운터 관계 매핑
# ═══════════════════════════════════════════════════════════════
# 로직 기반 카운터 관계 정의
COUNTER_LOGIC = {
    # 이 로직을 가진 캐릭터는 → 해당 특성에 강하다
    LogicType.REMOVE_BUFF: "버프 의존형 캐릭터 (M04 버프연쇄, 보호막 탱커)",
    LogicType.REMOVE_DEBUFF: "DoT/디버프 의존형 (M01 화상, M03 독정원)",
    LogicType.DEBUFF_IMMUNE: "CC/디버프 의존형 (M02 빙결, M08 크리연쇄)",
    LogicType.DAMAGE_PENETRATION: "고DEF 탱커 (M05 철벽요새)",
    LogicType.SP_STEAL: "얼티밋 의존형 캐릭터",
    LogicType.SP_LOCK: "SP 축적 의존 팀",
    LogicType.CRI_UNAVAILABLE: "크리 의존형 (M08 크리연쇄, 에르제베트)",
    LogicType.COUNTER_UNAVAILABLE: "반격 의존형 (M06 반격요새)",
    LogicType.IGNORE_ELEMENT: "속성 상성 유리한 적",
}

# 이 로직을 가진 캐릭터는 → 이것에 약하다
WEAK_TO_LOGIC = {
    LogicType.DOT: "디버프 제거/면역 (REMOVE_DEBUFF, DEBUFF_IMMUNE)",
    LogicType.CC: "디버프 면역 (DEBUFF_IMMUNE)",
    LogicType.BARRIER: "버프 제거 (REMOVE_BUFF)",
    LogicType.BARRIER_RATIO: "버프 제거 (REMOVE_BUFF)",
    LogicType.SELF_DAMAGE: "빠른 집중공격 (자해 후 HP 낮아진 상태)",
    LogicType.DAMAGE_BUFF_SCALE: "버프 제거로 딜 기반 무력화",
    LogicType.COUNTER: "반격 불가 (COUNTER_UNAVAILABLE)",
}


# ═══════════════════════════════════════════════════════════════
# 설계 의도 자동 생성
# ═══════════════════════════════════════════════════════════════
ROLE_DESIGN_INTENT = {
    Role.ATTACKER: "높은 ATK와 공격 배율로 적을 빠르게 처치하는 메인 딜러. 팀의 화력 핵심이며, 서포터/힐러의 보호 아래 최대 딜을 뽑아내는 것이 목표.",
    Role.MAGICIAN: "빠른 SPD(100)로 선제 행동하여 CC와 디버프로 적을 제압. 딜보다는 적 행동 방해와 전장 통제에 특화된 컨트롤러.",
    Role.DEFENDER: "높은 DEF/HP와 도발로 아군을 보호하는 탱커. 적의 공격을 집중시키고 반격/CC로 방어적 가치를 제공.",
    Role.HEALER: "아군 HP 회복과 디버프 정화로 팀 생존을 보장. SP Cost 3으로 빠른 얼티밋 회전이 가능하여 지속적 지원 가능.",
    Role.SUPPORTER: "가장 빠른 SPD(120)으로 매 라운드 먼저 행동. 버프/디버프로 팀 전투력을 극대화하는 인에이블러.",
}

def generate_design_intent(c, concepts, logic_set):
    """캐릭터별 설계 의도 서술문 생성"""
    lines = []
    _, role_kr, _ = ROLE_KR[c.role]
    _, elem_kr, _ = ELEM_KR[c.element]
    base = ROLE_DESIGN_INTENT[c.role]
    lines.append(f"**기본 역할 설계**: {base}")
    lines.append("")

    # 고유 메커니즘 분석
    unique = []
    if LogicType.DAMAGE_BURN_BONUS in logic_set:
        unique.append("**화상 증폭 메커니즘**: 화상 상태의 적에게 2배 피해 + 강제 크리티컬을 적용. 화상을 유지하는 아군(다비, 드미테르 등)이 많을수록 폭발적으로 강해지도록 설계.")
    if LogicType.DAMAGE_MISSING_HP_SCALE in logic_set:
        unique.append("**잃은 HP 비례 딜**: 자해(SELF_DAMAGE)나 전투 경과로 HP가 줄어들수록 피해가 증가하는 하이리스크-하이리턴 설계. 힐러와의 밸런스가 핵심.")
    if LogicType.DAMAGE_ESCALATE in logic_set:
        unique.append("**점진 강화**: 같은 스킬을 반복 사용할수록 피해가 누적 증가. 장기전에서 점점 강해지는 레이트 캐리형 설계.")
    if LogicType.DAMAGE_REPEAT_TARGET in logic_set:
        unique.append("**집중 타격**: 같은 대상을 반복 공격할수록 피해가 증가. 보스전이나 핵심 위협 제거에 특화된 싱글 타겟 킬러.")
    if LogicType.DAMAGE_PENETRATION in logic_set:
        unique.append("**관통 딜링**: DEF를 무시하는 관통 데미지로 탱커도 효과적으로 처리. 철벽요새(M05) 같은 방어덱에 대한 카운터 설계.")
    if LogicType.DAMAGE_CRI in logic_set:
        unique.append("**확정 크리**: 크리율에 관계없이 100% 크리티컬 발동. CRI_DMG 버프와의 시너지가 극대화되며, 안정적인 고피해를 보장.")
    if LogicType.DAMAGE_BUFF_SCALE in logic_set:
        unique.append("**버프 비례 딜링**: 자신에게 걸린 버프 수에 비례하여 피해 증가. 트리플 버퍼(루미나+시트리+아우로라)와 조합 시 폭발적 딜 가능.")
    if LogicType.DAMAGE_BUFF_SCALE_TARGET in logic_set:
        unique.append("**적 버프 역이용**: 적이 가진 버프 수에 비례하여 피해 증가. 자가 버프가 많은 팀(M04 등)을 역으로 카운터하는 설계.")
    if LogicType.DAMAGE_DEBUFF_SCALE_TARGET in logic_set:
        unique.append("**디버프 비례 딜링**: 적에게 쌓인 디버프(화상/독/방깎 등)가 많을수록 피해 증가. 디버프를 다량 부여하는 팀과 시너지.")
    if LogicType.SELF_DAMAGE in logic_set:
        unique.append("**자해 메커니즘**: 스킬 사용 시 자신의 HP를 소모. MISSING_HP_SCALE과 연동하여 '피해를 입을수록 강해지는' 광전사 판타지를 구현.")
    if LogicType.USE_SKILL in logic_set:
        unique.append("**스킬 체인**: 하나의 스킬이 다른 스킬을 자동 발동시키는 연쇄 시스템. 한 턴에 복수 스킬을 실행하여 행동 효율 극대화.")
    if LogicType.STAT_STEAL in logic_set:
        unique.append("**스탯 강탈**: 적의 스탯을 빼앗아 자신에게 부여. 딜과 디버프를 동시에 수행하는 효율적 설계.")
    if LogicType.LINK_BUFF in logic_set:
        unique.append("**연결 버프**: 자신의 버프를 뒤쪽 유닛에게 공유. 배치 전략이 중요해지며, 전열 탱커→후열 딜러 버프 전달 시너지.")
    if LogicType.DEBUFF_SPREAD in logic_set:
        unique.append("**디버프 전이**: 한 적에게 걸린 디버프를 주변 적에게 확산. 소수 타겟 디버프를 전체 디버프로 전환하는 효율적 CC 확장.")
    if LogicType.IGNORE_ELEMENT in logic_set:
        unique.append("**속성 무시**: 속성 상성을 무시하여 불리한 매치업에서도 안정적 딜 가능. 상성에 구애받지 않는 범용 딜러.")
    if LogicType.REVIVE in logic_set:
        unique.append("**부활 능력**: 사망한 아군을 되살려 전투를 역전. 후반 전투에서 결정적인 수적 우위를 확보하는 보험 스킬.")
    if LogicType.SP_STEAL in logic_set:
        unique.append("**SP 강탈**: 적 팀의 SP를 빼앗아 얼티밋 사용을 지연시키는 자원 전쟁 설계. 적의 폭딜 타이밍을 무너뜨리는 핵심 견제.")
    if LogicType.SP_LOCK in logic_set:
        unique.append("**SP 잠금**: 적의 SP 충전을 일정 턴 차단. SP 강탈과 함께 적 얼티밋을 완전히 봉쇄하는 콤보 가능.")

    # 트리거 설계 의도
    trigger_intents = []
    if c.triggers:
        for t in c.triggers:
            if t.event == TriggerEvent.ON_KILL:
                once_str = "1회 한정 보험" if t.once_per_battle else "무제한 연쇄 — 킬 체인의 핵심"
                trigger_intents.append(f"- **ON_KILL**: 적 처치 시 패시브 발동 ({once_str}). 마무리를 넣을수록 추가 행동/피해가 발생하여 스노우볼을 굴리는 설계.")
            elif t.event == TriggerEvent.ON_HIT:
                trigger_intents.append(f"- **ON_HIT**: 피격 시 패시브 발동 (1회). 도발/탱킹과 연동하여 맞으면 되받아치는 방어적 공격 패턴.")
            elif t.event == TriggerEvent.ON_BATTLE_START:
                trigger_intents.append(f"- **ON_BATTLE_START**: 전투 시작 즉시 패시브 자동 발동. 사전 버프/힐/DoT로 라운드 1부터 이점을 확보하는 선제 설계.")
            elif t.event == TriggerEvent.ON_CRITICAL_HIT:
                trigger_intents.append(f"- **ON_CRITICAL_HIT**: 크리티컬 적중 시 패시브 발동. CRI 버프와 연동하면 매 공격마다 추가 액션이 발생하는 연쇄 설계.")
            elif t.event == TriggerEvent.ON_ULTIMATE_USED:
                trigger_intents.append(f"- **ON_ULTIMATE_USED**: 얼티밋 사용 후 패시브 발동. 엑스트라 턴 → 얼티밋 → 패시브의 3단 콤보를 만드는 폭발 설계.")
            elif t.event == TriggerEvent.ON_BUFF_GAINED:
                trigger_intents.append(f"- **ON_BUFF_GAINED**: 버프 획득 시 패시브 발동. 팀이 버프를 걸 때마다 추가 효과가 발생하는 버프 스노우볼 설계.")

    if unique:
        lines.append("**고유 메커니즘**:")
        lines.append("")
        for u in unique:
            lines.append(f"- {u}")
        lines.append("")

    if trigger_intents:
        lines.append("**트리거 설계 의도**:")
        lines.append("")
        for ti in trigger_intents:
            lines.append(ti)
        lines.append("")

    return lines


# ═══════════════════════════════════════════════════════════════
# 이상적 전투 흐름 생성
# ═══════════════════════════════════════════════════════════════
def generate_battle_flow(c):
    """캐릭터의 역할/스킬에 기반한 이상적 5턴 전투 시나리오"""
    lines = []
    spd = c.stats.spd
    action_time = 300 / spd

    # 패시브 트리거 종류
    has_battle_start = any(t.event == TriggerEvent.ON_BATTLE_START for t in (c.triggers or []))
    has_on_kill = any(t.event == TriggerEvent.ON_KILL for t in (c.triggers or []))
    has_on_hit = any(t.event == TriggerEvent.ON_HIT for t in (c.triggers or []))
    has_on_crit = any(t.event == TriggerEvent.ON_CRITICAL_HIT for t in (c.triggers or []))
    has_on_ult = any(t.event == TriggerEvent.ON_ULTIMATE_USED for t in (c.triggers or []))

    _, role_kr, _ = ROLE_KR[c.role]
    n_name = c.normal_skill.name if c.normal_skill else "노말"
    a_name = c.active_skill.name if c.active_skill else "액티브"
    u_name = c.ultimate_skill.name if c.ultimate_skill else "얼티밋"
    p_name = c.passive_skill.name if c.passive_skill else "패시브"

    sp_cost = c.ultimate_skill.sp_cost if c.ultimate_skill and hasattr(c.ultimate_skill, 'sp_cost') and c.ultimate_skill.sp_cost else 6
    active_cd = c.active_skill.cooldown_turns if c.active_skill else 3

    lines.append(f"> CTB 행동 간격: **{action_time:.2f}초** (SPD {spd})")
    lines.append(f"> SP 요구량: **{sp_cost}** (팀 공유)")
    lines.append(f"> 액티브 쿨타임: **{active_cd}턴**")
    lines.append("")

    # 전투 시작 페이즈
    if has_battle_start:
        lines.append(f"**[전투 시작]** 「{p_name}」 자동 발동")
        # 패시브 효과 요약
        if c.passive_skill and c.passive_skill.effects:
            eff_summary = []
            for e in c.passive_skill.effects:
                descs = describe_effect(e)
                eff_summary.extend(descs)
            lines.append(f"  → {' / '.join(eff_summary[:3])}")
        lines.append("")

    # 턴 시나리오
    if c.role == Role.ATTACKER:
        lines.append(f"**[T1]** (행동시간 {action_time:.2f}s) 「{n_name}」 사용")
        lines.append(f"  → 가장 가까운 적에게 기본 딜. 서포터/구속형이 먼저 움직여 디버프를 걸어둔 상태가 이상적.")
        lines.append(f"")
        lines.append(f"**[T2]** (행동시간 {action_time*2:.2f}s) 「{n_name}」 사용")
        lines.append(f"  → 노말 반복으로 딜 축적. 액티브 쿨타임 대기.")
        lines.append(f"")
        lines.append(f"**[T3]** (행동시간 {action_time*3:.2f}s) 「{a_name}」 사용 (액티브 쿨 해제)")
        lines.append(f"  → 핵심 액티브 스킬 발동. 추가 효과(화상/방깎/CC 등)로 적 제압력 강화.")
        lines.append(f"")
        if sp_cost <= 4:
            lines.append(f"**[T4]** (SP 충족 시) 「{u_name}」 발동 → **엑스트라 턴**")
        else:
            lines.append(f"**[T4~5]** (SP {sp_cost} 충족 시) 「{u_name}」 발동 → **엑스트라 턴**")
        lines.append(f"  → 얼티밋으로 최대 딜. 엑스트라 턴에서 노말/액티브 추가 사용.")
        if has_on_kill:
            lines.append(f"  → 처치 성공 시 「{p_name}」 연쇄 발동 — **킬 체인 시작**")
        lines.append(f"")
        if has_on_kill:
            lines.append(f"**[킬 체인]** 적 처치 → 패시브 추가 딜 → 다음 적 위협 → 연쇄 처치 가능")
            lines.append(f"  → 이 캐릭터의 최대 포텐셜은 '첫 킬'에서 시작됨. 팀이 적 HP를 깎아놓으면 연쇄 처치로 전투를 결정.")

    elif c.role == Role.MAGICIAN:
        lines.append(f"**[T1]** (행동시간 {action_time:.2f}s — 서포터 다음으로 빠름) 「{n_name}」 사용")
        lines.append(f"  → 선제 공격 + CC/디버프 부여. 적 딜러보다 먼저 행동하여 위협 제거.")
        lines.append(f"")
        lines.append(f"**[T2]** 「{n_name}」 반복")
        lines.append(f"  → CC 재적용 또는 디버프 유지. 적의 행동 기회를 계속 줄임.")
        lines.append(f"")
        lines.append(f"**[T3]** 「{a_name}」 발동 (쿨타임 해제)")
        lines.append(f"  → 핵심 CC/디버프 콤보. 적 핵심 유닛을 무력화.")
        lines.append(f"")
        lines.append(f"**[T4]** (SP {sp_cost} 충족 시) 「{u_name}」 발동 → **엑스트라 턴**")
        lines.append(f"  → AoE CC/디버프로 적 전체 제압. 엑스트라 턴에서 노말로 추가 CC.")
        if has_on_kill:
            lines.append(f"  → 처치 시 「{p_name}」 연쇄 발동")

    elif c.role == Role.DEFENDER:
        lines.append(f"**[T1]** (행동시간 {action_time:.2f}s — SPD 110으로 딜러보다 먼저 행동) 「{n_name}」 사용")
        lines.append(f"  → 기본 공격으로 어그로 생성. 전열 배치로 적 공격을 자연스럽게 유도.")
        lines.append(f"")
        lines.append(f"**[T2]** 「{a_name}」 발동 (핵심)")
        lines.append(f"  → 도발/보호막/반격 준비 등 방어 체계 구축. 이 시점부터 팀 방어막 역할 시작.")
        lines.append(f"")
        lines.append(f"**[T3~4]** 「{n_name}」 반복 + 피격 유도")
        lines.append(f"  → 도발 상태에서 적 공격을 받으며 반격/패시브 발동으로 딜 기여.")
        if has_on_hit:
            lines.append(f"  → 피격 시 「{p_name}」 발동 — 반격 + 추가 효과")
        lines.append(f"")
        lines.append(f"**[T4~5]** (SP {sp_cost} 충족 시) 「{u_name}」 발동 → **엑스트라 턴**")
        lines.append(f"  → 팀 보호 얼티밋으로 결정적 순간에 팀을 지킴.")

    elif c.role == Role.HEALER:
        lines.append(f"**[T1]** (행동시간 {action_time:.2f}s) 「{n_name}」 사용")
        lines.append(f"  → 아직 아군이 건강한 상태. 기본 공격으로 딜 기여.")
        lines.append(f"")
        lines.append(f"**[T2~3]** 「{a_name}」 발동 (핵심 회복)")
        lines.append(f"  → 아군 피해가 누적되기 시작. HP가 가장 낮은 아군을 우선 회복.")
        lines.append(f"")
        lines.append(f"**[T3~4]** (SP {sp_cost} 충족 — 힐러는 SP 3으로 빠른 얼티밋) 「{u_name}」 발동 → **엑스트라 턴**")
        lines.append(f"  → 전체 회복 + 추가 효과. 팀 HP를 한번에 끌어올리는 결정적 힐.")
        lines.append(f"  → 엑스트라 턴에서 추가 노말/액티브로 이중 힐 가능.")
        lines.append(f"")
        lines.append(f"**[T5]** 「{a_name}」 재발동")
        lines.append(f"  → 액티브 쿨타임 돌아옴. 팀 HP 유지 관리 지속.")

    elif c.role == Role.SUPPORTER:
        lines.append(f"**[T1]** (행동시간 {action_time:.2f}s — **팀 내 가장 빠른 행동**) 「{n_name}」 사용")
        lines.append(f"  → 모든 아군보다 먼저 행동. 기본 공격으로 전장 정리 시작.")
        lines.append(f"")
        lines.append(f"**[T2]** 「{a_name}」 발동 (핵심 버프/디버프)")
        lines.append(f"  → 팀 전체에 버프 부여 또는 적에게 디버프. 이후 아군 딜러의 공격이 강화된 상태로 타격.")
        lines.append(f"")
        lines.append(f"**[T3]** 「{n_name}」 반복")
        lines.append(f"  → 빠른 SPD로 다시 행동. 적 위협 제거 또는 추가 지원.")
        lines.append(f"")
        lines.append(f"**[T4]** (SP {sp_cost} 충족 시) 「{u_name}」 발동 → **엑스트라 턴**")
        lines.append(f"  → 팀 전체 강화 또는 적 전체 약화. 엑스트라 턴에서 액티브 재사용으로 이중 버프.")
        lines.append(f"")
        lines.append(f"**[T5]** 버프 갱신 사이클")
        lines.append(f"  → 2턴짜리 버프가 만료되는 시점. 액티브 재발동으로 버프 유지.")

    return lines


# ═══════════════════════════════════════════════════════════════
# 시너지/카운터 분석 생성
# ═══════════════════════════════════════════════════════════════
def generate_synergy_counter(c, logic_set, all_chars_map):
    """시너지 파트너 + 카운터 관계 분석"""
    lines = []

    # 시너지 파트너
    synergies = SYNERGY_MAP.get(c.name, {})
    if synergies:
        lines.append("### 주요 시너지 파트너\n")
        lines.append("| 파트너 | 공유 메타 | 시너지 이유 |")
        lines.append("|--------|----------|-------------|")
        for partner, metas in sorted(synergies.items(), key=lambda x: -len(x[1])):
            meta_str = ", ".join(metas[:2])
            # 시너지 이유 자동 생성
            pc = all_chars_map.get(partner)
            reason = _get_synergy_reason(c, pc) if pc else "같은 메타 편성"
            lines.append(f"| **{partner}** | {meta_str} | {reason} |")
        lines.append("")
    else:
        # 메타 미편성이라도 속성 기반 시너지 제안
        lines.append("### 추천 시너지 파트너\n")
        same_elem = [ch for ch in all_chars_map.values() if ch.element == c.element and ch.name != c.name and ch.role != c.role]
        if same_elem:
            for sc in same_elem[:3]:
                _, sr_kr, _ = ROLE_KR[sc.role]
                lines.append(f"- **{sc.name}** ({sr_kr}): 같은 속성으로 ALLY_SAME_ELEMENT 타겟 시너지")
            lines.append("")

    # 카운터: 이 캐릭터가 강한 상대
    lines.append("### 카운터 관계\n")
    counters = []
    for logic, desc in COUNTER_LOGIC.items():
        if logic in logic_set:
            counters.append(f"- **이 캐릭터 → 유리**: {LOGIC_KR.get(logic, str(logic))} 보유 → {desc}에 강함")

    # 카운터: 이 캐릭터가 약한 상대
    weak_to = []
    for logic, desc in WEAK_TO_LOGIC.items():
        if logic in logic_set:
            weak_to.append(f"- **이 캐릭터 ← 불리**: {LOGIC_KR.get(logic, str(logic))} 의존 → {desc}에 취약")

    if counters:
        lines.append("**유리한 상대**:\n")
        lines.extend(counters)
        lines.append("")
    if weak_to:
        lines.append("**불리한 상대**:\n")
        lines.extend(weak_to)
        lines.append("")
    if not counters and not weak_to:
        lines.append("특별한 카운터 관계 없이 범용적으로 운용 가능.\n")

    return lines


def _get_synergy_reason(c1, c2):
    """두 캐릭터 간 시너지 이유 자동 분석"""
    if c2 is None:
        return "같은 메타 편성"

    reasons = []

    # 역할 시너지
    r_synergy = {
        (Role.ATTACKER, Role.SUPPORTER): "서포터 버프 → 딜러 화력 극대화",
        (Role.ATTACKER, Role.HEALER): "힐러 보호 → 딜러 생존 보장",
        (Role.DEFENDER, Role.HEALER): "탱커+힐러 이중 보호",
        (Role.DEFENDER, Role.ATTACKER): "도발로 딜러 보호",
    }
    pair = (c1.role, c2.role)
    if pair in r_synergy:
        reasons.append(r_synergy[pair])
    pair_r = (c2.role, c1.role)
    if pair_r in r_synergy:
        reasons.append(r_synergy[pair_r])

    # 스킬 로직 시너지
    c1_logics = _get_all_logics(c1)
    c2_logics = _get_all_logics(c2)

    # 화상 시너지
    if _has_dot_type(c1, "burn") and LogicType.DAMAGE_BURN_BONUS in c2_logics:
        reasons.append(f"{c1.name} 화상 → {c2.name} burn_bonus 피해 증가")
    if _has_dot_type(c2, "burn") and LogicType.DAMAGE_BURN_BONUS in c1_logics:
        reasons.append(f"{c2.name} 화상 → {c1.name} burn_bonus 피해 증가")

    # 디버프 + 디버프 비례딜
    if LogicType.DOT in c1_logics and LogicType.DAMAGE_DEBUFF_SCALE_TARGET in c2_logics:
        reasons.append(f"{c1.name} 디버프 → {c2.name} 디버프 비례 딜 강화")
    if LogicType.DOT in c2_logics and LogicType.DAMAGE_DEBUFF_SCALE_TARGET in c1_logics:
        reasons.append(f"{c2.name} 디버프 → {c1.name} 디버프 비례 딜 강화")

    # 버프 + 버프 비례딜
    if LogicType.STAT_CHANGE in c2_logics and LogicType.DAMAGE_BUFF_SCALE in c1_logics:
        reasons.append(f"{c2.name} 버프 → {c1.name} 버프 비례 딜 강화")

    # CC 체인
    if LogicType.CC in c1_logics and LogicType.CC in c2_logics:
        reasons.append("CC 릴레이 → 적 행동 완전 봉쇄")

    # 디버프 연장 + DoT
    if LogicType.DEBUFF_TURN_INCREASE in c1_logics and LogicType.DOT in c2_logics:
        reasons.append(f"{c1.name} 디버프 연장 → {c2.name} DoT 지속시간 증가")
    if LogicType.DEBUFF_TURN_INCREASE in c2_logics and LogicType.DOT in c1_logics:
        reasons.append(f"{c2.name} 디버프 연장 → {c1.name} DoT 지속시간 증가")

    # 속성 동일
    if c1.element == c2.element:
        reasons.append("같은 속성 — ALLY_SAME_ELEMENT 타겟 시너지")

    return " / ".join(reasons[:2]) if reasons else "같은 메타 편성"


def _get_all_logics(c):
    s = set()
    for sk in [c.normal_skill, c.active_skill, c.ultimate_skill, c.passive_skill]:
        if sk and sk.effects:
            for e in sk.effects:
                if e.logic_type:
                    s.add(e.logic_type)
    return s


def _has_dot_type(c, dot_type):
    for sk in [c.normal_skill, c.active_skill, c.ultimate_skill, c.passive_skill]:
        if sk and sk.effects:
            for e in sk.effects:
                if e.logic_type == LogicType.DOT and e.buff_data and getattr(e.buff_data, 'dot_type', '') == dot_type:
                    return True
    return False


# ═══════════════════════════════════════════════════════════════
# SkillEffect 한글 설명 (기존 로직)
# ═══════════════════════════════════════════════════════════════
def describe_effect(e):
    parts = []
    logic_name = LOGIC_KR.get(e.logic_type, str(e.logic_type))
    target_name = TARGET_KR.get(e.target_type, str(e.target_type))

    if e.logic_type in (LogicType.DAMAGE, LogicType.DAMAGE_BURN_BONUS, LogicType.DAMAGE_ESCALATE,
                         LogicType.DAMAGE_REPEAT_TARGET, LogicType.DAMAGE_PENETRATION,
                         LogicType.DAMAGE_CRI, LogicType.DAMAGE_BUFF_SCALE,
                         LogicType.DAMAGE_BUFF_SCALE_TARGET, LogicType.DAMAGE_DEBUFF_SCALE_TARGET,
                         LogicType.DAMAGE_MISSING_HP_SCALE):
        s = f"`{logic_name}` {e.multiplier:.2f}x → {target_name}"
        if e.hit_count and e.hit_count > 1:
            s += f" ({e.hit_count}연타)"
        if e.condition:
            if e.condition.get('burn_bonus_per_stack', 0) > 0:
                s += f" + 화상스택당 +{e.condition['burn_bonus_per_stack']:.0%}"
            if e.condition.get('target_hp_below', 0) > 0:
                s += f" + HP {e.condition['target_hp_below']:.0%} 이하 시 추가발동"
        if e.value and e.logic_type == LogicType.DAMAGE_MISSING_HP_SCALE:
            s += f" (스케일: {e.value})"
        if e.value and e.logic_type in (LogicType.DAMAGE_BUFF_SCALE, LogicType.DAMAGE_BUFF_SCALE_TARGET, LogicType.DAMAGE_DEBUFF_SCALE_TARGET):
            s += f" (버프/디버프당 +{e.value:.0%})"
        parts.append(s)
    elif e.logic_type == LogicType.DAMAGE_HP_RATIO:
        parts.append(f"`대상 최대HP% 데미지` {e.value:.0%} → {target_name}")
    elif e.logic_type in (LogicType.HEAL_HP_RATIO, LogicType.HEAL_PER_HIT, LogicType.HEAL_LOSS_SCALE, LogicType.HEAL_CURRENT_HP_SCALE):
        if e.multiplier and e.multiplier > 0:
            parts.append(f"`{logic_name}` {e.multiplier:.0%} (heal_ratio={e.value}) → {target_name}")
        else:
            parts.append(f"`{logic_name}` {e.value:.0%} → {target_name}")
    elif e.logic_type == LogicType.STAT_CHANGE and e.buff_data:
        bd = e.buff_data
        direction = "↓" if bd.is_debuff else "↑"
        pct = "%" if bd.is_ratio else ""
        parts.append(f"`스탯 변경` {bd.stat} {direction}{bd.value:.0%}{pct} ({bd.duration}턴) → {target_name}")
    elif e.logic_type == LogicType.DOT and e.buff_data:
        bd = e.buff_data
        dot_name = {"burn": "화상", "poison": "중독", "bleed": "출혈"}.get(bd.dot_type, bd.dot_type)
        parts.append(f"`{dot_name}` maxHP×{bd.value:.0%} ({bd.duration}턴, 최대 {bd.max_stacks}스택) → {target_name}")
    elif e.logic_type == LogicType.DOT_HEAL_HP_RATIO and e.buff_data:
        bd = e.buff_data
        parts.append(f"`지속 회복` maxHP×{bd.value:.0%} ({bd.duration}턴) → {target_name}")
    elif e.logic_type == LogicType.CC and e.buff_data:
        bd = e.buff_data
        cc_name = CC_KR.get(bd.cc_type, str(bd.cc_type))
        parts.append(f"`{cc_name}` {bd.duration}턴 → {target_name}")
    elif e.logic_type == LogicType.TAUNT:
        parts.append(f"`도발` {int(e.value)}턴 → {target_name}")
    elif e.logic_type == LogicType.COUNTER:
        parts.append(f"`반격 준비` {int(e.value)}턴 → {target_name}")
    elif e.logic_type == LogicType.REVIVE:
        parts.append(f"`부활` HP {e.value:.0%}로 → {target_name}")
    elif e.logic_type == LogicType.SP_INCREASE:
        parts.append(f"`SP +{int(e.value)}` → {target_name}")
    elif e.logic_type == LogicType.SP_STEAL:
        parts.append(f"`SP 강탈 {int(e.value)}` → {target_name}")
    elif e.logic_type == LogicType.SP_LOCK:
        parts.append(f"`SP 잠금` {int(e.value)}턴 → {target_name}")
    elif e.logic_type in (LogicType.BARRIER, LogicType.BARRIER_RATIO):
        parts.append(f"`보호막` maxHP×{e.value:.0%} → {target_name}")
    elif e.logic_type == LogicType.INVINCIBILITY:
        parts.append(f"`무적` {int(e.value)}턴 → {target_name}")
    elif e.logic_type == LogicType.UNDYING:
        parts.append(f"`불사` {int(e.value)}턴 → {target_name}")
    elif e.logic_type == LogicType.DEBUFF_IMMUNE:
        parts.append(f"`디버프 면역` {int(e.value)}턴 → {target_name}")
    elif e.logic_type == LogicType.REMOVE_DEBUFF:
        parts.append(f"`디버프 제거` → {target_name}")
    elif e.logic_type == LogicType.REMOVE_BUFF:
        parts.append(f"`버프 제거` → {target_name}")
    elif e.logic_type == LogicType.BUFF_TURN_INCREASE:
        parts.append(f"`버프 턴 +{int(e.value)}` → {target_name}")
    elif e.logic_type == LogicType.DEBUFF_TURN_INCREASE:
        parts.append(f"`디버프 턴 +{int(e.value)}` → {target_name}")
    elif e.logic_type == LogicType.DEBUFF_SPREAD:
        parts.append(f"`디버프 전이` → {target_name}")
    elif e.logic_type == LogicType.CRI_UNAVAILABLE:
        parts.append(f"`크리 불가` {int(e.value)}턴 → {target_name}")
    elif e.logic_type == LogicType.COUNTER_UNAVAILABLE:
        parts.append(f"`반격 불가` {int(e.value)}턴 → {target_name}")
    elif e.logic_type == LogicType.USE_SKILL:
        sid = e.condition.get('skill_id', '?') if e.condition else '?'
        parts.append(f"`스킬 체인` → {sid} 발동")
    elif e.logic_type == LogicType.IGNORE_ELEMENT:
        parts.append(f"`속성 무시` {int(e.value)}턴 → {target_name}")
    elif e.logic_type == LogicType.ACTIVE_CD_CHANGE:
        v = int(e.value)
        parts.append(f"`쿨타임 {'+' if v > 0 else ''}{v}` → {target_name}")
    elif e.logic_type == LogicType.SELF_DAMAGE:
        parts.append(f"`자해` HP×{e.value:.0%} → 자기 자신")
    elif e.logic_type == LogicType.STAT_STEAL and e.buff_data:
        bd = e.buff_data
        parts.append(f"`{bd.stat} 강탈` {bd.value:.0f} ({bd.duration}턴) → {target_name}")
    elif e.logic_type == LogicType.LINK_BUFF:
        parts.append(f"`연결 버프` → {target_name}")
    else:
        parts.append(f"`{logic_name}` → {target_name}")
    return parts


# ═══════════════════════════════════════════════════════════════
# 컨셉 키워드 자동 추출
# ═══════════════════════════════════════════════════════════════
def get_concept_keywords(c):
    keywords = []
    all_effects = []
    for sk in [c.normal_skill, c.active_skill, c.ultimate_skill, c.passive_skill]:
        if sk and sk.effects:
            all_effects.extend(sk.effects)
    logic_set = set(e.logic_type for e in all_effects if e.logic_type)

    kw_map = [
        (LogicType.DAMAGE_BURN_BONUS, "화상 폭발"),
        (LogicType.DAMAGE_MISSING_HP_SCALE, "잃은 HP 비례 폭딜"),
        (LogicType.DAMAGE_ESCALATE, "점진 강화"),
        (LogicType.DAMAGE_REPEAT_TARGET, "집중 타격"),
        (LogicType.DAMAGE_PENETRATION, "관통"),
        (LogicType.DAMAGE_CRI, "확정 크리"),
        (LogicType.DAMAGE_BUFF_SCALE, "버프 비례 딜"),
        (LogicType.DAMAGE_BUFF_SCALE_TARGET, "적 버프 비례 딜"),
        (LogicType.DAMAGE_DEBUFF_SCALE_TARGET, "디버프 비례 딜"),
        (LogicType.SELF_DAMAGE, "자해 리스크"),
        (LogicType.STAT_STEAL, "스탯 강탈"),
        (LogicType.LINK_BUFF, "연결 버프"),
        (LogicType.DEBUFF_SPREAD, "디버프 전이"),
        (LogicType.USE_SKILL, "스킬 체인"),
        (LogicType.IGNORE_ELEMENT, "속성 무시"),
    ]
    for lt, kw in kw_map:
        if lt in logic_set:
            keywords.append(kw)

    dot_types = set()
    for e in all_effects:
        if e.logic_type == LogicType.DOT and e.buff_data:
            dot_types.add(getattr(e.buff_data, 'dot_type', ''))
    if 'burn' in dot_types: keywords.append("화상")
    if 'poison' in dot_types: keywords.append("중독")
    if 'bleed' in dot_types: keywords.append("출혈")

    cc_types = set()
    for e in all_effects:
        if e.logic_type == LogicType.CC and e.buff_data:
            ct = getattr(e.buff_data, 'cc_type', None)
            if ct:
                cc_types.add(ct)
    for ct in cc_types:
        keywords.append(CC_KR.get(ct, str(ct)))

    heal_logics = {LogicType.HEAL_HP_RATIO, LogicType.HEAL_PER_HIT, LogicType.HEAL_LOSS_SCALE, LogicType.HEAL_CURRENT_HP_SCALE}
    if logic_set & heal_logics: keywords.append("회복")
    if LogicType.DOT_HEAL_HP_RATIO in logic_set: keywords.append("지속 회복")
    if LogicType.BARRIER in logic_set or LogicType.BARRIER_RATIO in logic_set: keywords.append("보호막")
    if LogicType.REVIVE in logic_set: keywords.append("부활")
    if LogicType.DEBUFF_IMMUNE in logic_set: keywords.append("디버프 면역")
    if LogicType.COUNTER in logic_set: keywords.append("반격")
    if LogicType.TAUNT in logic_set: keywords.append("도발")
    if LogicType.SP_STEAL in logic_set: keywords.append("SP 강탈")
    if LogicType.SP_LOCK in logic_set: keywords.append("SP 잠금")
    if LogicType.REMOVE_BUFF in logic_set: keywords.append("버프 제거")
    if LogicType.REMOVE_DEBUFF in logic_set: keywords.append("디버프 정화")
    if LogicType.BUFF_TURN_INCREASE in logic_set: keywords.append("버프 연장")
    if LogicType.DEBUFF_TURN_INCREASE in logic_set: keywords.append("디버프 연장")

    for e in all_effects:
        if e.condition and e.condition.get('burn_bonus_per_stack', 0) > 0:
            if "화상 증폭" not in keywords:
                keywords.append("화상 증폭")

    return keywords[:8] if keywords else ["기본 딜러"], logic_set


# ═══════════════════════════════════════════════════════════════
# 메인 문서 생성
# ═══════════════════════════════════════════════════════════════
def generate_doc(c, all_chars_map):
    elem_icon, elem_kr, elem_en = ELEM_KR[c.element]
    role_icon, role_kr, role_en = ROLE_KR[c.role]
    hp_map = {
        Role.ATTACKER: {2400: "1", 3200: "2", 4000: "3", 4500: "3", 4600: "3.5", 5000: "3"},
        Role.MAGICIAN: {3000: "1", 4000: "2", 5000: "3", 5750: "3.5"},
        Role.DEFENDER: {3600: "1", 4800: "2", 6000: "3", 6900: "3.5"},
        Role.HEALER: {2400: "1", 3200: "2", 4000: "3", 4600: "3.5"},
        Role.SUPPORTER: {3000: "1", 4000: "2", 5000: "3", 5750: "3.5"},
    }
    grade_val = hp_map.get(c.role, {}).get(c.stats.hp, "3")
    star = f"★{grade_val}"
    spd = c.stats.spd
    sp_cost = c.ultimate_skill.sp_cost if c.ultimate_skill and hasattr(c.ultimate_skill, 'sp_cost') and c.ultimate_skill.sp_cost else 6
    concepts, logic_set = get_concept_keywords(c)
    concept_str = " · ".join(concepts)

    # 메타 참여
    v8_metas = [k for k, (members, _) in META_V8.items() if c.name in members]
    v7_metas = [k for k, members in META_V7.items() if c.name in members]

    adv, disadv = ELEM_ADVANTAGE.get(c.element, (None, None))

    L = []

    # ═══ 헤더 ═══
    L.append(f"# {elem_icon} {c.name} ({c.id}) — 스킬 컨셉 상세 기획서\n")

    # ═══ 1. 캐릭터 아이덴티티 ═══
    L.append(f"## 1. 캐릭터 아이덴티티\n")
    L.append(f"| 항목 | 값 |")
    L.append(f"|------|-----|")
    L.append(f"| **ID** | {c.id} |")
    L.append(f"| **속성** | {elem_icon} {elem_kr} ({elem_en}) |")
    L.append(f"| **역할** | {role_icon} {role_kr} ({role_en}) |")
    L.append(f"| **등급** | {star} |")
    L.append(f"| **기본 스탯** | ATK {c.stats.atk} · DEF {c.stats.def_} · HP {c.stats.hp} · SPD {spd} · CRI {getattr(c, '_cri', 15)}% · SP Cost {sp_cost} |")
    L.append(f"| **CTB 행동 간격** | {300/spd:.2f}초 |")
    if c.tile_pos:
        row_name = {0: "전열", 1: "중열", 2: "후열"}.get(c.tile_pos[0], "?")
        L.append(f"| **기본 배치** | ({c.tile_pos[0]}, {c.tile_pos[1]}) — {row_name} |")
    L.append(f"")
    L.append(f"**컨셉 키워드**: *\"{concept_str}\"*\n")

    # ═══ 2. 스킬 상세 ═══
    L.append(f"---\n")
    L.append(f"## 2. 스킬 상세\n")
    skills = [
        ("노말 스킬", c.normal_skill, "NORMAL", "쿨타임 없음, 매 턴 사용 가능"),
        ("액티브 스킬", c.active_skill, "ACTIVE", f"쿨타임 {c.active_skill.cooldown_turns if c.active_skill else 3}턴"),
        ("얼티밋 스킬", c.ultimate_skill, "ULTIMATE", f"SP {sp_cost} 소모, 엑스트라 턴 발동"),
        ("패시브 스킬", c.passive_skill, "PASSIVE", "자동 발동 (트리거 조건 충족 시)"),
    ]
    for i, (title, skill, stype, desc) in enumerate(skills, 1):
        if not skill:
            continue
        L.append(f"### 2.{i}. {title} — 「{skill.name}」\n")
        L.append(f"| 항목 | 상세 |")
        L.append(f"|------|------|")
        L.append(f"| **타입** | {stype} ({desc}) |")
        if skill.effects:
            for j, eff in enumerate(skill.effects):
                descs = describe_effect(eff)
                for d in descs:
                    L.append(f"| **효과 {j+1}** | {d} |")
        L.append(f"")

    # 트리거 조건
    if c.triggers:
        L.append(f"### 패시브 트리거 조건\n")
        L.append(f"| 트리거 | 설명 | 횟수 제한 |")
        L.append(f"|--------|------|-----------|")
        for t in c.triggers:
            event_kr = TRIGGER_KR.get(t.event, str(t.event))
            once = "전투당 1회" if t.once_per_battle else "무제한"
            L.append(f"| `{t.event.value}` | {event_kr} | {once} |")
        L.append(f"")

    # ═══ 3. 설계 의도 & 밸런스 히스토리 ═══
    L.append(f"---\n")
    L.append(f"## 3. 설계 의도\n")
    intent_lines = generate_design_intent(c, concepts, logic_set)
    L.extend(intent_lines)

    # 밸런스 히스토리
    history = BALANCE_HISTORY.get(c.id, [])
    if history:
        L.append(f"### 밸런스 변경 이력\n")
        seen_h = set()
        for h in history:
            if h not in seen_h:
                L.append(f"- {h}")
                seen_h.add(h)
        L.append(f"")
    else:
        L.append(f"### 밸런스 변경 이력\n")
        L.append(f"출시 이후 밸런스 변경 없음.\n")

    # ═══ 4. 이상적 전투 흐름 ═══
    L.append(f"---\n")
    L.append(f"## 4. 이상적 전투 흐름\n")
    flow_lines = generate_battle_flow(c)
    L.extend(flow_lines)
    L.append(f"")

    # ═══ 5. 시너지 & 카운터 분석 ═══
    L.append(f"---\n")
    L.append(f"## 5. 시너지 & 카운터 분석\n")
    synergy_lines = generate_synergy_counter(c, logic_set, all_chars_map)
    L.extend(synergy_lines)

    # ═══ 6. 메타 참여 ═══
    L.append(f"---\n")
    L.append(f"## 6. 메타 참여\n")
    if v8_metas:
        L.append(f"### v8 메타")
        for m in v8_metas:
            desc = META_V8[m][1]
            L.append(f"- **{m}** — {desc}")
        L.append(f"")
    if v7_metas:
        L.append(f"### v7 메타")
        for m in v7_metas:
            L.append(f"- **{m}**")
        L.append(f"")
    if not v8_metas and not v7_metas:
        L.append(f"현재 메타 조합에 미편성. 향후 밸런스 패치에서 메타 편입 가능성 있음.\n")

    # ═══ 7. 속성 상성 ═══
    L.append(f"---\n")
    L.append(f"## 7. 속성 상성\n")
    if c.element in (Element.LIGHT, Element.DARK):
        adv_str = ELEM_KR[adv][1] if adv else "없음"
        L.append(f"- **유리**: {adv_str} (1.2x) — 광·암은 서로 항상 유리")
        L.append(f"- **불리**: 없음 — 광·암은 불리 상성 없음")
    else:
        adv_str = ELEM_KR[adv][1] if adv else "없음"
        disadv_str = ELEM_KR[disadv][1] if disadv else "없음"
        L.append(f"- **유리**: {adv_str} 속성에 1.2x 피해")
        L.append(f"- **불리**: {disadv_str} 속성에 0.8x 피해 / 1.2x 피해를 받음")
    L.append(f"")

    # ═══ 8. 핵심 포인트 ═══
    L.append(f"---\n")
    L.append(f"## 8. 핵심 포인트\n")

    strengths = []
    weaknesses = []

    if c.role == Role.ATTACKER:
        strengths.append(f"높은 ATK({c.stats.atk})로 강력한 딜링 — 팀의 화력 핵심")
        weaknesses.append(f"낮은 DEF({c.stats.def_})/HP({c.stats.hp})로 집중공격에 취약")
        weaknesses.append(f"느린 SPD({spd}), 행동 간격 {300/spd:.2f}초 — 서포터/힐러 지원 필수")
        weaknesses.append(f"높은 SP 비용({sp_cost}), 팀 SP 관리 부담")
    elif c.role == Role.MAGICIAN:
        strengths.append(f"SPD {spd}의 빠른 행동으로 선제 CC/디버프")
        strengths.append(f"SP Cost {sp_cost}로 효율적인 얼티밋 사용")
        weaknesses.append(f"중간 수준의 내구도 (HP {c.stats.hp}, DEF {c.stats.def_})")
        weaknesses.append(f"딜 기여가 CC/디버프에 비해 제한적")
    elif c.role == Role.DEFENDER:
        strengths.append(f"높은 DEF({c.stats.def_})/HP({c.stats.hp})로 최전선 탱킹")
        strengths.append(f"SP Cost {sp_cost}로 빠른 얼티밋 회전 가능")
        weaknesses.append(f"낮은 ATK({c.stats.atk})로 직접 딜 기여 제한")
    elif c.role == Role.HEALER:
        strengths.append(f"팀 생존의 핵심 — 회복 + 정화로 장기전 우위")
        strengths.append(f"SP Cost {sp_cost}로 가장 빠른 얼티밋 회전")
        weaknesses.append(f"낮은 ATK({c.stats.atk})로 딜 기여 부족")
    elif c.role == Role.SUPPORTER:
        strengths.append(f"SPD {spd} — 팀 내 가장 빠른 행동으로 선제 버프/디버프")
        strengths.append(f"SP Cost {sp_cost}로 효율적인 얼티밋")
        weaknesses.append(f"직접 딜 기여 제한, 팀 의존도 높음")

    # 스킬 기반 강점
    skill_strengths = {
        "화상 증폭": "화상 시너지로 DoT + burn_bonus 폭발 딜",
        "관통": "DEF 무시 관통으로 탱커도 효과적으로 처리",
        "확정 크리": "확정 크리로 안정적인 고피해 보장, CRI_DMG 버프와 극대화",
        "보호막": "보호막으로 팀 생존력 대폭 강화",
        "디버프 면역": "디버프 면역으로 CC/DoT 차단",
        "부활": "부활로 전투 후반 역전 가능",
        "반격": "반격으로 피격 시에도 지속적 딜 기여",
        "도발": "도발로 아군 보호 + 어그로 집중",
        "버프 제거": "적 버프 스트립으로 보호막/버프 무력화",
        "SP 강탈": "적 SP 강탈로 얼티밋 타이밍 교란",
        "스킬 체인": "스킬 체인으로 한 턴에 복수 스킬 실행",
        "잃은 HP 비례 폭딜": "잃은 HP 비례 딜로 후반 갈수록 강해짐",
        "자해 리스크": "자해 → HP 감소 → MISSING_HP_SCALE 폭발 콤보",
        "버프 비례 딜": "버프 스택에 비례한 폭발적 딜링",
        "디버프 연장": "디버프 턴 연장으로 DoT/CC 지속시간 극대화",
        "디버프 전이": "디버프 전이로 단일 디버프를 전체로 확산",
    }
    for kw in concepts:
        if kw in skill_strengths:
            strengths.append(skill_strengths[kw])

    if v8_metas:
        strengths.append(f"v8 메타 {len(v8_metas)}개 조합에 편성 — 검증된 범용성")
    if v7_metas and not v8_metas:
        strengths.append(f"v7 메타 {len(v7_metas)}개 조합에 편성")

    L.append(f"### 강점\n")
    for s in strengths[:6]:
        L.append(f"- {s}")
    L.append(f"")
    L.append(f"### 약점\n")
    for w in weaknesses[:5]:
        L.append(f"- {w}")
    L.append(f"")

    return "\n".join(L)


# ═══════════════════════════════════════════════════════════════
# 캐릭터 팩토리 목록
# ═══════════════════════════════════════════════════════════════
ALL_MAKERS = [
    make_morgan, make_dabi, make_gumiho, make_jiva, make_kararatri,
    make_deresa, make_ragaraja, make_salmakis, make_demeter,
    make_dabi_sup, make_yuda, make_neide, make_verdelet,
    make_eve, make_sangah, make_thisbe, make_bari, make_dogyehwa,
    make_elysion, make_nirrti, make_arhat, make_lisa, make_virupa,
    make_euros, make_mayahuel, make_leo, make_deino,
    make_brownie, make_pan, make_miriam, make_aurora, make_metis,
    make_grilla, make_danu, make_mammon, make_freya, make_diana,
    make_europe, make_midas, make_jacheongbi,
    make_ashtoreth, make_sitri, make_mona, make_semele, make_tiwaz,
    make_titania, make_oneiroi, make_c600, make_dana, make_hildr,
    make_charlotte, make_leda, make_yana, make_mafdet,
    make_frey, make_banshee, make_artemis, make_mircalla, make_yuna,
    make_kubaba, make_anubis, make_c601, make_cain, make_elizabeth,
    make_duetsha, make_mona_dark, make_persephone, make_nevan, make_medusa,
    make_batory,
]


def main():
    out_dir = pathlib.Path(__file__).resolve().parents[1] / "docs" / "character"
    out_dir.mkdir(parents=True, exist_ok=True)

    # 전체 캐릭터 맵 빌드
    all_chars = {}
    for maker in ALL_MAKERS:
        c = maker()
        if c.side != "enemy":
            all_chars[c.name] = c

    # 문서 생성
    generated = 0
    seen_names = {}
    for maker in ALL_MAKERS:
        c = maker()
        if c.side == "enemy":
            continue
        doc = generate_doc(c, all_chars)
        # 동명 캐릭터 처리
        if c.name in seen_names:
            prev_id, prev_fname = seen_names[c.name]
            new_prev = out_dir / f"{c.name}({prev_id}).md"
            if prev_fname.exists() and not new_prev.exists():
                prev_fname.rename(new_prev)
                print(f"  📝 동명 처리: {prev_fname.name} → {new_prev.name}")
                seen_names[c.name] = (prev_id, new_prev)
            fname = out_dir / f"{c.name}({c.id}).md"
        else:
            fname = out_dir / f"{c.name}.md"
            seen_names[c.name] = (c.id, fname)
        fname.write_text(doc, encoding="utf-8")
        generated += 1
        print(f"  ✅ {c.name} ({c.id}) → {fname.name}")

    print(f"\n총 {generated}개 캐릭터 문서 생성 완료!")
    print(f"경로: {out_dir}")


if __name__ == "__main__":
    main()
