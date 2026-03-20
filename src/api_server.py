"""FastAPI backend for the Battle Simulator web UI."""
from __future__ import annotations

import copy
import inspect
import os
import sys
from typing import List, Optional

# Ensure src/ is on the path so battle.* and fixtures.* imports work
sys.path.insert(0, os.path.dirname(__file__))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from fixtures import test_data as td
from battle.battle_engine import BattleEngine
from battle.battle_recorder import BattleRecorder

# ─── App setup ───────────────────────────────────────────────────────────────

app = FastAPI(title="BattleAgent API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Character registry (built once at startup) ───────────────────────────────

CHAR_REGISTRY: dict = {}

for _name, _func in inspect.getmembers(td, inspect.isfunction):
    if _name.startswith("make_") and not _name.startswith("make_teddy"):
        try:
            _c = _func()
            if _c.side == "ally":
                CHAR_REGISTRY[_c.id] = _func
        except Exception:
            pass

# ─── Meta team definitions ────────────────────────────────────────────────────

META_TEAMS = {
    "M01": {"name": "화상연소", "desc": "🔥 Burn Stack + debuff_turn_inc", "fn": td.get_meta_burn_inferno},
    "M02": {"name": "빙결감옥", "desc": "🧊 FREEZE Chain + SP_LOCK",       "fn": td.get_meta_freeze_prison},
    "M03": {"name": "독정원",   "desc": "🌿 Poison + HoT Sustain",         "fn": td.get_meta_poison_garden},
    "M04": {"name": "하이퍼캐리","desc": "💎 Triple Buffer → Carry",        "fn": td.get_meta_hyper_carry},
    "M05": {"name": "철벽요새", "desc": "🛡️ Barrier + Revive",             "fn": td.get_meta_iron_fortress},
    "M06": {"name": "반격요새", "desc": "⚔️ Counter Cascade",              "fn": td.get_meta_counter_bruiser},
    "M07": {"name": "속도처형", "desc": "⚡ Speed → Execute",              "fn": td.get_meta_speed_execute},
    "M08": {"name": "암속강공", "desc": "🌙 Penetration + Bleed",          "fn": td.get_meta_dark_assault},
    "M09": {"name": "전멸폭격", "desc": "💥 AoE Cleave + Poison",          "fn": td.get_meta_aoe_cleave},
    "M10": {"name": "광전사",   "desc": "⚔️ Self-buff + ON_KILL",          "fn": td.get_meta_berserker},
    "M11": {"name": "광속성벽", "desc": "✨ Debuff Immune + Barrier",      "fn": td.get_meta_holy_bastion},
    "M12": {"name": "CC킬체인", "desc": "🎭 CC Relay → Kill",              "fn": td.get_meta_cc_kill_chain},
}

# ─── Cached character list (from _all_chars.json + passive from test_data) ────

import json as _json

def _load_char_list() -> List[dict]:
    """_all_chars.json 기반 캐릭터 목록 생성. 패시브 이름은 test_data에서 보충."""
    json_path = os.path.join(os.path.dirname(__file__), "..", "data", "_all_chars.json")
    with open(json_path, encoding="utf-8") as f:
        raw_chars = _json.load(f)

    # test_data에서 패시브 스킬 이름 매핑
    passive_names = {}
    for cid, factory in CHAR_REGISTRY.items():
        try:
            c = factory()
            if c.passive_skill:
                passive_names[cid] = c.passive_skill.name
        except Exception:
            pass

    result = []
    for rc in raw_chars:
        cid = rc["id"]
        if cid not in CHAR_REGISTRY:
            continue
        result.append({
            "id": cid,
            "name": rc["name"],
            "element": rc["element"].lower(),
            "role": rc["role"].lower(),
            "star": (lambda g: str(g) if g != int(g) else str(int(g)))(rc.get("grade", 3)),
            "stats": {
                "atk": rc["atk"],
                "def": rc["def"],
                "hp": rc["hp"],
                "spd": rc["spd"],
            },
            "skills": {
                "normal": rc["normal"]["name"],
                "active": rc["active"]["name"],
                "ultimate": rc["ultimate"]["name"],
                "passive": passive_names.get(cid),
            },
        })
    return result


_CHAR_LIST_CACHE: List[dict] = _load_char_list()


def _get_char_list() -> List[dict]:
    return _CHAR_LIST_CACHE

# ─── Enemy team helper ────────────────────────────────────────────────────────

def _make_enemy_team(characters):
    enemies = []
    for c in characters:
        ec = copy.deepcopy(c)
        ec.id = ec.id + "_e"
        ec.side = "enemy"
        skills = [ec.normal_skill, ec.active_skill, ec.ultimate_skill]
        if ec.passive_skill:
            skills.append(ec.passive_skill)
        for skill in skills:
            skill.id = skill.id + "_e"
            for eff in skill.effects:
                if eff.buff_data:
                    eff.buff_data.id = eff.buff_data.id + "_e"
                    eff.buff_data.source_skill_id = eff.buff_data.source_skill_id + "_e"
        for trigger in ec.triggers:
            if trigger.skill_id:
                trigger.skill_id = trigger.skill_id + "_e"
        enemies.append(ec)
    return enemies

# ─── Request/response models ──────────────────────────────────────────────────

class BattleRequest(BaseModel):
    ally_ids: List[str]
    enemy_ids: List[str]
    seed: int = 42
    deck_type: str = "offense"

# ─── Endpoints ────────────────────────────────────────────────────────────────

@app.get("/api/characters")
def get_characters():
    """Return all ally characters."""
    return _get_char_list()


@app.get("/api/meta-teams")
def get_meta_teams():
    """Return 12 meta team presets."""
    result = []
    for team_id, info in META_TEAMS.items():
        try:
            chars = info["fn"]()
            char_ids = [c.id for c in chars]
        except Exception:
            char_ids = []
        result.append({
            "id": team_id,
            "name": info["name"],
            "description": info["desc"],
            "character_ids": char_ids,
        })
    return result


@app.post("/api/battle")
def run_battle(req: BattleRequest):
    """Execute a battle and return turn-by-turn data."""
    # Resolve ally characters
    missing_ally = [cid for cid in req.ally_ids if cid not in CHAR_REGISTRY]
    if missing_ally:
        raise HTTPException(status_code=404, detail=f"Unknown ally character IDs: {missing_ally}")

    missing_enemy = [cid for cid in req.enemy_ids if cid not in CHAR_REGISTRY]
    if missing_enemy:
        raise HTTPException(status_code=404, detail=f"Unknown enemy character IDs: {missing_enemy}")

    allies = [CHAR_REGISTRY[cid]() for cid in req.ally_ids]
    enemy_templates = [CHAR_REGISTRY[cid]() for cid in req.enemy_ids]
    enemies = _make_enemy_team(enemy_templates)

    recorder = BattleRecorder()
    engine = BattleEngine(
        ally_units=allies,
        enemy_units=enemies,
        recorder=recorder,
        seed=req.seed,
        deck_type=req.deck_type,
    )
    result = engine.run()

    data = recorder.to_dict()

    def _unit_summary(units):
        return [
            {
                "id": u.id,
                "name": u.name,
                "is_alive": u.is_alive,
                "hp": round(u.current_hp, 1),
                "max_hp": u.max_hp,
            }
            for u in units
        ]

    return {
        "result": result.value if hasattr(result, "value") else str(result),
        "turn_count": len(recorder.records),
        "turns": data,
        "allies": _unit_summary(engine.allies),
        "enemies": _unit_summary(engine.enemies),
    }


# ─── Static files & root ──────────────────────────────────────────────────────

_WEB_DIR = os.path.join(os.path.dirname(__file__), "..", "web")

if os.path.isdir(_WEB_DIR):
    @app.get("/")
    def root():
        html_path = os.path.join(_WEB_DIR, "battle_simulator.html")
        return FileResponse(html_path, headers={"Cache-Control": "no-cache, no-store, must-revalidate"})

    app.mount("/static", StaticFiles(directory=_WEB_DIR), name="web")
