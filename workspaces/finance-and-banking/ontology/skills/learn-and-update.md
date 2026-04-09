## Skill: Learn and Update

**Purpose:** STAR feedback loop — how consumer agents report gaps and learnings back to the ontology.

**When to use:** After any agent interaction that reveals missing knowledge, incorrect relationships, or new patterns.

**Inputs:**
- query: The question or task that triggered learning
- outcome: What happened (success, partial, failure)
- gap_description: What knowledge was missing or wrong

**Procedure:**
1. Classify the learning: extraction_miss, hallucinated_link, wrong_abstraction, causal_overclaim, stale_knowledge
2. Write to `ontology/docs/gaps.md` with priority (HIGH/MEDIUM/LOW)
3. If from a consumer agent, also write to `ontology/docs/usage-log.md`
4. If a pattern emerges across 3+ interactions, write to `ontology/docs/patterns.md`
5. Neo.Architect reads gaps on next session startup and prioritizes fixes

**Outputs:**
- Updated gaps.md entry
- Updated usage-log.md entry (if from consumer agent)

**Rules applied:** None (judgment-based)
**Data sources:** Agent interaction logs
