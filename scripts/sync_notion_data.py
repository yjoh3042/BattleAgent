"""
Sync _all_chars.json with Notion '수정버전 3차' reclassification data.
Updates element, role, spd, sp for each character based on the Notion mapping.
"""
import json
import sys
from pathlib import Path

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "_all_chars.json"

# Role defaults from rules.py
ROLE_SPD = {
    "ATTACKER": 80,
    "HEALER": 90,
    "MAGICIAN": 100,
    "DEFENDER": 110,
    "SUPPORTER": 120,
}
ROLE_SP = {
    "ATTACKER": 6,
    "HEALER": 3,
    "MAGICIAN": 4,
    "DEFENDER": 3,
    "SUPPORTER": 4,
}

# Korean -> English mappings
ROLE_MAP = {
    "공격": "ATTACKER",
    "방어": "DEFENDER",
    "회복": "HEALER",
    "구속": "MAGICIAN",
    "보조": "SUPPORTER",
}
ELEM_MAP = {
    "화": "FIRE",
    "수": "WATER",
    "목": "FOREST",
    "광": "LIGHT",
    "암": "DARK",
}

# Element sort order
ELEM_ORDER = ["FIRE", "WATER", "FOREST", "LIGHT", "DARK"]
ROLE_ORDER = ["ATTACKER", "MAGICIAN", "HEALER", "DEFENDER", "SUPPORTER"]

# Complete Notion reclassification: (vidx, korean_element, korean_role)
NOTION_RAW = """
c028/광/보조, c033/목/구속, c286/화/회복, c035/암/보조, c022/수/구속,
c366/수/방어, c031/목/회복, c037/화/방어, c362/수/보조, c353/광/방어,
c062/목/공격, c083/화/공격, c064/암/공격, c221/광/공격, c048/암/회복,
c354/화/보조, c180/목/방어, c398/목/보조, c183/광/회복, c514/암/구속,
c437/수/회복, c003/화/구속, c227/광/구속, c296/광/공격, c193/수/공격,
c001/암/방어, c132/목/공격, c156/암/공격, c412/화/공격, c002/수/공격,
c448/암/회복, c468/목/방어, c400/암/구속, c429/화/회복, c533/광/보조,
c167/수/보조, c417/화/구속, c438/광/구속, c339/화/구속, c445/화/공격,
c462/화/방어, c486/암/공격, c318/수/구속, c442/수/공격, c194/광/공격,
c124/수/공격, c283/화/구속, c461/목/보조, c051/암/방어, c294/암/보조,
c562/화/보조, c229/목/회복, c281/수/회복, c473/광/방어, c537/수/방어,
c502/수/구속, c485/암/보조, c432/암/구속, c393/광/방어, c336/목/구속,
c447/목/공격, c525/목/보조, c549/목/공격, c364/광/보조, c455/광/회복,
c501/화/공격, c464/수/보조, c601/목/구속, c600/광/구속, c532/암/공격
"""

def parse_notion_mapping(raw: str) -> dict:
    """Parse the raw Notion data into {vidx: (element, role)} dict."""
    mapping = {}
    for token in raw.replace("\n", " ").split(","):
        token = token.strip()
        if not token:
            continue
        parts = token.split("/")
        if len(parts) != 3:
            print(f"WARNING: Skipping malformed token: {token!r}")
            continue
        vidx, kr_elem, kr_role = parts
        vidx = vidx.strip()
        elem = ELEM_MAP.get(kr_elem.strip())
        role = ROLE_MAP.get(kr_role.strip())
        if not elem or not role:
            print(f"WARNING: Unknown elem/role in {token!r}")
            continue
        mapping[vidx] = (elem, role)
    return mapping


def main():
    # Load current data
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        chars = json.load(f)

    notion = parse_notion_mapping(NOTION_RAW)
    print(f"Notion mapping: {len(notion)} characters")
    print(f"JSON has: {len(chars)} characters")

    changes = []
    not_in_notion = []

    for ch in chars:
        vid = ch["id"]
        if vid not in notion:
            not_in_notion.append(vid)
            continue

        new_elem, new_role = notion[vid]
        old_elem = ch["element"]
        old_role = ch["role"]

        elem_changed = old_elem != new_elem
        role_changed = old_role != new_role

        if elem_changed or role_changed:
            desc = f"{vid} ({ch['name']}): "
            parts = []
            if elem_changed:
                parts.append(f"element {old_elem}->{new_elem}")
                ch["element"] = new_elem
            if role_changed:
                old_spd, old_sp = ch["spd"], ch["sp"]
                ch["role"] = new_role
                ch["spd"] = ROLE_SPD[new_role]
                ch["sp"] = ROLE_SP[new_role]
                parts.append(f"role {old_role}->{new_role}")
                parts.append(f"spd {old_spd}->{ch['spd']}")
                parts.append(f"sp {old_sp}->{ch['sp']}")
            desc += ", ".join(parts)
            changes.append(desc)

    # Sort: element order, then role order within element
    chars.sort(key=lambda c: (
        ELEM_ORDER.index(c["element"]),
        ROLE_ORDER.index(c["role"]),
        c["id"],
    ))

    # Write back
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(chars, f, ensure_ascii=False, indent=1)

    # Summary
    print(f"\n=== Changes Summary ({len(changes)} characters changed) ===")
    for c in changes:
        print(f"  {c}")

    if not_in_notion:
        print(f"\n=== Not in Notion mapping ({len(not_in_notion)}) ===")
        for v in not_in_notion:
            print(f"  {v}")

    print(f"\nTotal characters in output: {len(chars)}")
    print("Done. File written to:", DATA_PATH)


if __name__ == "__main__":
    main()
