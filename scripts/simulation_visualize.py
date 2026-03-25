"""BattleAgent 시뮬레이션 v3.0 결과 시각화

3×3 그리드 포지셔닝 분석 결과를 차트로 출력한다.
- 10×10 승률 히트맵
- 팀 티어 바 차트
- 그리드 배치도
- 전열 배치 효과 분석

실행: py -3 -X utf8 scripts/simulation_visualize.py
"""
import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import matplotlib
matplotlib.use('Agg')  # 비GUI 백엔드
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.colors import LinearSegmentedColormap
import numpy as np

from battle.battle_engine import BattleEngine
from battle.enums import BattleResult
from fixtures.test_data import (
    as_enemy_party,
    get_meta_v82_m01, get_meta_v82_m02, get_meta_v82_m03,
    get_meta_v82_m04, get_meta_v82_m05, get_meta_v82_m06,
    get_meta_v82_m07, get_meta_v82_m08, get_meta_v82_m09,
    get_meta_v82_m10,
)

# 한글 폰트 설정
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

TEAMS = [
    ("M01\n화상연소", get_meta_v82_m01),
    ("M02\n빙결제어", get_meta_v82_m02),
    ("M03\n수면폭발", get_meta_v82_m03),
    ("M04\n치명타학살", get_meta_v82_m04),
    ("M05\n속도압도", get_meta_v82_m05),
    ("M06\n철벽수호", get_meta_v82_m06),
    ("M07\n출혈암살", get_meta_v82_m07),
    ("M08\n보호막연합", get_meta_v82_m08),
    ("M09\n디버프착취", get_meta_v82_m09),
    ("M10\n혼성엘리트", get_meta_v82_m10),
]

TEAM_NAMES_SHORT = [
    "M01 화상연소", "M02 빙결제어", "M03 수면폭발", "M04 치명타학살",
    "M05 속도압도", "M06 철벽수호", "M07 출혈암살", "M08 보호막연합",
    "M09 디버프착취", "M10 혼성엘리트",
]

RUNS = 20


def run_simulation():
    """10×10 매치업 시뮬레이션 실행"""
    n = len(TEAMS)
    matrix = np.zeros((n, n))
    total = n * (n - 1) * RUNS
    count = 0
    start = time.time()

    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            _, af = TEAMS[i]
            _, ef = TEAMS[j]
            wins = 0
            for seed in range(RUNS):
                try:
                    allies = af()
                    enemies = as_enemy_party(ef())
                    engine = BattleEngine(ally_units=allies, enemy_units=enemies, seed=seed)
                    result = engine.run()
                    if result == BattleResult.ALLY_WIN:
                        wins += 1
                except Exception:
                    pass
            matrix[i][j] = wins / RUNS * 100
            count += RUNS
            pct = count / total * 100
            elapsed = time.time() - start
            print(f"\r  진행: {count}/{total} ({pct:.0f}%) | 경과 {elapsed:.1f}s", end="", flush=True)

    print(f"\n  완료: {total}전투, {time.time()-start:.1f}초")
    return matrix


def plot_heatmap(matrix, output_path):
    """10×10 승률 히트맵"""
    n = len(TEAM_NAMES_SHORT)
    fig, ax = plt.subplots(figsize=(14, 11))

    # 커스텀 컬러맵: 빨강(0%) → 노랑(50%) → 초록(100%)
    colors = ['#d32f2f', '#ff9800', '#ffeb3b', '#8bc34a', '#2e7d32']
    cmap = LinearSegmentedColormap.from_list('wr', colors, N=256)

    # 대각선은 NaN
    display = matrix.copy()
    np.fill_diagonal(display, np.nan)

    im = ax.imshow(display, cmap=cmap, vmin=0, vmax=100, aspect='equal')

    # 셀 텍스트
    for i in range(n):
        for j in range(n):
            if i == j:
                ax.text(j, i, "—", ha='center', va='center', fontsize=11,
                        fontweight='bold', color='#666')
            else:
                val = matrix[i][j]
                color = 'white' if val < 25 or val > 75 else 'black'
                ax.text(j, i, f"{val:.0f}%", ha='center', va='center',
                        fontsize=10, fontweight='bold', color=color)

    ax.set_xticks(range(n))
    ax.set_yticks(range(n))
    ax.set_xticklabels(TEAM_NAMES_SHORT, fontsize=9, rotation=45, ha='right')
    ax.set_yticklabels(TEAM_NAMES_SHORT, fontsize=9)
    ax.set_xlabel("적팀 (방어)", fontsize=12, fontweight='bold')
    ax.set_ylabel("아군팀 (공격)", fontsize=12, fontweight='bold')
    ax.set_title("BattleAgent v3.0 — 10×10 메타팀 승률 매트릭스\n(3×3 그리드 포지셔닝 적용)",
                 fontsize=14, fontweight='bold', pad=20)

    # 컬러바
    cbar = fig.colorbar(im, ax=ax, shrink=0.8, label='승률 (%)')
    cbar.set_ticks([0, 25, 50, 75, 100])

    plt.tight_layout()
    fig.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"  📊 히트맵 저장: {output_path}")


def plot_tier_chart(matrix, output_path):
    """팀별 평균 승률 + 티어 바 차트"""
    n = len(TEAM_NAMES_SHORT)
    avg_rates = []
    for i in range(n):
        rates = [matrix[i][j] for j in range(n) if i != j]
        avg_rates.append(np.mean(rates))

    # 승률 순 정렬
    order = np.argsort(avg_rates)[::-1]
    sorted_names = [TEAM_NAMES_SHORT[i] for i in order]
    sorted_rates = [avg_rates[i] for i in order]

    # 티어 색상
    tier_colors = []
    tier_labels = []
    for r in sorted_rates:
        if r >= 70:
            tier_colors.append('#ff6f00')  # S: 오렌지
            tier_labels.append('S')
        elif r >= 55:
            tier_colors.append('#1565c0')  # A: 블루
            tier_labels.append('A')
        elif r >= 40:
            tier_colors.append('#558b2f')  # B: 그린
            tier_labels.append('B')
        else:
            tier_colors.append('#c62828')  # C: 레드
            tier_labels.append('C')

    fig, ax = plt.subplots(figsize=(14, 7))

    bars = ax.barh(range(n), sorted_rates, color=tier_colors, edgecolor='white', linewidth=1.5, height=0.7)

    # 50% 기준선
    ax.axvline(x=50, color='#999', linestyle='--', linewidth=1, alpha=0.7)
    ax.text(51, -0.7, "50% 기준선", fontsize=8, color='#999')

    # 바 라벨
    for i, (bar, rate, tier) in enumerate(zip(bars, sorted_rates, tier_labels)):
        ax.text(rate + 1.5, i, f"{rate:.1f}% [{tier}티어]",
                va='center', fontsize=11, fontweight='bold', color=tier_colors[i])

    ax.set_yticks(range(n))
    ax.set_yticklabels(sorted_names, fontsize=11)
    ax.set_xlabel("평균 승률 (%)", fontsize=12, fontweight='bold')
    ax.set_title("BattleAgent v3.0 — 팀별 평균 승률 & 티어\n(3×3 그리드 포지셔닝 적용)",
                 fontsize=14, fontweight='bold')
    ax.set_xlim(0, 105)
    ax.invert_yaxis()

    # 범례
    legend_patches = [
        mpatches.Patch(color='#ff6f00', label='S티어 (70%+)'),
        mpatches.Patch(color='#1565c0', label='A티어 (55-69%)'),
        mpatches.Patch(color='#558b2f', label='B티어 (40-54%)'),
        mpatches.Patch(color='#c62828', label='C티어 (<40%)'),
    ]
    ax.legend(handles=legend_patches, loc='lower right', fontsize=10)

    plt.tight_layout()
    fig.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"  📊 티어 차트 저장: {output_path}")


def plot_grid_layouts(output_path):
    """팀별 3×3 그리드 배치도"""
    fig, axes = plt.subplots(2, 5, figsize=(24, 10))
    fig.suptitle("BattleAgent v3.0 — 10팀 3×3 그리드 배치도",
                 fontsize=16, fontweight='bold', y=1.02)

    role_colors = {
        'attacker': '#e53935',
        'defender': '#1565c0',
        'magician': '#7b1fa2',
        'healer': '#2e7d32',
        'supporter': '#ef6c00',
    }
    role_labels_kr = {
        'attacker': '딜러',
        'defender': '탱커',
        'magician': '마법사',
        'healer': '힐러',
        'supporter': '서포터',
    }

    for idx, (team_name, factory) in enumerate(TEAMS):
        ax = axes[idx // 5][idx % 5]
        chars = factory()

        # 3×3 그리드 그리기
        for r in range(3):
            for c in range(3):
                rect = plt.Rectangle((c, 2-r), 1, 1, fill=True,
                                      facecolor='#f5f5f5', edgecolor='#bbb', linewidth=1)
                ax.add_patch(rect)

        # 캐릭터 배치
        for ch in chars:
            r, c = ch.tile_pos
            role = ch.role.value
            color = role_colors.get(role, '#999')
            # 역할별 색상 원
            circle = plt.Circle((c + 0.5, 2 - r + 0.5), 0.38,
                                facecolor=color, edgecolor='white', linewidth=2, alpha=0.85)
            ax.add_patch(circle)
            # 이름
            name_short = ch.name[:3]
            ax.text(c + 0.5, 2 - r + 0.55, name_short,
                    ha='center', va='center', fontsize=8, fontweight='bold', color='white')
            # 역할 약자
            role_short = role_labels_kr.get(role, '?')[:1]
            ax.text(c + 0.5, 2 - r + 0.25, role_short,
                    ha='center', va='center', fontsize=7, color='#eee')

        ax.set_xlim(-0.1, 3.1)
        ax.set_ylim(-0.1, 3.1)
        ax.set_aspect('equal')
        ax.set_xticks([0.5, 1.5, 2.5])
        ax.set_xticklabels(['좌', '중', '우'], fontsize=8)
        ax.set_yticks([0.5, 1.5, 2.5])
        ax.set_yticklabels(['후열', '중열', '전열'], fontsize=8)
        # 팀 이름 (줄바꿈 제거)
        title = team_name.replace('\n', ' ')
        ax.set_title(title, fontsize=11, fontweight='bold', pad=8)

    # 범례
    legend_patches = [
        mpatches.Patch(color=v, label=f"{role_labels_kr[k]}({k})")
        for k, v in role_colors.items()
    ]
    fig.legend(handles=legend_patches, loc='lower center', ncol=5,
               fontsize=10, bbox_to_anchor=(0.5, -0.02))

    plt.tight_layout()
    fig.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"  📊 그리드 배치도 저장: {output_path}")


def plot_position_analysis(matrix, output_path):
    """포지셔닝 분석 — 전열 배치 수 vs 승률, 전열 탱커 효과"""
    n = len(TEAMS)
    avg_rates = []
    for i in range(n):
        rates = [matrix[i][j] for j in range(n) if i != j]
        avg_rates.append(np.mean(rates))

    # 팀별 배치 분석
    front_counts = []
    has_front_tank = []
    back_counts = []

    for _, factory in TEAMS:
        chars = factory()
        fc = sum(1 for c in chars if c.tile_pos[0] == 0)
        bc = sum(1 for c in chars if c.tile_pos[0] == 2)
        ft = any(c.role.value == 'defender' and c.tile_pos[0] == 0 for c in chars)
        front_counts.append(fc)
        back_counts.append(bc)
        has_front_tank.append(ft)

    fig, axes = plt.subplots(1, 3, figsize=(20, 7))

    # ── 차트 1: 전열 유닛 수 vs 승률 산점도 ──
    ax1 = axes[0]
    colors = ['#1565c0' if ft else '#e53935' for ft in has_front_tank]
    scatter = ax1.scatter(front_counts, avg_rates, c=colors, s=200, edgecolors='white',
                          linewidth=2, zorder=5)
    for i, name in enumerate(TEAM_NAMES_SHORT):
        ax1.annotate(name.split()[0], (front_counts[i], avg_rates[i]),
                     textcoords="offset points", xytext=(8, 5),
                     fontsize=9, fontweight='bold')

    ax1.set_xlabel("전열 유닛 수", fontsize=12, fontweight='bold')
    ax1.set_ylabel("평균 승률 (%)", fontsize=12, fontweight='bold')
    ax1.set_title("전열 유닛 수 vs 승률", fontsize=13, fontweight='bold')
    ax1.axhline(y=50, color='#999', linestyle='--', alpha=0.5)
    ax1.set_xlim(-0.5, 5)
    ax1.set_ylim(-5, 105)
    ax1.grid(True, alpha=0.3)

    legend_elements = [
        plt.scatter([], [], c='#1565c0', s=100, label='전열 탱커 O'),
        plt.scatter([], [], c='#e53935', s=100, label='전열 탱커 X'),
    ]
    ax1.legend(handles=legend_elements, loc='upper right', fontsize=10)

    # ── 차트 2: 전열 탱커 배치 효과 (박스플롯) ──
    ax2 = axes[1]
    tank_rates = [avg_rates[i] for i in range(n) if has_front_tank[i]]
    no_tank_rates = [avg_rates[i] for i in range(n) if not has_front_tank[i]]

    bp = ax2.boxplot([tank_rates, no_tank_rates],
                     labels=['전열 탱커\n배치팀', '전열 탱커\n미배치팀'],
                     patch_artist=True, widths=0.5)
    bp['boxes'][0].set_facecolor('#1565c0')
    bp['boxes'][0].set_alpha(0.6)
    bp['boxes'][1].set_facecolor('#e53935')
    bp['boxes'][1].set_alpha(0.6)

    # 평균선
    if tank_rates:
        avg_t = np.mean(tank_rates)
        ax2.axhline(y=avg_t, color='#1565c0', linestyle=':', alpha=0.7)
        ax2.text(2.4, avg_t, f"평균 {avg_t:.1f}%", fontsize=9, color='#1565c0')
    if no_tank_rates:
        avg_nt = np.mean(no_tank_rates)
        ax2.axhline(y=avg_nt, color='#e53935', linestyle=':', alpha=0.7)
        ax2.text(2.4, avg_nt, f"평균 {avg_nt:.1f}%", fontsize=9, color='#e53935')

    ax2.set_ylabel("평균 승률 (%)", fontsize=12, fontweight='bold')
    ax2.set_title("전열 탱커 배치 효과", fontsize=13, fontweight='bold')
    ax2.axhline(y=50, color='#999', linestyle='--', alpha=0.5)
    ax2.set_ylim(-5, 105)
    ax2.grid(True, alpha=0.3, axis='y')

    # ── 차트 3: 행별 배치 비율 스택드 바 ──
    ax3 = axes[2]
    order = np.argsort(avg_rates)[::-1]
    names_sorted = [TEAM_NAMES_SHORT[i].split()[0] for i in order]
    front_sorted = [front_counts[i] for i in order]
    mid_sorted = [5 - front_counts[i] - back_counts[i] for i in order]
    back_sorted = [back_counts[i] for i in order]
    rates_sorted = [avg_rates[i] for i in order]

    x = range(n)
    ax3.bar(x, front_sorted, color='#e53935', label='전열', alpha=0.8)
    ax3.bar(x, mid_sorted, bottom=front_sorted, color='#ff9800', label='중열', alpha=0.8)
    bottoms = [f + m for f, m in zip(front_sorted, mid_sorted)]
    ax3.bar(x, back_sorted, bottom=bottoms, color='#1565c0', label='후열', alpha=0.8)

    # 승률 라벨
    ax3_twin = ax3.twinx()
    ax3_twin.plot(x, rates_sorted, 'ko-', markersize=8, linewidth=2, label='승률', zorder=10)
    ax3_twin.set_ylabel("평균 승률 (%)", fontsize=11, fontweight='bold')
    ax3_twin.set_ylim(-5, 105)
    ax3_twin.axhline(y=50, color='#999', linestyle='--', alpha=0.3)

    ax3.set_xticks(x)
    ax3.set_xticklabels(names_sorted, fontsize=9, rotation=45, ha='right')
    ax3.set_ylabel("유닛 수", fontsize=11, fontweight='bold')
    ax3.set_title("행별 배치 분포 & 승률", fontsize=13, fontweight='bold')
    ax3.legend(loc='upper left', fontsize=9)
    ax3_twin.legend(loc='upper right', fontsize=9)

    fig.suptitle("BattleAgent v3.0 — 3×3 포지셔닝 분석",
                 fontsize=15, fontweight='bold', y=1.02)
    plt.tight_layout()
    fig.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"  📊 포지셔닝 분석 저장: {output_path}")


def main():
    output_dir = os.path.join(os.path.dirname(__file__), '..', 'docs', 'images')
    os.makedirs(output_dir, exist_ok=True)

    print("=" * 60)
    print("  BattleAgent v3.0 시뮬레이션 시각화")
    print("=" * 60)

    # 시뮬레이션 실행
    print("\n  [1/4] 시뮬레이션 실행...")
    matrix = run_simulation()

    # 차트 생성
    print("\n  [2/4] 승률 히트맵 생성...")
    plot_heatmap(matrix, os.path.join(output_dir, 'v3_heatmap.png'))

    print("\n  [3/4] 티어 차트 + 그리드 배치도 생성...")
    plot_tier_chart(matrix, os.path.join(output_dir, 'v3_tier_chart.png'))
    plot_grid_layouts(os.path.join(output_dir, 'v3_grid_layouts.png'))

    print("\n  [4/4] 포지셔닝 분석 차트 생성...")
    plot_position_analysis(matrix, os.path.join(output_dir, 'v3_position_analysis.png'))

    print("\n" + "=" * 60)
    print("  ✅ 시각화 완료! 파일 위치:")
    print(f"    {os.path.abspath(output_dir)}")
    print("    - v3_heatmap.png          (10×10 승률 히트맵)")
    print("    - v3_tier_chart.png       (팀 티어 바 차트)")
    print("    - v3_grid_layouts.png     (10팀 그리드 배치도)")
    print("    - v3_position_analysis.png (포지셔닝 효과 분석)")
    print("=" * 60)


if __name__ == "__main__":
    main()
