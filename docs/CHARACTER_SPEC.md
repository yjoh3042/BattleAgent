# 캐릭터 스탯 & 스킬 상세 명세서

> 총 70캐릭터 | ATK/DEF ×2 + 스킬배율 ×2 적용 (v7.0)
> 자동 생성: test_data.py 기준

---

## 🔥 화속성

### 네이드 (c083) — 화/딜러 1★

| 스탯 | ATK | DEF | HP | SPD | CRI | PEN | SP비용 |
|:----:|:---:|:---:|:--:|:---:|:---:|:---:|:-----:|
| 값 | 480 | 240 | 2400 | 80 | 15% | 0% | 6 |

**NORMAL** 「파이어 스트라이크」
- 데미지 3.60x → ENEMY_NEAR

**ACTIVE (CD:3)** 「플레임 버스트」
- 데미지 2.20x → ALL_ENEMY
- burn maxHP×15% (2T, max3스택) → ALL_ENEMY

**ULTIMATE (SP:6)** 「인페르노」
- 데미지 6.40x → ENEMY_NEAR

---
### 카인 (c412) — 화/딜러 2★

| 스탯 | ATK | DEF | HP | SPD | CRI | PEN | SP비용 |
|:----:|:---:|:---:|:--:|:---:|:---:|:---:|:-----:|
| 값 | 640 | 320 | 3200 | 80 | 15% | 0% | 6 |

**NORMAL** 「암흑 참격」
- 데미지 4.00x → ENEMY_NEAR

**ACTIVE (CD:3)** 「광기의 힘」
- atk+30% (2T) → SELF
- cri_ratio+0 (2T) → SELF

**ULTIMATE (SP:6)** 「어둠의 폭풍」
- 데미지 2.60x → ALL_ENEMY

---
### 카라라트리 (c445) — 화/딜러 3★

| 스탯 | ATK | DEF | HP | SPD | CRI | PEN | SP비용 |
|:----:|:---:|:---:|:--:|:---:|:---:|:---:|:-----:|
| 값 | 800 | 400 | 4000 | 80 | 15% | 0% | 6 |

**NORMAL** 「무기법」
- 데미지 3.00x [화상스택당 +0.30x] → ENEMY_NEAR

**ACTIVE (CD:3)** 「무루의 고통」
- 데미지 3.60x → ENEMY_NEAR_ROW
- burn maxHP×15% (2T, max3스택) → ENEMY_NEAR_ROW

**ULTIMATE (SP:6)** 「출세간의 선법」
- 데미지 2.60x → ALL_ENEMY
- def_-20% (2T) → ALL_ENEMY

---
### 라가라자 (c501) — 화/딜러 3.5★

| 스탯 | ATK | DEF | HP | SPD | CRI | PEN | SP비용 |
|:----:|:---:|:---:|:--:|:---:|:---:|:---:|:-----:|
| 값 | 920 | 460 | 4600 | 80 | 15% | 0% | 6 |

**NORMAL** 「지장」
- 데미지 4.00x → ENEMY_NEAR
- def_+15% (2T) → SELF

**ACTIVE (CD:3)** 「관음」
- 데미지 3.00x → ENEMY_NEAR
- def_+25% (2T) → ALL_ALLY

**ULTIMATE (SP:6)** 「맹화」
- 데미지 4.40x → ALL_ENEMY

---
### 다비 (c003) — 화/마법사 2★

| 스탯 | ATK | DEF | HP | SPD | CRI | PEN | SP비용 |
|:----:|:---:|:---:|:--:|:---:|:---:|:---:|:-----:|
| 값 | 480 | 320 | 4000 | 100 | 15% | 0% | 4 |

**NORMAL** 「다비의 불꽃」
- 데미지 2.40x → ENEMY_NEAR

**ACTIVE (CD:3)** 「화상 촉진」
- atk+15% (2T) → ALL_ALLY
- burn maxHP×15% (2T, max3스택) → ENEMY_NEAR

**ULTIMATE (SP:4)** 「업화」
- 데미지 2.80x → ENEMY_NEAR_CROSS
- burn maxHP×20% (3T, max3스택) → ENEMY_NEAR_CROSS

---
### 모건 (c283) — 화/마법사 3★

| 스탯 | ATK | DEF | HP | SPD | CRI | PEN | SP비용 |
|:----:|:---:|:---:|:--:|:---:|:---:|:---:|:-----:|
| 값 | 600 | 400 | 5000 | 100 | 15% | 0% | 4 |

**NORMAL** 「철화의 검」
- 데미지 1.80x ×2hit (총 3.60x) → ENEMY_NEAR

**ACTIVE (CD:3)** 「홍염의 비도」
- atk+15% (3T) → SELF

**ULTIMATE (SP:4)** 「화도난무」
- 데미지 3.20x → ALL_ENEMY
- bleed maxHP×15% (2T, max3스택) → ALL_ENEMY

---
### 다비 (c339) — 화/마법사 3★

| 스탯 | ATK | DEF | HP | SPD | CRI | PEN | SP비용 |
|:----:|:---:|:---:|:--:|:---:|:---:|:---:|:-----:|
| 값 | 600 | 400 | 5000 | 100 | 15% | 0% | 4 |

**NORMAL** 「파이어리 서펀트」
- 데미지 4.00x → ENEMY_NEAR

**ACTIVE (CD:3)** 「화차」
- 데미지 3.40x → ENEMY_RANDOM
- burn maxHP×15% (2T, max3스택) → ENEMY_RANDOM

**ULTIMATE (SP:4)** 「나비효과」
- 데미지 2.80x → ALL_ENEMY
- burn maxHP×15% (2T, max3스택) → ALL_ENEMY

---
### 구미호 (c417) — 화/마법사 3★

| 스탯 | ATK | DEF | HP | SPD | CRI | PEN | SP비용 |
|:----:|:---:|:---:|:--:|:---:|:---:|:---:|:-----:|
| 값 | 600 | 400 | 5000 | 100 | 15% | 0% | 4 |

**NORMAL** 「꼬리의 매질」
- 데미지 3.00x → ENEMY_NEAR

**ACTIVE (CD:3)** 「원혼의 아홉 꼬리」
- 데미지 4.00x → ENEMY_RANDOM
- CC:panic (1T) → ENEMY_RANDOM
- def_-15% (2T) → ENEMY_RANDOM

**ULTIMATE (SP:4)** 「붉은 원망의 폭풍」
- 데미지 5.00x → ALL_ENEMY
- CC:panic (1T) → ALL_ENEMY

---
### 유다 (c037) — 화/탱커 1★

| 스탯 | ATK | DEF | HP | SPD | CRI | PEN | SP비용 |
|:----:|:---:|:---:|:--:|:---:|:---:|:---:|:-----:|
| 값 | 300 | 360 | 3600 | 110 | 15% | 0% | 3 |

**NORMAL** 「마탄」
- 데미지 2.40x → ENEMY_NEAR

**ACTIVE (CD:3)** 「악마의 방패」
- 도발 (2T) → ALL_ENEMY
- 배리어 maxHP×15% → SELF

**ULTIMATE (SP:3)** 「심판」
- 데미지 1.80x → ALL_ENEMY
- atk-15% (2T) → ALL_ENEMY

---
### 데레사 (c462) — 화/탱커 3★

| 스탯 | ATK | DEF | HP | SPD | CRI | PEN | SP비용 |
|:----:|:---:|:---:|:--:|:---:|:---:|:---:|:-----:|
| 값 | 500 | 600 | 6000 | 110 | 15% | 0% | 3 |

**NORMAL** 「스틸 웨일링」
- 데미지 3.00x → ENEMY_NEAR

**ACTIVE (CD:3)** 「데털민트 소드」
- 데미지 3.60x → ENEMY_NEAR
- def_+30% (2T) → SELF
- 반격 준비 (2T) → SELF

**ULTIMATE (SP:3)** 「새크리파이스」
- 데미지 5.00x → ENEMY_NEAR_ROW
- 도발 (2T) → ALL_ENEMY

---
### 베르들레 (c286) — 화/힐러 1★

| 스탯 | ATK | DEF | HP | SPD | CRI | PEN | SP비용 |
|:----:|:---:|:---:|:--:|:---:|:---:|:---:|:-----:|
| 값 | 240 | 240 | 2400 | 90 | 15% | 0% | 3 |

**NORMAL** 「생명의 불길」
- 데미지 2.00x → ENEMY_NEAR

**ACTIVE (CD:3)** 「화염 치유」
- 힐 maxHP×45% → ALL_ALLY

**ULTIMATE (SP:3)** 「불사조의 축복」
- 힐 maxHP×55% → ALL_ALLY
- 디버프 제거 → ALL_ALLY

---
### 지바 (c429) — 화/힐러 3★

| 스탯 | ATK | DEF | HP | SPD | CRI | PEN | SP비용 |
|:----:|:---:|:---:|:--:|:---:|:---:|:---:|:-----:|
| 값 | 400 | 400 | 4000 | 90 | 15% | 0% | 3 |

**NORMAL** 「물의 촉수」
- 데미지 2.00x → ENEMY_NEAR

**ACTIVE (CD:3)** 「생명수」
- 힐 maxHP×30% → ALLY_LOWEST_HP
- atk+15% (2T) → ALLY_LOWEST_HP

**ULTIMATE (SP:3)** 「대자연의 손길」
- 힐 maxHP×30% → ALL_ALLY
- atk+20% (2T) → ALL_ALLY
- SP+1 → ALL_ALLY

---
### 드미테르 (c354) — 화/서포터 2★

| 스탯 | ATK | DEF | HP | SPD | CRI | PEN | SP비용 |
|:----:|:---:|:---:|:--:|:---:|:---:|:---:|:-----:|
| 값 | 400 | 320 | 4000 | 120 | 15% | 0% | 4 |

**NORMAL** 「프릭킹 니들」
- 데미지 3.60x → ENEMY_NEAR

**ACTIVE (CD:3)** 「사이드 이펙트」
- 데미지 1.00x [화상스택당 +0.20x] → ALL_ENEMY
- burn maxHP×20% (2T, max3스택) → ALL_ENEMY
- spd-15% (2T) → ALL_ENEMY

**ULTIMATE (SP:4)** 「극약처방」
- 데미지 4.40x → ENEMY_NEAR
- def_-20% (2T) → ENEMY_NEAR

---
### 살마키스 (c562) — 화/서포터 3★

| 스탯 | ATK | DEF | HP | SPD | CRI | PEN | SP비용 |
|:----:|:---:|:---:|:--:|:---:|:---:|:---:|:-----:|
| 값 | 500 | 400 | 5000 | 120 | 15% | 0% | 4 |

**NORMAL** 「물의 손길」
- 데미지 2.00x → ENEMY_NEAR

**ACTIVE (CD:3)** 「축복」
- atk+36% (2T) → ALLY_LOWEST_HP
- spd+15 (2T) → ALLY_LOWEST_HP

**ULTIMATE (SP:4)** 「대축복」
- 데미지 1.60x → ALL_ENEMY
- def_-20% (2T) → ALL_ENEMY
- atk+20% (2T) → ALL_ALLY

---

## 💧 수속성

### 리자 (c002) — 수/딜러 2★

| 스탯 | ATK | DEF | HP | SPD | CRI | PEN | SP비용 |
|:----:|:---:|:---:|:--:|:---:|:---:|:---:|:-----:|
| 값 | 640 | 320 | 3200 | 80 | 15% | 0% | 6 |

**NORMAL** 「수정 화살」
- 데미지 1.20x → ENEMY_NEAR

**ACTIVE (CD:3)** 「얼음 창」
- 데미지 2.70x → ENEMY_NEAR

**ULTIMATE (SP:6)** 「빙하 세례」
- 데미지 0.60x → ENEMY_NEAR
- atk+15% (2T) → ALL_ALLY

---
### 이브 (c124) — 수/딜러 3★

| 스탯 | ATK | DEF | HP | SPD | CRI | PEN | SP비용 |
|:----:|:---:|:---:|:--:|:---:|:---:|:---:|:-----:|
| 값 | 800 | 400 | 4000 | 80 | 15% | 0% | 6 |

**NORMAL** 「다크 미스트」
- 데미지 3.60x → ENEMY_NEAR

**ACTIVE (CD:3)** 「레인 드랍」
- 데미지 4.00x → ENEMY_LOWEST_HP
- 데미지 3.00x [HP<25% 조건부] → ENEMY_LOWEST_HP

**ULTIMATE (SP:6)** 「실낙원」
- 데미지 5.00x → ENEMY_LOWEST_HP
- 데미지 2.00x [HP<25% 조건부] → ENEMY_LOWEST_HP

**패시브 트리거:**
- on_kill → 「다크 미스트」발동

---
### 비루파 (c193) — 수/딜러 2★

| 스탯 | ATK | DEF | HP | SPD | CRI | PEN | SP비용 |
|:----:|:---:|:---:|:--:|:---:|:---:|:---:|:-----:|
| 값 | 640 | 320 | 3200 | 80 | 15% | 0% | 6 |

**NORMAL** 「퇴마의 일격」
- 데미지 3.60x → ENEMY_NEAR

**ACTIVE (CD:3)** 「집중 강화」
- atk+25% (2T) → SELF
- 데미지 3.00x → ENEMY_NEAR

**ULTIMATE (SP:6)** 「파마의 일격」
- 데미지 7.00x → ENEMY_NEAR
- atk+20% (2T) → SELF

---
### 니르티 (c442) — 수/딜러 3★

| 스탯 | ATK | DEF | HP | SPD | CRI | PEN | SP비용 |
|:----:|:---:|:---:|:--:|:---:|:---:|:---:|:-----:|
| 값 | 800 | 400 | 4000 | 80 | 15% | 0% | 6 |

**NORMAL** 「암류의 일격」
- 데미지 5.00x → ENEMY_NEAR

**ACTIVE (CD:3)** 「심연의 창」
- 데미지 9.00x → ENEMY_NEAR
- def_+15% (2T) → SELF

**ULTIMATE (SP:6)** 「파도의 심판」
- 데미지 5.00x → ENEMY_NEAR_CROSS
- 힐 maxHP×20% → ALL_ALLY

---
### 마야우엘 (c022) — 수/마법사 1★

| 스탯 | ATK | DEF | HP | SPD | CRI | PEN | SP비용 |
|:----:|:---:|:---:|:--:|:---:|:---:|:---:|:-----:|
| 값 | 360 | 240 | 3000 | 120 | 15% | 0% | 4 |

**NORMAL** 「물의 채찍」
- 데미지 2.40x → ENEMY_NEAR

**ACTIVE (CD:3)** 「빙결의 손길」
- CC:freeze (1T) → ENEMY_NEAR
- 데미지 2.00x → ENEMY_NEAR
- def_-20% (2T) → ENEMY_NEAR

**ULTIMATE (SP:4)** 「얼어붙은 세계」
- 데미지 5.00x → ALL_ENEMY
- CC:freeze (2T) → ALL_ENEMY
- poison maxHP×15% (2T, max3스택) → ALL_ENEMY
- spd-30% (2T) → ALL_ENEMY
- def_-20% (2T) → ALL_ENEMY

---
### 바리 (c318) — 수/마법사 3★

| 스탯 | ATK | DEF | HP | SPD | CRI | PEN | SP비용 |
|:----:|:---:|:---:|:--:|:---:|:---:|:---:|:-----:|
| 값 | 600 | 400 | 5000 | 100 | 15% | 0% | 4 |

**NORMAL** 「삼재」
- 데미지 1.50x ×2hit (총 3.00x) → ENEMY_NEAR
- poison maxHP×20% (2T, max3스택) → ENEMY_NEAR

**ACTIVE (CD:3)** 「천라홍수」
- 데미지 2.40x → ENEMY_RANDOM_3
- poison maxHP×20% (2T, max3스택) → ENEMY_RANDOM_3

**ULTIMATE (SP:4)** 「은하수 곡성」
- 데미지 2.00x → ALL_ENEMY
- poison maxHP×20% (2T, max3스택) → ALL_ENEMY

---
### 도계화 (c502) — 수/마법사 3★

| 스탯 | ATK | DEF | HP | SPD | CRI | PEN | SP비용 |
|:----:|:---:|:---:|:--:|:---:|:---:|:---:|:-----:|
| 값 | 600 | 400 | 5000 | 100 | 15% | 0% | 4 |

**NORMAL** 「원거만리」
- 데미지 4.00x → ENEMY_NEAR

**ACTIVE (CD:3)** 「신행귀신 속거천리」
- 데미지 3.60x → ENEMY_NEAR
- poison maxHP×20% (2T, max3스택) → ENEMY_NEAR
- CC:stun (1T) → ENEMY_NEAR
- def_-15% (2T) → ENEMY_NEAR

**ULTIMATE (SP:4)** 「급급여율령」
- 데미지 3.00x → ENEMY_BACK_ROW
- poison maxHP×20% (3T, max3스택) → ENEMY_BACK_ROW

---
### 데이노 (c366) — 수/탱커 1★

| 스탯 | ATK | DEF | HP | SPD | CRI | PEN | SP비용 |
|:----:|:---:|:---:|:--:|:---:|:---:|:---:|:-----:|
| 값 | 300 | 360 | 3600 | 110 | 15% | 0% | 3 |

**NORMAL** 「수류 강타」
- 데미지 2.40x → ENEMY_NEAR

**ACTIVE (CD:3)** 「철벽 방어」
- 도발 (2T) → ALL_ENEMY
- 배리어 maxHP×20% → SELF

**ULTIMATE (SP:3)** 「해일의 장벽」
- 배리어 maxHP×15% → ALL_ALLY
- def_+20% (2T) → ALL_ALLY

---
### 엘리시온 (c537) — 수/탱커 3★

| 스탯 | ATK | DEF | HP | SPD | CRI | PEN | SP비용 |
|:----:|:---:|:---:|:--:|:---:|:---:|:---:|:-----:|
| 값 | 500 | 600 | 6000 | 110 | 15% | 0% | 3 |

**NORMAL** 「정화의 물」
- 데미지 2.00x → ENEMY_NEAR

**ACTIVE (CD:3)** 「생명수」
- 힐 maxHP×80% → ALLY_LOWEST_HP
- 배리어 maxHP×40% → ALLY_LOWEST_HP
- 도발 (2T) → ALL_ENEMY
- 디버프 제거 → ALLY_LOWEST_HP
- def_+40% (3T) → ALL_ALLY

**ULTIMATE (SP:3)** 「성역」
- 힐 maxHP×75% → ALL_ALLY
- def_+20% (2T) → ALL_ALLY
- SP+1 → ALL_ALLY

**패시브 트리거:**
- on_hit (1회) → 「정화의 물」발동

---
### 티스베 (c281) — 수/힐러 3★

| 스탯 | ATK | DEF | HP | SPD | CRI | PEN | SP비용 |
|:----:|:---:|:---:|:--:|:---:|:---:|:---:|:-----:|
| 값 | 400 | 400 | 4000 | 90 | 15% | 0% | 3 |

**NORMAL** 「오아시스」
- 데미지 2.00x → ENEMY_NEAR

**ACTIVE (CD:3)** 「하늘의 창문」
- spd+20 (2T) → SELF
- spd+15 (2T) → ALLY_SAME_ROW

**ULTIMATE (SP:3)** 「헤븐리 웰」
- spd+15 (3T) → ALL_ALLY
- 힐 maxHP×22% → ALL_ALLY

---
### 에우로스 (c437) — 수/힐러 2★

| 스탯 | ATK | DEF | HP | SPD | CRI | PEN | SP비용 |
|:----:|:---:|:---:|:--:|:---:|:---:|:---:|:-----:|
| 값 | 320 | 320 | 3200 | 90 | 15% | 0% | 3 |

**NORMAL** 「바람의 속삭임」
- 데미지 2.00x → ENEMY_NEAR

**ACTIVE (CD:3)** 「회복의 바람」
- 힐 maxHP×30% → ALLY_LOWEST_HP
- def_+15% (2T) → ALLY_LOWEST_HP

**ULTIMATE (SP:3)** 「대기의 은혜」
- 힐 maxHP×55% → ALL_ALLY
- 디버프 제거 → ALL_ALLY

---
### 상아 (c167) — 수/서포터 3★

| 스탯 | ATK | DEF | HP | SPD | CRI | PEN | SP비용 |
|:----:|:---:|:---:|:--:|:---:|:---:|:---:|:-----:|
| 값 | 500 | 400 | 5000 | 120 | 15% | 0% | 4 |

**NORMAL** 「수류」
- 데미지 2.00x → ENEMY_NEAR

**ACTIVE (CD:3)** 「수렁」
- 데미지 3.00x → ALL_ENEMY
- spd-20 (2T) → ALL_ENEMY
- def_-15% (2T) → ALL_ENEMY
- 버프 제거 → ALL_ENEMY

**ULTIMATE (SP:4)** 「대조수」
- spd-20 (2T) → ALL_ENEMY
- atk+30% (2T) → ALL_ALLY

---
### 레오 (c362) — 수/서포터 1★

| 스탯 | ATK | DEF | HP | SPD | CRI | PEN | SP비용 |
|:----:|:---:|:---:|:--:|:---:|:---:|:---:|:-----:|
| 값 | 300 | 240 | 3000 | 120 | 15% | 0% | 4 |

**NORMAL** 「물결 타격」
- 데미지 2.40x → ENEMY_NEAR

**ACTIVE (CD:3)** 「수류 가호」
- def_+15% (2T) → ALL_ALLY

**ULTIMATE (SP:4)** 「해류의 축복」
- atk+20% (2T) → ALL_ALLY
- 힐 maxHP×15% → ALL_ALLY

---
### 아라한 (c464) — 수/서포터 3.5★

| 스탯 | ATK | DEF | HP | SPD | CRI | PEN | SP비용 |
|:----:|:---:|:---:|:--:|:---:|:---:|:---:|:-----:|
| 값 | 574 | 460 | 5750 | 120 | 15% | 0% | 4 |

**NORMAL** 「장풍」
- 데미지 8.56x → ENEMY_NEAR

**ACTIVE (CD:3)** 「진천뢰」
- 데미지 6.60x → ENEMY_NEAR

**ULTIMATE (SP:4)** 「파천일격」
- 데미지 2.20x → ALL_ENEMY
- def_-20% (2T) → ALL_ENEMY

---

## 🌿 목속성

### 에우로페 (c062) — 목/딜러 1★

| 스탯 | ATK | DEF | HP | SPD | CRI | PEN | SP비용 |
|:----:|:---:|:---:|:--:|:---:|:---:|:---:|:-----:|
| 값 | 480 | 240 | 2400 | 80 | 15% | 0% | 6 |

**NORMAL** 「넝쿨 타격」
- 데미지 3.60x → ENEMY_NEAR

**ACTIVE (CD:3)** 「자연의 분노」
- 데미지 2.20x → ALL_ENEMY
- poison maxHP×15% (2T, max3스택) → ALL_ENEMY

**ULTIMATE (SP:6)** 「가이아의 심판」
- 데미지 6.40x → ENEMY_NEAR

---
### 미다스 (c132) — 목/딜러 2★

| 스탯 | ATK | DEF | HP | SPD | CRI | PEN | SP비용 |
|:----:|:---:|:---:|:--:|:---:|:---:|:---:|:-----:|
| 값 | 640 | 320 | 3200 | 80 | 15% | 0% | 6 |

**NORMAL** 「황금 주먹」
- 데미지 3.60x → ENEMY_NEAR

**ACTIVE (CD:3)** 「황금의 손길」
- 데미지 4.00x → ENEMY_NEAR
- def_-20% (2T) → ENEMY_NEAR

**ULTIMATE (SP:6)** 「황금폭풍」
- 데미지 3.60x → ALL_ENEMY
- def_-15% (2T) → ALL_ENEMY

---
### 미리암 (c447) — 목/딜러 3★

| 스탯 | ATK | DEF | HP | SPD | CRI | PEN | SP비용 |
|:----:|:---:|:---:|:--:|:---:|:---:|:---:|:-----:|
| 값 | 800 | 400 | 4000 | 80 | 15% | 0% | 6 |

**NORMAL** 「웨이팅 포 딜」
- 데미지 3.40x [화상스택당 +0.20x] → ENEMY_NEAR

**ACTIVE (CD:3)** 「크로스 더 루비콘」
- atk+30% (3T) → SELF

**ULTIMATE (SP:6)** 「퓨리오스」
- 데미지 7.50x → ALL_ENEMY
- CC:panic (2T) → ALL_ENEMY

---
### 다누 (c549) — 목/딜러 3★

| 스탯 | ATK | DEF | HP | SPD | CRI | PEN | SP비용 |
|:----:|:---:|:---:|:--:|:---:|:---:|:---:|:-----:|
| 값 | 800 | 400 | 4000 | 80 | 15% | 0% | 6 |

**NORMAL** 「생명의 손길」
- 데미지 8.00x → ENEMY_NEAR
- poison maxHP×15% (2T, max3스택) → ENEMY_NEAR

**ACTIVE (CD:3)** 「대지의 치유」
- 데미지 4.00x → ENEMY_NEAR
- 힐 maxHP×30% → ALL_ALLY
- 디버프 제거 → ALL_ALLY

**ULTIMATE (SP:6)** 「부활의 땅」
- 데미지 3.00x → ALL_ENEMY
- 힐 maxHP×40% → ALL_ALLY
- 부활 HP 50% → ALLY_DEAD_RANDOM

---
### 다이아나 (c033) — 목/마법사 1★

| 스탯 | ATK | DEF | HP | SPD | CRI | PEN | SP비용 |
|:----:|:---:|:---:|:--:|:---:|:---:|:---:|:-----:|
| 값 | 360 | 240 | 3000 | 120 | 15% | 0% | 4 |

**NORMAL** 「달빛 화살」
- 데미지 2.40x → ENEMY_NEAR

**ACTIVE (CD:3)** 「숲의 속박」
- CC:stun (1T) → ENEMY_NEAR
- 데미지 2.00x → ENEMY_NEAR

**ULTIMATE (SP:4)** 「달빛 심판」
- 데미지 2.00x → ALL_ENEMY
- CC:sleep (2T) → ALL_ENEMY
- spd-20% (2T) → ALL_ENEMY

---
### 판 (c336) — 목/마법사 3★

| 스탯 | ATK | DEF | HP | SPD | CRI | PEN | SP비용 |
|:----:|:---:|:---:|:--:|:---:|:---:|:---:|:-----:|
| 값 | 600 | 400 | 5000 | 100 | 15% | 0% | 4 |

**NORMAL** 「목동의 휘파람」
- 데미지 3.00x → ENEMY_NEAR

**ACTIVE (CD:3)** 「작은 양을 위한 굴레」
- 데미지 4.00x → ENEMY_RANDOM
- CC:sleep (1T) → ENEMY_RANDOM

**ULTIMATE (SP:4)** 「고요한 봄의 들판」
- 데미지 3.00x → ALL_ENEMY
- CC:sleep (1T) → ALL_ENEMY

---
### 에레보스 (c601) — 목/마법사 3.5★

| 스탯 | ATK | DEF | HP | SPD | CRI | PEN | SP비용 |
|:----:|:---:|:---:|:--:|:---:|:---:|:---:|:-----:|
| 값 | 690 | 460 | 5750 | 100 | 15% | 0% | 4 |

**NORMAL** 「심연의 쌍격」
- 데미지 4.00x ×2hit (총 8.00x) → ENEMY_NEAR

**ACTIVE (CD:3)** 「종결자의 일격」
- 데미지 5.00x → ENEMY_LOWEST_HP
- 데미지 2.40x [HP<50% 조건부] → ENEMY_LOWEST_HP
- def_-25% (2T) → ENEMY_LOWEST_HP

**ULTIMATE (SP:4)** 「심판의 심연」
- 데미지 3.40x → ALL_ENEMY
- def_-15% (2T) → ALL_ENEMY
- bleed maxHP×20% (3T, max3스택) → ALL_ENEMY

**패시브 트리거:**
- on_kill (1회) → 「심연의 쌍격」발동

---
### 맘몬 (c180) — 목/탱커 2★

| 스탯 | ATK | DEF | HP | SPD | CRI | PEN | SP비용 |
|:----:|:---:|:---:|:--:|:---:|:---:|:---:|:-----:|
| 값 | 400 | 480 | 4800 | 110 | 15% | 0% | 3 |

**NORMAL** 「대지의 주먹」
- 데미지 3.60x → ENEMY_NEAR

**ACTIVE (CD:3)** 「지진 강타」
- 데미지 2.70x → ENEMY_NEAR
- CC:stun (1T) → ENEMY_NEAR

**ULTIMATE (SP:3)** 「대지 분쇄」
- 데미지 3.20x → ALL_ENEMY

**패시브 트리거:**
- on_hit (1회) → 「대지의 주먹」발동

---
### 메티스 (c468) — 목/탱커 3★

| 스탯 | ATK | DEF | HP | SPD | CRI | PEN | SP비용 |
|:----:|:---:|:---:|:--:|:---:|:---:|:---:|:-----:|
| 값 | 500 | 600 | 6000 | 110 | 15% | 0% | 3 |

**NORMAL** 「지혜의 일격」
- 데미지 2.00x → ENEMY_NEAR

**ACTIVE (CD:3)** 「철벽 수호」
- 데미지 1.60x → ALL_ENEMY
- def_+25% (2T) → ALL_ALLY
- 버프 제거 → ALL_ENEMY

**ULTIMATE (SP:3)** 「지혜의 방패」
- def_+20% (2T) → ALL_ALLY
- atk-20% (2T) → ALL_ENEMY
- 디버프 제거 → ALL_ALLY

---
### 프레이야 (c031) — 목/힐러 1★

| 스탯 | ATK | DEF | HP | SPD | CRI | PEN | SP비용 |
|:----:|:---:|:---:|:--:|:---:|:---:|:---:|:-----:|
| 값 | 240 | 240 | 2400 | 90 | 15% | 0% | 3 |

**NORMAL** 「자연의 가시」
- 데미지 2.00x → ENEMY_NEAR

**ACTIVE (CD:3)** 「생명의 꽃」
- 힐 maxHP×30% → ALLY_LOWEST_HP
- 디버프 제거 → ALLY_LOWEST_HP

**ULTIMATE (SP:3)** 「대지의 은총」
- 힐 maxHP×35% → ALL_ALLY
- def_+15% (2T) → ALL_ALLY

---
### 브라우니 (c229) — 목/힐러 3★

| 스탯 | ATK | DEF | HP | SPD | CRI | PEN | SP비용 |
|:----:|:---:|:---:|:--:|:---:|:---:|:---:|:-----:|
| 값 | 400 | 400 | 4000 | 90 | 15% | 0% | 3 |

**NORMAL** 「고급정보입니다!」
- 데미지 2.00x → ENEMY_NEAR

**ACTIVE (CD:3)** 「특급정보입니다!」
- spd+15 (2T) → ALLY_LOWEST_HP_2

**ULTIMATE (SP:3)** 「데스페라도 친칠라」
- 디버프 제거 → ALL_ALLY
- 힐 maxHP×28% → ALL_ALLY
- SP+1 → ALL_ALLY

---
### 자청비 (c398) — 목/서포터 2★

| 스탯 | ATK | DEF | HP | SPD | CRI | PEN | SP비용 |
|:----:|:---:|:---:|:--:|:---:|:---:|:---:|:-----:|
| 값 | 400 | 320 | 4000 | 120 | 15% | 0% | 4 |

**NORMAL** 「바람의 일격」
- 데미지 2.40x → ENEMY_NEAR

**ACTIVE (CD:3)** 「숲의 가호」
- atk+15% (2T) → ALL_ALLY
- def_+10% (2T) → ALL_ALLY
- 버프 제거 → ALL_ENEMY

**ULTIMATE (SP:4)** 「대자연의 축복」
- atk+25% (2T) → ALL_ALLY
- 힐 maxHP×15% → ALL_ALLY

---
### 아우로라 (c461) — 목/서포터 3★

| 스탯 | ATK | DEF | HP | SPD | CRI | PEN | SP비용 |
|:----:|:---:|:---:|:--:|:---:|:---:|:---:|:-----:|
| 값 | 500 | 400 | 5000 | 120 | 15% | 0% | 4 |

**NORMAL** 「기다림의 끝」
- 데미지 2.00x → ENEMY_NEAR

**ACTIVE (CD:3)** 「지켜주는 나무」
- atk+25% (2T) → ALLY_HIGHEST_ATK
- cri_ratio+0 (2T) → ALLY_HIGHEST_ATK

**ULTIMATE (SP:4)** 「당신을 향한 고백」
- atk+20% (3T) → ALL_ALLY
- cri_ratio+0 (3T) → ALL_ALLY

---
### 그릴라 (c525) — 목/서포터 3★

| 스탯 | ATK | DEF | HP | SPD | CRI | PEN | SP비용 |
|:----:|:---:|:---:|:--:|:---:|:---:|:---:|:-----:|
| 값 | 500 | 400 | 5000 | 120 | 15% | 0% | 4 |

**NORMAL** 「악마의 야망」
- 데미지 4.00x → ENEMY_RANDOM

**ACTIVE (CD:3)** 「발푸르기스의 밤」
- cri_ratio+0 (2T) → ALL_ALLY
- atk+15% (2T) → ALL_ALLY

**ULTIMATE (SP:4)** 「드림 오브 레기온」
- atk+20% (2T) → ALL_ALLY
- def_-20% (2T) → ALL_ENEMY

**패시브 트리거:**
- on_battle_start → 「발푸르기스의 밤」발동

---

## ☀️ 광속성

### 아슈토레스 (c194) — 광/딜러 3★

| 스탯 | ATK | DEF | HP | SPD | CRI | PEN | SP비용 |
|:----:|:---:|:---:|:--:|:---:|:---:|:---:|:-----:|
| 값 | 800 | 400 | 4000 | 80 | 15% | 0% | 6 |

**NORMAL** 「밤의 속삭임」
- 데미지 4.00x → ENEMY_RANDOM_2

**ACTIVE (CD:3)** 「심연의 덫」
- 데미지 4.50x → ENEMY_NEAR

**ULTIMATE (SP:6)** 「가시 무도회」
- 데미지 4.00x → ENEMY_NEAR

---
### 야나 (c221) — 광/딜러 1★

| 스탯 | ATK | DEF | HP | SPD | CRI | PEN | SP비용 |
|:----:|:---:|:---:|:--:|:---:|:---:|:---:|:-----:|
| 값 | 480 | 240 | 2400 | 80 | 15% | 0% | 6 |

**NORMAL** 「광선 타격」
- 데미지 3.60x → ENEMY_NEAR

**ACTIVE (CD:3)** 「섬광 일격」
- 데미지 4.40x → ENEMY_NEAR
- def_-15% (2T) → ENEMY_NEAR

**ULTIMATE (SP:6)** 「광폭발」
- 데미지 3.60x → ALL_ENEMY

---
### 힐드 (c296) — 광/딜러 2★

| 스탯 | ATK | DEF | HP | SPD | CRI | PEN | SP비용 |
|:----:|:---:|:---:|:--:|:---:|:---:|:---:|:-----:|
| 값 | 640 | 320 | 3200 | 80 | 15% | 0% | 6 |

**NORMAL** 「빛의 검」
- 데미지 4.50x → ENEMY_NEAR

**ACTIVE (CD:3)** 「섬광 베기」
- 데미지 0.80x → ENEMY_NEAR
- acc-20 (2T) → ENEMY_NEAR

**ULTIMATE (SP:6)** 「발키리의 심판」
- 데미지 6.40x → ENEMY_NEAR_ROW
- SP+1 → SELF

---
### 마프데트 (c227) — 광/마법사 2★

| 스탯 | ATK | DEF | HP | SPD | CRI | PEN | SP비용 |
|:----:|:---:|:---:|:--:|:---:|:---:|:---:|:-----:|
| 값 | 480 | 320 | 4000 | 120 | 15% | 0% | 4 |

**NORMAL** 「빛의 발톱」
- 데미지 2.40x → ENEMY_NEAR

**ACTIVE (CD:3)** 「심판의 사슬」
- CC:stun (1T) → ENEMY_NEAR
- spd-20% (2T) → ENEMY_NEAR

**ULTIMATE (SP:4)** 「정의의 심판」
- 데미지 7.50x → ALL_ENEMY
- CC:stun (2T) → ALL_ENEMY
- atk-20% (2T) → ALL_ENEMY

---
### 세멜레 (c438) — 광/마법사 3★

| 스탯 | ATK | DEF | HP | SPD | CRI | PEN | SP비용 |
|:----:|:---:|:---:|:--:|:---:|:---:|:---:|:-----:|
| 값 | 600 | 400 | 5000 | 100 | 15% | 0% | 4 |

**NORMAL** 「신성 강타」
- 데미지 2.00x ×2hit (총 4.00x) → ENEMY_NEAR

**ACTIVE (CD:3)** 「제우스의 불꽃」
- burn maxHP×15% (2T, max3스택) → ENEMY_NEAR
- atk-20% (2T) → ENEMY_NEAR

**ULTIMATE (SP:4)** 「신의 번개」
- 데미지 6.00x → ALL_ENEMY
- burn maxHP×15% (2T, max3스택) → ALL_ENEMY

---
### 루미나 (c600) — 광/마법사 3.5★

| 스탯 | ATK | DEF | HP | SPD | CRI | PEN | SP비용 |
|:----:|:---:|:---:|:--:|:---:|:---:|:---:|:-----:|
| 값 | 690 | 460 | 5750 | 100 | 15% | 0% | 4 |

**NORMAL** 「성광의 채찍」
- 데미지 2.40x → ENEMY_NEAR

**ACTIVE (CD:3)** 「빛의 축복」
- atk+15% (2T) → ALL_ALLY
- spd+15 (2T) → ALL_ALLY
- 디버프 제거 → ALL_ALLY

**ULTIMATE (SP:4)** 「성역의 은총」
- 힐 maxHP×25% → ALL_ALLY
- atk+25% (3T) → ALL_ALLY
- cri_dmg_ratio+0 (3T) → ALL_ALLY

---
### 샤를 (c353) — 광/탱커 1★

| 스탯 | ATK | DEF | HP | SPD | CRI | PEN | SP비용 |
|:----:|:---:|:---:|:--:|:---:|:---:|:---:|:-----:|
| 값 | 300 | 360 | 3600 | 110 | 15% | 0% | 3 |

**NORMAL** 「빛의 방패」
- 데미지 2.40x → ENEMY_NEAR

**ACTIVE (CD:3)** 「성벽」
- 배리어 maxHP×100% → ALL_ALLY

**ULTIMATE (SP:3)** 「수호의 빛」
- 데미지 4.00x → ENEMY_NEAR_ROW
- 힐 maxHP×50% → ALL_ALLY
- 배리어 maxHP×100% → ALL_ALLY

**패시브 트리거:**
- on_battle_start → 「성벽」발동

---
### 모나 (c393) — 광/탱커 3★

| 스탯 | ATK | DEF | HP | SPD | CRI | PEN | SP비용 |
|:----:|:---:|:---:|:--:|:---:|:---:|:---:|:-----:|
| 값 | 500 | 600 | 6000 | 100 | 15% | 0% | 3 |

**NORMAL** 「이클립스」
- 데미지 2.00x → ENEMY_NEAR

**ACTIVE (CD:3)** 「트릭스타」
- 힐 maxHP×20% → ALLY_LOWEST_HP
- spd+15 (2T) → ALLY_LOWEST_HP

**ULTIMATE (SP:3)** 「사랑을 담아」
- spd+15 (3T) → ALL_ALLY
- 힐 maxHP×10% → ALL_ALLY

---
### 티타니아 (c473) — 광/탱커 3★

| 스탯 | ATK | DEF | HP | SPD | CRI | PEN | SP비용 |
|:----:|:---:|:---:|:--:|:---:|:---:|:---:|:-----:|
| 값 | 500 | 600 | 6000 | 110 | 15% | 0% | 3 |

**NORMAL** 「요정의 손길」
- 데미지 2.00x → ENEMY_NEAR

**ACTIVE (CD:3)** 「요정의 축복」
- 힐 maxHP×15% → ALL_ALLY
- cri_ratio+0 (2T) → ALL_ALLY

**ULTIMATE (SP:3)** 「요정의 여왕」
- 힐 maxHP×20% → ALL_ALLY
- atk+20% (3T) → ALL_ALLY
- spd+10 (3T) → ALL_ALLY

---
### 다나 (c183) — 광/힐러 2★

| 스탯 | ATK | DEF | HP | SPD | CRI | PEN | SP비용 |
|:----:|:---:|:---:|:--:|:---:|:---:|:---:|:-----:|
| 값 | 320 | 320 | 3200 | 90 | 15% | 0% | 3 |

**NORMAL** 「빛의 화살」
- 데미지 8.56x → ENEMY_NEAR

**ACTIVE (CD:3)** 「성스러운 기도」
- 힐 maxHP×25% → ALLY_LOWEST_HP

**ULTIMATE (SP:3)** 「빛의 은총」
- 힐 maxHP×30% → ALL_ALLY
- atk+20% (3T) → ALL_ALLY

---
### 티와즈 (c455) — 광/힐러 3★

| 스탯 | ATK | DEF | HP | SPD | CRI | PEN | SP비용 |
|:----:|:---:|:---:|:--:|:---:|:---:|:---:|:-----:|
| 값 | 400 | 400 | 4000 | 90 | 15% | 0% | 3 |

**NORMAL** 「전쟁신의 검」
- 데미지 4.00x → ENEMY_NEAR

**ACTIVE (CD:3)** 「관통 공격」
- 데미지 5.00x → ENEMY_SAME_COL

**ULTIMATE (SP:3)** 「신의 선언」
- 데미지 3.00x → ALL_ENEMY
- def_-25% (2T) → ALL_ENEMY

---
### 레다 (c028) — 광/서포터 1★

| 스탯 | ATK | DEF | HP | SPD | CRI | PEN | SP비용 |
|:----:|:---:|:---:|:--:|:---:|:---:|:---:|:-----:|
| 값 | 300 | 240 | 3000 | 120 | 15% | 0% | 4 |

**NORMAL** 「빛의 화살」
- 데미지 2.40x → ENEMY_NEAR

**ACTIVE (CD:3)** 「성광의 가호」
- atk+15% (2T) → ALL_ALLY
- 힐 maxHP×40% → ALL_ALLY

**ULTIMATE (SP:4)** 「빛의 은혜」
- 데미지 3.50x → ALL_ENEMY
- atk+15% (2T) → ALL_ALLY
- def_+20% (2T) → ALL_ALLY

---
### 시트리 (c364) — 광/서포터 3★

| 스탯 | ATK | DEF | HP | SPD | CRI | PEN | SP비용 |
|:----:|:---:|:---:|:--:|:---:|:---:|:---:|:-----:|
| 값 | 500 | 400 | 5000 | 120 | 15% | 0% | 4 |

**NORMAL** 「폴 인 러브」
- 데미지 2.00x → ENEMY_NEAR

**ACTIVE (CD:3)** 「크런치 캔디」
- atk+25% (3T) → ALL_ALLY
- spd+10 (3T) → ALL_ALLY

**ULTIMATE (SP:4)** 「라 돌체 비타」
- 데미지 2.30x → ALL_ENEMY
- atk+25% (3T) → ALL_ALLY
- cri_dmg_ratio+0 (3T) → ALL_ALLY

---
### 오네이로이 (c533) — 광/서포터 3★

| 스탯 | ATK | DEF | HP | SPD | CRI | PEN | SP비용 |
|:----:|:---:|:---:|:--:|:---:|:---:|:---:|:-----:|
| 값 | 500 | 400 | 5000 | 120 | 15% | 0% | 4 |

**NORMAL** 「꿈의 속삭임」
- 데미지 3.00x → ENEMY_NEAR

**ACTIVE (CD:3)** 「잠의 손길」
- 데미지 5.00x → ENEMY_RANDOM
- CC:sleep (1T) → ENEMY_RANDOM
- def_-15% (2T) → ENEMY_RANDOM

**ULTIMATE (SP:4)** 「영원한 꿈」
- 데미지 3.00x → ALL_ENEMY
- CC:sleep (2T) → ALL_ENEMY

---

## 🌙 암속성

### 메두사 (c064) — 암/딜러 1★

| 스탯 | ATK | DEF | HP | SPD | CRI | PEN | SP비용 |
|:----:|:---:|:---:|:--:|:---:|:---:|:---:|:-----:|
| 값 | 480 | 240 | 2400 | 80 | 15% | 0% | 6 |

**NORMAL** 「석화의 눈」
- 데미지 3.60x → ENEMY_NEAR

**ACTIVE (CD:3)** 「독사의 일격」
- 데미지 4.00x → ENEMY_NEAR
- CC:stone (1T) → ENEMY_NEAR

**ULTIMATE (SP:6)** 「석화의 시선」
- 데미지 3.20x → ALL_ENEMY
- CC:stone (1T) → ALL_ENEMY

---
### 에르제베트 (c156) — 암/딜러 2★

| 스탯 | ATK | DEF | HP | SPD | CRI | PEN | SP비용 |
|:----:|:---:|:---:|:--:|:---:|:---:|:---:|:-----:|
| 값 | 640 | 320 | 3200 | 80 | 15% | 0% | 6 |

**NORMAL** 「피의 채찍」
- 데미지 7.50x ×2hit (총 15.00x) → ENEMY_NEAR

**ACTIVE (CD:3)** 「선혈의 창」
- 데미지 8.00x → ENEMY_NEAR
- acc+15 (2T) → SELF
- atk+30% (2T) → SELF

**ULTIMATE (SP:6)** 「핏빛 향연」
- 데미지 2.00x → ALL_ENEMY
- poison maxHP×30% (2T, max3스택) → ALL_ENEMY

**패시브 트리거:**
- on_kill → 「피의 채찍」발동

---
### 쿠바바 (c486) — 암/딜러 3★

| 스탯 | ATK | DEF | HP | SPD | CRI | PEN | SP비용 |
|:----:|:---:|:---:|:--:|:---:|:---:|:---:|:-----:|
| 값 | 800 | 400 | 4000 | 80 | 15% | 0% | 6 |

**NORMAL** 「와일드 로드」
- 데미지 3.80x → ENEMY_NEAR

**ACTIVE (CD:3)** 「오버 더 리밋」
- 데미지 3.60x → ALL_ENEMY
- def_-20% (2T) → ALL_ENEMY

**ULTIMATE (SP:6)** 「데스 스키드 마크」
- 데미지 7.00x → ENEMY_NEAR

**패시브 트리거:**
- on_kill → 「와일드 로드」발동

---
### 아누비스 (c532) — 암/딜러 3.5★

| 스탯 | ATK | DEF | HP | SPD | CRI | PEN | SP비용 |
|:----:|:---:|:---:|:--:|:---:|:---:|:---:|:-----:|
| 값 | 920 | 460 | 4600 | 80 | 15% | 0% | 6 |

**NORMAL** 「사자의 인도」
- 데미지 3.40x → ENEMY_NEAR

**ACTIVE (CD:3)** 「직선 심판」
- 데미지 4.00x ×3hit (총 12.00x) → ENEMY_SAME_COL

**ULTIMATE (SP:6)** 「심판의 저울」
- 데미지 6.00x → ENEMY_LOWEST_HP

**패시브 트리거:**
- on_kill → 「사자의 인도」발동

---
### 반시 (c400) — 암/마법사 3★

| 스탯 | ATK | DEF | HP | SPD | CRI | PEN | SP비용 |
|:----:|:---:|:---:|:--:|:---:|:---:|:---:|:-----:|
| 값 | 600 | 400 | 5000 | 100 | 15% | 0% | 4 |

**NORMAL** 「4연격」
- 데미지 2.00x ×4hit (총 8.00x) → ENEMY_NEAR

**ACTIVE (CD:3)** 「전투 기도」
- atk+30% (2T) → SELF
- cri_ratio+0 (2T) → SELF

**ULTIMATE (SP:4)** 「뱅시의 절규」
- 데미지 3.00x → ALL_ENEMY

---
### 아르테미스 (c432) — 암/마법사 3★

| 스탯 | ATK | DEF | HP | SPD | CRI | PEN | SP비용 |
|:----:|:---:|:---:|:--:|:---:|:---:|:---:|:-----:|
| 값 | 600 | 400 | 5000 | 100 | 15% | 0% | 4 |

**NORMAL** 「나이트메어 이블」
- 데미지 4.00x ×4hit (총 16.00x) → ENEMY_RANDOM

**ACTIVE (CD:3)** 「광포한 분노」
- 데미지 3.00x → ENEMY_NEAR
- def_-25% (2T) → ENEMY_NEAR
- 버프 제거 → ENEMY_NEAR

**ULTIMATE (SP:4)** 「침식하는 어둠」
- 데미지 5.00x → ALL_ENEMY
- def_-20% (2T) → ALL_ENEMY

---
### 두엣샤 (c514) — 암/마법사 2★

| 스탯 | ATK | DEF | HP | SPD | CRI | PEN | SP비용 |
|:----:|:---:|:---:|:--:|:---:|:---:|:---:|:-----:|
| 값 | 480 | 320 | 4000 | 100 | 15% | 0% | 4 |

**NORMAL** 「그림자 베기」
- 데미지 4.50x → ENEMY_NEAR

**ACTIVE (CD:3)** 「이중 참격」
- 데미지 2.40x → ALL_ENEMY
- def_-10% (1T) → ALL_ENEMY

**ULTIMATE (SP:4)** 「심연의 무도」
- 데미지 5.00x → ENEMY_NEAR_ROW

---
### 모나 (c001) — 암/탱커 2★

| 스탯 | ATK | DEF | HP | SPD | CRI | PEN | SP비용 |
|:----:|:---:|:---:|:--:|:---:|:---:|:---:|:-----:|
| 값 | 400 | 480 | 4800 | 110 | 15% | 0% | 3 |

**NORMAL** 「암흑 타격」
- 데미지 2.40x → ENEMY_NEAR

**ACTIVE (CD:3)** 「암흑 장벽」
- 도발 (2T) → ALL_ENEMY
- 배리어 maxHP×20% → SELF

**ULTIMATE (SP:3)** 「어둠의 수호」
- 배리어 maxHP×20% → ALL_ALLY
- atk-20% (2T) → ALL_ENEMY

---
### 프레이 (c051) — 암/탱커 3★

| 스탯 | ATK | DEF | HP | SPD | CRI | PEN | SP비용 |
|:----:|:---:|:---:|:--:|:---:|:---:|:---:|:-----:|
| 값 | 500 | 600 | 6000 | 110 | 15% | 0% | 3 |

**NORMAL** 「그림 리퍼」
- 데미지 3.00x → ENEMY_NEAR

**ACTIVE (CD:3)** 「사신의 잔상」
- atk+25% (2T) → SELF
- cri_ratio+0 (2T) → SELF
- 반격 준비 (2T) → SELF

**ULTIMATE (SP:3)** 「트릭스터」
- 데미지 4.00x → ENEMY_NEAR_ROW
- def_-25% (2T) → ENEMY_NEAR_ROW

**패시브 트리거:**
- on_hit (1회) → 「그림 리퍼」발동

---
### 네반 (c048) — 암/힐러 1★

| 스탯 | ATK | DEF | HP | SPD | CRI | PEN | SP비용 |
|:----:|:---:|:---:|:--:|:---:|:---:|:---:|:-----:|
| 값 | 240 | 240 | 2400 | 90 | 15% | 0% | 3 |

**NORMAL** 「어둠의 손길」
- 데미지 2.00x → ENEMY_NEAR

**ACTIVE (CD:3)** 「암흑 치유」
- 힐 maxHP×65% → ALLY_LOWEST_HP
- 디버프 제거 → ALLY_LOWEST_HP
- 배리어 maxHP×35% → ALLY_LOWEST_HP

**ULTIMATE (SP:3)** 「명계의 은혜」
- 힐 maxHP×75% → ALL_ALLY
- 배리어 maxHP×55% → ALL_ALLY

---
### 미르칼라 (c448) — 암/힐러 3★

| 스탯 | ATK | DEF | HP | SPD | CRI | PEN | SP비용 |
|:----:|:---:|:---:|:--:|:---:|:---:|:---:|:-----:|
| 값 | 400 | 400 | 4000 | 90 | 15% | 0% | 3 |

**NORMAL** 「흡혈」
- 데미지 3.60x → ENEMY_NEAR

**ACTIVE (CD:3)** 「핏빛 저주」
- 데미지 4.00x → ENEMY_NEAR
- bleed maxHP×15% (3T, max3스택) → ENEMY_NEAR
- atk-20% (2T) → ENEMY_NEAR

**ULTIMATE (SP:3)** 「뱀파이어 폭풍」
- 데미지 3.60x → ALL_ENEMY
- bleed maxHP×15% (2T, max3스택) → ALL_ENEMY

---
### 페르세포네 (c035) — 암/서포터 1★

| 스탯 | ATK | DEF | HP | SPD | CRI | PEN | SP비용 |
|:----:|:---:|:---:|:--:|:---:|:---:|:---:|:-----:|
| 값 | 300 | 240 | 3000 | 120 | 15% | 0% | 4 |

**NORMAL** 「암흑의 가시」
- 데미지 2.40x → ENEMY_NEAR

**ACTIVE (CD:3)** 「명계의 축복」
- atk+15% (2T) → ALL_ALLY
- def_+10% (2T) → ALL_ALLY

**ULTIMATE (SP:4)** 「명계의 꽃」
- atk+25% (2T) → ALL_ALLY
- 힐 maxHP×15% → ALL_ALLY

---
### 바토리 (c294) — 암/서포터 3★

| 스탯 | ATK | DEF | HP | SPD | CRI | PEN | SP비용 |
|:----:|:---:|:---:|:--:|:---:|:---:|:---:|:-----:|
| 값 | 500 | 400 | 5000 | 120 | 15% | 0% | 4 |

**NORMAL** 「동반자 예우」
- 데미지 4.40x → ENEMY_NEAR

**ACTIVE (CD:3)** 「피의 맹세」
- 데미지 4.50x → ENEMY_NEAR_ROW
- bleed maxHP×15% (2T, max3스택) → ENEMY_NEAR_ROW

**ULTIMATE (SP:4)** 「에스코트」
- 데미지 7.00x → ENEMY_NEAR

---
### 유나 (c485) — 암/서포터 3★

| 스탯 | ATK | DEF | HP | SPD | CRI | PEN | SP비용 |
|:----:|:---:|:---:|:--:|:---:|:---:|:---:|:-----:|
| 값 | 500 | 400 | 5000 | 120 | 15% | 0% | 4 |

**NORMAL** 「달그림자」
- 데미지 2.00x → ENEMY_NEAR

**ACTIVE (CD:3)** 「어둠의 가호」
- 힐 maxHP×25% → ALLY_LOWEST_HP
- def_+20% (2T) → ALLY_LOWEST_HP
- spd-15 (2T) → ALL_ENEMY

**ULTIMATE (SP:4)** 「달의 수호」
- atk+20% (2T) → ALL_ALLY
- def_+20% (2T) → ALL_ALLY

---