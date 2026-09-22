<!-- build_intent_index.py 생성물. 직접 편집하지 마십시오. -->
<!-- 갱신일은 색인 내용이 실제로 바뀐 날짜다. 스크립트 실행일이 아니다. -->

# 의도 기록 색인

갱신: 2026-09-22

## 활성 결정

| id | 제목 | scope | tags | 날짜 |
|---|---|---|---|---|
| [0001](0001-intent-index-script/decision.md) | intent 색인은 별도 생성기로 분리하고 검증 루프에 편입한다 | `scripts/build_intent_index.py`, `docs/intent/INDEX.md`, `docs/intent/CONVENTION.md`, `AGENTS.md`, `CLAUDE.md` | pipeline, tooling | 2026-09-07 |
| [0002](0002-drop-reign-era-use-ganji/decision.md) | 연호를 빼고 간지로 시간을 적는다 | `drafts/연표.md`, `canon/body-and-mind/10_스키마.md`, `scripts/check_ganji.py`, `README.md` | canon, schema, pipeline | 2026-09-08 |
| [0003](0003-adopt-late-material-early/decision.md) | 실제보다 늦게 나온 소재는 앞당겨 이미 있는 것으로 둔다 | `canon/세력목록.md`, `drafts/factions/`, `drafts/연표.md` | canon, content | 2026-09-08 |
| [0004](0004-taesan-rite-broken-twice/decision.md) | 태산의 예는 두 번 끊겼고 두 번째가 마지막이다 | `drafts/연표.md`, `drafts/factions/태산파.md`, `drafts/미결모음.md` | canon, content | 2026-09-08 |
| [0005](0005-annotate-settings-docs/decision.md) | 설정 문서에는 서력을 병기하고 습작 원고에는 넣지 않는다 | `drafts/factions/`, `drafts/저장소현황.md`, `specs/집필가이드.md` | content, naming | 2026-09-08 |
| [0006](0006-promote-from-writing-practice/decision.md) | 습작에서 나온 설정은 완결 시 승격 판정으로만 올라간다 | `drafts/writing-practice/`, `specs/집필가이드.md` | content | 2026-09-08 |
| [0007](0007-character-listing-is-separate/decision.md) | 인물은 승격과 별개로 목록 등재를 판단한다 | `drafts/writing-practice/` | content | 2026-09-08 |
| [0008](0008-rumor-stays-rumor/decision.md) | 30년 전의 준동은 소문으로만 두고 사실을 확정하지 않는다 | `drafts/소문.md`, `drafts/factions/천마신교.md`, `drafts/factions/무당파.md`, `drafts/연표.md` | canon, content | 2026-09-22 |
| [0010](0010-mudang-four-factions/decision.md) | 무당 장로의 파벌을 넷으로 두고 만류에서 하나로 모은다 | `drafts/factions/무당파.md`, `drafts/미결모음.md` | content | 2026-09-22 |

## 번복된 결정

(없음)

## scope 역인덱스

| 경로 | 활성 결정 |
|---|---|
| `AGENTS.md` | 0001 |
| `CLAUDE.md` | 0001 |
| `README.md` | 0002 |
| `canon/body-and-mind/10_스키마.md` | 0002 |
| `canon/세력목록.md` | 0003 |
| `docs/intent/CONVENTION.md` | 0001 |
| `docs/intent/INDEX.md` | 0001 |
| `drafts/factions/` | 0003, 0005 |
| `drafts/factions/무당파.md` | 0008, 0010 |
| `drafts/factions/천마신교.md` | 0008 |
| `drafts/factions/태산파.md` | 0004 |
| `drafts/writing-practice/` | 0006, 0007 |
| `drafts/미결모음.md` | 0004, 0010 |
| `drafts/소문.md` | 0008 |
| `drafts/연표.md` | 0002, 0003, 0004, 0008 |
| `drafts/저장소현황.md` | 0005 |
| `scripts/build_intent_index.py` | 0001 |
| `scripts/check_ganji.py` | 0002 |
| `specs/집필가이드.md` | 0005, 0006 |
