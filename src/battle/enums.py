"""열거형 정의 모듈 - 전투 시스템의 모든 Enum 타입"""
from enum import Enum, auto


class Element(Enum):
    """속성 (원소)"""
    FIRE = "fire"
    WATER = "water"
    FOREST = "forest"
    LIGHT = "light"
    DARK = "dark"
    NONE = "none"


class Role(Enum):
    """캐릭터 역할"""
    ATTACKER = "attacker"
    DEFENDER = "defender"
    MAGICIAN = "magician"
    SUPPORTER = "supporter"
    HEALER = "healer"


class SkillType(Enum):
    """스킬 종류"""
    NORMAL = "normal"      # 기본 공격, 쿨타임 없음
    ACTIVE = "active"      # 액티브 스킬, 사용 후 2턴 쿨타임
    ULTIMATE = "ultimate"  # 얼티밋, SP 소모 + 엑스트라 턴
    PASSIVE = "passive"    # 패시브, 트리거/전투시작 시 자동 발동


class LogicType(Enum):
    """스킬/버프 로직 타입"""
    DAMAGE = "damage"                          # 데미지
    HEAL = "heal"                              # 힐 (최대 HP 비율 또는 고정값)
    HEAL_HP_RATIO = "heal_hp_ratio"            # 최대 HP % 힐
    STAT_CHANGE = "stat_change"                # 스탯 버프/디버프
    DOT = "dot"                                # 지속 피해 (화상 등)
    DOT_HEAL_HP_RATIO = "dot_heal_hp_ratio"    # 지속 회복 (최대 HP %)
    BARRIER = "barrier"                        # 보호막
    TAUNT = "taunt"                            # 도발
    REVIVE = "revive"                          # 부활
    SP_INCREASE = "sp_increase"                # SP 증가
    CC = "cc"                                  # 상태이상 부여
    REMOVE_BUFF = "remove_buff"                # 버프 제거
    REMOVE_DEBUFF = "remove_debuff"            # 디버프 제거
    COUNTER = "counter"                        # 반격 준비 상태
    ABSORB = "absorb"                          # 피해 흡수
    # ── 추가 로직 타입 ──────────────────────────────────────────────
    DAMAGE_PENETRATION = "damage_penetration"  # DEF 무시 대미지
    DAMAGE_HP_RATIO = "damage_hp_ratio"        # 대상 HP% 대미지
    DAMAGE_CRI = "damage_cri"                  # 무조건 크리 대미지
    DAMAGE_BUFF_SCALE = "damage_buff_scale"    # 시전자 버프 수 비례 대미지
    DAMAGE_BUFF_SCALE_TARGET = "damage_buff_scale_target"    # 타겟 버프 수 비례 대미지
    DAMAGE_DEBUFF_SCALE_TARGET = "damage_debuff_scale_target"  # 타겟 디버프 수 비례 대미지
    HEAL_LOSS_SCALE = "heal_loss_scale"        # 잃은 HP 비례 회복
    BARRIER_RATIO = "barrier_ratio"            # 대상 HP% 보호막
    INVINCIBILITY = "invincibility"            # 무적
    UNDYING = "undying"                        # 불사 (HP 1 미만 불가)
    DEBUFF_IMMUNE = "debuff_immune"            # 디버프 면역
    SP_STEAL = "sp_steal"                      # SP 강탈
    SP_LOCK = "sp_lock"                        # SP 충전 잠금
    BUFF_TURN_INCREASE = "buff_turn_increase"  # 버프 턴 증가
    DEBUFF_TURN_INCREASE = "debuff_turn_increase"  # 디버프 턴 증가
    CRI_UNAVAILABLE = "cri_unavailable"        # 크리 불가
    COUNTER_UNAVAILABLE = "counter_unavailable"  # 반격 불가
    USE_SKILL = "use_skill"                    # 스킬 발동
    IGNORE_ELEMENT = "ignore_element"          # 속성 상성 무시
    ACTIVE_CD_CHANGE = "active_cd_change"      # 액티브 쿨타임 변경
    # ── 스킬 디자인 v2 추가 로직 ──────────────────────────────────────
    DAMAGE_BURN_BONUS = "damage_burn_bonus"    # 화상 대상 2배 피해 + 강제 크리
    DAMAGE_ESCALATE = "damage_escalate"        # 사용 횟수 비례 피해 증가 (전투 초기화)
    DAMAGE_REPEAT_TARGET = "damage_repeat_target"  # 같은 적 반복공격 시 피해 증가
    DAMAGE_MISSING_HP_SCALE = "damage_missing_hp_scale"  # 시전자 잃은 HP 비례 피해 증가
    HEAL_PER_HIT = "heal_per_hit"              # 적중 수만큼 아군 회복
    HEAL_CURRENT_HP_SCALE = "heal_current_hp_scale"  # 현재 HP 높을수록 회복량 증가
    STAT_STEAL = "stat_steal"                  # 적 스탯 빼앗아 자신에게 부여
    DEBUFF_SPREAD = "debuff_spread"            # 디버프 주변(십자) 전이
    SELF_DAMAGE = "self_damage"                # 자신 HP 소모
    EXTRA_TURN = "extra_turn"                  # 추가 행동 획득
    TRICK_ROOM = "trick_room"                  # 속도 반전 필드
    LINK_BUFF = "link_buff"                    # 연결 아군 버프 공유

    # ══════════════════════════════════════════════════════════════
    # 3대 RPG 메타 로직 확장 (서머너즈워 / 스타레일 / 에픽세븐)
    # ══════════════════════════════════════════════════════════════

    # ── 데미지 변형 ──────────────────────────────────────────────
    DAMAGE_SPD_SCALE = "damage_spd_scale"                    # SPD 비례 데미지
    DAMAGE_DEF_SCALE = "damage_def_scale"                    # DEF 비례 데미지
    DAMAGE_DUAL_SCALE = "damage_dual_scale"                  # ATK+SPD 이중 스케일링
    DAMAGE_CURRENT_HP_SCALE = "damage_current_hp_scale"      # 시전자 현재HP 높을수록 데미지 증가
    DAMAGE_TARGET_LOST_HP_SCALE = "damage_target_lost_hp_scale"  # 적이 잃은 HP 비례 추가 피해
    DAMAGE_ENEMY_COUNT_SCALE = "damage_enemy_count_scale"    # 적 수 비례 데미지
    DAMAGE_ALLY_COUNT_SCALE = "damage_ally_count_scale"      # 아군 수 비례 데미지
    DAMAGE_KILL_COUNT_SCALE = "damage_kill_count_scale"      # 킬 카운트 비례 영구 강화
    DAMAGE_SURVIVAL_TURN_SCALE = "damage_survival_turn_scale"  # 생존 턴 비례 강화
    DAMAGE_ACCUMULATE_COUNTER = "damage_accumulate_counter"  # 받은 피해 축적 → 카운터 폭발
    DAMAGE_CHAIN = "damage_chain"                            # 체인 라이트닝 (연쇄 감소)
    DAMAGE_SPLASH = "damage_splash"                          # 스플래시 데미지 (주변 피해)
    DAMAGE_AOE_SPLIT = "damage_aoe_split"                    # 총합 고정 광역 분할
    DAMAGE_REFLECT = "damage_reflect"                        # 피해 반사 (즉시)
    DAMAGE_WEAKPOINT = "damage_weakpoint"                    # 약점 탐지 (최저 스탯 기준)
    DAMAGE_EXECUTE = "damage_execute"                        # 멸살 (HP% 이하 즉사)
    DAMAGE_BARRIER_PIERCE = "damage_barrier_pierce"          # 보호막 관통 HP 직타
    DAMAGE_KILL_SPLASH = "damage_kill_splash"                # 처치 시 잔여 피해 전파
    DAMAGE_FIXED = "damage_fixed"                            # 고정 피해 (스탯 무관)
    DAMAGE_COUNTER_SCALE = "damage_counter_scale"            # 반격 시 크리 데미지 증가 (문스트라이크)
    DAMAGE_REFLECT_ATK_SCALE = "damage_reflect_atk_scale"    # 적 ATK 비례 반사 데미지

    # ── 힐 변형 ─────────────────────────────────────────────────
    HEAL_OVERHEAL_BARRIER = "heal_overheal_barrier"          # 초과 회복 → 보호막 전환
    HEAL_DEF_SCALE = "heal_def_scale"                        # DEF 비례 회복
    HEAL_BLOCK = "heal_block"                                # 회복 불가
    HEAL_REDUCE = "heal_reduce"                              # 회복 효율 감소
    HEAL_CURSE = "heal_curse"                                # 저주: 회복 시 피해로 전환

    # ── HP 조작 ──────────────────────────────────────────────────
    HP_EQUALIZE = "hp_equalize"                              # 아군 전체 HP 균등화
    HP_SWAP = "hp_swap"                                      # 자신/대상 HP 비율 교환

    # ── ATB/CR/행동 게이지 조작 ──────────────────────────────────
    ATB_PUSH = "atb_push"                                    # 아군 ATB/CR 증가
    ATB_PULL = "atb_pull"                                    # 적 ATB/CR 감소
    ATB_STEAL = "atb_steal"                                  # ATB 흡수 (적→자신)
    ATB_RESET = "atb_reset"                                  # 적 전체 ATB 리셋
    DAMAGE_TO_ATB = "damage_to_atb"                          # 받은 피해 → ATB 전환

    # ── 버프 조작 ────────────────────────────────────────────────
    BUFF_STEAL = "buff_steal"                                # 적 버프 탈취 → 자신에게
    BUFF_INVERSION = "buff_inversion"                        # 적 버프 → 디버프 반전
    DEBUFF_TRANSFER = "debuff_transfer"                      # 자신 디버프 → 적에게 전이
    DEBUFF_DETONATE = "debuff_detonate"                      # 디버프 전체 제거 + 피해
    DEBUFF_CONTAGION = "debuff_contagion"                    # 디버프 전염 (사망 시 주변)
    BUFF_BLOCK = "buff_block"                                # 버프 적용 불가 디버프
    BUFF_IRREMOVABLE = "buff_irremovable"                    # 해제 불가 버프 마커
    COOLDOWN_RESET = "cooldown_reset"                        # 스킬 쿨타임 전체 초기화
    PASSIVE_SEAL = "passive_seal"                            # 패시브 봉인

    # ── 방어/생존 ────────────────────────────────────────────────
    DAMAGE_SHARE = "damage_share"                            # 받은 피해 아군 분산
    PROTECT_ALLY = "protect_ally"                            # 지정 아군 대리 피격
    BARRIER_SHARE = "barrier_share"                          # 보호막 아군 공유
    DEFENSE_STANCE = "defense_stance"                        # 방어 자세 (DEF 2배, 피해 50%)
    STEALTH = "stealth"                                      # 스텔스 (타겟 불가)
    CONSECUTIVE_HIT_REDUCE = "consecutive_hit_reduce"        # 같은 턴 연속 피격 감소
    DAMAGE_CAP = "damage_cap"                                # 피해 상한 설정
    REVIVE_SEAL = "revive_seal"                              # 부활 봉인
    REFLECT_BUFF = "reflect_buff"                            # 피해 반사 버프

    # ── 특수 디버프/상태 ─────────────────────────────────────────
    BOMB = "bomb"                                            # 시한 폭탄 (N턴 후 폭발)
    MARK = "mark"                                            # 표적/낙인 (집중 공격 보너스)
    DOOM = "doom"                                            # 파멸 (회복불가+회복→피해)
    VULNERABILITY = "vulnerability"                          # 피해 증폭 디버프
    WEAKEN = "weaken"                                        # 가하는 피해 감소 디버프
    BANISH = "banish"                                        # 차원 추방 (N턴 전투 제외)
    RESIST_IGNORE = "resist_ignore"                          # 효과 저항 무시

    # ── DOT 확장 ─────────────────────────────────────────────────
    DOT_INSTANT_TRIGGER = "dot_instant_trigger"              # 걸린 DOT 전부 즉시 발동
    DOT_STACK_DETONATE = "dot_stack_detonate"                # DOT 스택 폭발 (제거+일괄피해)
    DOT_BLEED = "dot_bleed"                                  # 출혈 (ATK 비례 DOT)
    DOT_SHOCK = "dot_shock"                                  # 감전 (DOT + 인접 확산)
    DOT_WIND_SHEAR = "dot_wind_shear"                        # 풍화 (중첩형 DOT, 최대 5스택)

    # ── 소환/변신/협공 ───────────────────────────────────────────
    SUMMON_CLONE = "summon_clone"                             # 분신 소환
    TRANSFORM = "transform"                                  # 변신 (스킬셋 변경)
    JOINT_ATTACK = "joint_attack"                            # 합체 공격 (아군 1명과 협공)
    FOLLOW_UP_ATTACK = "follow_up_attack"                    # 추격 공격 (아군 공격 후 자동)
    DUAL_ATTACK = "dual_attack"                              # 듀얼어택 (랜덤 아군 참여)
    TOTEM = "totem"                                          # 토템/오브젝트 설치

    # ── 리소스 게이지 ────────────────────────────────────────────
    FIGHTING_SPIRIT = "fighting_spirit"                      # 투지 게이지 축적/소모
    FOCUS_STACK = "focus_stack"                               # 집중 스택 획득
    SOUL_COLLECT = "soul_collect"                             # 영혼 수집 (킬 스택)
    SOUL_BURN = "soul_burn"                                  # 소울번 강화
    ENERGY_CHARGE = "energy_charge"                          # 에너지/궁극기 게이지 충전
    ENERGY_DRAIN = "energy_drain"                            # 적 에너지 감소

    # ── 트리거/패시브 로직 ───────────────────────────────────────
    KILL_EXTRA_TURN = "kill_extra_turn"                       # 처치 시 추가 턴
    CRIT_CHAIN = "crit_chain"                                # 크리 시 추가 타격
    COUNTERATTACK_PASSIVE = "counterattack_passive"          # 피격 시 확률 반격 (패시브)
    ALLY_DEATH_RAGE = "ally_death_rage"                      # 아군 사망 시 영구 버프
    FIRST_STRIKE_BONUS = "first_strike_bonus"                # 첫 타격 2배
    FULL_HP_BONUS = "full_hp_bonus"                          # HP 100% 시 추가 효과
    LAST_STAND = "last_stand"                                # 단독 생존 시 전 스탯 강화
    STACK_PASSIVE = "stack_passive"                           # 행동 시 스택 축적 패시브

    # ── 필드/환경/리더 ───────────────────────────────────────────
    ELEMENT_CHANGE = "element_change"                        # 속성 변환
    LEADER_SKILL = "leader_skill"                            # 리더 스킬 (팀 패시브)
    EFFECT_RES_DOWN = "effect_res_down"                      # 효과 저항 감소
    TOUGHNESS_BREAK = "toughness_break"                      # 터프니스/약점 격파

    # ── 보스/PvE 전용 ────────────────────────────────────────────
    BOSS_ENRAGE = "boss_enrage"                              # 보스 광폭화
    BOSS_PHASE_ATTACK = "boss_phase_attack"                  # 보스 페이즈 전환 공격
    COUNTDOWN_WIPE = "countdown_wipe"                        # 카운트다운 즉사기
    SHIELD_PHASE = "shield_phase"                            # 쉴드 페이즈 (약점만 격파)
    PART_BREAK = "part_break"                                # 보스 부위 파괴

    # ── 스킬컨셉 NEW v2 추가 ──────────────────────────────────────
    KNOCKBACK = "knockback"                                  # 넉백 (전열→후열 강제 이동)
    DAMAGE_POISON_SCALE = "damage_poison_scale"              # 중독 스택 비례 대미지
    DAMAGE_STONE_BONUS = "damage_stone_bonus"                # 석화 대상 2배 대미지
    DAMAGE_POSITION_SCALE = "damage_position_scale"          # 위치(행) 기반 대미지 증가
    INSTANT_KILL = "instant_kill"                            # 즉사 (HP% 이하 시)
    EXECUTE = "execute"                                      # 처형 (최저HP 대상 배율 증가)


class CCType(Enum):
    """상태이상 타입"""
    # Hard CC (행동 불가)
    STUN = "stun"
    SLEEP = "sleep"
    FREEZE = "freeze"
    STONE = "stone"
    ABNORMAL_SKILL = "abnormal_skill"
    # Soft CC (확률적)
    ELECTRIC_SHOCK = "electric_shock"   # 30% 확률로 행동 불가
    PANIC = "panic"                     # 30% 확률로 행동 불가
    # 디버프성
    POISON = "poison"
    BURN = "burn"
    BLIND = "blind"
    SILENCE = "silence"
    CONFUSED = "confused"              # 혼란 (노멀 타겟 랜덤, 액티브 사용 불가)
    # ── 3대 RPG 확장 CC ──────────────────────────────────────────
    PROVOKE = "provoke"                # 도발 (기본공격만 + 도발자만 공격)
    BLEED = "bleed"                    # 출혈
    ENTANGLE = "entangle"              # 얽힘 (행동 지연 + 추가 행동 시 피해)
    IMPRISON = "imprison"              # 구속 (행동 지연 + 방깎)
    BOMB_TICK = "bomb_tick"            # 시한 폭탄 (N턴 후 폭발)
    BANISHED = "banished"              # 추방 (전투 제외)
    MARKED = "marked"                  # 표적/낙인
    CURSED = "cursed"                  # 저주 (회복→피해)
    DOOMED = "doomed"                  # 파멸 (회복불가+회복→피해)
    SEALED = "sealed"                  # 패시브 봉인
    BUFF_BLOCKED = "buff_blocked"      # 버프 적용 불가


class TargetType(Enum):
    """타겟 선택 방식"""
    SELF = "self"
    ALLY_LOWEST_HP = "ally_lowest_hp"
    ALLY_HIGHEST_ATK = "ally_highest_atk"
    ALL_ALLY = "all_ally"
    ENEMY_LOWEST_HP = "enemy_lowest_hp"
    ENEMY_HIGHEST_HP = "enemy_highest_hp"
    ENEMY_HIGHEST_SPD = "enemy_highest_spd"
    ENEMY_RANDOM = "enemy_random"
    ALL_ENEMY = "all_enemy"
    ENEMY_RANDOM_2 = "enemy_random_2"   # 랜덤 최대 2명
    ENEMY_RANDOM_3 = "enemy_random_3"   # 랜덤 최대 3명
    ALLY_DEAD_RANDOM = "ally_dead_random"  # 사망한 아군 1명 (부활용)
    ALLY_LOWEST_HP_2 = "ally_lowest_hp_2"  # 체력 낮은 아군 2명
    ALLY_ROLE_ATTACKER = "ally_role_attacker"  # 공격형 아군 전체
    ALLY_ROLE_DEFENDER = "ally_role_defender"  # 방어형 아군 전체

    # ── 타일 포지셔닝 기반 (3×3 그리드) ────────────────────────────
    # Near 계열: 타일 거리 기반 (거리 = caster.row + target.row + |caster.col - target.col|)
    ENEMY_NEAR       = "enemy_near"       # 가장 가까운 적 1명 (2000011: 가까운 적 1명)
    ENEMY_NEAR_ROW   = "enemy_near_row"   # 가장 가까운 적 + 동일 행 전체 (2000014: 가까운 적 1명 2행)
    ENEMY_NEAR_CROSS = "enemy_near_cross" # 가장 가까운 적 + 십자(±1행 & ±1열) (2000016: 가까운 적 1명 십자)
    ENEMY_LAST_COL   = "enemy_last_col"   # 적 최우열(col 최댓값) 전체 (920013: 논타겟 적 3열)
    ENEMY_FRONT_ROW  = "enemy_front_row"  # 적 최전열 전체 (생존자 중 row 최솟값)
    ENEMY_BACK_ROW   = "enemy_back_row"   # 적 최후열 전체 (생존자 중 row 최댓값)
    ENEMY_SAME_COL   = "enemy_same_col"   # 시전자와 동일 열(col)의 적 — 관통 공격
    ENEMY_ADJACENT   = "enemy_adjacent"   # 시전자 기준 ±1행·±1열 인접 타일의 적
    ALLY_SAME_ROW    = "ally_same_row"    # 시전자와 동일 행(row)의 아군
    ALLY_BEHIND      = "ally_behind"      # 자신 바로 뒤 1칸 (6: 자신 뒤 1칸)
    # ── 스킬 디자인 v2 추가 타겟 ──────────────────────────────────────
    ALLY_LOWEST_HP_3   = "ally_lowest_hp_3"    # 체력 낮은 아군 3명
    ALLY_SAME_ELEMENT  = "ally_same_element"   # 같은 속성 아군 전체
    ALLY_ADJACENT      = "ally_adjacent"       # 자신 양옆 아군 (같은 행 ±1열)
    ALLY_FRONT         = "ally_front"          # 자신 바로 앞 1칸 (row-1, 같은 col)
    ENEMY_ELEMENT_WEAK = "enemy_element_weak"  # 상성 약점 적 우선 타겟
    # ── 3대 RPG 확장 타겟 ────────────────────────────────────────
    ALL_UNITS = "all_units"                    # 적+아군 전체 (필드 효과)
    ALLY_DEAD_ALL = "ally_dead_all"            # 사망한 아군 전체 (전멸 방지)
    ENEMY_MARKED = "enemy_marked"              # 낙인/표적 적 우선
    ENEMY_MOST_DEBUFFS = "enemy_most_debuffs"  # 디버프 가장 많은 적
    ENEMY_MOST_BUFFS = "enemy_most_buffs"      # 버프 가장 많은 적
    ALLY_MOST_BUFFS = "ally_most_buffs"        # 버프 가장 많은 아군
    ENEMY_LOWEST_DEF = "enemy_lowest_def"      # DEF 가장 낮은 적

    # ── 스킬컨셉 NEW v2 추가 ──────────────────────────────────────
    ENEMY_BACK_ROW_PRIORITY = "enemy_back_row_priority"  # 후열 우선 (후열 없으면 전열)


class TriggerEvent(Enum):
    """트리거 발동 이벤트"""
    ON_BATTLE_START = "on_battle_start"
    ON_ROUND_START = "on_round_start"
    ON_TURN_START = "on_turn_start"
    ON_TURN_END = "on_turn_end"
    ON_HIT = "on_hit"           # 피격 시
    ON_ATTACK = "on_attack"     # 공격 시
    ON_KILL = "on_kill"
    ON_DEATH = "on_death"
    ON_HP_THRESHOLD = "on_hp_threshold"   # HP가 특정 % 이하
    ON_BURN_APPLIED = "on_burn_applied"   # 화상 부여 시
    ON_STATUS_APPLIED = "on_status_applied"
    # ── 스킬 디자인 v2 추가 트리거 ──────────────────────────────────
    ON_CRITICAL_HIT = "on_critical_hit"      # 치명타 적중 시
    ON_ULTIMATE_USED = "on_ultimate_used"    # 얼티밋 스킬 사용 후
    ON_BUFF_GAINED = "on_buff_gained"        # 버프 획득 시
    # ── 3대 RPG 확장 트리거 ──────────────────────────────────────
    ON_ALLY_DEATH = "on_ally_death"          # 아군 사망 시
    ON_ENEMY_DEATH = "on_enemy_death"        # 적 사망 시 (debuff 전염 등)
    ON_ALLY_ATTACK = "on_ally_attack"        # 아군 공격 시 (추격/듀얼어택)
    ON_DEBUFF_APPLIED = "on_debuff_applied"  # 디버프 부여 시
    ON_BARRIER_BREAK = "on_barrier_break"    # 보호막 파괴 시
    ON_REVIVE = "on_revive"                  # 부활 시
    ON_HEAL = "on_heal"                      # 회복 시
    ON_COUNTER = "on_counter"                # 반격 발동 시
    ON_DODGE = "on_dodge"                    # 회피 성공 시
    ON_BOMB_EXPLODE = "on_bomb_explode"      # 폭탄 폭발 시
    ON_TOUGHNESS_BREAK = "on_toughness_break"  # 터프니스 격파 시
    ON_ENERGY_FULL = "on_energy_full"        # 에너지 만충 시

    # ── 스킬컨셉 NEW v2 추가 ──────────────────────────────────────
    ON_KNOCKBACK = "on_knockback"            # 넉백 성공 시
    ON_STONE_APPLIED = "on_stone_applied"    # 석화 부여 시
    ON_POISON_APPLIED = "on_poison_applied"  # 중독 부여 시
    ON_DEBUFF_REMOVED = "on_debuff_removed"  # 디버프 제거 시
    ON_ALLY_DODGE = "on_ally_dodge"          # 아군 회피 시 (ON_DODGE는 자신, 이건 아군)


class Side(Enum):
    """진영"""
    ALLY = "ally"
    ENEMY = "enemy"


class DeckType(Enum):
    """덱 타입 — 타임오버 승패 기준 결정"""
    OFFENSE = "offense"    # 공격덱: 타임오버 시 패배 (적 전멸 실패)
    DEFENSE = "defense"    # 방어덱: 타임오버 시 승리 (생존 성공)


class BattleResult(Enum):
    """전투 결과"""
    ALLY_WIN = "ally_win"
    ENEMY_WIN = "enemy_win"
    TIME_OVER = "time_over"
    IN_PROGRESS = "in_progress"


class StatType(Enum):
    """버프/디버프 대상 스탯"""
    ATK = "atk"
    DEF = "def_"
    HP = "hp"
    SPD = "spd"
    CRI_RATIO = "cri_ratio"
    CRI_DMG_RATIO = "cri_dmg_ratio"
    CRI_RESIST = "cri_resist"
    BURN_STACK_BONUS = "burn_stack_bonus"   # 화상 스택당 추가 대미지
    # ── 3대 RPG 확장 스탯 ────────────────────────────────────────
    EFFECT_RES = "effect_res"                # 효과 저항
    EFFECT_HIT = "effect_hit"                # 효과 적중
    HEAL_BONUS = "heal_bonus"                # 치유 보너스
    DMG_BONUS = "dmg_bonus"                  # 피해 보너스 (%)
    DMG_REDUCE = "dmg_reduce"                # 피해 감소 (%)
    LIFESTEAL = "lifesteal"                  # 흡혈 비율
    TOUGHNESS = "toughness"                  # 터프니스 (격파 게이지)
    ENERGY = "energy"                        # 에너지 (궁극기 게이지)
    FIGHTING_SPIRIT_GAUGE = "fighting_spirit_gauge"  # 투지 게이지
    FOCUS_GAUGE = "focus_gauge"              # 집중 게이지
    SOUL_GAUGE = "soul_gauge"                # 소울 게이지
