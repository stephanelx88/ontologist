# DREA Loop and Iteration Protocol

Neo's learning system operates at three timescales through the DREA loop,
graduated memory, an immune system, and an autoresearch-style iteration protocol.

---

## 1. The DREA Loop

Every Neo action follows **Do-Receive-Evaluate-Adapt**.

### Do

Neo performs an ontological action (extract, structure, generate, simulate).
Each action logged with `action_id`, timestamp, input hash, phase.

### Receive

Feedback from four sources:

| Source | Signal | Latency | Reliability |
|--------|--------|---------|-------------|
| Held-out test | Prediction accuracy (0-100%) | Minutes | HIGH |
| QA loop | Pass/Review/Fail + issues | Minutes | HIGH |
| Consumer agent | Gap logs, error traces | Hours-days | MEDIUM |
| Human review | User's corrections | Hours-days | HIGHEST |

### Evaluate

Classify errors into taxonomy:

| Error Type | Signal | Fix Target |
|------------|--------|------------|
| extraction_miss | Gap logged; found on re-read | Extraction pass |
| hallucinated_link | Critic flags UNSOURCED edge | Critic pass |
| wrong_abstraction | Consumer can't map ontology to task | Structuring + binding |
| causal_overclaim | Correlation presented as causation | Causal edge extraction |
| stale_knowledge | Newer source contradicts | Deprecation |
| meta_overgeneralization | Domain B worse than baseline | Immune system |

### Adapt

Actions specific to error type:

| Error Type | Adaptation | Writes To |
|------------|-----------|-----------|
| extraction_miss | Re-read with targeted query | Domain ontology + extraction checklist |
| hallucinated_link | Remove edge; tighten critic | Domain ontology + anti-patterns |
| wrong_abstraction | Adjust granularity | Domain ontology + templates |
| causal_overclaim | Downgrade to `type: correlates` | Domain ontology + anti-patterns |
| stale_knowledge | Deprecate; flag for re-extraction | Domain ontology + deprecated/ |
| meta_overgeneralization | Narrow meta-rule scope | Graduated meta-rule updated |

---

## 2. Three Timescales

### Within-Domain (minutes to hours)
- **Scope:** Single ontology extraction session
- **What changes:** The domain ontology itself
- **Governance:** Autonomous for extraction corrections, staged for new causal claims
- Analogous to SGD updates within one training epoch

### Cross-Domain (days to weeks)
- **Scope:** Patterns across 2+ domains
- **What changes:** Meta-knowledge — patterns, anti-patterns, templates
- **Governance:** Proposed → validated across domains → graduated (or deprecated)
- Analogous to learning rate schedule adjustments

### Lifetime (months to years)
- **Scope:** Neo's core capabilities and identity
- **What changes:** DREA parameters, extraction strategies, SKILL.md
- **Governance:** NEVER autonomous. Always requires user review.
- Analogous to architecture changes between model generations

---

## 3. Graduated Memory Model

```
neo/meta-knowledge/
├── proposed/                    # Tier 1: Observations (auto-write)
│   ├── domain-observations/     # Raw observations from current domain
│   ├── cross-domain-patterns/   # Candidate meta-rules
│   └── anti-pattern-candidates/ # Candidate anti-patterns
│
├── graduated/                   # Tier 2: Validated (earned promotion)
│   ├── meta-patterns/           # Confirmed cross-domain patterns
│   ├── anti-patterns/           # Confirmed pitfalls to avoid
│   ├── domain-templates/        # Reusable starting structures
│   └── deprecated/              # Retired rules (kept for audit)
│
├── core/                        # Tier 3: Foundational (user-approved only)
│   ├── extraction-strategy.md
│   ├── critic-protocol.md
│   ├── structuring-rules.md
│   └── drea-parameters.md
│
└── identity/                    # Tier 4: Immutable
    └── SKILL.md                 # Changes only with user
```

**Graduation Criteria:**

| From → To | Criteria |
|-----------|----------|
| Observation → Proposed | Auto (observed in 1 domain) |
| Proposed → Graduated | Validated across 2+ domains with >5% score improvement |
| Graduated → Core | Proven across 5+ domains, user explicitly approves |
| Any → Deprecated | Not validated after 3 attempts, OR user rejects, OR score regression >5% |

**Deprecation Sweeps:** Every 10 domains processed, Neo audits graduated rules.
Stale or underperforming rules moved to `deprecated/` with full audit trail.

---

## 4. Immune System

### Provenance Tracking

Every meta-knowledge carries: origin domain, evidence, corroboration history,
application results, confidence, scope.

### Validation-Before-Graduation

No meta-knowledge moves from `proposed/` to `graduated/` without:
1. Cross-domain test (2+ domains)
2. Score improvement test (>5% in validated domains)
3. Non-regression test (no domain scored worse >3%)
4. Phase gate (Phase 1 needs user approval; Phase 2+ auto-graduate if tests pass)

### Periodic Forgetting

Every 10 domains:
- Last successfully applied >5 domains ago → flag for review
- Lifetime success rate <60% → flag for review
- Ever caused >5% regression → immediately deprecate

---

## 5. Held-Out Prediction Test (PPT)

**The primary quantitative metric for ontology quality.**

### Setup

1. Split source material 80/20 by content units (deterministic, hash-based, stratified)
2. Build ontology from 80%
3. Generate test questions from 20%:
   - FACTUAL (20% weight): "What is X?"
   - RELATIONAL (30%): "How does X relate to Y?"
   - CAUSAL (35%): "What happens when X?"
   - COUNTERFACTUAL (15%): "What if X didn't exist?"

### Scoring

- CORRECT: 1.0 (matches held-out content)
- PARTIAL: 0.5 (captures main idea, misses detail)
- WRONG: 0.0 (contradicts held-out content)
- ABSTAIN: 0.3 (honest "I don't know" — better than wrong)

### Interpretation

| Score | Meaning | Action |
|-------|---------|--------|
| >85% | Excellent | Ship it |
| 70-85% | Good | One more iteration |
| 50-70% | Mediocre | Review extraction strategy |
| <50% | Poor | Re-extract from scratch |

---

## 6. Autoresearch Mapping

| autoresearch | Neo Equivalent |
|-------------|----------------|
| `train.py` (one modifiable file) | `ontology/` workspace (one modifiable directory) |
| `prepare.py` (fixed eval, read-only) | `eval/` — held-out test + structural checks (READ-ONLY) |
| `program.md` (human instructions) | `SKILL.md` (Neo's cognitive operations protocol) |
| `val_bpb` (single metric) | `neo_score` — weighted composite (see formula) |
| `results.tsv` | `iterations.tsv` (commit, score, status, description) |
| 5-minute budget | Fixed token budget per iteration (~30K tokens) |
| `NEVER STOP` | `NEVER STOP` — iterate until user interrupts or plateau |

---

## 7. The Neo Score (Single Scalar)

```python
# eval/evaluate.py — READ-ONLY, never modified by Neo

def compute_neo_score(ontology, held_out_passages, source_text):
    ppt_score = passage_prediction_test(ontology, held_out_passages)  # 40%
    structural_score = structural_check(ontology)                      # 20%
    coverage_score = coverage_scan(ontology, source_text)              # 25%
    coherence_score = coherence_check(ontology)                        # 15%

    return ppt_score * 0.40 + structural_score * 0.20 + \
           coverage_score * 0.25 + coherence_score * 0.15
```

---

## 8. The Iteration Loop

```
SETUP:
1. User provides source material
2. Neo.Architect produces initial ontology (7 cognitive operations)
3. eval/ reserves 10 held-out passages (Neo never sees these)
4. Baseline neo_score computed and logged
5. git commit baseline

LOOP FOREVER:
1. Read git state + iterations.tsv (what worked, what didn't)
2. Identify ONE highest-impact improvement (Gap Sensing priority order):
   a. Fix structural failures (free points)
   b. Fill coverage gaps (re-read source for missed concepts)
   c. Improve predictions (revise hierarchies, add causal chains)
   d. Resolve contradictions
   e. Simplify (remove elements that don't improve score)
3. Modify ontology workspace — ONE change per iteration
4. git commit -m "neo-iter-N: {description}"
5. Run evaluation: ./eval/run_eval.sh > eval.log 2>&1
6. Read results: grep neo_score eval.log
7. DECISION:
   - neo_score improved → KEEP commit
   - neo_score equal + simpler → KEEP (simplification win)
   - neo_score decreased → git reset --hard HEAD~1
8. Log to iterations.tsv
9. Plateau check: 10 consecutive reverts → pause, notify user
10. NEVER STOP unless plateaued or user interrupts
```

---

## 9. Simplicity Criterion

From Karpathy's autoresearch:
- 0.01 improvement + 20 lines of complexity? Probably not worth it.
- 0.01 improvement from DELETING code? Definitely keep.
- ~0 improvement but simpler? Keep.
- Threshold: complexity justified if neo_score improves >2 points.

---

## 10. iterations.tsv Format

```tsv
iteration	commit	neo_score	ppt	structural	coverage	coherence	loc	status	description
1	a3f2d1e	42.30	35	80	45	60	120	baseline	Initial extraction
2	b7c4e2f	48.50	40	85	50	65	135	kept	Added money hierarchy
3	c9d1f3a	47.20	38	85	52	60	142	reverted	Elasticity as entity (hurt PPT)
4	d2e5a4b	51.80	45	90	55	65	138	kept	Elasticity as property instead
```

---

## 11. NEVER STOP Policy

| Phase | Behavior |
|-------|----------|
| 1 | Loop DISABLED. One change at a time, user approves. |
| 2 | Runs up to `max_autonomous_iterations` (default 5). Shows log to user. |
| 3 | NEVER STOP. Runs until user interrupts or context limit (80%). |

---

## 12. Overnight Example

```
22:00 — User: "/neo process Mehrling, iterate overnight"
22:05 — Baseline: neo_score = 42.3
22:06 — Loop begins (~4-6 iterations/hour on Opus)
06:00 — 96 iterations complete. neo_score = 83.2
06:05 — QA loop runs. 2 findings (MEDIUM, LOW). Auto-fixed.
06:10 — Final: neo_score = 84.1, 94 entities, 168 edges, 3 gaps remaining

08:00 — User reads iterations.tsv:
  "Started at 42.3, ended at 84.1. 47 kept, 49 reverted.
   Key wins: temporal chains (+5), hierarchy (+5), crisis counterfactuals (+5).
   Plateau at iter 88. 3 gaps need new sources."
```

---

## 13. Compounding Skill Library

As Neo processes more domains, extraction speed and quality compound:

```
Domain 1:  Baseline. No meta-knowledge. 5 iterations to reach 75%.
Domain 5:  3 meta-patterns applied. 3 iterations to reach 75%.
Domain 10: 12 meta-patterns. 1-2 iterations. Most extraction near-automatic.
```

**Skill library structure:**

```
neo/meta-knowledge/graduated/
├── meta-patterns/           # "For hierarchical domains, start top-down"
├── anti-patterns/           # "Co-occurrence ≠ causation"
├── domain-templates/        # Starter structures per archetype
└── extraction-strategies/   # Per input type (PDF, code, interview)
```

Each skill file has: id, name, type, confidence, scope, validated_in, failed_in,
graduated date, lifetime success rate, and detailed procedure.
