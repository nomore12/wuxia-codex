#!/usr/bin/env python3
"""NotebookLM 업로드용 설정 묶음을 생성한다.

원본 문서를 수정하거나 요약하지 않고, NOTEBOOKLM.md에 정한 순서대로
`drafts/notebooklm/`에 결합한다.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = ROOT / "drafts" / "notebooklm"

MAX_FILES = 50
MAX_BYTES = 200 * 1024 * 1024
MAX_WORDS = 500_000


@dataclass(frozen=True)
class Bundle:
    filename: str
    title: str
    authority: str
    description: str
    sources: tuple[str, ...] = ()
    body: str = ""


USAGE_GUIDE = """## 자료를 읽는 순서

자료가 충돌하면 정전, 잠금, 초안, 자동 생성 자료 순으로 판단한다.

1. `01_정전_몸과마음.md`와 `02_정전_세력과미확정.md`를 가장 먼저 따른다.
2. 초안은 현재 작업 중인 설정이며 확정된 사실로 단정하지 않는다.
3. 미확정·미결 항목은 합리적으로 보이더라도 추론해서 채우지 않는다.
4. 명칭색인은 검색과 중복 확인용이며 개별 항목을 정전으로 승격하지 않는다.
5. 답변에서는 가능하면 근거가 정전인지 초안인지 함께 표시한다.

## 권장 질문 형식

> 정전과 초안을 구분해서 답해줘. 정전에 없는 내용은 초안이라고 표시하고,
> 미확정·미결 항목은 추론해서 채우지 마. 근거가 있는 묶음과 세력명을 함께 알려줘.

## 습작에 사용할 때

- 기존 설정을 찾는 것과 새로운 설정을 제안하는 것을 구분한다.
- 새로운 제안은 정전처럼 서술하지 않고 작품용 가안으로 표시한다.
- 심·체 수치를 본문에 노출하거나 통합 등급표로 바꾸지 않는다.
- 기를 실체화하거나 내공을 소모·회복되는 에너지로 다루지 않는다.
- 주화입마는 해당 인물의 심법을 확인하지 않고 판정하지 않는다.
"""


BUNDLES = (
    Bundle(
        "00_자료사용법과권한.md",
        "NotebookLM 자료 사용법과 권한",
        "안내",
        "이 묶음 전체를 조회할 때 적용할 자료 구분과 응답 원칙이다.",
        body=USAGE_GUIDE,
    ),
    Bundle(
        "01_정전_몸과마음.md",
        "정전 — 몸과 마음",
        "정전",
        "무공, 심법, 몸, 힘, 주화입마, 평판과 스키마를 규정한 최우선 자료다.",
        sources=tuple(
            ["canon/body-and-mind/00_INDEX.md"]
            + [f"canon/body-and-mind/{number:02d}_{name}.md" for number, name in (
                (1, "두개의축"),
                (2, "관문과문턱"),
                (3, "몸"),
                (4, "마음"),
                (5, "힘"),
                (6, "무공과심법"),
                (7, "주화입마"),
                (8, "별호와평판"),
                (9, "성격어휘"),
                (10, "스키마"),
            )]
        ),
    ),
    Bundle(
        "02_정전_세력과미확정.md",
        "정전 — 세력과 미확정 사항",
        "정전·잠금",
        "확정된 세력 범위와 임의로 채워서는 안 되는 설정을 함께 둔다.",
        sources=("canon/세력목록.md", "미확정사항.md"),
    ),
    Bundle(
        "03_세계_연표.md",
        "세계 연표",
        "초안",
        "무림력 1150년을 현재로 둔 사건 배치 초안이다.",
        sources=("drafts/연표.md",),
    ),
    Bundle(
        "04_세계_지리와이동.md",
        "세계 지리와 이동",
        "초안",
        "세력의 위치, 길, 이동 시간과 계절 조건을 정리한 초안이다.",
        sources=("drafts/지리.md",),
    ),
    Bundle(
        "05_세력관계.md",
        "세력 관계",
        "초안",
        "갈라짐, 대칭, 거래, 소속과 다툼에 관한 관계 단서다.",
        sources=("drafts/세력관계.md",),
    ),
    Bundle(
        "06_무공명칭색인.md",
        "무공 명칭 색인",
        "초안 기반 자동 생성 색인",
        "명칭 검색과 중복 확인용이다. 경로와 달리 독립적인 정전 권한은 없다.",
        sources=("canon/명칭색인.md",),
    ),
    Bundle(
        "07_정파_구파일방.md",
        "정파 — 구파일방",
        "초안",
        "구파일방 열 세력의 1차 초안을 묶는다.",
        sources=tuple(f"drafts/factions/{name}.md" for name in (
            "소림사", "무당파", "화산파", "종남파", "청성파",
            "아미파", "곤륜파", "공동파", "점창파", "개방",
        )),
    ),
    Bundle(
        "08_정파_오대세가.md",
        "정파 — 오대세가",
        "초안",
        "오대세가 다섯 세력의 1차 초안을 묶는다.",
        sources=tuple(f"drafts/factions/{name}.md" for name in (
            "남궁세가", "제갈세가", "사천당가", "하북팽가", "황보세가",
        )),
    ),
    Bundle(
        "09_정파_오악과중소세력.md",
        "정파 — 오악과 중소 세력",
        "초안",
        "오악검파와 중소 문파·세가 아홉의 1차 초안을 묶는다.",
        sources=tuple(f"drafts/factions/{name}.md" for name in (
            "태산파", "형산파", "항산파", "숭산파", "해남파",
            "모용세가", "진주언가", "산서석가", "황산파",
        )),
    ),
    Bundle(
        "10_표국과만금전장.md",
        "표국과 만금전장",
        "초안",
        "운송과 금융을 담당하는 세 표국과 만금전장을 묶는다.",
        sources=tuple(f"drafts/factions/{name}.md" for name in (
            "용문표국", "만금표국", "금룡표국", "만금전장",
        )),
    ),
    Bundle(
        "11_사파_연합과방파.md",
        "사파 — 연합과 방파",
        "초안",
        "사도련과 방파·수로·정보 조직 아홉의 1차 초안을 묶는다.",
        sources=tuple(f"drafts/factions/{name}.md" for name in (
            "사도련", "녹림맹", "장강수로채", "하오문", "흑사방",
            "백사방", "흑풍채", "철혈문", "패도문",
        )),
    ),
    Bundle(
        "12_사파_살수와기타.md",
        "사파 — 살수와 기타",
        "초안",
        "살수 조직과 채화방 네 세력의 1차 초안을 묶는다.",
        sources=tuple(f"drafts/factions/{name}.md" for name in (
            "살막", "혈영문", "암향각", "채화방",
        )),
    ),
    Bundle(
        "13_마도.md",
        "마도",
        "초안",
        "천마신교, 혈교, 배화교의 1차 초안을 묶는다.",
        sources=tuple(f"drafts/factions/{name}.md" for name in (
            "천마신교", "혈교", "배화교",
        )),
    ),
    Bundle(
        "14_무소속.md",
        "무소속",
        "초안",
        "세력에 속하지 않은 자들의 무공과 심법 모음이다. "
        "세력 문서가 아니며 항목 사이에 관계가 없다.",
        sources=("drafts/others/무소속.md",),
    ),
    Bundle(
        "15_습작작성가드레일.md",
        "습작 작성 가드레일",
        "작업 지침",
        "세계관을 사용해 설정이나 원고를 생성할 때 지켜야 할 규칙이다.",
        sources=("CLAUDE.md", "specs/AI생성규칙.md"),
    ),
    Bundle(
        "16_미결과잠금목록.md",
        "미결과 잠금 목록",
        "초안·미결",
        "세력 문서에서 수집한 미결을 보여주며 이 파일 안에서 해소하지 않는다.",
        sources=("drafts/미결모음.md",),
    ),
)


def source_path(relative: str) -> Path:
    return ROOT / relative


def render(bundle: Bundle) -> str:
    """한 묶음을 결정적인 문자열로 만든다."""
    source_lines = ["sources:"]
    if bundle.sources:
        source_lines.extend(f"  - {source}" for source in bundle.sources)
    else:
        source_lines.append("  - generated-guide")

    parts = [
        "---",
        "doc_type: notebooklm_bundle",
        "status: generated",
        "generated_by: scripts/build_notebooklm.py",
        f"authority: {bundle.authority}",
        *source_lines,
        "---",
        "",
        f"# {bundle.title}",
        "",
        "> **NotebookLM 업로드용 자동 생성 파일이다. 직접 편집하지 않는다.**",
        "> 원본을 수정한 뒤 `python3 scripts/build_notebooklm.py`로 다시 만든다.",
        "",
        "## 자료 성격",
        "",
        bundle.description,
        "",
    ]

    if bundle.body:
        parts.extend((bundle.body.rstrip(), ""))

    if bundle.sources:
        parts.extend(("## 포함 원본", ""))
        parts.extend(f"- `{source}`" for source in bundle.sources)
        parts.append("")

    for source in bundle.sources:
        original = source_path(source).read_text(encoding="utf-8").rstrip()
        parts.extend((
            "---",
            "",
            f"<!-- NOTEBOOKLM_SOURCE_START: {source} -->",
            f"## 원본 문서: `{source}`",
            "",
            original,
            "",
            f"<!-- NOTEBOOKLM_SOURCE_END: {source} -->",
            "",
        ))

    return "\n".join(parts).rstrip() + "\n"


def validate_definition() -> list[str]:
    """묶음 정의와 입력 파일을 검사한다."""
    errors: list[str] = []
    filenames = [bundle.filename for bundle in BUNDLES]
    if len(filenames) >= MAX_FILES:
        errors.append(f"묶음이 {len(filenames)}개다. {MAX_FILES}개 미만이어야 한다")
    if len(filenames) != len(set(filenames)):
        errors.append("묶음 파일명이 중복된다")

    seen_sources: dict[str, str] = {}
    for bundle in BUNDLES:
        for source in bundle.sources:
            path = source_path(source)
            if not path.is_file():
                errors.append(f"원본 파일이 없다: {source}")
            if source in seen_sources:
                errors.append(
                    f"원본이 둘 이상의 묶음에 있다: {source} "
                    f"({seen_sources[source]}, {bundle.filename})"
                )
            else:
                seen_sources[source] = bundle.filename
    return errors


def measure(content: str) -> tuple[int, int]:
    """UTF-8 바이트 수와 공백 기준 단어 수를 센다."""
    return len(content.encode("utf-8")), len(content.split())


def validate_content(bundle: Bundle, content: str) -> list[str]:
    """NotebookLM의 파일별 제한을 사전 검사한다."""
    errors: list[str] = []
    byte_count, word_count = measure(content)
    if byte_count > MAX_BYTES:
        errors.append(
            f"{bundle.filename}: {byte_count:,}바이트로 200MB 제한을 넘는다"
        )
    if word_count > MAX_WORDS:
        errors.append(
            f"{bundle.filename}: {word_count:,}단어로 500,000단어 제한을 넘는다"
        )
    return errors


def build_all() -> int:
    errors = validate_definition()
    if errors:
        for error in errors:
            print(f"오류  {error}", file=sys.stderr)
        return 1

    rendered = [(bundle, render(bundle)) for bundle in BUNDLES]
    for bundle, content in rendered:
        errors.extend(validate_content(bundle, content))
    if errors:
        for error in errors:
            print(f"오류  {error}", file=sys.stderr)
        return 1

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    changed = 0
    for bundle, content in rendered:
        target = OUTPUT_DIR / bundle.filename
        old = target.read_text(encoding="utf-8") if target.exists() else None
        if old == content:
            state = "변경 없음"
        else:
            target.write_text(content, encoding="utf-8")
            state = "생성" if old is None else "갱신"
            changed += 1
        byte_count, word_count = measure(content)
        print(
            f"{state:7} {bundle.filename} — "
            f"{word_count:,}단어 · {byte_count:,}바이트"
        )

    print(f"\n묶음 {len(BUNDLES)}개 · 변경 {changed}개 · 출력 {OUTPUT_DIR.relative_to(ROOT)}")
    return 0


def check_all() -> int:
    errors = validate_definition()
    if errors:
        for error in errors:
            print(f"오류  {error}", file=sys.stderr)
        return 1

    stale = 0
    for bundle in BUNDLES:
        content = render(bundle)
        errors.extend(validate_content(bundle, content))
        target = OUTPUT_DIR / bundle.filename
        if not target.exists():
            print(f"누락  {target.relative_to(ROOT)}")
            stale += 1
        elif target.read_text(encoding="utf-8") != content:
            print(f"변경  {target.relative_to(ROOT)}")
            stale += 1
        else:
            print(f"최신  {target.relative_to(ROOT)}")

    if errors:
        for error in errors:
            print(f"오류  {error}", file=sys.stderr)
    if errors or stale:
        print(f"\n최신이 아닌 묶음 {stale}개", file=sys.stderr)
        return 1

    print(f"\n묶음 {len(BUNDLES)}개가 모두 최신이며 제한 안에 있다.")
    return 0


def list_all() -> int:
    errors = validate_definition()
    if errors:
        for error in errors:
            print(f"오류  {error}", file=sys.stderr)
        return 1

    for bundle in BUNDLES:
        content = render(bundle)
        byte_count, word_count = measure(content)
        print(
            f"{bundle.filename} — {bundle.authority} · "
            f"원본 {len(bundle.sources)}개 · {word_count:,}단어 · {byte_count:,}바이트"
        )
        for source in bundle.sources:
            print(f"  - {source}")
    print(f"\n총 {len(BUNDLES)}개")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="NotebookLM 업로드용 설정 묶음 생성")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true", help="출력의 최신성과 제한만 검사")
    mode.add_argument("--list", action="store_true", help="묶음 구성과 예상 크기를 출력")
    args = parser.parse_args()

    if args.check:
        return check_all()
    if args.list:
        return list_all()
    return build_all()


if __name__ == "__main__":
    raise SystemExit(main())
