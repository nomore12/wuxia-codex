#!/usr/bin/env python3
"""
세력 문서 검증기.

사용법:
    python scripts/validate.py drafts/factions/화산파.md
    python scripts/validate.py drafts/factions/          # 디렉토리 전체
    python scripts/validate.py --all                     # drafts/factions/ 전체

종료 코드: 0 통과 / 1 오류 있음
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

from build_index import is_current

ROOT = Path(__file__).resolve().parent.parent
INDEX_PATH = ROOT / "canon" / "명칭색인.md"
VARIANCE_PATH = ROOT / "specs" / "세력별_차별화지시.md"

# ── 세계관 금지 규칙 ────────────────────────────────────────────────
# 기(氣)는 이 세계에 실체로 존재하지 않는다. canon/body-and-mind/05_힘.md
FORBIDDEN_HANJA = {
    "氣": "기(氣)는 실체로 존재하지 않는다",
    "罡": "강기(罡氣) 계열 표현",
}
FORBIDDEN_HANGUL = {
    "진기": "기(氣)를 실체로 다루는 표현",
    "내공심법": "심법으로 표기한다",
}
# 동음이의어라 문맥 판단이 필요하다. 명칭 열에서만 오류, 산문에서는 경고.
#   내력(內力) = 금지 / 내력(來歷) = 유래. 무방하다
AMBIGUOUS_HANGUL = {
    "내력": "내력(內力)이면 금지. 내력(來歷)이면 무방",
}
# 공인 등급표는 존재하지 않는다. canon/body-and-mind/08_별호와평판.md
FORBIDDEN_TIERS = [
    "삼류", "이류", "일류", "절정", "초절정", "화경", "현경", "생사경",
]

VALID_ORIGINS = {"전승", "관용", "창작"}

# 세력 문서의 최상위 절(## )이 그 항목의 층을 정한다. canon/body-and-mind/06 §6
LAYERS = {"심법": "심법", "무공": "무공", "기술": "기술", "물": "물"}

# 기술과 물의 kind는 정전이 못박았다. 무공의 kind는 세력마다 새로 생기므로 열어둔다
VALID_KINDS = {
    "기술": {"제작", "지식"},
    "물": {"독", "미혹", "암기", "기관물", "영약", "신병"},
}

REQUIRED_SECTIONS = ["## 개요", "## 심법", "## 무공", "## 대표 항목"]

# 1차에서 다루지 않는 것
PHASE1_FORBIDDEN_SECTIONS = ["## 초식", "## 절기", "## 인물", "## 연표"]


@dataclass
class Entry:
    """표의 한 행 = 무공 또는 심법 하나."""
    name: str
    hanja: str
    origin: str
    note: str
    layer: str           # 무공 | 심법 | 기술 | 물
    kind: str            # '심법' 또는 각 층의 kind
    is_daepyo: bool
    line: int


@dataclass
class Report:
    path: Path
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    infos: list[str] = field(default_factory=list)
    entries: list[Entry] = field(default_factory=list)

    def error(self, line: int | None, msg: str) -> None:
        loc = f"L{line}: " if line else ""
        self.errors.append(f"{loc}{msg}")

    def warn(self, line: int | None, msg: str) -> None:
        loc = f"L{line}: " if line else ""
        self.warnings.append(f"{loc}{msg}")

    @property
    def ok(self) -> bool:
        return not self.errors


# ── 파싱 ────────────────────────────────────────────────────────────

FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\n", re.S)


def split_frontmatter(text: str) -> tuple[dict[str, str], str, int]:
    """frontmatter를 얕게 파싱한다. 본문과 본문 시작 줄번호를 함께 반환."""
    m = FRONTMATTER_RE.match(text)
    if not m:
        return {}, text, 1
    meta: dict[str, str] = {}
    for line in m.group(1).split("\n"):
        if ":" in line and not line.startswith(" "):
            k, _, v = line.partition(":")
            meta[k.strip()] = v.strip()
    offset = text[: m.end()].count("\n") + 1
    return meta, text[m.end():], offset


def is_separator_row(cells: list[str]) -> bool:
    return all(re.fullmatch(r":?-{2,}:?", c) for c in cells if c)


def parse_row(line: str) -> list[str]:
    return [c.strip() for c in line.strip().strip("|").split("|")]


def parse_entries(body: str, offset: int, rep: Report) -> None:
    """`| 명칭 | 한자 | origin | 비고 |` 형태의 표에서 항목을 수집한다."""
    current_kind = "?"
    current_layer = "?"
    in_target_table = False

    for i, raw in enumerate(body.split("\n"), start=offset):
        line = raw.strip()

        if line.startswith("#"):
            heading = line.lstrip("#").strip()
            # '### 검법 (劍法)' -> '검법'
            current_kind = re.sub(r"\s*\(.*?\)\s*", "", heading).strip()
            # '## 무공' 처럼 최상위 절이면 층이 바뀐다
            if re.match(r"^##[^#]", line):
                current_layer = LAYERS.get(current_kind, "?")
            in_target_table = False
            continue

        if not line.startswith("|"):
            in_target_table = False
            continue

        cells = parse_row(line)

        # 헤더 행 판별
        if cells[:1] == ["명칭"]:
            in_target_table = "origin" in cells
            if not in_target_table:
                rep.warn(i, f"'{current_kind}' 표에 origin 열이 없다")
            continue

        if is_separator_row(cells) or not in_target_table:
            continue

        if len(cells) < 3:
            rep.error(i, f"열이 부족한 행: {line[:40]}")
            continue

        name, hanja, origin = cells[0], cells[1], cells[2]
        note = cells[3] if len(cells) > 3 else ""
        is_daepyo = "[대표]" in name or "[대표]" in note
        clean = re.sub(r"\*\*|\[대표\]", "", name).strip()

        rep.entries.append(
            Entry(clean, hanja, origin, note, current_layer, current_kind, is_daepyo, i)
        )


# ── 검사 ────────────────────────────────────────────────────────────

def check_forbidden(text: str, rep: Report, offset: int) -> None:
    for i, line in enumerate(text.split("\n"), start=offset):
        if line.strip().startswith(">"):
            continue  # 인용문(규칙 설명 등)은 건너뛴다
        for ch, why in FORBIDDEN_HANJA.items():
            if ch in line:
                rep.error(i, f"금지 한자 '{ch}' — {why}: {line.strip()[:60]}")
        for word, why in FORBIDDEN_HANGUL.items():
            if word in line:
                rep.error(i, f"금지 표현 '{word}' — {why}: {line.strip()[:60]}")
        for word, why in AMBIGUOUS_HANGUL.items():
            if word in line:
                rep.warn(i, f"확인 필요 '{word}' — {why}: {line.strip()[:60]}")
        for tier in FORBIDDEN_TIERS:
            # 앞에 한글이 붙어 있으면 다른 낱말의 꼬리다 (남화경의 '화경')
            # 뒤는 막지 않는다. '화경에', '절정의'처럼 조사가 붙는 것이 정상이다
            if re.search(rf"(?<![가-힣]){tier}", line):
                rep.error(i, f"등급 표현 '{tier}' — 공인 등급표는 존재하지 않는다")


def check_structure(body: str, meta: dict[str, str], rep: Report) -> None:
    if not meta:
        rep.error(None, "frontmatter가 없다")
    else:
        for key in ("doc_type", "status", "sect_id"):
            if key not in meta:
                rep.error(None, f"frontmatter에 '{key}'가 없다")
        if meta.get("doc_type") == "canon":
            rep.error(None, "drafts 문서의 doc_type이 canon이다. 승격은 작성자만 한다")

    for sec in REQUIRED_SECTIONS:
        if sec not in body:
            rep.error(None, f"필수 절 누락: '{sec}'")

    for sec in PHASE1_FORBIDDEN_SECTIONS:
        if sec in body:
            rep.error(None, f"1차에서 다루지 않는 절: '{sec}'")

    # 숫자 수치 노출 검사
    for pat, why in [
        (r"\bdepth\s*[:=]", "심/체 수치는 1차에서 다루지 않는다"),
        (r"\btier\s*[:=]", "tier는 이 세계관에 존재하지 않는다"),
        (r"\bfit\s*[:=]\s*0", "fit은 계산 방식 미확정. null로 둔다"),
    ]:
        if re.search(pat, body):
            rep.error(None, why)


def check_entries(rep: Report) -> None:
    if not rep.entries:
        rep.error(None, "수집된 항목이 없다. 표 형식을 확인할 것")
        return

    seen: dict[str, int] = {}
    for e in rep.entries:
        if not e.hanja or e.hanja == "—":
            rep.error(e.line, f"한자 누락: {e.name}")
        elif not re.search(r"[\u4e00-\u9fff]", e.hanja):
            rep.error(e.line, f"한자 열에 한자가 없다: {e.name} | {e.hanja}")

        for word in list(FORBIDDEN_HANGUL) + list(AMBIGUOUS_HANGUL):
            if word in e.name:
                rep.error(e.line, f"명칭에 금지 표현 '{word}': {e.name}")

        if e.origin not in VALID_ORIGINS:
            rep.error(e.line, f"origin 태그 오류: {e.name} → '{e.origin}'")

        allowed = VALID_KINDS.get(e.layer)
        if allowed and e.kind not in allowed:
            rep.error(
                e.line,
                f"{e.layer}의 kind는 {' | '.join(sorted(allowed))}만 쓴다: "
                f"{e.name} → '{e.kind}'",
            )

        if e.name in seen:
            rep.error(e.line, f"문서 내 중복: {e.name} (L{seen[e.name]})")
        else:
            seen[e.name] = e.line

    daepyo = [e for e in rep.entries if e.is_daepyo]
    if not 3 <= len(daepyo) <= 5:
        rep.error(None, f"대표 항목은 3~5개여야 한다. 현재 {len(daepyo)}개")

    simbeop = [e for e in rep.entries if "심법" in e.kind]
    if not simbeop:
        rep.warn(None, "심법 항목이 없다")


def check_index(rep: Report, sect_id: str) -> None:
    """색인과 대조한다. 관용/전승은 공통 가능, 창작 중복은 오류.

    세력 식별자는 파일명이 아니라 frontmatter의 sect_id를 쓴다.
    파일명은 사람이 읽기 위한 한글이고, id는 영문이기 때문이다.
    """
    if not INDEX_PATH.exists():
        rep.infos.append(f"색인 없음 ({INDEX_PATH.name}) — 대조 생략")
        return

    # 같은 명칭이 여러 세력에 있을 수 있으므로 소유자를 전부 모은다
    index: dict[str, list[tuple[str, str]]] = {}
    cols: dict[str, int] = {}
    for line in INDEX_PATH.read_text(encoding="utf-8").split("\n"):
        if not line.strip().startswith("|"):
            continue
        c = parse_row(line)
        if c[:1] == ["명칭"]:
            # 열 순서를 고정하지 않고 헤더 이름으로 찾는다
            cols = {name: i for i, name in enumerate(c)}
            continue
        if not cols or is_separator_row(c) or not c[0]:
            continue
        try:
            name = re.sub(r"\*\*", "", c[cols["명칭"]]).strip()
            index.setdefault(name, []).append((c[cols["origin"]], c[cols["sect_id"]]))
        except (KeyError, IndexError):
            continue

    if not cols:
        rep.infos.append("색인에 표 헤더가 없다 — 대조 생략")
        return

    sect = sect_id or rep.path.stem
    for e in rep.entries:
        # 자기 세력 항목은 제외한다. 색인에 이미 반영되어 있을 수 있다
        others = [(o, w) for o, w in index.get(e.name, []) if w != sect]
        if not others:
            continue
        owners = ", ".join(sorted({w for _, w in others}))
        if e.origin == "창작" or any(o == "창작" for o, _ in others):
            rep.error(e.line, f"창작 명칭 중복: {e.name} — 이미 '{owners}'에 있다")
        else:
            rep.infos.append(f"공통 무공: {e.name} (기존: {owners})")


def check_index_freshness(rep: Report) -> None:
    """색인이 세력 문서와 다르면 알린다. build_index.py가 내용으로 판정한다."""
    if not INDEX_PATH.exists():
        return
    if not is_current():
        rep.warn(None, "색인이 세력 문서와 다르다 — build_index.py를 실행할 것")


def report_origin_ratio(rep: Report, sect_id: str) -> None:
    total = len(rep.entries)
    if not total:
        return
    counts = {o: sum(1 for e in rep.entries if e.origin == o) for o in VALID_ORIGINS}
    parts = " · ".join(f"{o} {counts[o]}({counts[o]/total*100:.0f}%)" for o in ("전승", "관용", "창작"))
    rep.infos.append(f"항목 {total}개 — {parts}")

    # 차별화 지시는 세력명(한글)으로 적혀 있고 sect_id는 영문이므로 둘 다 시도한다
    expected = read_expected_ratio(sect_id) or read_expected_ratio(rep.path.stem)
    actual = counts["창작"] / total * 100
    if expected is not None and abs(actual - expected) >= 20:
        rep.warn(
            None,
            f"창작 비율이 예상과 {abs(actual-expected):.0f}%p 어긋난다 "
            f"(예상 {expected:.0f}% / 실제 {actual:.0f}%) — 보고할 것",
        )


def read_expected_ratio(key: str) -> float | None:
    """차별화 지시에서 해당 세력의 창작 예상 비율을 읽는다.

    지시 문서는 세력명(한글)으로 적혀 있으므로 파일명 또는 세력명으로 찾는다.
    """
    if not VARIANCE_PATH.exists() or not key:
        return None
    for line in VARIANCE_PATH.read_text(encoding="utf-8").split("\n"):
        if not line.strip().startswith("|") or key not in line:
            continue
        m = re.search(r"\|\s*(\d+)%\s*\|", line)
        if m:
            return float(m.group(1))
    return None


# ── 실행 ────────────────────────────────────────────────────────────

def validate(path: Path) -> Report:
    rep = Report(path)
    text = path.read_text(encoding="utf-8")
    meta, body, offset = split_frontmatter(text)

    sect_id = meta.get("sect_id", "")

    check_forbidden(body, rep, offset)
    check_structure(body, meta, rep)
    parse_entries(body, offset, rep)
    check_entries(rep)
    check_index(rep, sect_id)
    check_index_freshness(rep)
    # 차별화 지시는 세력명(한글)으로 적혀 있으므로 파일명으로도 찾아본다
    report_origin_ratio(rep, sect_id)
    return rep


def print_report(rep: Report) -> None:
    mark = "PASS" if rep.ok else "FAIL"
    print(f"\n[{mark}] {rep.path}")
    for msg in rep.errors:
        print(f"  오류   {msg}")
    for msg in rep.warnings:
        print(f"  경고   {msg}")
    for msg in rep.infos:
        print(f"  정보   {msg}")


def collect(targets: list[str]) -> list[Path]:
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
    ap = argparse.ArgumentParser(description="세력 문서 검증")
    ap.add_argument("targets", nargs="*", help="파일 또는 디렉토리")
    ap.add_argument("--all", action="store_true", help="drafts/factions/ 와 drafts/others/ 전체 검사")
    args = ap.parse_args()

    # drafts/ 아래에는 세력 문서가 아닌 것도 있다(세력관계.md 등).
    # 이 검증기는 세력 문서만 본다.
    all_dirs = [str(ROOT / "drafts" / "factions"), str(ROOT / "drafts" / "others")]
    targets = args.targets or (all_dirs if args.all else [])
    if not targets:
        ap.print_help()
        return 1

    paths = collect(targets)
    if not paths:
        print("검사할 파일이 없다.")
        return 1

    failed = 0
    for p in paths:
        rep = validate(p)
        print_report(rep)
        failed += not rep.ok

    print(f"\n{'─'*50}\n{len(paths)}개 검사 · 통과 {len(paths)-failed} · 실패 {failed}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
