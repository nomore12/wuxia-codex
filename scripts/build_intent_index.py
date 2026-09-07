#!/usr/bin/env python3
"""
의도 기록 색인 생성기.

docs/intent/ 아래 NNNN-<slug>/decision.md 를 훑어 docs/intent/INDEX.md 를 다시 만든다.
색인은 **손으로 관리하지 않는다.** 항상 이 스크립트로 재생성한다.

사용법:
    python scripts/build_intent_index.py           # 재생성
    python scripts/build_intent_index.py --check   # 최신 여부만 확인 (쓰지 않음)

frontmatter 위반이 하나라도 있으면 INDEX.md를 쓰지 않고 전부 나열한 뒤 종료한다.
경고 수준은 없다. 자동 수정(--fix)도 없다. 손으로 고칠 것들이다.

종료 코드: 0 통과 / 1 오류 있음
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INTENT_DIR = ROOT / "docs" / "intent"
INDEX_PATH = INTENT_DIR / "INDEX.md"

# 결정 디렉터리 이름. id 4자리 + 소문자 영문 슬러그. CONVENTION.md §3
DIR_RE = re.compile(r"\A(\d{4})-[a-z0-9]+(?:-[a-z0-9]+)*\Z")

REQUIRED_KEYS = ["id", "date", "status", "scope", "tags"]
VALID_STATUS = {"active", "superseded", "retroactive"}
# CONVENTION.md §4. 새 태그는 사용자 확인을 거쳐 여기에 추가한다
VALID_TAGS = {"canon", "schema", "pipeline", "tooling", "ci", "naming", "content"}

HEADING_RE = re.compile(r"^# +(.+?)\s*$", re.M)
FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\n", re.S)


@dataclass
class Report:
    errors: list[str] = field(default_factory=list)

    def error(self, where: str, msg: str) -> None:
        self.errors.append(f"{where}: {msg}")

    @property
    def ok(self) -> bool:
        return not self.errors


@dataclass
class Decision:
    dir_name: str
    id: str
    date: str
    status: str
    scope: list[str]
    tags: list[str]
    supersedes: str | None
    superseded_by: str | None
    title: str

    @property
    def link(self) -> str:
        return f"[{self.id}]({self.dir_name}/decision.md)"


# ── 파싱 ────────────────────────────────────────────────────────────

COMMENT_RE = re.compile(r"\s+#.*\Z")


def strip_comment(value: str) -> str:
    """따옴표로 감싸지 않은 값의 꼬리 주석을 떼어낸다."""
    if value.startswith(('"', "'")):
        return value
    return COMMENT_RE.sub("", value)


def scalar(value: str) -> str | None:
    """YAML 스칼라를 얕게 읽는다. null / ~ / 빈 값은 None."""
    v = strip_comment(value).strip()
    if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
        v = v[1:-1]
    if v in ("", "null", "~"):
        return None
    return v


def parse_frontmatter(text: str) -> dict[str, object] | None:
    """frontmatter를 얕게 파싱한다. 스칼라, 블록 목록, 인라인 목록만 다룬다."""
    m = FRONTMATTER_RE.match(text)
    if not m:
        return None
    meta: dict[str, object] = {}
    key: str | None = None
    for line in m.group(1).split("\n"):
        if line.startswith((" ", "\t")):
            item = line.strip()
            if key and item.startswith("- "):
                meta.setdefault(key, [])
                if isinstance(meta[key], list):
                    v = scalar(item[2:])
                    if v is not None:
                        meta[key].append(v)   # type: ignore[union-attr]
            continue
        if ":" not in line:
            continue
        k, _, raw = line.partition(":")
        key = k.strip()
        raw = strip_comment(raw).strip()
        if raw.startswith("[") and raw.endswith("]"):
            meta[key] = [x.strip().strip("\"'") for x in raw[1:-1].split(",") if x.strip()]
        elif raw == "":
            meta[key] = []          # 뒤따르는 블록 목록이 채운다
        else:
            meta[key] = scalar(raw)
    return meta


# ── 검증 ────────────────────────────────────────────────────────────

def load_decision(d: Path, rep: Report) -> Decision | None:
    where = f"docs/intent/{d.name}"
    path = d / "decision.md"
    if not path.exists():
        rep.error(where, "decision.md가 없다")
        return None

    text = path.read_text(encoding="utf-8")
    meta = parse_frontmatter(text)
    if meta is None:
        rep.error(where, "frontmatter가 없다")
        return None

    ok = True
    for k in REQUIRED_KEYS:
        if k not in meta or meta[k] in (None, []):
            rep.error(where, f"frontmatter에 '{k}'가 없다")
            ok = False
    if not ok:
        return None

    ident = str(meta["id"])
    if ident != d.name[:4]:
        rep.error(where, f"id '{ident}'가 디렉터리명 앞 4자리 '{d.name[:4]}'와 다르다")
        ok = False

    status = str(meta["status"])
    if status not in VALID_STATUS:
        rep.error(where, f"status '{status}'는 허용값이 아니다 ({' / '.join(sorted(VALID_STATUS))})")
        ok = False

    scope = meta["scope"]
    if not isinstance(scope, list):
        rep.error(where, "scope가 목록이 아니다")
        ok = False
        scope = []

    tags = meta["tags"]
    if not isinstance(tags, list):
        rep.error(where, "tags가 목록이 아니다")
        ok = False
        tags = []
    for t in tags:
        if t not in VALID_TAGS:
            rep.error(where, f"tags '{t}'는 허용 목록에 없다 ({', '.join(sorted(VALID_TAGS))})")
            ok = False

    superseded_by = meta.get("superseded_by")
    if status == "superseded" and superseded_by is None:
        rep.error(where, "status가 superseded인데 superseded_by가 비어 있다")
        ok = False

    heading = HEADING_RE.search(text[len(FRONTMATTER_RE.match(text).group(0)):])
    if not heading:
        rep.error(where, "본문에 '# ' 제목이 없다")
        ok = False

    if not ok:
        return None

    return Decision(
        dir_name=d.name,
        id=ident,
        date=str(meta["date"]),
        status=status,
        scope=[str(s) for s in scope],
        tags=[str(t) for t in tags],
        supersedes=meta.get("supersedes"),          # type: ignore[arg-type]
        superseded_by=superseded_by,                # type: ignore[arg-type]
        title=heading.group(1),
    )


def check_cross_refs(decisions: list[Decision], rep: Report) -> None:
    """id 중복과 supersedes / superseded_by가 가리키는 id의 실재를 확인한다."""
    seen: dict[str, str] = {}
    for dec in decisions:
        if dec.id in seen:
            rep.error(f"docs/intent/{dec.dir_name}",
                      f"id '{dec.id}'가 {seen[dec.id]}와 중복된다")
        else:
            seen[dec.id] = dec.dir_name

    known = set(seen)
    for dec in decisions:
        where = f"docs/intent/{dec.dir_name}"
        for label, ref in (("supersedes", dec.supersedes), ("superseded_by", dec.superseded_by)):
            if ref is not None and ref not in known:
                rep.error(where, f"{label}가 가리키는 id '{ref}'가 없다")


# ── 색인 생성 ───────────────────────────────────────────────────────

def fmt_row(cells: list[str]) -> str:
    return "| " + " | ".join(cells) + " |"


def section_table(title: str, header: list[str], rows: list[list[str]]) -> list[str]:
    out = [f"## {title}", ""]
    if not rows:
        out += ["(없음)", ""]
        return out
    out.append(fmt_row(header))
    out.append("|" + "|".join(["---"] * len(header)) + "|")
    out += [fmt_row(r) for r in rows]
    out.append("")
    return out


def render(decisions: list[Decision]) -> str:
    by_id = {d.id: d for d in decisions}

    def ref(ident: str | None) -> str:
        if ident is None:
            return "—"
        target = by_id.get(ident)
        return f"[{ident}]({target.dir_name}/decision.md)" if target else ident

    def code_join(items: list[str]) -> str:
        return ", ".join(f"`{i}`" for i in items) if items else "—"

    active = sorted((d for d in decisions if d.status == "active"), key=lambda d: d.id)
    superseded = sorted((d for d in decisions if d.status == "superseded"),
                        key=lambda d: (d.date, d.id), reverse=True)
    retroactive = sorted((d for d in decisions if d.status == "retroactive"), key=lambda d: d.id)

    lines = [
        "<!-- build_intent_index.py 생성물. 직접 편집하지 마십시오. -->",
        "<!-- 갱신일은 색인 내용이 실제로 바뀐 날짜다. 스크립트 실행일이 아니다. -->",
        "",
        "# 의도 기록 색인",
        "",
        f"갱신: {date.today().isoformat()}",
        "",
    ]

    lines += section_table(
        "활성 결정", ["id", "제목", "scope", "tags", "날짜"],
        [[d.link, d.title, code_join(d.scope), ", ".join(d.tags) or "—", d.date] for d in active],
    )
    lines += section_table(
        "번복된 결정", ["id", "제목", "대체", "날짜"],
        [[d.link, d.title, f"→ {ref(d.superseded_by)}", d.date] for d in superseded],
    )
    if retroactive:
        lines += section_table(
            "소급 기록", ["id", "제목", "scope", "tags", "날짜"],
            [[d.link, d.title, code_join(d.scope), ", ".join(d.tags) or "—", d.date]
             for d in retroactive],
        )

    # 역인덱스는 활성 결정만 모은다. glob은 풀지 않고 문자열 그대로 키가 된다
    reverse: dict[str, list[str]] = {}
    for d in active:
        for s in d.scope:
            reverse.setdefault(s, []).append(d.id)
    lines += section_table(
        "scope 역인덱스", ["경로", "활성 결정"],
        [[f"`{s}`", ", ".join(sorted(reverse[s]))] for s in sorted(reverse)],
    )

    return "\n".join(lines).rstrip("\n") + "\n"


# ── 실행 ────────────────────────────────────────────────────────────

# 「갱신:」 줄은 비교에서 뺀다. 그래야 이 줄이 「내용이 바뀐 날」로 남는다
UPDATED_RE = re.compile(r"^갱신: .*$", re.M)


def comparable(text: str) -> str:
    return UPDATED_RE.sub("갱신:", text)


def main() -> int:
    ap = argparse.ArgumentParser(description="의도 기록 색인 생성")
    ap.add_argument("--check", action="store_true", help="최신 여부만 확인 (쓰지 않음)")
    args = ap.parse_args()

    dirs = []
    if INTENT_DIR.is_dir():
        dirs = sorted(p for p in INTENT_DIR.iterdir() if p.is_dir() and DIR_RE.match(p.name))

    rep = Report()
    decisions = [dec for d in dirs if (dec := load_decision(d, rep)) is not None]
    check_cross_refs(decisions, rep)

    if not rep.ok:
        print(f"\n[FAIL] {INDEX_PATH.relative_to(ROOT)}", file=sys.stderr)
        for msg in rep.errors:
            print(f"  오류   {msg}", file=sys.stderr)
        print(f"\n{'─'*50}\n오류 {len(rep.errors)}건 · INDEX.md를 쓰지 않았다", file=sys.stderr)
        return 1

    content = render(decisions)
    old = INDEX_PATH.read_text(encoding="utf-8") if INDEX_PATH.exists() else ""
    current = bool(old) and comparable(old) == comparable(content)

    if args.check:
        if current:
            print("의도 기록 색인이 최신이다.")
            return 0
        print("의도 기록 색인이 최신이 아니다. build_intent_index.py를 실행할 것.",
              file=sys.stderr)
        return 1

    # 내용이 같으면 생성일도 그대로 둔다. 의미 없는 diff를 만들지 않기 위함
    INTENT_DIR.mkdir(parents=True, exist_ok=True)
    INDEX_PATH.write_text(old if current else content, encoding="utf-8")

    counts = {k: sum(1 for d in decisions if d.status == k) for k in sorted(VALID_STATUS)}
    status = "변경 없음" if current else "갱신"
    print(f"[OK] {INDEX_PATH.relative_to(ROOT)} {status} · 결정 {len(decisions)}건 "
          f"(활성 {counts['active']} · 번복 {counts['superseded']} · 소급 {counts['retroactive']})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
