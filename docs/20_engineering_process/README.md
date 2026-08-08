# Engineering Process

How we track the work, decisions, risk, and quality.

| Doc | Purpose |
|---|---|
| `engineering_audit.md` | Full technical audit of the V0.3 Bible (verdict, scores, corrections P0–P3) |
| `risk_register.md` | Living risk table — updated as things change |
| `decisions/` | Architecture Decision Records (ADRs) — why we chose what we chose |
| `quality_gates.md` | The checklist a version must pass before it is "done" |
| `changelog.md` | Dated log of significant changes |

## Working agreement

- Small, reviewable PRs. One topic per PR.
- Every decision that matters gets an ADR (even a short one).
- Risk items are owned by a named person.
- A version is not "shipped" until it passes `quality_gates.md`.
