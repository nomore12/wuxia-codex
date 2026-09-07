---
id: "0001"
date: 2026-09-07
status: active
supersedes: null
superseded_by: null
scope:
  - scripts/build_intent_index.py
  - docs/intent/INDEX.md
  - docs/intent/CONVENTION.md
  - AGENTS.md
  - CLAUDE.md
tags: [pipeline, tooling]
---

# intent 색인은 별도 생성기로 분리하고 검증 루프에 편입한다

## 문제
CONVENTION.md §3은 INDEX.md를 「build_index.py가 생성」한다고 적었고 §5-5는 그 실행을
절차에 넣었다. 그러나 `scripts/build_index.py`에는 `docs/` 참조가 0건이다. 생성기가
없었고, 만든 뒤에도 실행을 지시하는 곳이 없어 색인이 조용히 낡을 자리가 남는다.

## 검토한 대안
1. **build_index.py 확장** — 입력이 `drafts/factions/`, 출력이 `canon/명칭색인.md`로
   고정된 스크립트다. 호출 시점도 세력 문서 생성 직후로 다르다.
2. **INDEX.md 미생성, 조회 시 glob** — §6 조회 절차가 INDEX.md를 전제한다. 생성기가 없으면 손으로 쓰게 된다.
3. **별도 스크립트 + 검증 루프 편입** ← 선택

검증 루프 편입 방식으로 pre-commit 훅 강제도 검토했으나 기각했다 — 세력 문서 작업마다
전체 검증이 돌아 `--no-verify` 우회를 습관화시킨다. 기존 `--check` 관행을 따른다.

## 근거
두 색인은 입력·출력·호출 시점이 겹치지 않고 공유할 코드도 없다(세력 문서는 표 파싱,
decision.md는 frontmatter 파싱). 합쳤다면 decision.md의 frontmatter 오류 하나가
세력 색인 재생성까지 막는다. 분리의 대가는 `--check`를 AGENTS.md 검증 목록에 넣어 갚았다.

## 가정
- decision.md는 §4 스키마를 따른다. 벗어난 파일은 색인에 실리지 않고 오류가 된다.
- 두 색인은 서로의 입력을 참조하지 않는다.
- 에이전트가 AGENTS.md 「검증」 절의 명령을 실제로 실행한다. 강제 장치는 없다.
- INDEX.md의 가치는 결정 건수가 아니라 §6 조회 절차의 scope 역인덱스에서 나온다.
  건수가 적어도 역인덱스는 필요하다.

## 폐기 조건
- 두 색인이 서로의 데이터를 참조해야 하면 대안 1로 간다.
- 두 스크립트가 같은 frontmatter 파서를 요구하면 공용 모듈로 분리하고 재검토한다.
- 검증이 자발적 준수만으로 유지되지 않으면(낡은 색인이 커밋되는 일 3건 이상)
  CI 도입을 검토한다. pre-commit 훅은 2026-09-07 검토 후 제외했다.
- §6 조회 절차가 사문화되면 — 색인을 거치지 않고 grep으로 조회하는 관행이 굳으면 —
  대안 2를 재검토한다.
