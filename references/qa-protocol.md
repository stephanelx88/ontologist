# QA Protocol and Team Communication

Neo's quality assurance system uses three parallel Opus reviewers, structured
consensus rules, error attribution via shadow queries, and consumer feedback loops.

---

## 1. Three-Agent QA Loop

**Trigger:** Automatically after Neo.Architect completes any ontology build or
iteration loop converges.
**Execution:** Three Opus subagents run in PARALLEL.

### Implementation Auditor

Checks:
- Every entity cites source page/paragraph
- Cited quotes exist on cited pages (spot-check 20%)
- No EXTRACTED claims that are actually INFERRED
- No orphan entities (entities with no relationships)
- No terminology inconsistencies
- Coverage: all source sections represented

### Consistency Reviewer

Checks:
- Internal contradictions
- Circular causality (not flagged as feedback loops)
- Hallucination detection (claims unsupported by source)
- Graph structure quality
- Statistical plausibility of relationships

### Ontological Rigor Reviewer

Checks:
- IS-A hierarchies clean (no diamond inheritance)
- Causal chains directional and non-trivial
- Missing intermediate entities
- Abstraction level consistency across ontology
- Rules vs. skills correctly separated
- Gaps explicitly documented

---

## 2. Consensus and Escalation

```
All three return results in parallel
  |
  +-- 3/3 PASS --> auto-approve
  +-- 2/3 flag same claim --> CRITICAL --> escalate to user
  +-- 1/3 flags --> rebuttal round --> resolved or escalate
  +-- Any CRITICAL severity --> escalate to user
```

---

## 3. QA Modes (from neo-trust.yaml)

| Mode | Behavior |
|------|----------|
| autonomous | Auto-approve if all pass. User sees report after. |
| supervised | User reviews report before finalization. |
| mandatory-review | User approves each finding individually. |

---

## 4. Reviewer Participation Points

The three QA reviewers participate at THREE moments, not just post-build:

| Moment | Trigger | Reviewer Role |
|--------|---------|---------------|
| **Post-build QA** | Neo.Architect completes ontology or iteration loop converges | Full 3-reviewer audit (parallel Opus agents) |
| **Gap escalation** | Neo.Architect finds structural gap it can't resolve | Clark-reviewer advises on commitment revision |
| **Cross-domain review** | Neo proposes graduating a meta-rule | All 3 validate: does this pattern generalize? |

---

## 5. Gap Escalation Protocol

```
Neo.Architect encounters structural gap (ontology can't represent something)
  --> Spawns Clark-reviewer with specific question:
      "Current commitment: [X]. This prevents representing [Y].
       Options: (A) revise commitment, (B) add exception, (C) accept limitation.
       Which is best for this domain?"
  --> Clark-reviewer analyzes and recommends
  --> If Phase 1: recommendation goes to user
  --> If Phase 2+: Neo.Architect follows recommendation, logs in commitment journal
```

---

## 6. Cross-Domain Graduation Review

```
Neo proposes graduating a meta-rule (validated in 2+ domains)
  --> Spawns all 3 reviewers with:
      "Proposed meta-rule: [description].
       Evidence from domain A: [evidence].
       Evidence from domain B: [evidence].
       Should this graduate to permanent meta-knowledge?"
  --> Each reviewer evaluates from their perspective:
      - Clark: Is this ontologically sound? Does it generalize?
      - Karpathy: Is the evidence statistically meaningful? Any confounders?
      - ClaudeAIExpert: Is this implementable? Any context window concerns?
  --> 2/3 approve --> graduate
  --> 1/3 or fewer --> stay in proposed/
```

---

## 7. Error Attribution: Shadow Query System

When Neo.Oracle gives a wrong answer:

```
1. Run shadow query: /graphify query "[original question]"
2. Compare:
   - Shadow CORRECT + Oracle WRONG --> Fix consumer agent (prompt/skill issue)
   - Shadow WRONG/EMPTY + Oracle WRONG --> Fix ontology (write to gaps.md)
   - Shadow PARTIAL --> Add relationship edges to connect existing knowledge
```

---

## 8. Consumer Feedback Loop

Consumer agents write to `ontology/docs/gaps.md`:

```markdown
## Gap: [title]
- **Reported by:** Neo.Oracle:{agent-name}
- **Query that failed:** "[the question]"
- **What was missing:** [description]
- **Priority:** HIGH | MEDIUM | LOW
- **Status:** OPEN | IN_PROGRESS | RESOLVED
```

**Resolution autonomy by phase:**

| Phase | Gap from existing sources | Gap needing new sources |
|-------|--------------------------|------------------------|
| 1 | Ask user | Escalate |
| 2 | Fix autonomously, show diff | Escalate |
| 3 | Fix autonomously, log only | Escalate |

New source acquisition ALWAYS requires user approval.

### Usage Log (New Mechanism)

Oracle tracks which ontology nodes it actually queries in `ontology/docs/usage-log.md`.
Entities that Oracle NEVER uses are candidates for removal (simplification).

---

## 9. Shared Knowledge Contract

```
Neo.Architect WRITES:
  - ontology/entities/*.yaml
  - ontology/rules/*.yaml
  - ontology/skills/*.md
  - graphify-out/graph.json
  - QA_REPORT.md
  - iterations.tsv

Neo.Oracle READS:
  - All of the above

Neo.Oracle WRITES:
  - ontology/docs/gaps.md (gap reports)
  - ontology/docs/usage-log.md (which entities/rules were actually used)

Neo.Architect READS:
  - gaps.md (feedback from Oracle)
  - usage-log.md (which parts of ontology are actually useful)
```

---

## 10. Full Team Communication Map

```
+-----------------------------------------------------------+
|                        User (Human)                        |
|  Reviews: commitment journal, QA reports, plateau msgs     |
|  Approves: phase promotions, new sources, structural       |
|            gap resolutions (Phase 1-2)                     |
+----------+------------------------+-----------------------+
           | escalations            | approvals
           v                        v
+---------------------+    +---------------------+
|   Neo.Architect      |<-->|   Neo.Oracle         |
|                      |    |                      |
|  Builds ontology     |    |  Uses ontology       |
|  Runs iteration loop |    |  Spawns domain agents|
|  Fixes gaps          |    |  Logs gaps + usage   |
|                      |    |                      |
|  WRITES: ontology/*  |    |  WRITES: gaps.md     |
|  READS: gaps.md      |    |         usage-log.md |
|         usage-log.md |    |  READS: ontology/*   |
+----------+-----------+    +----------------------+
           |
           | triggers QA
           v
+-----------------------------------------+
|         QA Review Committee             |
|                                         |
|  Clark-Reviewer                         |
|    Ontological rigor, commitments       |
|    Also: gap escalation advisor         |
|    Also: cross-domain graduation judge  |
|                                         |
|  Karpathy-Reviewer                      |
|    Consistency, hallucination, evidence  |
|    Also: cross-domain graduation judge  |
|                                         |
|  ClaudeAIExpert-Reviewer                |
|    Implementation, citations, structure |
|    Also: cross-domain graduation judge  |
|                                         |
|  Triggered by:                          |
|  1. Post-build / iteration convergence  |
|  2. Structural gap escalation           |
|  3. Meta-rule graduation proposal       |
+-----------------------------------------+
```

---

## 11. Learning Flow

### Within a Session

```
Oracle uses ontology --> hits gap --> writes gaps.md --> Architect reads --> fixes
```

### Across Sessions

- Session N: Architect builds domain A, Oracle uses it
- Session N+1: Architect reads gaps.md from Oracle, fixes gaps, proposes meta-learnings
- Session N+2: Architect builds domain B, applies meta-learnings, measures improvement
- Session N+3: QA reviewers validate graduation proposal

### Across Phases

- **Phase 1:** All learning surfaces to user. Dense feedback, slow but accurate.
- **Phase 2:** Tactical learning autonomous. Strategic surfaces to user.
- **Phase 3:** All learning autonomous with audit log. QA reviewers are the check, not user.

---

## 12. Neo.Architect <-> Neo.Oracle Communication

### Synchronous (Same Session)

```
Neo.Oracle:{agent} answers question
  --> Gets it wrong
  --> Runs shadow query against ontology
  --> Determines: ontology gap
  --> Writes to gaps.md immediately
  --> If Neo.Architect is active in same session:
        Sends direct message: "Gap found: [description].
        Shadow query returned empty for [query].
        Priority: [HIGH/MEDIUM/LOW]"
  --> Neo.Architect receives, prioritizes, may fix in real-time
```

### Asynchronous (Across Sessions)

```
Session N: Neo.Oracle:{agent} logs gaps to gaps.md
Session N+1: Neo.Architect reads gaps.md at startup (step 3 of startup protocol)
  --> Prioritizes gaps by severity
  --> Fixes autonomous gaps before starting new work
  --> Escalates structural gaps to user
```
