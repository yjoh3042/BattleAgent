"""Skill JSON 재생성 - Target 필드 대문자 수정"""
import sys, json
sys.path.insert(0, '.')
from fixtures.test_data import *

CHAR_URLS = {
    'c283': 'https://www.notion.so/320e3b3baf6181fcb7a0df35976de1e7',
    'c339': 'https://www.notion.so/320e3b3baf61810aac70d7af804087b7',
    'c417': 'https://www.notion.so/320e3b3baf6181a5ae7cdce1ff31dc4b',
    'c429': 'https://www.notion.so/320e3b3baf61819a8aa5f8ccf90165d9',
    'c445': 'https://www.notion.so/320e3b3baf61810a8cb7e9103d2bacb9',
    'c462': 'https://www.notion.so/320e3b3baf61816999e8dc7454cf8870',
    'c501': 'https://www.notion.so/320e3b3baf618155ba32e5fd45277778',
    'c562': 'https://www.notion.so/320e3b3baf618113ad67c6d6bd703a2b',
    'c124': 'https://www.notion.so/320e3b3baf6181cbb8edf0810e755ecd',
    'c167': 'https://www.notion.so/320e3b3baf6181dd9df7ca8de17df99a',
    'c281': 'https://www.notion.so/320e3b3baf6181ab9b99cd70b0ff5878',
    'c318': 'https://www.notion.so/320e3b3baf6181f7afd6e0185d3c8cfd',
    'c502': 'https://www.notion.so/320e3b3baf61818fa343c9fcb67b3fe3',
    'c537': 'https://www.notion.so/320e3b3baf6181c9beeaf1d8de842e7d',
    'c229': 'https://www.notion.so/320e3b3baf6181c5a7a8ffe8b7634b85',
    'c294': 'https://www.notion.so/320e3b3baf61812a9a6ac735e6a031b0',
    'c336': 'https://www.notion.so/320e3b3baf6181ffbd1fcaef9a708472',
    'c447': 'https://www.notion.so/320e3b3baf618115a292f93fa22e2298',
    'c461': 'https://www.notion.so/320e3b3baf61814892e9c68ed012b6e0',
    'c468': 'https://www.notion.so/320e3b3baf61811688acf24d17721a13',
    'c525': 'https://www.notion.so/320e3b3baf6181b08b12cc12fb844fec',
    'c549': 'https://www.notion.so/320e3b3baf61812880abc95836899f78',
    'c194': 'https://www.notion.so/320e3b3baf61814386e0ed1153c354fd',
    'c364': 'https://www.notion.so/320e3b3baf61813aaddad5b218dfcd4f',
    'c393': 'https://www.notion.so/320e3b3baf618118a50bc17f64c95107',
    'c438': 'https://www.notion.so/320e3b3baf61813080a5f12f79dbea5b',
    'c455': 'https://www.notion.so/320e3b3baf6181c9935ae9fc0ca02b8f',
    'c473': 'https://www.notion.so/320e3b3baf618165960ec9a2059f6039',
    'c533': 'https://www.notion.so/320e3b3baf618122b7abea1793688f65',
    'c600': 'https://www.notion.so/320e3b3baf61818cac4bf67245d1f441',
    'c051': 'https://www.notion.so/320e3b3baf618125b87edf2d5946c984',
    'c400': 'https://www.notion.so/320e3b3baf6181b497c4f6eab211f667',
    'c432': 'https://www.notion.so/320e3b3baf618183a0ccf2b31e78676f',
    'c448': 'https://www.notion.so/320e3b3baf618173b9c5da449bba679d',
    'c485': 'https://www.notion.so/320e3b3baf618110b695e4ec76aecd5c',
    'c486': 'https://www.notion.so/320e3b3baf6181a18f86f7eb0a563090',
    'c532': 'https://www.notion.so/320e3b3baf61816d98c6e211c80794f9',
    'c601': 'https://www.notion.so/320e3b3baf6181b08546d09cf873ce65',
}

VALID_TARGETS = {
    'SELF', 'ENEMY_NEAR', 'ENEMY_FAR', 'ENEMY_RANDOM', 'ENEMY_LOWEST_HP',
    'ENEMY_SAME_COL', 'ALL_ENEMY', 'ALLY_LOWEST_HP', 'ALLY_SELF', 'ALL_ALLY',
}

MAKERS = [
    ('c283', make_morgan), ('c339', make_dabi), ('c417', make_gumiho),
    ('c429', make_jiva), ('c445', make_kararatri), ('c462', make_deresa),
    ('c501', make_ragaraja), ('c562', make_salmakis),
    ('c124', make_eve), ('c167', make_sangah), ('c281', make_thisbe),
    ('c318', make_bari), ('c502', make_dogyehwa), ('c537', make_elysion),
    ('c229', make_brownie), ('c294', make_batory), ('c336', make_pan),
    ('c447', make_miriam), ('c461', make_aurora), ('c468', make_metis),
    ('c525', make_grilla), ('c549', make_danu),
    ('c194', make_ashtoreth), ('c364', make_sitri), ('c393', make_mona),
    ('c438', make_semele), ('c455', make_tiwaz), ('c473', make_titania),
    ('c533', make_oneiroi), ('c600', make_c600),
    ('c051', make_frey), ('c400', make_banshee), ('c432', make_artemis),
    ('c448', make_mircalla), ('c485', make_yuna), ('c486', make_kubaba),
    ('c532', make_anubis), ('c601', make_c601),
]

all_skills = []

for cid, maker_fn in MAKERS:
    c = maker_fn()
    char_url = CHAR_URLS[cid]
    char_name = c.name

    for skill_type, skill in [('Normal', c.normal_skill), ('Active', c.active_skill), ('Ultimate', c.ultimate_skill)]:
        # Build effects string
        effects_parts = []
        for eff in skill.effects:
            part = ''
            if eff.multiplier and eff.multiplier > 0:
                part = f'DMG {eff.multiplier}x'
                if eff.hit_count and eff.hit_count > 1:
                    part += f' x{eff.hit_count}'
            elif eff.heal_ratio and eff.heal_ratio > 0:
                part = f'Heal {int(eff.heal_ratio * 100)}%'
            elif eff.buff_data:
                b = eff.buff_data
                if b.dot_type:
                    part = f'{b.dot_type.value}({b.value},{b.duration}T)'
                elif b.cc_type:
                    part = f'{b.cc_type.value}({b.duration}T)'
                else:
                    part = 'stat_change'
            if eff.condition:
                part += f' {eff.condition}'

            # Target label for display
            tgt_upper = eff.target_type.value.upper() if eff.target_type else 'SELF'
            if tgt_upper in VALID_TARGETS and tgt_upper != 'SELF':
                part += f' [{eff.target_type.value}]'

            if part:
                effects_parts.append(part)

        effects_str = ' | '.join(effects_parts) if effects_parts else 'stat_change'

        # Primary target (UPPERCASE for Notion SELECT)
        primary_target = skill.effects[0].target_type.value.upper() if skill.effects else 'SELF'
        if primary_target not in VALID_TARGETS:
            primary_target = 'SELF'

        entry = {
            'properties': {
                'Skill Name': f'{char_name} - {skill.name}',
                'Character': char_url,
                'Type': skill_type,
                'Target': primary_target,
                'Effects': effects_str,
            }
        }
        if skill.effects and skill.effects[0].multiplier and skill.effects[0].multiplier > 0:
            entry['properties']['Multiplier'] = skill.effects[0].multiplier
        if skill.effects and skill.effects[0].hit_count and skill.effects[0].hit_count > 1:
            entry['properties']['Hit Count'] = skill.effects[0].hit_count
        if skill_type == 'Ultimate':
            entry['properties']['SP Cost'] = skill.sp_cost
        if skill_type == 'Active':
            entry['properties']['Cooldown'] = skill.cooldown_turns

        all_skills.append(entry)

# Split into batches
batch1 = all_skills[:100]
batch2 = all_skills[100:]

with open('skill_batch1.json', 'w', encoding='utf-8') as f:
    json.dump(batch1, f, ensure_ascii=False, indent=2)
with open('skill_batch2.json', 'w', encoding='utf-8') as f:
    json.dump(batch2, f, ensure_ascii=False, indent=2)

print(f'Total skills: {len(all_skills)}')
print(f'Batch 1: {len(batch1)} skills')
print(f'Batch 2: {len(batch2)} skills')

# Verify targets
targets = set()
for s in all_skills:
    targets.add(s['properties']['Target'])
print(f'Unique targets: {sorted(targets)}')

# Show first 5 entries
for s in all_skills[:5]:
    print(f"  {s['properties']['Skill Name']} -> Target: {s['properties']['Target']}")
