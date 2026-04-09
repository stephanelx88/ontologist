# Extraction Skills — Compounding Skill Library

This directory contains Neo's compounding extraction skills. As Neo processes
more domains, extraction speed and quality improve.

## Expected Growth

```
Domain 1:  Baseline. No meta-knowledge. 5 iterations to reach 75%.
Domain 5:  3 meta-patterns applied. 3 iterations to reach 75%.
Domain 10: 12 meta-patterns. 1-2 iterations. Most extraction near-automatic.
```

## Skill File Format

Each skill file uses this frontmatter:

```yaml
---
id: unique-skill-id
name: Human-readable name
type: meta-pattern | anti-pattern | domain-template | extraction-strategy
confidence: 0.0-1.0
scope: [list of domain archetypes this applies to]
validated_in: [list of domains where validated]
failed_in: [list of domains where failed]
graduated: null | YYYY-MM-DD
lifetime_success_rate: 0.0-1.0
---
```

Followed by a detailed procedure section.

## Directory Structure

- `meta-patterns/` — "For hierarchical domains, start top-down"
- `anti-patterns/` — "Co-occurrence ≠ causation"
- `domain-templates/` — Starter structures per archetype
- `extraction-strategies/` — Per input type (PDF, code, interview)

Files appear here as Neo processes domains and graduates observations
from `proposed/` to `graduated/` in domain workspaces.

## Graduation Path

```
Domain workspace: neo/meta-knowledge/proposed/
  → Validated across 2+ domains with >5% score improvement
  → Moves to: neo/meta-knowledge/graduated/
  → QA committee approves (2/3 reviewers)
  → Copies to: this directory (skill-level compounding library)
```
