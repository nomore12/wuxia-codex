#!/usr/bin/env python3
"""간지 검산 — 서력과 간지가 맞는지 대조한다.

  python3 scripts/check_ganji.py              # drafts/연표.md 의 표를 검사
  python3 scripts/check_ganji.py --year 1042  # 서력 하나의 간지를 구한다

연호를 쓰지 않기로 한 결정에 딸린 검사기다. docs/intent/0002
"""
import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
YEONPYO = ROOT / "drafts" / "연표.md"

CHEON, JI = "갑을병정무기경신임계", "자축인묘진사오미신유술해"
CHEON_H, JI_H = "甲乙丙丁戊己庚辛壬癸", "子丑寅卯辰巳午未申酉戌亥"


def ganji(y: int) -> str:
    return CHEON[(y - 4) % 10] + JI[(y - 4) % 12]


def ganji_h(y: int) -> str:
    return CHEON_H[(y - 4) % 10] + JI_H[(y - 4) % 12]


ALL = {ganji(y) for y in range(4, 64)}          # 60간지
PAIR = re.compile(r"([가-힣]{2})\(([一-鿿]{2})\)")
YEAR = re.compile(r"(\d{2,4})년?")


def check(path: Path) -> int:
    bad = seen = 0
    for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.lstrip().startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        for i, cell in enumerate(cells):
            for m in PAIR.finditer(cell):
                kr, hj = m.group(1), m.group(2)
                if kr not in ALL:               # 간지가 아닌 병기는 건너뛴다
                    continue
                src = YEAR.search(cell) or (YEAR.search(cells[i - 1]) if i else None)
                if not src:
                    continue
                seen += 1
                y = int(src.group(1))
                if (kr, hj) != (ganji(y), ganji_h(y)):
                    print(f"  오류 {path.name}:{n}  {y} → "
                          f"{ganji(y)}({ganji_h(y)}) 인데 {kr}({hj})라고 적혔다")
                    bad += 1
    print(f"{path} · 대조 {seen}건 · 어긋남 {bad}건")
    return 1 if bad else 0


def main() -> int:
    ap = argparse.ArgumentParser(description="간지 검산")
    ap.add_argument("--year", type=int, help="서력 하나의 간지를 구한다")
    ap.add_argument("targets", nargs="*", help="검사할 파일 (기본: drafts/연표.md)")
    a = ap.parse_args()
    if a.year is not None:
        print(f"{a.year} → {ganji(a.year)}({ganji_h(a.year)})")
        return 0
    return max(check(Path(t)) for t in (a.targets or [YEONPYO]))


if __name__ == "__main__":
    sys.exit(main())
