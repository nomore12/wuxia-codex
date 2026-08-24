#!/usr/bin/env python3
"""
무공·심법 색인 생성기.

drafts/factions/ 아래 모든 세력 문서를 훑어 canon/무공색인.md를 다시 만든다.
색인은 **손으로 관리하지 않는다.** 항상 이 스크립트로 재생성한다.

사용법:
    python scripts/build_index.py              # 재생성
    python scripts/build_index.py --check      # 변경 여부만 확인 (쓰지 않음)
    python scripts/build_index.py --dry-run    # 결과를 표준출력으로

색인은 canon/ 아래에 있으나 **기계가 관리하는 파일**이므로,
이 스크립트를 통한 갱신은 "canon 수정 금지" 규칙의 예외다.
그 외의 방법으로 색인을 편집하지 않는다.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FACTIONS_DIR = ROOT / "drafts" / "factions"
INDEX_PATH = ROOT / "canon" / "무공색인.md"

HEADER = """---
doc_type: canon
status: 확정
scope: 전 세력의 무공·심법 색인. 중복 방지와 공통 무공 참조에 쓴다
generated_by: scripts/build_index.py
---

# 무공·심법 색인

> **이 파일은 자동 생성된다. 손으로 편집하지 않는다.**
> 세력 문서를 고친 뒤 `python scripts/build_index.py`를 실행한다.

세력 문서를 작성하기 **전에 반드시 조회한다.**

| 상황 | 처리 |
|---|---|
| 기존 **관용·전승** 명칭과 겹침 | 공통 무공으로 참조. 비고에 「여러 문파에 공통」 |
| 기존 **창작** 명칭과 겹침 | **다른 이름을 쓴다** |
| 같은 이름이 다른 세력에 있음 | 임의로 결정하지 말고 보고 |

`세력` 열은 사람이 읽기 위한 것이고, 대조에 쓰이는 것은 `sect_id` 열이다.

"""


@dataclass
class Row:
    name: str
    hanja: str
    origin: str
    sect_name: str
    sect_id: str
    kind: str


def parse_row(line: str) -> list[str]:
    return [c.strip() for c in line.strip().strip("|").split("|")]


def is_separator(cells: list[str]) -> bool:
    return all(re.fullmatch(r":?-{2,}:?", c) for c in cells if c)


def read_faction(path: Path) -> tuple[list[Row], list[str]]:
    """세력 문서 하나에서 항목을 추출한다. (행 목록, 경고 목록)"""
    warns: list[str] = []
    text = path.read_text(encoding="utf-8")

    m = re.match(r"\A---\n(.*?)\n---\n", text, re.S)
    if not m:
        return [], [f"{path.name}: frontmatter가 없다"]

    meta = {}
    for line in m.group(1).split("\n"):
        if ":" in line and not line.startswith(" "):
            k, _, v = line.partition(":")
            meta[k.strip()] = v.strip()

    sect_id = meta.get("sect_id", "")
    if not sect_id:
        return [], [f"{path.name}: sect_id가 없다"]

    body = text[m.end():]

    # 세력명: 첫 H1에서 한자 괄호를 뺀 것. 없으면 파일명.
    h1 = re.search(r"^# (.+)$", body, re.M)
    sect_name = re.sub(r"\s*\(.*?\)\s*", "", h1.group(1)).strip() if h1 else path.stem

    rows: list[Row] = []
    kind = "?"
    in_table = False

    for raw in body.split("\n"):
        line = raw.strip()

        if line.startswith("#"):
            kind = re.sub(r"\s*\(.*?\)\s*", "", line.lstrip("#").strip()).strip()
            in_table = False
            continue

        if not line.startswith("|"):
            in_table = False
            continue

        cells = parse_row(line)

        if cells[:1] == ["명칭"]:
            in_table = "origin" in cells
            continue

        if is_separator(cells) or not in_table or len(cells) < 3:
            continue

        name = re.sub(r"\*\*|\[대표\]", "", cells[0]).strip()
        rows.append(Row(name, cells[1], cells[2], sect_name, sect_id, kind))

    if not rows:
        warns.append(f"{path.name}: 수집된 항목이 없다")
    return rows, warns


def build() -> tuple[str, list[str], list[Row], list[str]]:
    if not FACTIONS_DIR.exists():
        return HEADER, [f"{FACTIONS_DIR} 없음"], [], []

    rows: list[Row] = []
    warns: list[str] = []
    errors: list[str] = []
    for p in sorted(FACTIONS_DIR.glob("*.md")):
        r, w = read_faction(p)
        rows.extend(r)
        warns.extend(w)

    # 같은 명칭이 여러 세력에 있는 경우를 알린다
    by_name: dict[str, list[Row]] = {}
    for r in rows:
        by_name.setdefault(r.name, []).append(r)
    for name, group in by_name.items():
        sects = {g.sect_id for g in group}
        if len(sects) > 1:
            origins = {g.origin for g in group}
            if "창작" in origins:
                errors.append(f"창작 명칭 중복: {name} — {', '.join(sorted(sects))}")
            else:
                warns.append(f"공통 무공: {name} — {', '.join(sorted(sects))}")

    rows.sort(key=lambda r: (r.sect_id, r.kind, r.name))

    lines = [HEADER.rstrip("\n"), ""]
    lines.append("| 명칭 | 한자 | origin | 세력 | sect_id | 분류 |")
    lines.append("|---|---|---|---|---|---|")
    for r in rows:
        lines.append(
            f"| {r.name} | {r.hanja} | {r.origin} | {r.sect_name} | {r.sect_id} | {r.kind} |"
        )
    lines.append("")
    return "\n".join(lines), warns, rows, errors


def main() -> int:
    ap = argparse.ArgumentParser(description="무공·심법 색인 생성")
    ap.add_argument("--check", action="store_true", help="변경 여부만 확인")
    ap.add_argument("--dry-run", action="store_true", help="표준출력으로만")
    args = ap.parse_args()

    content, warns, rows, errors = build()

    for w in warns:
        print(f"  경고  {w}", file=sys.stderr)
    for e in errors:
        print(f"  오류  {e}", file=sys.stderr)

    if args.dry_run:
        print(content)
        return 0

    old = INDEX_PATH.read_text(encoding="utf-8") if INDEX_PATH.exists() else ""

    if args.check:
        if old == content:
            print("색인이 최신이다.")
            return 0
        print("색인이 최신이 아니다. build_index.py를 실행할 것.", file=sys.stderr)
        return 1

    INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    INDEX_PATH.write_text(content, encoding="utf-8")

    sects = len({r.sect_id for r in rows})
    status = "변경 없음" if old == content else "갱신"
    print(f"{INDEX_PATH.relative_to(ROOT)} {status} — 세력 {sects}개 · 항목 {len(rows)}개")

    if errors:
        print(f"\n창작 명칭 중복 {len(errors)}건. 이름을 바꾸거나 origin을 고칠 것.",
              file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
