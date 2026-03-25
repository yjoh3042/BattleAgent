"""BattleAgent 전투 시뮬레이션 툴 — 웹 UI

차일드 5명 선택 + 3×3 그리드 배치 + 시뮬레이션 실행

실행: py -3 scripts/battle_tool/app.py
브라우저: http://localhost:5000
"""
import sys
import os
import json
import copy

# 프로젝트 루트 경로 설정
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, os.path.join(PROJECT_ROOT, 'src'))

from flask import Flask, render_template, jsonify, request
from battle.battle_engine import BattleEngine
from battle.enums import BattleResult, Element, Role
from battle.models import CharacterData
from battle.rules import ROLE_STAT_STANDARD
from fixtures import test_data

app = Flask(__name__)

# ════════════════════════════════════════════════════════════
# 캐릭터 레지스트리 — make_* 함수를 자동 수집
# ════════════════════════════════════════════════════════════

def _detect_grade(char: CharacterData) -> float:
    """캐릭터 HP와 역할 기준으로 성급 역산 (ROLE_STAT_STANDARD 기준)

    HP가 표준 테이블과 정확 일치하면 해당 성급 반환.
    불일치 시 (커스터마이즈된 캐릭터) DEF 기반으로 2차 판별.
    """
    # 수동 오버라이드 (HP가 커스터마이즈된 특수 캐릭터)
    _GRADE_OVERRIDE = {
        'c095': 3.5,   # 에르제베트 (ATK=1000, HP=5000 커스텀)
        'c063': 3.5,   # 쿠바바 (ATK=870, HP=4500 커스텀)
        'c064': 3.5,   # 메두사 (ATK=980, HP=5000 커스텀)
    }
    if char.id in _GRADE_OVERRIDE:
        return _GRADE_OVERRIDE[char.id]

    role = char.role
    hp = char.stats.hp
    if role in ROLE_STAT_STANDARD:
        hp_table = ROLE_STAT_STANDARD[role].get("hp", {})
        # 정확 일치 우선
        for grade, standard_hp in hp_table.items():
            if hp == standard_hp:
                return grade
        # 불일치 시 DEF 기반 2차 판별
        def_table = ROLE_STAT_STANDARD[role].get("def", {})
        def_val = char.stats.def_
        for grade, standard_def in def_table.items():
            if def_val == standard_def:
                return grade
        # 최종 fallback: HP 가장 가까운 값
        return min(hp_table.keys(), key=lambda g: abs(hp_table[g] - hp))
    return 3.0


def _build_char_registry():
    """test_data 모듈에서 make_* 함수를 자동 수집하여 캐릭터 목록 생성"""
    registry = {}
    skip = {'make_teddy_a', 'make_teddy_b', 'make_teddy_c', 'make_teddy_d', 'make_teddy_e'}
    for name in dir(test_data):
        if name.startswith('make_') and name not in skip:
            fn = getattr(test_data, name)
            if callable(fn):
                try:
                    char = fn()
                    if isinstance(char, CharacterData):
                        grade = _detect_grade(char)
                        registry[name] = {
                            'factory': name,
                            'id': char.id,
                            'name': char.name,
                            'element': char.element.value,
                            'role': char.role.value,
                            'grade': grade,
                            'tile_pos': list(char.tile_pos),
                            'stats': {
                                'atk': char.stats.atk,
                                'def': char.stats.def_,
                                'hp': char.stats.hp,
                                'spd': char.stats.spd,
                                'cri_ratio': char.stats.cri_ratio,
                            }
                        }
                except Exception:
                    pass
    return registry

CHAR_REGISTRY = _build_char_registry()


# ════════════════════════════════════════════════════════════
# API 엔드포인트
# ════════════════════════════════════════════════════════════

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/characters')
def api_characters():
    """전체 캐릭터 목록 반환"""
    chars = sorted(CHAR_REGISTRY.values(), key=lambda c: (c['element'], c['role'], c['name']))
    return jsonify(chars)


@app.route('/api/simulate', methods=['POST'])
def api_simulate():
    """시뮬레이션 실행
    Request Body:
    {
        "allies": [{"factory": "make_xxx", "row": 0, "col": 1}, ...],
        "enemies": [{"factory": "make_xxx", "row": 0, "col": 1}, ...],
        "runs": 20,
        "show_log": false
    }
    """
    data = request.json
    ally_specs = data.get('allies', [])
    enemy_specs = data.get('enemies', [])
    runs = min(data.get('runs', 20), 100)
    show_log = data.get('show_log', False)

    if len(ally_specs) == 0 or len(enemy_specs) == 0:
        return jsonify({'error': '양 진영에 최소 1명 이상 배치해주세요.'}), 400
    if len(ally_specs) > 5 or len(enemy_specs) > 5:
        return jsonify({'error': '각 진영은 최대 5명까지 배치 가능합니다.'}), 400

    # 캐릭터 생성
    def build_party(specs, side):
        party = []
        for sp in specs:
            factory_name = sp['factory']
            fn = getattr(test_data, factory_name, None)
            if fn is None:
                return None, f"캐릭터 팩토리 '{factory_name}' 을 찾을 수 없습니다."
            char = fn()
            # 위치 오버라이드
            row = max(0, min(2, sp.get('row', char.tile_pos[0])))
            col = max(0, min(2, sp.get('col', char.tile_pos[1])))
            char.tile_pos = (row, col)
            # 적군 변환
            if side == 'enemy':
                char = copy.deepcopy(char)
                char.side = 'enemy'
                char.id = f"enemy_{char.id}"
            party.append(char)
        return party, None

    allies, err = build_party(ally_specs, 'ally')
    if err:
        return jsonify({'error': err}), 400
    enemies, err = build_party(enemy_specs, 'enemy')
    if err:
        return jsonify({'error': err}), 400

    # 시뮬레이션 실행
    wins, losses, draws = 0, 0, 0
    last_log = []
    turn_counts = []
    ally_survivors = []
    enemy_survivors = []

    for seed in range(runs):
        try:
            # 매 시행마다 새로운 캐릭터 인스턴스 생성
            a_party, _ = build_party(ally_specs, 'ally')
            e_party, _ = build_party(enemy_specs, 'enemy')

            engine = BattleEngine(
                ally_units=a_party,
                enemy_units=e_party,
                seed=seed,
            )
            result = engine.run()
            turn_counts.append(engine.turn_count)

            if result == BattleResult.ALLY_WIN:
                wins += 1
            elif result == BattleResult.ENEMY_WIN:
                losses += 1
            else:
                draws += 1

            # 마지막 시행의 로그 및 생존자 기록
            if seed == runs - 1:
                if show_log:
                    last_log = engine.get_log()[-50:]  # 마지막 50줄
                ally_survivors = [
                    {
                        'name': u.name,
                        'hp': round(u.current_hp),
                        'max_hp': round(u.max_hp),
                        'alive': u.is_alive,
                        'tile_pos': [u.tile_row, u.tile_col],
                    }
                    for u in engine.allies
                ]
                enemy_survivors = [
                    {
                        'name': u.name,
                        'hp': round(u.current_hp),
                        'max_hp': round(u.max_hp),
                        'alive': u.is_alive,
                        'tile_pos': [u.tile_row, u.tile_col],
                    }
                    for u in engine.enemies
                ]
        except Exception as e:
            draws += 1
            last_log.append(f"seed={seed} 오류: {str(e)}")

    win_rate = wins / runs * 100 if runs > 0 else 0
    avg_turns = sum(turn_counts) / len(turn_counts) if turn_counts else 0

    return jsonify({
        'wins': wins,
        'losses': losses,
        'draws': draws,
        'runs': runs,
        'win_rate': round(win_rate, 1),
        'avg_turns': round(avg_turns, 1),
        'ally_survivors': ally_survivors,
        'enemy_survivors': enemy_survivors,
        'log': last_log,
    })


@app.route('/api/meta_teams')
def api_meta_teams():
    """프리셋 메타팀 목록 반환"""
    # 팀별 고유 배치 (겹침 없이 5명 × 고유 셀)
    # cell = row*3+col, row: 전열0/중열1/후열2, col: 0/1/2
    teams = {
        'M01 화상연소': [
            {'factory': 'make_deresa',    'row': 0, 'col': 1},  # cell1 전열 탱커
            {'factory': 'make_kararatri', 'row': 1, 'col': 0},  # cell3 중열 딜러
            {'factory': 'make_dabi_sup',  'row': 2, 'col': 0},  # cell6 후열 마법사
            {'factory': 'make_salmakis',  'row': 2, 'col': 1},  # cell7 후열 서포터
            {'factory': 'make_jiva',      'row': 2, 'col': 2},  # cell8 후열 힐러
        ],
        'M02 빙결제어': [
            {'factory': 'make_bari',      'row': 0, 'col': 0},  # cell0 전열 마법사
            {'factory': 'make_virupa',    'row': 0, 'col': 1},  # cell1 전열 딜러
            {'factory': 'make_mayahuel',  'row': 1, 'col': 2},  # cell5 중열 마법사
            {'factory': 'make_thisbe',    'row': 2, 'col': 1},  # cell7 후열 힐러
            {'factory': 'make_sangah',    'row': 2, 'col': 2},  # cell8 후열 서포터
        ],
        'M03 수면폭발': [
            {'factory': 'make_c601',      'row': 0, 'col': 2},  # cell2 전열 마법사(에레보스)
            {'factory': 'make_grilla',    'row': 1, 'col': 0},  # cell3 중열 서포터
            {'factory': 'make_pan',       'row': 1, 'col': 1},  # cell4 중열 마법사
            {'factory': 'make_diana',     'row': 1, 'col': 2},  # cell5 중열 마법사
            {'factory': 'make_aurora',    'row': 2, 'col': 2},  # cell8 후열 서포터
        ],
        'M04 치명타학살': [
            {'factory': 'make_anubis',    'row': 0, 'col': 1},  # cell1 전열 딜러
            {'factory': 'make_batory',    'row': 0, 'col': 2},  # cell2 전열 서포터
            {'factory': 'make_artemis',   'row': 1, 'col': 2},  # cell5 중열 마법사
            {'factory': 'make_persephone','row': 2, 'col': 1},  # cell7 후열 서포터
            {'factory': 'make_yuna',      'row': 2, 'col': 2},  # cell8 후열 서포터
        ],
        'M05 속도압도': [
            {'factory': 'make_eve',       'row': 0, 'col': 1},  # cell1 전열 딜러
            {'factory': 'make_sangah',    'row': 1, 'col': 2},  # cell5 중열 서포터
            {'factory': 'make_arhat',     'row': 2, 'col': 0},  # cell6 후열 서포터(아라한)
            {'factory': 'make_euros',     'row': 2, 'col': 1},  # cell7 후열 힐러
            {'factory': 'make_elysion',   'row': 2, 'col': 2},  # cell8 후열 탱커
        ],
        'M06 철벽수호': [
            {'factory': 'make_mammon',    'row': 1, 'col': 0},  # cell3 중열 탱커
            {'factory': 'make_danu',      'row': 1, 'col': 2},  # cell5 중열 딜러
            {'factory': 'make_brownie',   'row': 2, 'col': 0},  # cell6 후열 힐러
            {'factory': 'make_metis',     'row': 2, 'col': 1},  # cell7 후열 탱커
            {'factory': 'make_mona',      'row': 2, 'col': 2},  # cell8 후열 탱커
        ],
        'M07 출혈암살': [
            {'factory': 'make_kubaba',    'row': 0, 'col': 0},  # cell0 전열 딜러
            {'factory': 'make_frey',      'row': 0, 'col': 1},  # cell1 전열 탱커
            {'factory': 'make_batory',    'row': 0, 'col': 2},  # cell2 전열 서포터
            {'factory': 'make_mircalla',  'row': 1, 'col': 0},  # cell3 중열 힐러
            {'factory': 'make_duetsha',   'row': 1, 'col': 2},  # cell5 중열 마법사
        ],
        'M08 보호막연합': [
            {'factory': 'make_oneiroi',   'row': 1, 'col': 1},  # cell4 중열 서포터
            {'factory': 'make_c600',      'row': 2, 'col': 0},  # cell6 후열 마법사(루미나)
            {'factory': 'make_titania',   'row': 2, 'col': 1},  # cell7 후열 탱커
            {'factory': 'make_dana',      'row': 2, 'col': 2},  # cell8 후열 힐러
            {'factory': 'make_sitri',     'row': 0, 'col': 2},  # cell2 전열 서포터
        ],
        'M09 디버프착취': [
            {'factory': 'make_ashtoreth', 'row': 0, 'col': 0},  # cell0 전열 딜러
            {'factory': 'make_cain',      'row': 0, 'col': 1},  # cell1 전열 딜러
            {'factory': 'make_morgan',    'row': 0, 'col': 2},  # cell2 전열 마법사
            {'factory': 'make_demeter',   'row': 1, 'col': 1},  # cell4 중열 서포터
            {'factory': 'make_c600',      'row': 2, 'col': 0},  # cell6 후열 마법사(루미나)
        ],
        'M10 혼성엘리트': [
            {'factory': 'make_anubis',    'row': 0, 'col': 1},  # cell1 전열 딜러
            {'factory': 'make_c601',      'row': 0, 'col': 2},  # cell2 전열 마법사(에레보스)
            {'factory': 'make_kararatri', 'row': 1, 'col': 0},  # cell3 중열 딜러
            {'factory': 'make_arhat',     'row': 2, 'col': 1},  # cell7 후열 서포터(아라한)
            {'factory': 'make_jiva',      'row': 2, 'col': 2},  # cell8 후열 힐러
        ],
    }
    # 각 팀 캐릭터에 기본 위치 정보 추가
    result = {}
    for team_name, members in teams.items():
        enriched = []
        for m in members:
            fn = getattr(test_data, m['factory'], None)
            if fn:
                char = fn()
                enriched.append({
                    'factory': m['factory'],
                    'name': char.name,
                    'element': char.element.value,
                    'role': char.role.value,
                    'grade': _detect_grade(char),
                    'row': m['row'],
                    'col': m['col'],
                })
        result[team_name] = enriched
    return jsonify(result)


if __name__ == '__main__':
    print("=" * 60)
    print("  BattleAgent 전투 시뮬레이션 툴")
    print("  http://localhost:5000")
    print("=" * 60)
    app.run(debug=False, port=5000)
