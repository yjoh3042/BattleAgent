#!/usr/bin/env python3
"""직업별 ATK/DEF/HP 스탯 평균값 규칙 검증 및 자동 수정 스크립트.

사용법:
    py -3 -X utf8 scripts/validate_role_stats.py          # 검증만
    py -3 -X utf8 scripts/validate_role_stats.py --fix     # 검증 + 자동 수정
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# ── 프로젝트 루트 → src 를 PYTHONPATH 에 추가 ──────────────
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from battle.enums import Role          # noqa: E402
from battle.rules import (            # noqa: E402
    ROLE_BASE_SPD,
    ROLE_BASE_SP,
    ROLE_BASE_ATK,
    ROLE_BASE_DEF,
    ROLE_BASE_HP,
)

DATA_PATH = ROOT / "data" / "_all_chars.json"

# _all_chars.json 의 role 문자열 → Role enum 매핑
ROLE_MAP: dict[str, Role] = {
    "ATTACKER":  Role.ATTACKER,
    "MAGICIAN":  Role.MAGICIAN,
    "DEFENDER":  Role.DEFENDER,
    "HEALER":    Role.HEALER,
    "SUPPORTER": Role.SUPPORTER,
}


def load_chars() -> list[dict]:
    with open(DATA_PATH, encoding="utf-8") as f:
        return json.load(f)


def save_chars(chars: list[dict]) -> None:
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(chars, f, ensure_ascii=False, indent=2)


class Violation:
    """스탯 규칙 위반 정보."""
    def __init__(self, char_name: str, char_id: str, role: str,
                 stat_name: str, current: int, expected: int):
        self.char_name = char_name
        self.char_id = char_id
        self.role = role
        self.stat_name = stat_name
        self.current = current
        self.expected = expected

    @property
    def delta(self) -> int:
        return self.expected - self.current


def validate_all(chars: list[dict], fix: bool = False) -> list[Violation]:
    """전체 캐릭터 검증. fix=True 이면 dict 를 직접 수정."""
    violations: list[Violation] = []

    for ch in chars:
        role_str = ch.get("role", "")
        role = ROLE_MAP.get(role_str)
        if role is None:
            print(f"  [WARN] 알 수 없는 역할: {ch['name']}({ch['id']}) role={role_str}")
            continue

        checks = [
            ("atk", "ATK", ROLE_BASE_ATK[role]),
            ("def", "DEF", ROLE_BASE_DEF[role]),
            ("hp",  "HP",  ROLE_BASE_HP[role]),
        ]

        for json_key, label, expected in checks:
            value = ch.get(json_key)
            if value is None:
                continue
            if value != expected:
                violations.append(Violation(
                    char_name=ch["name"],
                    char_id=ch["id"],
                    role=role_str,
                    stat_name=label,
                    current=value,
                    expected=expected,
                ))
                if fix:
                    ch[json_key] = expected

    return violations


def print_rules_table() -> None:
    """현재 규칙 테이블 출력."""
    print("=" * 70)
    print("  직업별 기본 스탯 규칙 (평균값)")
    print("=" * 70)
    print(f"  {'역할':<12} {'ATK':>6} {'DEF':>6} {'HP':>7} {'SPD':>5} {'SP':>4}")
    print("-" * 70)
    role_order = [Role.ATTACKER, Role.MAGICIAN, Role.DEFENDER, Role.HEALER, Role.SUPPORTER]
    for role in role_order:
        print(f"  {role.name:<12} {ROLE_BASE_ATK[role]:>6} {ROLE_BASE_DEF[role]:>6} "
              f"{ROLE_BASE_HP[role]:>7} {ROLE_BASE_SPD[role]:>5} {ROLE_BASE_SP[role]:>4}")
    print("=" * 70)


def print_violations(violations: list[Violation], fixed: bool) -> None:
    """위반 리포트 출력."""
    if not violations:
        print("\n  [OK] 모든 캐릭터가 역할별 기본 스탯 규칙을 준수합니다. (위반 0건)")
        return

    action = "수정됨" if fixed else "위반"
    print(f"\n  [{action.upper()}] 총 {len(violations)}건")
    print(f"  {'캐릭터':<12} {'역할':<12} {'스탯':<6} {'현재값':>6} {'기준값':>6} ", end="")
    if fixed:
        print(f"{'변동':>6}")
    else:
        print()
    print("-" * 60)
    for v in violations:
        line = f"  {v.char_name:<12} {v.role:<12} {v.stat_name:<6} {v.current:>6} {v.expected:>6} "
        if fixed:
            line += f"{v.delta:>+6}"
        print(line)
    print("-" * 60)


def print_summary(chars: list[dict]) -> None:
    """역할별 캐릭터 수 요약."""
    from collections import Counter
    roles = Counter(ch.get("role", "?") for ch in chars)
    print(f"\n  캐릭터 총 {len(chars)}명")
    for r, cnt in sorted(roles.items()):
        print(f"    {r}: {cnt}명")


def main() -> None:
    parser = argparse.ArgumentParser(description="직업별 스탯 평균값 규칙 검증")
    parser.add_argument("--fix", action="store_true", help="위반 스탯을 기준값으로 자동 수정")
    args = parser.parse_args()

    chars = load_chars()
    print_rules_table()
    print_summary(chars)

    violations = validate_all(chars, fix=args.fix)
    print_violations(violations, fixed=args.fix)

    if args.fix and violations:
        save_chars(chars)
        print(f"\n  [SAVE] {DATA_PATH.name} 저장 완료 ({len(violations)}건 수정)")

        # 수정 후 재검증
        chars2 = load_chars()
        v2 = validate_all(chars2, fix=False)
        if not v2:
            print("  [RE-VALIDATE] 재검증 통과 — 위반 0건")
        else:
            print(f"  [RE-VALIDATE] 아직 {len(v2)}건 위반 남음!")


if __name__ == "__main__":
    main()
