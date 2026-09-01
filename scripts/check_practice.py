#!/usr/bin/env python3
"""
습작 명칭 검사기.

습작을 쓰다 보면 새 명칭이 생긴다. 색인에 넣지 않으면 중복 검사에 걸리지 않고,
나중에 다른 세력이 같은 이름을 써도 잡지 못한다.

이 스크립트는 습작에서 무공 꼴의 말을 뽑아 색인과 대조한다.
**판정하지 않는다.** 후보를 내놓을 뿐이며, 무엇이 명칭인지는 사람이 정한다.

사용법:
    python scripts/check_practice.py drafts/writing-practice/.../귀도.md
    python scripts/check_practice.py --all        # drafts/writing-practice/ 전체

오탐이 반복되면 scripts/.practice_ignore에 한 줄씩 적는다.
**스크립트에 박지 않는다.**

종료 코드: 0 정상 / 1 색인을 읽지 못함
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from check_name import load

ROOT = Path(__file__).resolve().parent.parent
PRACTICE_DIR = ROOT / "drafts" / "writing-practice"
IGNORE_PATH = Path(__file__).resolve().parent / ".practice_ignore"

# 무공 명칭의 어미. 긴 것부터 본다 — 「검법」이 「검」보다 먼저 잡혀야 한다.
SUFFIXES = [
    "심결", "심법", "신공", "검법", "도법", "권법", "장법", "지법",
    "보법", "경공", "공", "결", "검", "도", "장", "지", "술", "진", "산", "단",
]
SUFFIXES.sort(key=len, reverse=True)

# 한 글자 어미는 흔한 말에도 붙는다 (수단·판단·유지·기술…).
# **어휘를 막지 않는다.** 길이 하한만 둔다 — 두 글자 말은 명칭이 되기 어렵다.
MIN_LEN_SHORT_SUFFIX = 3
MIN_LEN = 2

HANGUL = r"[가-힣]"
HANJA = r"[一-鿿]"
# 「단악참도법(斷岳斬刀法)」 · 「단악참도법 (斷岳斬刀法)」 · 「단악참도법」
TOKEN = re.compile(rf"({HANGUL}{{2,}})\s*(?:\(\s*({HANJA}{{2,}})\s*\))?")


def load_ignore() -> set[str]:
    if not IGNORE_PATH.exists():
        return set()
    out = set()
    for line in IGNORE_PATH.read_text(encoding="utf-8").splitlines():
        line = line.split("#", 1)[0].strip()
        if line:
            out.add(line)
    return out


def candidates(text: str) -> dict[str, str]:
    """무공 꼴로 끝나는 말을 뽑는다. {명칭: 한자 또는 ''}"""
    found: dict[str, str] = {}
    for m in TOKEN.finditer(text):
        name, hanja = m.group(1), m.group(2) or ""
        for suf in SUFFIXES:
            if not name.endswith(suf):
                continue
            floor = MIN_LEN_SHORT_SUFFIX if len(suf) == 1 else MIN_LEN
            if len(name) < floor or len(name) == len(suf):
                break
            # 한자를 한 번이라도 달고 나온 쪽을 남긴다
            if name not in found or (hanja and not found[name]):
                found[name] = hanja
            break
    return found


def collect(targets: list[str], use_all: bool) -> list[Path]:
    if use_all:
        return sorted(PRACTICE_DIR.rglob("*.md")) if PRACTICE_DIR.exists() else []
    paths: list[Path] = []
    for t in targets:
        p = Path(t)
        if p.is_dir():
            paths.extend(sorted(p.rglob("*.md")))
        elif p.exists():
            paths.append(p)
        else:
            print(f"경로 없음: {t}", file=sys.stderr)
    return paths


def main() -> int:
    ap = argparse.ArgumentParser(description="습작에서 새로 생긴 명칭을 찾는다")
    ap.add_argument("targets", nargs="*", help="습작 파일 또는 디렉토리")
    ap.add_argument("--all", action="store_true", help="drafts/writing-practice/ 전체")
    args = ap.parse_args()

    if not (args.targets or args.all):
        ap.print_help()
        return 0

    known = {r.name for r in load()}
    ignored = load_ignore()
    paths = collect(args.targets, args.all)
    if not paths:
        print("대상 문서가 없다.", file=sys.stderr)
        return 0

    total_missing = 0
    for path in paths:
        found = candidates(path.read_text(encoding="utf-8"))
        found = {n: h for n, h in found.items() if n not in ignored}
        missing = {n: h for n, h in found.items() if n not in known}
        present = sorted(n for n in found if n in known)

        print(f"\n{path.relative_to(ROOT)}")

        # 한자를 달고 나온 것은 거의 명칭이다. 그렇지 않은 것은 오탐이 섞인다.
        with_hanja = sorted(n for n, h in missing.items() if h)
        bare = sorted(n for n, h in missing.items() if not h)

        if with_hanja:
            print(f"\n  색인에 없다 · 한자가 붙어 있다 — {len(with_hanja)}")
            for n in with_hanja:
                print(f"    {n} ({missing[n]})")
        if bare:
            print(f"\n  색인에 없다 · 한자가 없다 — {len(bare)}  **오탐이 섞인다**")
            print("    " + " · ".join(bare))
        if not missing:
            print("\n  색인에 없는 것 — 없음")
        if present:
            print(f"\n  색인에 있다 — {len(present)}")
            print("    " + " · ".join(present))
        total_missing += len(missing)

    if total_missing:
        print(f"\n{'─' * 50}")
        print(f"색인에 없는 후보 {total_missing}개.")
        print("명칭이면 drafts/others/무소속.md에 넣고 build_index.py를 실행할 것.")
        print(f"명칭이 아니면 {IGNORE_PATH.relative_to(ROOT)}에 적을 것.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
