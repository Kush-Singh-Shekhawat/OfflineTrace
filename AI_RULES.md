# AI-Assisted Development Rules

This project may be developed with prompt engineering and AI coding tools. AI output is
untrusted until reviewed and tested.

1. Read `PROJECT_CONTEXT.md`, `API_CONTRACTS.md`, and `DEVELOPMENT_STATUS.md` first.
2. Work only inside the files assigned in the task. Do not silently refactor unrelated modules.
3. Do not invent existing functions, files, dependencies, API routes, or test results.
4. Inspect imports and call sites before changing a function signature.
5. Preserve agreed API request/response shapes unless the team approves a contract change.
6. Add or update tests. Never state that tests passed unless they were actually run.
7. Do not weaken validation, authentication, cryptographic checks, or error handling to make
   a demo pass.
8. Do not implement custom cryptographic primitives. Use reviewed libraries and standard
   algorithms selected by the team.
9. Never hard-code secrets, passwords, private keys, tokens, or real personal data.
10. Use synthetic PDFs and synthetic recipient identities in fixtures.
11. Keep functions small, typed where practical, and documented at module boundaries.
12. Before finishing, report: files changed, design decisions, commands run, test results,
    known limitations, and any integration impact.
13. If requirements conflict or an API contract is unclear, stop and ask rather than guessing.
14. Avoid broad formatting changes and generated-file churn.
15. Do not commit `.env`, virtual environments, `node_modules`, build output, runtime data,
    private keys, or real documents.
