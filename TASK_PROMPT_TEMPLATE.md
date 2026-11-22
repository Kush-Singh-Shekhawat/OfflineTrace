# Task Prompt Template

Copy this prompt into the coding assistant used for a task.

---

You are contributing to the OfflineTrace project.

## Read first
- `PROJECT_CONTEXT.md`
- `AI_RULES.md`
- `API_CONTRACTS.md`
- `DEVELOPMENT_STATUS.md`

## Assignment
- Member/owner: [A / B / C]
- Task: [one specific task]
- Allowed files/folders: [exact paths]
- Do not modify: [paths]
- Related API contract: [section/route]

## Requirements
[Write observable requirements and acceptance criteria.]

## Constraints
- Preserve existing interfaces unless a contract change is explicitly approved.
- Do not invent dependencies or claim tests passed without running them.
- Use synthetic data only.
- Do not add secrets or private keys.
- Ask before making an ambiguous security or architecture decision.

## Required response
1. Brief implementation plan.
2. Files to be changed.
3. Implementation.
4. Tests added/updated.
5. Exact commands run and actual results.
6. Known limitations and security considerations.
7. Integration notes for the other members.

Before editing, inspect the current repository and summarize relevant existing code. Do not
replace files wholesale when a targeted change is sufficient.
