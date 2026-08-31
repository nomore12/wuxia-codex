#!/usr/bin/env python3
"""
명칭 색인 조회기.

canon/명칭색인.md는 800줄이 넘는다. **전문을 읽지 말고 이것으로 조회한다.**

사용법:
    python scripts/check_name.py 매화검법                  # 단일 조회
    python scripts/check_name.py 매화검법 자하신공 삼재검법  # 여럿 한 번에
    python scripts/check_name.py --like 매화               # 이름에 든 말로 찾기
    python scripts/check_name.py --hanja 梅花              # 한자 글자로 찾기
    python scripts/check_name.py --sect sorim              # 한 세력의 어휘
    python scripts/check_name.py --sect mudang cheongseong # 여러 세력 + 한자 겹침

종료 코드: 0 정상 / 1 색인을 읽지 못함
"""

from __future__ import annotations

import argparse
import sys
from collections import defaultdict
from pathlib import Path

from build_index import FACTIONS_DIR, INDEX_PATH, Row, is_separator, parse_row

COLUMNS = ["명칭", "한자", "origin", "세력", "sect_id", "층", "분류"]


def load() -> list[Row]:
    """색인에서 행을 읽는다. 읽지 못하면 종료한다."""
    if not INDEX_PATH.exists():
        print(f"색인이 없다: {INDEX_PATH}", file=sys.stderr)
        print("python scripts/build_index.py 를 먼저 실행할 것.", file=sys.stderr)
        raise SystemExit(1)

    rows: list[Row] = []
    seen_header = False
    for line in INDEX_PATH.read_text(encoding="utf-8").splitlines():
        if not line.startswith("| "):
            continue
        cells = parse_row(line)
        if is_separator(cells):
            continue
        if cells[: len(COLUMNS)] == COLUMNS:
            seen_header = True
            continue
        if not seen_header or len(cells) != len(COLUMNS):
            continue
        rows.append(Row(*cells))

    if not seen_header:
        print(f"색인에 표 헤더가 없다: {INDEX_PATH}", file=sys.stderr)
        print("python scripts/build_index.py 를 먼저 실행할 것.", file=sys.stderr)
        raise SystemExit(1)
    return rows


def warn_if_stale() -> None:
    """색인이 세력 문서보다 오래되었으면 알린다. validate.py와 같은 방식."""
    if not FACTIONS_DIR.exists():
        return
    newest = max((p.stat().st_mtime for p in FACTIONS_DIR.glob("*.md")), default=0)
    if newest > INDEX_PATH.stat().st_mtime:
        print("경고  색인이 세력 문서보다 오래되었다 — build_index.py를 실행할 것",
              file=sys.stderr)


def line_of(r: Row) -> str:
    """한 항목을 한 줄로. 심법은 층과 분류가 같으므로 한 번만 적는다."""
    layer = r.layer if r.layer == r.kind else f"{r.layer} · {r.kind}"
    return f"  {r.sect_name} {r.sect_id} · {layer} · {r.origin}"


def cmd_lookup(rows: list[Row], names: list[str]) -> None:
    by_name: dict[str, list[Row]] = defaultdict(list)
    for r in rows:
        by_name[r.name].append(r)

    for name in names:
        hits = by_name.get(name, [])
        if not hits:
            print(f"{name} — 없음")
            continue
        hanja = hits[0].hanja
        mark = "" if len(hits) == 1 else f" · {len(hits)}개 세력"
        print(f"{name} ({hanja}) — 있음{mark}")
        for r in hits:
            print(line_of(r))


def cmd_like(rows: list[Row], word: str) -> None:
    hits = [r for r in rows if word in r.name]
    if not hits:
        print(f"이름에 「{word}」가 든 항목 — 없음")
        return
    print(f"이름에 「{word}」가 든 항목 {len(hits)}개")
    for r in sorted(hits, key=lambda r: (r.sect_id, r.layer, r.kind, r.name)):
        print(f"  {r.name} ({r.hanja}) · {r.sect_name} {r.sect_id} · {r.origin}")


def cmd_hanja(rows: list[Row], chars: str) -> None:
    for ch in dict.fromkeys(chars):          # 중복 글자 제거, 순서 유지
        hits = [r for r in rows if ch in r.hanja]
        if not hits:
            print(f"{ch} — 없음")
            continue
        sects = sorted({r.sect_id for r in hits})
        print(f"{ch} — {len(hits)}개 · 세력 {len(sects)}")
        for r in sorted(hits, key=lambda r: (r.sect_id, r.name)):
            print(f"  {r.name} ({r.hanja}) · {r.sect_id} · {r.origin}")


def cmd_sect(rows: list[Row], sect_ids: list[str]) -> None:
    known = {r.sect_id for r in rows}
    for sid in sect_ids:
        mine = [r for r in rows if r.sect_id == sid]
        if not mine:
            hint = "" if sid in known else "  (색인에 없는 sect_id)"
            print(f"{sid} — 항목 없음{hint}")
            continue
        print(f"{sid} {mine[0].sect_name} · {len(mine)}개")
        grouped: dict[tuple[str, str], list[Row]] = defaultdict(list)
        for r in mine:
            grouped[(r.layer, r.kind)].append(r)
        for (layer, kind), items in sorted(grouped.items()):
            label = layer if layer == kind else f"{layer}·{kind}"
            names = " ".join(r.name for r in sorted(items, key=lambda r: r.name))
            print(f"  {label} {len(items)}  {names}")

    if len(sect_ids) < 2:
        return

    # 한자 겹침 — 요청한 세력 둘 이상이 같은 글자를 쓰는 경우
    per_char: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for r in rows:
        if r.sect_id not in sect_ids:
            continue
        for ch in dict.fromkeys(r.hanja):
            per_char[ch][r.sect_id] += 1

    shared = {c: d for c, d in per_char.items() if len(d) >= 2}
    print(f"\n한자 겹침 — {len(shared)}자가 둘 이상의 세력에 있다")
    if not shared:
        return
    ordered = sorted(shared.items(), key=lambda kv: (-len(kv[1]), -sum(kv[1].values()), kv[0]))
    for ch, d in ordered:
        counts = " ".join(f"{s}({d[s]})" for s in sect_ids if s in d)
        print(f"  {ch}  {counts}")


def main() -> int:
    ap = argparse.ArgumentParser(
        description="명칭 색인 조회. 색인 전문을 읽지 않기 위한 도구다.",
        add_help=True,
    )
    ap.add_argument("names", nargs="*", help="조회할 명칭(들)")
    ap.add_argument("--like", metavar="말", help="이름에 그 말이 든 항목")
    ap.add_argument("--hanja", metavar="글자", help="한자에 그 글자가 든 항목. 여러 글자면 각각 낸다")
    ap.add_argument("--sect", nargs="+", metavar="sect_id", help="세력의 전 항목. 둘 이상이면 한자 겹침도 낸다")
    args = ap.parse_args()

    if not (args.names or args.like or args.hanja or args.sect):
        ap.print_help()
        return 0

    rows = load()
    warn_if_stale()

    if args.sect:
        cmd_sect(rows, args.sect)
    if args.hanja:
        cmd_hanja(rows, args.hanja)
    if args.like:
        cmd_like(rows, args.like)
    if args.names:
        cmd_lookup(rows, args.names)
    return 0


if __name__ == "__main__":
    sys.exit(main())
