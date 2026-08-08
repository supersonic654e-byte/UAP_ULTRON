# Architecture Decision Records (ADR)

We log the "why" behind significant decisions so nobody has to re-derive them.
Format is a stripped-down version of Michael Nygard's ADR pattern.

- `0001-dds-over-vpn.md` — why CycloneDDS + Tailscale instead of Zenoh/plain multicast

## Template

```markdown
# ADR-00XX: <short title>
Date: <YYYY-MM-DD>
Status: Accepted | Superseded by ADR-00YY | Rejected

## Context
<what problem, what constraints>

## Decision
<what we chose>

## Consequences
<what got easier / harder>
```

## Rules

- One decision per ADR. Number sequentially.
- A decision is "accepted" the moment it is committed; it can be superseded.
- Link the ADR from the PR that implements it.
