"""Precise skill name fix - function-scoped replacements.

First script caused collisions because it used global string replace.
This script targets specific maker functions by finding the function boundary
and replacing only within that scope.

Also restores wrongly-changed names for non-Excel characters (지바, 메티스, 엘리시온).
"""
import re

FILE = r'C:\Ai\BattleAgent\src\fixtures\test_data.py'

with open(FILE, 'r', encoding='utf-8') as f:
    content = f.read()

# Each entry: (function_name, [(old_name, new_name), ...])
# Characters IN Excel that still need updating:
TARGETED_FIXES = [
    # ── Excel characters needing name updates ──
    ('make_ragaraja',  [('신의 분노', '맹화')]),  # only ult
    ('make_dogyehwa',  [('독격', '원거만리'), ('마비독', '신행귀신 속거천리'), ('후방독격', '급급여율령')]),
    ('make_bari',      [('독침', '삼재'), ('독 살포', '천라홍수'), ('독무', '은하수 곡성')]),
    ('make_batory',    [('피의 강타', '동반자 예우'), ('피의 환희', '피의 맹세'), ('궁극의 출혈', '에스코트')]),
    ('make_brownie',   [('풀잎 매질', '고급정보입니다!'), ('야생의 박동', '특급정보입니다!'), ('숲의 환희', '데스페라도 친칠라')]),
    ('make_pan',       [('환상의 피리', '목동의 휘파람'), ('수면의 선율', '작은 양을 위한 굴레'), ('꿈의 나락', '고요한 봄의 들판')]),
    ('make_miriam',    [('맹타', '웨이팅 포 딜'), ('투지', '크로스 더 루비콘'), ('전장의 공포', '퓨리오스')]),
    ('make_aurora',    [('빛의 손길', '기다림의 끝'), ('전사의 축복', '지켜주는 나무'), ('오로라의 빛', '당신을 향한 고백')]),
    ('make_eve',       [('냉혹한 일격', '다크 미스트'), ('숨통 끊기', '레인 드랍'), ('사냥의 끝', '실낙원')]),
    ('make_sitri',     [('별빛 채찍', '폴 인 러브'), ('별의 축복', '크런치 캔디'), ('은하의 빛', '라 돌체 비타')]),
    ('make_mona',      [('달빛', '이클립스'), ('달의 가호', '트릭스타'), ('보름달', '사랑을 담아')]),
    ('make_ashtoreth', [('이중 타격', '밤의 속삭임'), ('반격불능', '심연의 덫'), ('신성 관통', '가시 무도회')]),
    ('make_thisbe',    [('파도', '오아시스'), ('질풍가도', '하늘의 창문'), ('광풍', '헤븐리 웰')]),
    ('make_grilla',    [('야성의 일격', '악마의 야망'), ('야성의 기운', '발푸르기스의 밤'), ('야성 해방', '드림 오브 레기온')]),
    ('make_artemis',   [('4연사', '나이트메어 이블'), ('관통 사격', '광포한 분노'), ('궁극의 화살비', '침식하는 어둠')]),
    ('make_kubaba',    [('여왕의 일격', '와일드 로드'), ('왕권 분쇄', '오버 더 리밋'), ('동행자의 힘', '데스 스키드 마크')]),
    ('make_frey',      [('어둠의 방패', '그림 리퍼'), ('치명의 자세', '사신의 잔상'), ('어둠의 지배', '트릭스터')]),

    # ── Non-Excel characters: RESTORE wrongly changed names ──
    ('make_jiva',     [('삼재', '물의 촉수'), ('천라홍수', '생명수'), ('은하수 곡성', '대자연의 손길')]),
    ('make_metis',    [('관음', '철벽 수호')]),   # was collateral from 라가라자 fix
    ('make_elysion',  [('천라홍수', '생명수')]),   # was collateral from 바리 fix
]

total_changes = 0

for func_name, replacements in TARGETED_FIXES:
    # Find the function boundary: from "def func_name():" to next "def " or end
    func_pattern = rf'(def {func_name}\(\).*?)(?=\ndef |\Z)'
    match = re.search(func_pattern, content, re.DOTALL)
    if not match:
        print(f"ERROR: function {func_name} not found!")
        continue

    func_body = match.group(1)
    new_func_body = func_body

    for old_name, new_name in replacements:
        if f'"{old_name}"' in new_func_body:
            new_func_body = new_func_body.replace(f'"{old_name}"', f'"{new_name}"')
            total_changes += 1
            print(f"  {func_name}: '{old_name}' -> '{new_name}'")
        else:
            print(f"  WARNING: '{old_name}' not found in {func_name}")

    if new_func_body != func_body:
        content = content[:match.start()] + new_func_body + content[match.end():]

with open(FILE, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"\nTotal: {total_changes} function-scoped skill name replacements")

# Verify final state
print("\n=== Final verification ===")
with open(FILE, 'r', encoding='utf-8') as f:
    verify = f.read()

pat = r'def (make_\w+)\(\).*?normal_skill=_normal\([^,]+,\s*"([^"]+)".*?active_skill=_active\([^,]+,\s*"([^"]+)".*?ultimate_skill=_ult\([^,]+,\s*"([^"]+)"'
for m in re.findall(pat, verify, re.DOTALL):
    fn, n, a, u = m
    if fn.startswith('make_teddy'):
        continue
    print(f'{fn}: N="{n}" A="{a}" U="{u}"')
