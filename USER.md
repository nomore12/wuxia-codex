# USER.md - User Model

Store stable user preferences and profile facts as directives that can guide future sessions.

Use one directive per entry:

```md
<!-- observed: YYYY-MM-DD | status: active -->

- Prefer concise progress updates during implementation work.
```

- Begin each directive with an imperative such as `Always`, `Never`, or `Prefer`.
- Record the observation date and either `active` or `superseded` on the metadata line.
- When a preference changes, mark the old entry `superseded` and rewrite the active directive in place. Never append a contradictory active directive.
- Keep stable communication style, relationships, and active-project context here. Put durable non-profile facts and decisions in `MEMORY.md`.

## Directives

_아직 기록된 항목이 없다. 대화 중 안정적인 선호가 확인되면 아래 형식으로 추가한다._

<!--
<!-- observed: YYYY-MM-DD | status: active -->
- Always/Never/Prefer ...
-->

## 참고

- 프로젝트 공통 규칙(정전 수정 금지, drafts 사용, 커밋 형식 등)은 `CLAUDE.md`에 있다.
  여기는 그 규칙과 별개로, 성호님 개인의 작업 스타일이 확인될 때만 채운다.

## Related

- [Agent workspace](/concepts/agent-workspace)
