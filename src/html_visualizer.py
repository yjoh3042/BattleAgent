"""html_visualizer.py - BattleRecorder 데이터로 자립형 HTML 배틀 리플레이 생성"""
from __future__ import annotations
import json


def generate_multi_html(scenarios_list: list, labels: list = None) -> str:
    """다중 시나리오 탭 지원 자립형 HTML 문자열 반환"""
    if labels is None:
        labels = [d.get("scenario", f"Scenario {i+1}") for i, d in enumerate(scenarios_list)]

    all_scen_js = json.dumps(
        [{"label": lab, "turns": d.get("turns", [])} for lab, d in zip(labels, scenarios_list)],
        ensure_ascii=False, separators=(',', ':')
    )

    tab_buttons_html = "\n  ".join(
        f'<button class="scen-tab{" active" if i == 0 else ""}" onclick="switchScenario({i})">'
        f'{lab}</button>'
        for i, lab in enumerate(labels)
    )

    first_label = labels[0] if labels else "Battle Replay"

    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{first_label}</title>
<style>
  :root {{
    --bg: #0d1117; --bg2: #161b22; --bg3: #21262d;
    --border: #30363d; --text: #e6edf3; --muted: #8b949e;
    --ally: #1f6feb; --ally-low: #f0883e; --ally-dead: #484f58;
    --enemy: #da3633; --enemy-low: #f0883e; --enemy-dead: #484f58;
    --barrier: #a371f7; --burn: #ff7b54; --ult: #ffd700;
    --sp-ally: #1f6feb; --sp-enemy: #da3633;
    --green: #3fb950; --yellow: #d29922; --purple: #a371f7;
    --radius: 8px; --shadow: 0 2px 8px rgba(0,0,0,.4);
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    background: var(--bg); color: var(--text);
    font-family: 'Segoe UI', system-ui, sans-serif;
    font-size: 13px; min-height: 100vh;
  }}
  /* ─── 시나리오 탭 바 ─── */
  #scenario-bar {{
    background: #0d1117;
    border-bottom: 1px solid #30363d;
    padding: 6px 16px;
    display: flex; gap: 6px; flex-wrap: wrap;
  }}
  .scen-tab {{
    background: #21262d; border: 1px solid #30363d;
    color: #8b949e; border-radius: 6px;
    padding: 4px 12px; cursor: pointer;
    font-size: 12px; transition: all .15s;
    white-space: nowrap;
  }}
  .scen-tab:hover {{ background: #2d333b; color: #e6edf3; }}
  .scen-tab.active {{
    background: rgba(31,111,235,.15); border-color: #1f6feb;
    color: #79c0ff; font-weight: 600;
  }}
  /* ─── 헤더 ─── */
  #header {{
    background: var(--bg2); border-bottom: 1px solid var(--border);
    padding: 10px 16px; display: flex; align-items: center;
    gap: 16px; flex-wrap: wrap;
  }}
  #header h1 {{ font-size: 15px; font-weight: 600; color: var(--ult); }}
  #turn-info {{ font-size: 13px; color: var(--muted); }}
  #turn-info span {{ color: var(--text); font-weight: 600; }}
  #result-badge {{
    margin-left: auto; padding: 3px 10px; border-radius: 12px;
    font-size: 12px; font-weight: 600; display: none;
  }}
  .badge-win {{ background: #1a4a1a; color: var(--green); border: 1px solid var(--green); }}
  .badge-lose {{ background: #4a1a1a; color: var(--enemy); border: 1px solid var(--enemy); }}
  .badge-timeout {{ background: #3a3a1a; color: var(--yellow); border: 1px solid var(--yellow); }}

  /* ─── CTB 타임라인 ─── */
  #ctb-row {{
    background: var(--bg2); border-bottom: 1px solid var(--border);
    padding: 8px 16px; display: flex; align-items: center; gap: 6px;
    overflow-x: auto; min-height: 52px;
  }}
  .ctb-label {{ color: var(--muted); font-size: 11px; white-space: nowrap; margin-right: 4px; }}
  .ctb-chip {{
    display: flex; flex-direction: column; align-items: center;
    padding: 4px 8px; border-radius: var(--radius);
    border: 1px solid var(--border); background: var(--bg3);
    font-size: 11px; white-space: nowrap; min-width: 52px;
    transition: all .15s;
  }}
  .ctb-chip.active {{
    border-color: var(--ult); background: rgba(255,215,0,.08);
    box-shadow: 0 0 8px rgba(255,215,0,.3);
  }}
  .ctb-chip.extra {{ border-color: var(--purple); background: rgba(163,113,247,.1); }}
  .ctb-chip .chip-name {{ font-weight: 600; }}
  .ctb-chip .chip-t {{ color: var(--muted); font-size: 10px; }}
  .chip-ally {{ color: #79c0ff; }}
  .chip-enemy {{ color: #ff7b72; }}

  /* ─── 메인 레이아웃 ─── */
  #main {{
    display: grid;
    grid-template-columns: 1fr 260px;
    grid-template-rows: auto 1fr;
    gap: 10px; padding: 10px 16px;
    max-height: calc(100vh - 120px);
  }}
  /* 유닛 패널 */
  #units-panel {{
    grid-column: 1; grid-row: 1;
    display: grid; grid-template-columns: 1fr 1fr;
    gap: 10px;
  }}
  .side-box {{
    background: var(--bg2); border: 1px solid var(--border);
    border-radius: var(--radius); padding: 10px;
  }}
  .side-title {{
    font-size: 11px; font-weight: 600; color: var(--muted);
    text-transform: uppercase; letter-spacing: .5px;
    margin-bottom: 8px; padding-bottom: 6px;
    border-bottom: 1px solid var(--border);
    display: flex; justify-content: space-between;
  }}
  .sp-bar-wrap {{
    display: flex; align-items: center; gap: 6px; margin-top: 6px;
  }}
  .sp-label {{ font-size: 11px; color: var(--muted); width: 44px; }}
  .sp-track {{
    flex: 1; height: 8px; background: var(--bg3);
    border-radius: 4px; overflow: hidden;
  }}
  .sp-fill {{
    height: 100%; border-radius: 4px; transition: width .3s;
  }}
  .sp-fill.ally {{ background: var(--sp-ally); }}
  .sp-fill.enemy {{ background: var(--sp-enemy); }}
  .sp-num {{ font-size: 11px; color: var(--text); min-width: 28px; text-align: right; }}

  /* 유닛 카드 */
  .unit-card {{
    background: var(--bg3); border: 1px solid var(--border);
    border-radius: 6px; padding: 7px 9px; margin-bottom: 6px;
    transition: border-color .15s;
  }}
  .unit-card.active-unit {{
    border-color: var(--ult);
    box-shadow: 0 0 6px rgba(255,215,0,.2);
  }}
  .unit-card.dead {{ opacity: .45; }}
  .unit-top {{ display: flex; align-items: center; gap: 6px; margin-bottom: 5px; }}
  .unit-name {{ font-weight: 600; font-size: 12px; flex: 1; }}
  .unit-role {{
    font-size: 10px; color: var(--muted);
    background: var(--bg2); padding: 1px 5px;
    border-radius: 10px;
  }}
  .unit-element {{
    font-size: 10px; padding: 1px 5px;
    border-radius: 10px; color: #fff;
  }}
  .el-fire {{ background: #8b2500; }}
  .el-water {{ background: #003d7a; }}
  .el-forest {{ background: #1a4a1a; }}
  .el-light {{ background: #6b5800; }}
  .el-dark {{ background: #3a1a5a; }}
  /* HP 바 */
  .hp-row {{ display: flex; align-items: center; gap: 5px; }}
  .hp-track {{
    flex: 1; height: 10px; background: var(--bg);
    border-radius: 5px; overflow: hidden; position: relative;
  }}
  .hp-fill {{
    height: 100%; border-radius: 5px; transition: width .3s;
  }}
  .barrier-fill {{
    position: absolute; top: 0; left: 0; height: 100%;
    background: var(--barrier); opacity: .7;
    pointer-events: none; transition: width .3s;
  }}
  .hp-text {{ font-size: 10px; color: var(--muted); min-width: 72px; text-align: right; }}
  /* 배지 행 */
  .unit-badges {{
    display: flex; gap: 3px; flex-wrap: wrap; margin-top: 4px;
  }}
  .badge {{
    font-size: 10px; padding: 1px 5px; border-radius: 10px;
    border: 1px solid transparent;
  }}
  .badge-cc {{ background: #3a1a1a; color: #ff7b72; border-color: #da3633; }}
  .badge-burn {{ background: #3a1a00; color: var(--burn); border-color: #ff7b54; }}
  .badge-cd {{ background: #1a1a3a; color: #79c0ff; border-color: #1f6feb; }}
  .badge-ult {{ background: #3a3300; color: var(--ult); border-color: #ffd700; }}
  .badge-buff {{ background: #1a3a1a; color: var(--green); border-color: #3fb950; }}
  .badge-debuff {{ background: #3a1a1a; color: #ff7b72; border-color: #da3633; }}

  /* ─── 오른쪽 패널 (이벤트 + 로그) ─── */
  #right-panel {{
    grid-column: 2; grid-row: 1 / 3;
    display: flex; flex-direction: column; gap: 10px;
    max-height: calc(100vh - 130px);
    overflow: hidden;
  }}
  .panel-box {{
    background: var(--bg2); border: 1px solid var(--border);
    border-radius: var(--radius); padding: 10px;
    display: flex; flex-direction: column;
    overflow: hidden;
  }}
  .panel-title {{
    font-size: 11px; font-weight: 600; color: var(--muted);
    text-transform: uppercase; letter-spacing: .5px;
    margin-bottom: 8px; flex-shrink: 0;
  }}
  #events-list {{
    overflow-y: auto; flex: 1;
    max-height: 160px;
  }}
  #log-box {{ flex: 1; overflow: hidden; }}
  #log-list {{
    overflow-y: auto; flex: 1;
    max-height: calc(100vh - 400px);
    min-height: 100px;
  }}
  .event-item {{
    padding: 3px 0; border-bottom: 1px solid var(--border);
    font-size: 11px; line-height: 1.4;
  }}
  .event-item:last-child {{ border-bottom: none; }}
  .ev-dmg {{ color: #ff7b72; }}
  .ev-heal {{ color: var(--green); }}
  .ev-buff {{ color: #79c0ff; }}
  .ev-debuff {{ color: #d29922; }}
  .ev-death {{ color: var(--muted); }}
  .ev-ult {{ color: var(--ult); }}
  .ev-sp {{ color: var(--purple); }}
  .ev-crit {{ font-weight: 700; }}
  .log-line {{
    padding: 2px 0; font-size: 11px; line-height: 1.5;
    color: var(--muted); border-bottom: 1px solid rgba(48,54,61,.5);
    white-space: pre-wrap; word-break: break-word;
  }}

  /* ─── 컨트롤 바 ─── */
  #controls {{
    grid-column: 1; grid-row: 2;
    background: var(--bg2); border: 1px solid var(--border);
    border-radius: var(--radius); padding: 10px 14px;
    display: flex; align-items: center; gap: 10px;
    flex-wrap: wrap;
  }}
  .ctrl-btn {{
    background: var(--bg3); border: 1px solid var(--border);
    color: var(--text); border-radius: 6px;
    padding: 5px 12px; cursor: pointer;
    font-size: 13px; transition: background .1s;
  }}
  .ctrl-btn:hover {{ background: #2d333b; }}
  .ctrl-btn:disabled {{ opacity: .4; cursor: not-allowed; }}
  .ctrl-btn.active {{ background: var(--ally); border-color: var(--ally); color: #fff; }}
  #turn-slider {{
    flex: 1; accent-color: var(--ally);
    min-width: 80px;
  }}
  #speed-label {{ color: var(--muted); font-size: 12px; white-space: nowrap; }}
  select#speed-select {{
    background: var(--bg3); border: 1px solid var(--border);
    color: var(--text); border-radius: 6px; padding: 4px 8px;
    font-size: 12px; cursor: pointer;
  }}

  /* ─── 결과 오버레이 ─── */
  #overlay {{
    display: none; position: fixed; inset: 0;
    background: rgba(13,17,23,.85);
    align-items: center; justify-content: center;
    z-index: 100; flex-direction: column; gap: 16px;
  }}
  #overlay.show {{ display: flex; }}
  #overlay-title {{ font-size: 48px; }}
  #overlay-sub {{ font-size: 18px; color: var(--muted); }}
  #overlay-close {{
    background: var(--bg3); border: 1px solid var(--border);
    color: var(--text); padding: 8px 24px; border-radius: var(--radius);
    cursor: pointer; font-size: 14px;
  }}
  #overlay-close:hover {{ background: #2d333b; }}

  /* 스크롤바 */
  ::-webkit-scrollbar {{ width: 6px; height: 6px; }}
  ::-webkit-scrollbar-track {{ background: var(--bg); }}
  ::-webkit-scrollbar-thumb {{ background: var(--border); border-radius: 3px; }}
</style>
</head>
<body>

<!-- 시나리오 탭 바 -->
<div id="scenario-bar">
  {tab_buttons_html}
</div>

<!-- 헤더 -->
<div id="header">
  <h1 id="header-title">⚔️ CTB 배틀 리플레이</h1>
  <div id="turn-info">
    턴 <span id="ti-cur">1</span>/<span id="ti-total">?</span>
    &nbsp;|&nbsp; t=<span id="ti-t">0</span>
    &nbsp;|&nbsp; R:<span id="ti-r">0</span>
    &nbsp;|&nbsp; <span id="ti-who">-</span>
    <span id="ti-extra" style="color:var(--purple);display:none"> [Extra Turn]</span>
    &nbsp;→&nbsp; <span id="ti-skill" style="color:var(--ult)">-</span>
  </div>
  <div id="result-badge"></div>
</div>

<!-- CTB 타임라인 큐 -->
<div id="ctb-row">
  <span class="ctb-label">CTB</span>
  <div id="ctb-chips" style="display:flex;gap:6px;"></div>
</div>

<!-- 결과 오버레이 -->
<div id="overlay">
  <div id="overlay-title"></div>
  <div id="overlay-sub"></div>
  <button id="overlay-close" onclick="document.getElementById('overlay').classList.remove('show')">닫기</button>
</div>

<!-- 메인 -->
<div id="main">
  <!-- 유닛 패널 -->
  <div id="units-panel">
    <!-- 아군 -->
    <div class="side-box" id="ally-box">
      <div class="side-title">
        <span>아군</span>
        <span id="ally-alive-count" style="color:var(--green)"></span>
      </div>
      <div id="ally-units"></div>
      <div class="sp-bar-wrap">
        <span class="sp-label">SP 아군</span>
        <div class="sp-track"><div class="sp-fill ally" id="sp-ally-fill" style="width:0%"></div></div>
        <span class="sp-num" id="sp-ally-num">0/10</span>
      </div>
    </div>
    <!-- 적군 -->
    <div class="side-box" id="enemy-box">
      <div class="side-title">
        <span>적군</span>
        <span id="enemy-alive-count" style="color:var(--enemy)"></span>
      </div>
      <div id="enemy-units"></div>
      <div class="sp-bar-wrap">
        <span class="sp-label">SP 적군</span>
        <div class="sp-track"><div class="sp-fill enemy" id="sp-enemy-fill" style="width:0%"></div></div>
        <span class="sp-num" id="sp-enemy-num">0/10</span>
      </div>
    </div>
  </div>

  <!-- 오른쪽 패널 -->
  <div id="right-panel">
    <!-- 이벤트 -->
    <div class="panel-box" style="max-height:220px;">
      <div class="panel-title">⚡ 이 턴 이벤트</div>
      <div id="events-list"></div>
    </div>
    <!-- 로그 -->
    <div class="panel-box" id="log-box">
      <div class="panel-title">📋 배틀 로그</div>
      <div id="log-list"></div>
    </div>
  </div>

  <!-- 컨트롤 -->
  <div id="controls">
    <button class="ctrl-btn" id="btn-first" onclick="goTurn(0)">⏮</button>
    <button class="ctrl-btn" id="btn-prev"  onclick="goTurn(curIdx-1)">◀</button>
    <input type="range" id="turn-slider" min="0" value="0"
           oninput="goTurn(parseInt(this.value))">
    <button class="ctrl-btn" id="btn-next"  onclick="goTurn(curIdx+1)">▶</button>
    <button class="ctrl-btn" id="btn-last"  onclick="goTurn(TURNS.length-1)">⏭</button>
    <button class="ctrl-btn" id="btn-play"  onclick="togglePlay()">▶ 자동재생</button>
    <span id="speed-label">속도</span>
    <select id="speed-select" onchange="setSpeed(this.value)">
      <option value="1200">0.5×</option>
      <option value="800">0.75×</option>
      <option value="500" selected>1×</option>
      <option value="300">2×</option>
      <option value="150">4×</option>
    </select>
  </div>
</div>

<script>
// ─── 다중 시나리오 데이터 임베드 ──────────────────────────────────
const ALL_SCENARIOS = {all_scen_js};
let curScenario = 0;
let TURNS = ALL_SCENARIOS[0].turns;

// ─── 상태 ──────────────────────────────────────────────────────
let curIdx = 0;
let playInterval = null;
let playSpeed = 500;

// ─── 유틸 ──────────────────────────────────────────────────────
const EL_CLASS = {{ fire:'el-fire', water:'el-water', forest:'el-forest', light:'el-light', dark:'el-dark' }};
const ROLE_KO = {{ attacker:'딜', defender:'탱', magician:'마법', supporter:'서포', healer:'힐' }};
const EVENT_ICON = {{
  damage:'🗡', heal:'💚', buff:'🔵', debuff:'🟡', death:'💀',
  revive:'✨', sp:'💎', ultimate:'💥', taunt:'🛡',
}};
const EVENT_CLASS = {{
  damage:'ev-dmg', heal:'ev-heal', buff:'ev-buff', debuff:'ev-debuff',
  death:'ev-death', revive:'ev-ult', sp:'ev-sp', ultimate:'ev-ult', taunt:'ev-buff',
}};

function hpColor(ratio, side) {{
  if (ratio > 0.5) return side === 'ally' ? 'var(--ally)' : 'var(--enemy)';
  if (ratio > 0.25) return 'var(--ally-low)';
  return '#da3633';
}}

function escHtml(s) {{
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}}

// ─── 시나리오 전환 ──────────────────────────────────────────────
function switchScenario(idx) {{
  if (ALL_SCENARIOS[idx] === undefined) return;
  curScenario = idx;
  TURNS = ALL_SCENARIOS[idx].turns;
  document.querySelectorAll('.scen-tab').forEach((btn, i) => {{
    btn.classList.toggle('active', i === idx);
  }});
  document.getElementById('header-title').textContent = '⚔️ CTB 배틀 리플레이  |  ' + ALL_SCENARIOS[idx].label;
  document.getElementById('overlay').classList.remove('show');
  if (playInterval) {{
    clearInterval(playInterval);
    playInterval = null;
    document.getElementById('btn-play').textContent = '▶ 자동재생';
    document.getElementById('btn-play').classList.remove('active');
  }}
  const slider = document.getElementById('turn-slider');
  slider.max = TURNS.length - 1;
  slider.value = 0;
  document.getElementById('ti-total').textContent = TURNS.length;
  curIdx = 0;
  renderTurn(0);
}}

// ─── 유닛 카드 렌더 ────────────────────────────────────────────
function renderUnit(snap, activeId) {{
  const isActive = snap.id === activeId;
  const isDead   = !snap.is_alive;
  const hpRatio  = snap.hp_ratio;
  const barW     = (hpRatio * 100).toFixed(1) + '%';
  const barrW    = snap.max_hp > 0 ? ((snap.barrier_hp / snap.max_hp) * 100).toFixed(1) + '%' : '0%';
  const color    = hpColor(hpRatio, snap.side);
  const elCls    = EL_CLASS[snap.element] || '';
  const roleTxt  = ROLE_KO[snap.role] || snap.role;

  let badges = '';
  if (snap.cc)      badges += `<span class="badge badge-cc">⛔CC</span>`;
  if (snap.soft_cc) badges += `<span class="badge badge-cc">⚡소프트CC</span>`;
  if (snap.burn > 0) badges += `<span class="badge badge-burn">🔥화상×${{snap.burn}}</span>`;
  if (snap.cd > 0)   badges += `<span class="badge badge-cd">🕐CD ${{snap.cd}}</span>`;
  if (snap.used_ult) badges += `<span class="badge badge-ult">✨얼티밋사용</span>`;
  if (snap.buffs && snap.buffs.length > 0) {{
    snap.buffs.forEach(b => {{
      const cls = b.is_debuff ? 'badge-debuff' : 'badge-buff';
      const stackTxt = b.stack > 1 ? `×${{b.stack}}` : '';
      badges += `<span class="badge ${{cls}}">${{escHtml(b.name)}}${{stackTxt}}(${{b.remaining}})</span>`;
    }});
  }}

  return `
  <div class="unit-card${{isActive?' active-unit':''}}${{isDead?' dead':''}}" id="uc-${{snap.id}}">
    <div class="unit-top">
      <span class="unit-name">${{isDead?'💀 ':''}}${{escHtml(snap.name)}}</span>
      <span class="unit-role">${{roleTxt}}</span>
      <span class="unit-element ${{elCls}}">${{snap.element}}</span>
    </div>
    <div class="hp-row">
      <div class="hp-track">
        <div class="hp-fill" style="width:${{barW}};background:${{color}}"></div>
        ${{snap.barrier_hp > 0 ? `<div class="barrier-fill" style="width:${{barrW}}"></div>` : ''}}
      </div>
      <span class="hp-text">${{Math.round(snap.hp)}}/${{Math.round(snap.max_hp)}}</span>
    </div>
    ${{badges ? `<div class="unit-badges">${{badges}}</div>` : ''}}
  </div>`;
}}

// ─── CTB 칩 렌더 ───────────────────────────────────────────────
function renderCtbChips(turn) {{
  const chips = document.getElementById('ctb-chips');
  if (!chips) return;
  const units = turn.units;
  const allUnitIds = Object.keys(units);

  const alive = allUnitIds.filter(id => units[id].is_alive);
  const sorted = [turn.active, ...alive.filter(id => id !== turn.active)];

  let html = '';
  sorted.forEach((id, i) => {{
    const u = units[id];
    if (!u) return;
    const isActive = (id === turn.active && i === 0);
    const isExtra  = isActive && turn.extra;
    const sideCls  = u.side === 'ally' ? 'chip-ally' : 'chip-enemy';
    const chipCls  = isActive ? (isExtra ? 'ctb-chip extra' : 'ctb-chip active') : 'ctb-chip';
    html += `<div class="${{chipCls}}">
      <span class="chip-name ${{sideCls}}">${{isActive && isExtra ? '⚡' : isActive ? '★' : ''}}${{escHtml(u.name)}}</span>
      <span class="chip-t">${{(u.hp_ratio*100).toFixed(0)}}%HP</span>
    </div>`;
  }});
  chips.innerHTML = html;
}}

// ─── 이벤트 렌더 ───────────────────────────────────────────────
function renderEvents(events, units) {{
  const list = document.getElementById('events-list');
  if (!events || events.length === 0) {{
    list.innerHTML = '<div style="color:var(--muted);font-size:11px;">이벤트 없음</div>';
    return;
  }}
  let html = '';
  events.forEach(ev => {{
    const icon  = EVENT_ICON[ev.type] || '•';
    const cls   = EVENT_CLASS[ev.type] || '';
    const srcN  = units[ev.src]?.name || ev.src;
    const dstN  = units[ev.dst]?.name || ev.dst;
    const critTxt = ev.is_crit ? '<span class="ev-crit"> 크리!</span>' : '';
    const valTxt  = ev.value ? ` <b>${{ev.value.toLocaleString()}}</b>` : '';
    html += `<div class="event-item ${{cls}}">${{icon}} ${{escHtml(ev.label || (srcN + ' → ' + dstN))}}${{valTxt}}${{critTxt}}</div>`;
  }});
  list.innerHTML = html;
}}

// ─── 로그 렌더 ─────────────────────────────────────────────────
function renderLog(lines) {{
  const list = document.getElementById('log-list');
  if (!lines || lines.length === 0) {{
    list.innerHTML = '<div class="log-line" style="color:var(--muted)">로그 없음</div>';
    return;
  }}
  list.innerHTML = lines.map(l => `<div class="log-line">${{escHtml(l)}}</div>`).join('');
  list.scrollTop = list.scrollHeight;
}}

// ─── 메인 렌더 함수 ────────────────────────────────────────────
function renderTurn(idx) {{
  const turn = TURNS[idx];
  if (!turn) return;
  const units = turn.units;

  // 헤더
  document.getElementById('ti-cur').textContent    = turn.n;
  document.getElementById('ti-total').textContent  = TURNS.length;
  document.getElementById('ti-t').textContent      = turn.t.toFixed(2);
  document.getElementById('ti-r').textContent      = turn.round;
  const activeU = units[turn.active];
  document.getElementById('ti-who').textContent    = activeU ? activeU.name : turn.active;
  const extraEl = document.getElementById('ti-extra');
  extraEl.style.display = turn.extra ? 'inline' : 'none';
  document.getElementById('ti-skill').textContent  = turn.skill || '-';

  // 결과 배지
  const badge = document.getElementById('result-badge');
  badge.style.display = 'none';
  if (turn.result) {{
    badge.style.display = 'inline-block';
    if (turn.result === 'ally_win') {{
      badge.className = 'badge-win'; badge.textContent = '🏆 아군 승리';
    }} else if (turn.result === 'enemy_win') {{
      badge.className = 'badge-lose'; badge.textContent = '💀 적군 패배';
    }} else {{
      badge.className = 'badge-timeout'; badge.textContent = '⏰ 타임오버';
    }}
  }}

  // SP
  const sp_a = turn.ally_sp, sp_e = turn.enemy_sp;
  document.getElementById('sp-ally-fill').style.width  = (sp_a/10*100) + '%';
  document.getElementById('sp-enemy-fill').style.width = (sp_e/10*100) + '%';
  document.getElementById('sp-ally-num').textContent   = sp_a + '/10';
  document.getElementById('sp-enemy-num').textContent  = sp_e + '/10';

  // 유닛 카드
  const allySide  = document.getElementById('ally-units');
  const enemySide = document.getElementById('enemy-units');
  let allyHtml = '', enemyHtml = '';
  let aliveA = 0, aliveE = 0;
  Object.values(units).forEach(snap => {{
    if (snap.side === 'ally') {{
      allyHtml += renderUnit(snap, turn.active);
      if (snap.is_alive) aliveA++;
    }} else {{
      enemyHtml += renderUnit(snap, turn.active);
      if (snap.is_alive) aliveE++;
    }}
  }});
  allySide.innerHTML  = allyHtml;
  enemySide.innerHTML = enemyHtml;
  document.getElementById('ally-alive-count').textContent  = `생존 ${{aliveA}}`;
  document.getElementById('enemy-alive-count').textContent = `생존 ${{aliveE}}`;

  // CTB 칩
  renderCtbChips(turn);

  // 이벤트
  renderEvents(turn.events, units);

  // 로그
  renderLog(turn.log);

  // 슬라이더
  document.getElementById('turn-slider').value = idx;

  // 버튼 상태
  document.getElementById('btn-first').disabled = (idx === 0);
  document.getElementById('btn-prev').disabled  = (idx === 0);
  document.getElementById('btn-next').disabled  = (idx === TURNS.length - 1);
  document.getElementById('btn-last').disabled  = (idx === TURNS.length - 1);

  // 최후 턴 오버레이
  if (turn.result && idx === TURNS.length - 1) {{
    const ot = document.getElementById('overlay-title');
    const os = document.getElementById('overlay-sub');
    if (turn.result === 'ally_win') {{ ot.textContent = '🏆 아군 승리!'; ot.style.color = 'var(--green)'; }}
    else if (turn.result === 'enemy_win') {{ ot.textContent = '💀 전멸...'; ot.style.color = 'var(--enemy)'; }}
    else {{ ot.textContent = '⏰ 타임오버'; ot.style.color = 'var(--yellow)'; }}
    os.textContent = `총 ${{TURNS.length}}턴 | 타임라인 t=${{turn.t.toFixed(2)}}`;
    document.getElementById('overlay').classList.add('show');
  }}
}}

// ─── 턴 이동 ───────────────────────────────────────────────────
function goTurn(idx) {{
  idx = Math.max(0, Math.min(TURNS.length - 1, idx));
  curIdx = idx;
  renderTurn(curIdx);
}}

// ─── 자동재생 ──────────────────────────────────────────────────
function togglePlay() {{
  const btn = document.getElementById('btn-play');
  if (playInterval) {{
    clearInterval(playInterval);
    playInterval = null;
    btn.textContent = '▶ 자동재생';
    btn.classList.remove('active');
  }} else {{
    btn.textContent = '⏸ 일시정지';
    btn.classList.add('active');
    playInterval = setInterval(() => {{
      if (curIdx >= TURNS.length - 1) {{
        togglePlay();
        return;
      }}
      goTurn(curIdx + 1);
    }}, playSpeed);
  }}
}}

function setSpeed(ms) {{
  playSpeed = parseInt(ms);
  if (playInterval) {{
    clearInterval(playInterval);
    playInterval = setInterval(() => {{
      if (curIdx >= TURNS.length - 1) {{ togglePlay(); return; }}
      goTurn(curIdx + 1);
    }}, playSpeed);
  }}
}}

// ─── 키보드 단축키 ─────────────────────────────────────────────
document.addEventListener('keydown', e => {{
  if (e.key === 'ArrowRight' || e.key === 'ArrowDown') goTurn(curIdx + 1);
  else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') goTurn(curIdx - 1);
  else if (e.key === ' ') {{ e.preventDefault(); togglePlay(); }}
  else if (e.key === 'Home') goTurn(0);
  else if (e.key === 'End')  goTurn(TURNS.length - 1);
}});

// ─── 초기화 ────────────────────────────────────────────────────
(function init() {{
  const slider = document.getElementById('turn-slider');
  slider.max = TURNS.length - 1;
  document.getElementById('ti-total').textContent = TURNS.length;
  document.getElementById('header-title').textContent = '⚔️ CTB 배틀 리플레이  |  ' + ALL_SCENARIOS[0].label;
  goTurn(0);
}})();
</script>
</body>
</html>"""


def generate_html(battle_data: dict, scenario_label: str = "") -> str:
    """단일 시나리오용 (하위호환)"""
    label = scenario_label or battle_data.get("scenario", "Battle Replay")
    return generate_multi_html([battle_data], [label])
