# -*- coding: utf-8 -*-
"""
메타팀 간 전투 시뮬레이션 - 간이 계산 모델
10대 메타팀 상성 매트릭스 수치 검증
"""

# ─────────────────────────────────────────────
# 1. 기본 스탯 테이블 (역할, 성급) → (ATK, DEF, HP, SPD)
# ─────────────────────────────────────────────
STATS = {
    ('Attacker',  1  ): (600, 300, 3000, 75),
    ('Attacker',  2  ): (700, 350, 3500, 78),
    ('Attacker',  3  ): (800, 400, 4000, 80),
    ('Attacker',  3.5): (900, 420, 4200, 85),
    ('Magician',  1  ): (550, 280, 2800, 78),
    ('Magician',  2  ): (650, 320, 3200, 80),
    ('Magician',  3  ): (750, 360, 3600, 83),
    ('Magician',  3.5): (850, 380, 3800, 88),
    ('Defender',  1  ): (400, 500, 4500, 65),
    ('Defender',  2  ): (450, 600, 5200, 68),
    ('Defender',  3  ): (500, 700, 6000, 70),
    ('Defender',  3.5): (520, 780, 6500, 72),
    ('Healer',    1  ): (350, 350, 3500, 72),
    ('Healer',    2  ): (400, 400, 4000, 75),
    ('Healer',    3  ): (450, 450, 4500, 78),
    ('Healer',    3.5): (480, 480, 4800, 80),
    ('Supporter', 1  ): (450, 320, 3200, 80),
    ('Supporter', 2  ): (520, 370, 3700, 83),
    ('Supporter', 3  ): (600, 420, 4200, 85),
    ('Supporter', 3.5): (650, 450, 4500, 90),
}

# ─────────────────────────────────────────────
# 2. 속성 상성 테이블
# ─────────────────────────────────────────────
# (공격 속성, 방어 속성) → 보정 배율
ELEMENT_ADVANTAGE = {
    ('Fire',   'Forest'): 1.30,
    ('Water',  'Fire'  ): 1.30,
    ('Forest', 'Water' ): 1.30,
    ('Light',  'Dark'  ): 1.30,
    ('Dark',   'Light' ): 1.30,
    ('Fire',   'Water' ): 0.70,
    ('Forest', 'Fire'  ): 0.70,
    ('Water',  'Forest'): 0.70,
    ('Dark',   'Light' ): 1.30,
    ('Light',  'Dark'  ): 1.30,
}

def element_mod(atk_elem: str, def_elem: str) -> float:
    if atk_elem == def_elem:
        return 1.0
    return ELEMENT_ADVANTAGE.get((atk_elem, def_elem), 1.0)

# ─────────────────────────────────────────────
# 3. 메타팀 정의
#    (이름, 속성, 역할, 성급)
# ─────────────────────────────────────────────
TEAMS = {
    'M01 화상연소': [
        ('카라라트리', 'Fire',   'Attacker',  3  ),
        ('다비2',      'Fire',   'Magician',  3  ),
        ('살마키스',   'Fire',   'Supporter', 3  ),
        ('지바',       'Fire',   'Healer',    3  ),
        ('데레사',     'Fire',   'Defender',  3  ),
    ],
    'M02 빙결제어': [
        ('바리',   'Water', 'Magician',  3  ),
        ('니르티', 'Water', 'Attacker',  3  ),
        ('도계화', 'Water', 'Magician',  3  ),
        ('티스베', 'Water', 'Healer',    3  ),
        ('상아',   'Water', 'Supporter', 3  ),
    ],
    'M03 수면폭발': [
        ('에레보스', 'Forest', 'Magician',  3.5),
        ('판',       'Forest', 'Magician',  3  ),
        ('다이아나', 'Forest', 'Magician',  1  ),
        ('아우로라', 'Forest', 'Healer',    3  ),
        ('그릴라',   'Forest', 'Supporter', 3  ),
    ],
    'M04 치명타학살': [
        ('아누비스',   'Dark',  'Attacker',  3.5),
        ('바토리',     'Dark',  'Supporter', 3  ),
        ('유나',       'Dark',  'Supporter', 3  ),
        ('아르테미스', 'Dark',  'Magician',  3  ),
        ('페르세포네', 'Dark',  'Supporter', 1  ),
    ],
    'M05 속도압도': [
        ('아라한', 'Water', 'Supporter', 3.5),
        ('이브',   'Water', 'Attacker',  3  ),
        ('리자',   'Water', 'Attacker',  2  ),
        ('에우로스','Water', 'Healer',    2  ),
        ('레오',   'Water', 'Supporter', 1  ),
    ],
    'M06 철벽수호': [
        ('맘몬',   'Forest', 'Defender',  2  ),
        ('메티스', 'Forest', 'Defender',  3  ),
        ('모나2',  'Light',  'Defender',  3  ),
        ('브라우니','Forest','Supporter', 3  ),
        ('자청비', 'Forest', 'Supporter', 2  ),
    ],
    'M07 출혈암살': [
        ('바토리',  'Dark',  'Supporter', 3  ),
        ('미르칼라','Dark',  'Healer',    3  ),
        ('두엣샤',  'Dark',  'Magician',  2  ),
        ('프레이',  'Dark',  'Defender',  3  ),
        ('쿠바바',  'Dark',  'Attacker',  3  ),
    ],
    'M08 보호막연합': [
        ('루미나',   'Light', 'Magician',  3.5),
        ('티타니아', 'Light', 'Defender',  3  ),
        ('오네이로이','Light','Supporter', 3  ),
        ('다나',     'Light', 'Healer',    2  ),
        ('시트리',   'Light', 'Supporter', 3  ),
    ],
    'M09 디버프착취': [
        ('아슈토레스','Light', 'Attacker',  3  ),
        ('드미테르',  'Fire',  'Supporter', 2  ),
        ('루미나',    'Light', 'Magician',  3.5),
        ('카인',      'Fire',  'Attacker',  2  ),
        ('모건',      'Fire',  'Magician',  3  ),
    ],
    'M10 혼성엘리트': [
        ('아누비스',   'Dark',   'Attacker',  3.5),
        ('에레보스',   'Forest', 'Magician',  3.5),
        ('카라라트리', 'Fire',   'Attacker',  3  ),
        ('루미나',     'Light',  'Magician',  3.5),
        ('아우로라',   'Forest', 'Healer',    3  ),
    ],
}

# ─────────────────────────────────────────────
# 4. CC 보유 정보
# ─────────────────────────────────────────────
CC_CHARS = {
    '카라라트리': 'burn',
    '다비2':      'burn',
    '데레사':     'burn',
    '바리':       'freeze',
    '니르티':     'freeze',
    '도계화':     'freeze',
    '상아':       'freeze',
    '에레보스':   'sleep',
    '판':         'sleep',
    '다이아나':   'poison+sleep',
    '아누비스':   'instant_kill',
    '아르테미스': 'silence',
    '바토리':     'bleed',
    '두엣샤':     'bleed',
    '이브':       'stun',
    '모나2':      'taunt',
    '맘몬':       'taunt',
    '프레이':     'taunt',
    '메두사':     'stone',
}

# ─────────────────────────────────────────────
# 5. 팀별 특수 시너지 보정
#    (own_dps_mult, opp_dps_mult, own_hp_mult)
# ─────────────────────────────────────────────
SYNERGY = {
    'M01 화상연소':   (1.15, 1.00, 1.00),
    'M02 빙결제어':   (1.00, 0.85, 1.00),
    'M03 수면폭발':   (1.20, 0.90, 1.00),
    'M04 치명타학살': (1.25, 1.00, 1.00),
    'M05 속도압도':   (1.10, 0.95, 1.00),
    'M06 철벽수호':   (1.00, 1.00, 1.30),
    'M07 출혈암살':   (1.10, 1.00, 1.10),
    'M08 보호막연합': (1.00, 0.95, 1.25),
    'M09 디버프착취': (1.20, 1.00, 1.00),
    'M10 혼성엘리트': (1.15, 1.00, 1.10),
}

# ─────────────────────────────────────────────
# 6. 팀 전투력 계산
# ─────────────────────────────────────────────
SKILL_MULTIPLIER = 2.5  # 평균 스킬 배율

def calc_team_power(team_name: str, members: list) -> dict:
    """팀의 DPS, 유효HP, CC 수, 주속성을 반환"""
    total_dps = 0.0
    total_ehp = 0.0
    elem_count: dict = {}
    cc_count = 0

    # 주 방어 속성: 가장 많은 속성
    for name, elem, role, stars in members:
        elem_count[elem] = elem_count.get(elem, 0) + 1
        if name in CC_CHARS:
            cc_count += 1

    dominant_elem = max(elem_count, key=lambda e: elem_count[e])

    for name, elem, role, stars in members:
        atk, defense, hp, spd = STATS[(role, stars)]
        # 팀 내 속성 시너지 보정 (동속성 멤버 수 × 5%)
        same_elem_count = elem_count.get(elem, 1)
        synergy_bonus = 1.0 + (same_elem_count - 1) * 0.05

        # 속성 보정은 vs 상대 시 적용하므로 여기선 1.0
        dps = atk * SKILL_MULTIPLIER * synergy_bonus / (300 / spd)
        ehp = hp * (1 + defense / 1000)

        total_dps += dps
        total_ehp += ehp

    return {
        'dps': total_dps,
        'ehp': total_ehp,
        'cc': cc_count,
        'elem_count': elem_count,
        'dominant_elem': dominant_elem,
        'members': members,
    }

# ─────────────────────────────────────────────
# 7. 1:1 전투 판정
# ─────────────────────────────────────────────
def battle(a_name: str, b_name: str) -> dict:
    """
    두 팀이 싸웠을 때 승/패/무 + 각 팀의 승리 예상 턴을 반환.
    반환: {'result': 'A_WIN'|'B_WIN'|'DRAW', 'a_turns': float, 'b_turns': float}
    """
    a_members = TEAMS[a_name]
    b_members = TEAMS[b_name]
    ap = calc_team_power(a_name, a_members)
    bp = calc_team_power(b_name, b_members)

    a_syn_dps, a_syn_opp, a_syn_hp = SYNERGY[a_name]
    b_syn_dps, b_syn_opp, b_syn_hp = SYNERGY[b_name]

    # 속성 보정: A팀 멤버별로 B팀 주속성에 대한 보정 평균
    def avg_elem_mod(attacker_members, def_dominant_elem):
        total = 0.0
        for name, elem, role, stars in attacker_members:
            total += element_mod(elem, def_dominant_elem)
        return total / len(attacker_members)

    a_elem = avg_elem_mod(a_members, bp['dominant_elem'])
    b_elem = avg_elem_mod(b_members, ap['dominant_elem'])

    # CC 보정: 상대 DPS 감소 (CC 보유 멤버 수 × 5%)
    a_cc_debuff = 1.0 - ap['cc'] * 0.05   # A가 B에게 가하는 CC → B DPS 감소
    b_cc_debuff = 1.0 - bp['cc'] * 0.05

    # 최종 A의 유효 DPS (B에게 가하는 딜)
    a_effective_dps = ap['dps'] * a_syn_dps * a_elem * b_syn_opp * b_cc_debuff
    b_effective_dps = bp['dps'] * b_syn_dps * b_elem * a_syn_opp * a_cc_debuff

    # 최종 유효 HP
    a_effective_ehp = ap['ehp'] * a_syn_hp
    b_effective_ehp = bp['ehp'] * b_syn_hp

    # 승리 턴 = 상대 유효HP / 자신 유효DPS
    a_turns = b_effective_ehp / a_effective_dps   # A가 B를 전멸시키는 턴
    b_turns = a_effective_ehp / b_effective_dps   # B가 A를 전멸시키는 턴

    DRAW_THRESHOLD = 0.05  # 5% 이내 차이는 무승부

    diff = abs(a_turns - b_turns) / max(a_turns, b_turns)
    if diff < DRAW_THRESHOLD:
        result = 'DRAW'
    elif a_turns < b_turns:
        result = 'A_WIN'
    else:
        result = 'B_WIN'

    return {
        'result': result,
        'a_turns': a_turns,
        'b_turns': b_turns,
        'a_dps': a_effective_dps,
        'b_dps': b_effective_dps,
        'a_ehp': a_effective_ehp,
        'b_ehp': b_effective_ehp,
    }

# ─────────────────────────────────────────────
# 8. 기존 예상 상성 매트릭스 (주관적 기획 기준)
#    값: 1=A 유리, 0=互角, -1=A 불리
#    [A_index][B_index]
# ─────────────────────────────────────────────
TEAM_NAMES = list(TEAMS.keys())
N = len(TEAM_NAMES)

# 기존 상성 매트릭스 (행=공격팀, 열=수비팀 기준 기획 예상)
# 1: 행팀 유리, -1: 행팀 불리, 0: 互角
EXPECTED_MATCHUP = {
    # M01 화상 vs 나머지
    ('M01 화상연소',   'M02 빙결제어' ): -1,  # 물>불
    ('M01 화상연소',   'M03 수면폭발' ): 1,   # 불>숲
    ('M01 화상연소',   'M06 철벽수호' ): -1,  # 철벽은 화상팀이 뚫기 어려움
    ('M01 화상연소',   'M08 보호막연합'): 0,
    ('M02 빙결제어',   'M01 화상연소' ): 1,   # 물>불
    ('M02 빙결제어',   'M03 수면폭발' ): 1,   # 빙결 행동봉쇄 > 숲
    ('M02 빙결제어',   'M05 속도압도' ): 0,   # 同속성 내전
    ('M03 수면폭발',   'M01 화상연소' ): -1,  # 숲<불
    ('M03 수면폭발',   'M06 철벽수호' ): 1,   # 수면폭발로 철벽 붕괴
    ('M04 치명타학살', 'M08 보호막연합'): -1,  # 보호막이 즉사 방어
    ('M04 치명타학살', 'M07 출혈암살' ): 1,   # 同다크 내전 크리 우위
    ('M05 속도압도',   'M04 치명타학살'): 1,   # 선제 속도
    ('M06 철벽수호',   'M05 속도압도' ): 1,   # 철벽이 속도 압살
    ('M07 출혈암살',   'M08 보호막연합'): -1,  # 보호막이 출혈 DoT 흡수
    ('M08 보호막연합', 'M09 디버프착취'): 0,   # 互角
    ('M09 디버프착취', 'M07 출혈암살' ): 1,   # 디버프 착취 우위
    ('M10 혼성엘리트', 'M06 철벽수호' ): 1,   # 올라운드가 철벽 돌파
    ('M10 혼성엘리트', 'M01 화상연소' ): 1,   # 엘리트 우위
}


# ─────────────────────────────────────────────
# 9. 전체 시뮬레이션 실행
# ─────────────────────────────────────────────
def run_simulation():
    # 결과 저장: matrix[i][j] = battle(team_i, team_j)
    matrix = {}
    records = {name: {'win': 0, 'lose': 0, 'draw': 0} for name in TEAM_NAMES}

    for i, a in enumerate(TEAM_NAMES):
        for j, b in enumerate(TEAM_NAMES):
            if i == j:
                matrix[(i, j)] = None
                continue
            if (j, i) in matrix and matrix[(j, i)] is not None:
                # 대칭 재활용 (방향 반전)
                prev = matrix[(j, i)]
                rev_result = {'A_WIN': 'B_WIN', 'B_WIN': 'A_WIN', 'DRAW': 'DRAW'}[prev['result']]
                matrix[(i, j)] = {
                    'result': rev_result,
                    'a_turns': prev['b_turns'],
                    'b_turns': prev['a_turns'],
                    'a_dps': prev['b_dps'],
                    'b_dps': prev['a_dps'],
                    'a_ehp': prev['b_ehp'],
                    'b_ehp': prev['a_ehp'],
                }
            else:
                res = battle(a, b)
                matrix[(i, j)] = res

            res = matrix[(i, j)]
            if res['result'] == 'A_WIN':
                records[a]['win'] += 1
                records[b]['lose'] += 1
            elif res['result'] == 'B_WIN':
                records[b]['win'] += 1
                records[a]['lose'] += 1
            else:
                records[a]['draw'] += 1
                records[b]['draw'] += 1

    return matrix, records


# ─────────────────────────────────────────────
# 10. 출력 함수들
# ─────────────────────────────────────────────
def short_name(full: str) -> str:
    """M01 화상연소 → M01"""
    return full.split()[0]

def print_matrix(matrix):
    COL_W = 9  # 각 셀 너비
    header_width = 16

    print("\n" + "=" * 100)
    print("  [1] 10×10 승패 매트릭스  (행=공격팀, 열=상대팀 | WIN=행팀 승, LOSE=행팀 패)")
    print("=" * 100)

    # 헤더
    header = f"{'':>{header_width}}"
    for name in TEAM_NAMES:
        header += f"  {short_name(name):^7}"
    print(header)
    print("-" * (header_width + N * (COL_W + 2) + 2))

    for i, a in enumerate(TEAM_NAMES):
        row = f"{a:>{header_width}}"
        for j, b in enumerate(TEAM_NAMES):
            if i == j:
                row += f"  {'---':^7}"
                continue
            res = matrix[(i, j)]
            if res['result'] == 'A_WIN':
                tag = f"WIN({res['a_turns']:.1f})"
            elif res['result'] == 'B_WIN':
                tag = f"LOSE({res['b_turns']:.1f})"
            else:
                tag = f"DRAW({res['a_turns']:.1f})"
            row += f"  {tag:^7}"
        print(row)

    print("-" * (header_width + N * (COL_W + 2) + 2))
    print("  숫자 = 승리팀의 예상 전멸 턴수 (낮을수록 압도적 승리)\n")


def print_records(records):
    print("=" * 60)
    print("  [2] 팀별 전적 요약")
    print("=" * 60)
    print(f"  {'팀명':<18} {'승':>4} {'패':>4} {'무':>4}  {'승률':>6}")
    print("-" * 60)

    sorted_teams = sorted(records.items(), key=lambda x: x[1]['win'], reverse=True)
    for name, rec in sorted_teams:
        total = rec['win'] + rec['lose'] + rec['draw']
        rate = rec['win'] / total * 100 if total else 0
        print(f"  {name:<18} {rec['win']:>4} {rec['lose']:>4} {rec['draw']:>4}  {rate:>5.1f}%")
    print()


def print_tier(records):
    print("=" * 60)
    print("  [3] 티어 판정 (승수 기반)")
    print("=" * 60)

    sorted_teams = sorted(records.items(), key=lambda x: x[1]['win'], reverse=True)
    tiers = {9: 'S+', 8: 'S', 7: 'S', 6: 'A', 5: 'A', 4: 'B', 3: 'B', 2: 'C', 1: 'C', 0: 'D'}

    for name, rec in sorted_teams:
        wins = rec['win']
        tier = tiers.get(wins, 'D')
        bar = '█' * wins + '░' * (9 - wins)
        print(f"  [{tier:>2}] {name:<18}  {bar}  {wins}승")
    print()


def print_comparison(matrix):
    print("=" * 70)
    print("  [4] 기존 예상 상성 vs 시뮬레이션 결과 비교")
    print("=" * 70)
    print(f"  {'매치업':<35} {'예상':>5}  {'결과':>8}  {'판정'}")
    print("-" * 70)

    match_count = 0
    total_count = 0

    for (a, b), expected in EXPECTED_MATCHUP.items():
        i = TEAM_NAMES.index(a)
        j = TEAM_NAMES.index(b)
        res = matrix[(i, j)]

        sim_val = 1 if res['result'] == 'A_WIN' else (-1 if res['result'] == 'B_WIN' else 0)
        expected_str = {1: 'A 유리', -1: 'A 불리', 0: '互角'}[expected]
        result_str   = {1: 'A 승리', -1: 'B 승리', 0: '무승부'}[sim_val]

        match = (expected == sim_val)
        judge = '✓ 일치' if match else '✗ 불일치'
        match_count += int(match)
        total_count += 1

        print(f"  {a:<18} vs {b:<14}  {expected_str:>5}  {result_str:>8}  {judge}")

    print("-" * 70)
    print(f"  일치율: {match_count}/{total_count} ({match_count/total_count*100:.1f}%)\n")


# ─────────────────────────────────────────────
# 11. 메인
# ─────────────────────────────────────────────
if __name__ == '__main__':
    print("\n" + "=" * 100)
    print("  BattleAgent 메타팀 전투 시뮬레이션 v1.0")
    print("  10대 메타팀 상성 매트릭스 수치 검증")
    print("=" * 100)

    matrix, records = run_simulation()

    print_matrix(matrix)
    print_records(records)
    print_tier(records)
    print_comparison(matrix)

    print("시뮬레이션 완료.")
