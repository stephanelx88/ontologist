# Neo Ontologist Agent — Detailed Specification

**Version:** 1.0
**Date:** 2026-04-09
**Authors:** ClarkOntologist, Karpathy, ClaudeAIExpert, Son (Human)
**Status:** Design Complete — Ready for Implementation

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [System Architecture](#2-system-architecture)
3. [Cognitive Architecture](#3-cognitive-architecture)
4. [Learning System](#4-learning-system)
5. [Implementation Architecture](#5-implementation-architecture)
6. [Quality Assurance](#6-quality-assurance)
7. [Visualization](#7-visualization)
8. [Design Decisions Log](#8-design-decisions-log)

---

## 1. Executive Summary

### What Neo Is

Neo is a **persistent ontologist agent** that extracts, organizes, and evolves domain ontologies from any input (PDFs, code, data, conversations). Neo produces executable ontologies as Python classes, interactive knowledge graph visualizations, and deployable domain agents — all while learning and improving across domains.

### Two Subsystems, One Interface

- **Neo.Architect** — the ontologist. Builds, validates, and evolves domain ontologies.
- **Neo.Oracle** — a router that spawns domain-specific consumer agents (PerryAgent, FraudDetector, etc.) with the appropriate ontology loaded.

The user types `/neo` for everything. Neo auto-detects intent and routes internally.

```
User: /neo
  │
  ├─ "Build/extract/organize" intent  → Neo.Architect
  ├─ "Teach/explain/analyze" intent   → Neo.Oracle → spawns consumer agent
  └─ "Visualize/explore" intent       → Neo.Visualize → opens atlas.html
```

### Core Principles

1. **One interface, smart routing** — user never manages complexity
2. **Phased autonomy** — earned, not scheduled, with permanent human veto on ontological commitments
3. **DREA loop** — Do, Receive feedback, Evaluate, Adapt — at every level
4. **Honest uncertainty** — every claim carries confidence, provenance, and source type
5. **Auto-detect knowledge type** — proprietary vs. domain expertise, never asks user
6. **Executable ontologies** — Python classes, not YAML. Testable, benchmarkable, debuggable.
7. **Quality over cost** — Opus 4.6 for everything

### Outcomes (What Neo Produces)

| Output | Format | Purpose |
|--------|--------|---------|
| Domain agent skill | `become-{domain}/SKILL.md` | Deployable consumer agent |
| Knowledge graph | `graph.json` + `galaxy.html` | Queryable, visualizable domain map |
| Executable ontology | Python classes | Testable, simulatable domain model |
| QA report | `QA_REPORT.md` | Three-reviewer quality verdict |
| Commitment journal | YAML | Every "what is real" decision with rationale |
| Atlas visualization | `atlas.html` | 3D galaxy + dashboard + simulation playground |
| Neo's meta-learnings | claude-mem + `graduated/` | Compounding cross-domain wisdom |

### Inspiration

- **Karpathy's autoresearch** — fixed infra + single modifiable artifact + evaluation loop + NEVER STOP
- **WorldCoder (NeurIPS 2024)** — executable world models as code, 10,000x faster than deep RL
- **Voyager (NVIDIA)** — compounding skill library, 3.3x more discoveries
- **Graphiti/Zep** — temporal knowledge graphs with validity windows
- **DeepMind Aletheia** — decouple generation from verification

---

## 2. System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         /neo                                 │
│                    (single entry point)                       │
│                                                              │
│    ┌──────────────────┐          ┌──────────────────┐       │
│    │  Neo.Architect    │          │   Neo.Oracle      │       │
│    │  (builds ontology)│          │   (uses ontology) │       │
│    │                   │          │                   │       │
│    │  7 Cognitive Ops  │  ──────► │  Routes to:       │       │
│    │  DREA Loop        │  ontology│  - PerryAgent     │       │
│    │  QA Loop          │          │  - FraudDetector  │       │
│    │  Learning System  │  ◄────── │  - [any agent]    │       │
│    │                   │  gaps.md │                   │       │
│    └──────────────────┘          └──────────────────┘       │
│              │                                               │
│              ▼                                               │
│    ┌──────────────────────────────────────────┐              │
│    │           Three Memory Systems           │              │
│    │                                          │              │
│    │  Episodic: claude-mem (learnings)        │              │
│    │  Semantic: Graphify (knowledge graphs)   │              │
│    │  Procedural: SKILL.md (how Neo works)    │              │
│    └──────────────────────────────────────────┘              │
│              │                                               │
│              ▼                                               │
│    ┌──────────────────────────────────────────┐              │
│    │           Visualization Layer            │              │
│    │                                          │              │
│    │  galaxy.html — 3D exploration            │              │
│    │  dashboard.html — health + audit         │              │
│    │  playground.html — simulation sandbox    │              │
│    └──────────────────────────────────────────┘              │
└─────────────────────────────────────────────────────────────┘
```

### Autonomy Model

```
Phase 1 (Co-creation)
  │  Son and Neo work as partners. Socratic dialogue.
  │  All commitments surface to Son.
  │  Graduation: >80% prediction accuracy across 3 consecutive domains
  ▼
Phase 2 (Propose+Approve)
  │  Neo works independently, Son reviews.
  │  Structural commitments auto-commit. Foundational ones need Son.
  │  Graduation: Ontologies pass validation without correction on first attempt
  ▼
Phase 3 (Graduated Autonomy)
  │  Neo earns trust per capability type.
  │  Most operations autonomous with audit log.
  │
  ■  PERMANENT: Ontological commitments in NEW domains always need human sign-off.
     Meta-reasoning changes always need human sign-off. This never changes.
```

### Autoresearch Adaptation

Mapping Karpathy's autoresearch pattern to Neo:

| autoresearch | Neo Equivalent |
|-------------|----------------|
| `prepare.py` (fixed, read-only) | Graphify pipeline + QA loop agents + held-out test framework |
| `train.py` (agent modifies) | The domain ontology workspace (entities, rules, skills, causal edges) |
| `program.md` (human writes) | Neo's SKILL.md + domain-specific constraints from Son |
| `val_bpb` (single metric) | Held-out prediction score (0-100%) + QA scorecard |
| `results.tsv` (experiment log) | `iterations.tsv` (commit, score, qa_status, changes_made) |
| `LOOP FOREVER` | DREA loop with max 5 iterations per session (configurable) |
| `git commit` per experiment | Each ontology revision committed for revert capability |
| Keep if improved, revert if not | Same — score must improve or changes are reverted |

### Neo's Iteration Protocol (Autoresearch-Adapted)

```
LOOP (max iterations from neo-trust.yaml, default 5):

1. Look at current ontology state (version, scores, gaps)
2. Identify highest-impact improvement target from eval report
3. Make targeted change to ontology workspace
4. git commit -m "neo-iteration-N: [description of change]"
5. Run held-out prediction test → new_score
6. Run structural validation → coherence_check
7. If new_score > baseline AND coherence_check PASS:
     Accept. Update baseline. Log to iterations.tsv as "keep"
   Else:
     git revert. Log to iterations.tsv as "discard"
8. Log: commit_hash, score, status, description
9. If score improvement < 2% (diminishing returns): STOP
10. Else: continue to next iteration

Iterations.tsv format:
commit    score    qa_status    status    description
a1b2c3d   68.0     n/a         keep      baseline extraction
b2c3d4e   72.0     pass        keep      added causal edges for crisis cascade
c3d4e5f   71.5     pass        discard   restructured hierarchy (regression)
d4e5f6g   76.0     pass        keep      filled 2 coverage gaps from ch.6
```

---

## 3. Cognitive Architecture

### Overview

Neo's cognitive architecture consists of seven ontological operations, a commitment journal, a gap sensing protocol, and a knowledge state model. These components work together to transform unstructured domain knowledge into executable, testable, honest ontologies.

The seven operations are not sequential steps — they are **concurrent cognitive processes** that activate based on input context. Multiple operations fire simultaneously during any extraction or reasoning task. The architecture is inspired by dual-process cognitive theory: some operations are fast and pattern-based (Ontological Listening, Gap Sensing, Analogical Transfer), while others are slow and deliberative (Commitment Weighing, Abstraction Calibration, Contradiction Integration, Self-Aware Limitation).

---

### The Seven Cognitive Operations

#### Operation 1: Ontological Listening

**Purpose:** Detect implicit ontological structure in domain input — entities, relationships, and causal models that are assumed but never stated.

**Triggers:**
- Any new text input (document, conversation, transcript)
- Domain expert interview or Q&A session
- API schema, database schema, or configuration file ingestion

**Process:**
1. Parse input for explicit entities (named things, defined concepts)
2. Identify implicit entities (referenced but undefined concepts, assumed categories)
3. Map assumed relationships (hierarchical, causal, temporal, spatial)
4. Detect domain-specific terminology that diverges from common usage
5. Flag unstated assumptions that the source takes for granted

**Produces:**
```yaml
listening_output:
  explicit_entities:
    - name: "dealer"
      source: "Mehrling ch.2 p.34"
      definition_given: true
  implicit_entities:
    - name: "hierarchy of money"
      source: "Mehrling ch.2 p.41"
      definition_given: false
      inferred_meaning: "Ranked structure of monetary promises where position determines liquidity and safety"
      confidence: 0.8
  assumed_relationships:
    - subject: "bank deposit"
      predicate: "is_a"
      object: "monetary promise"
      stated_explicitly: false
      evidence: "Mehrling consistently treats deposits as promises banks make to depositors"
  terminology_flags:
    - term: "dealer"
      common_meaning: "seller of goods"
      domain_meaning: "market-maker who holds inventory and absorbs imbalances"
      disambiguation_required: true
  unstated_assumptions:
    - assumption: "Money is fundamentally relational, not substantive"
      evidence: "Pervades all examples but never stated as axiom"
      ontological_impact: "high — determines whether primary entities are things or relationships"
```

**Knowledge type behavior:**
- Proprietary mode: Listen for structure but NEVER infer beyond what's stated. Flag implicit entities as "requires confirmation from source owner."
- Expertise mode: Actively infer implicit structure. Cross-reference with Claude's training knowledge to validate inferences.

---

#### Operation 2: Commitment Weighing

**Purpose:** Make and record ontological commitments — decisions about what entities, relationships, and structures are "real" in the domain model. Every commitment constrains future modeling options.

**Triggers:**
- Ontological Listening produces implicit entities that need to be formalized or rejected
- Multiple valid modeling approaches exist for the same domain concept
- A downstream agent spec requires a specific entity structure
- User provides guidance that resolves an ambiguity

**Process:**
1. Identify the decision point (what needs to be committed?)
2. Enumerate alternatives (minimum 2, ideally 3+)
3. For each alternative, assess:
   - Faithfulness to source material
   - Utility for downstream agents
   - Composability with existing ontology
   - Reversibility cost (how hard to change later)
   - Abstraction level fit
4. Make the commitment
5. Record in Commitment Journal

**Escalation rules:**
- Phase 1: ALL commitments surface to user for approval
- Phase 2: Structural commitments auto-commit. Foundational commitments surface to user.
- Phase 3: All auto-commit. User reviews commitment journal asynchronously.
- **PERMANENT:** Ontological commitments about what's "real" in a NEW domain always require human ratification, regardless of phase.

---

#### Operation 3: Analogical Transfer

**Purpose:** Bootstrap ontological structure in unfamiliar domains by pattern-matching against known domain archetypes and previously built ontologies.

**Triggers:**
- Neo encounters a new domain for the first time
- A domain concept has no direct precedent but resembles something from another domain

**Process:**
1. Classify the input domain by archetype:
   - **Inspection domain** (fraud, QA, audit) — artifact → rules → anomaly detection
   - **Diagnostic domain** (HVAC, medical, debugging) — symptoms → causal chains → root cause
   - **Optimization domain** (energy, logistics, finance) — variables → constraints → objective
   - **Theoretical framework** (academic, philosophical) — constructs → tensions → regime dynamics
   - **Operational domain** (manufacturing, service delivery) — process → steps → exceptions
2. Load the archetype's starter ontology pattern
3. Map source material concepts onto the archetype's entity slots
4. Identify where the analogy breaks down
5. Record the analogy and its limits in the commitment journal

**Produces:**
```yaml
analogical_transfer:
  source_domain: "Vietnamese banking fraud detection"
  target_domain: "insurance claims fraud"
  archetype: "inspection"
  mappings:
    - source: "bank statement" → target: "insurance claim form" (confidence: 0.9)
    - source: "transaction" → target: "claim line item" (confidence: 0.85)
  analogy_limits:
    - "Banking fraud has running balances; insurance claims do not have cumulative state"
  archetype_modifications_needed:
    - "Add 'assessor' entity type not present in banking archetype"
```

---

#### Operation 4: Gap Sensing

**Purpose:** Detect structural holes in the ontology — missing entities, unrepresented relationships, absent causal chains.

**Triggers:**
- After any ontology modification (continuous background process)
- After Passage Prediction Test reveals uncovered passages
- After downstream agent reports a question it couldn't answer
- After QA review identifies missing coverage

**Process:**
1. **Coverage scan:** Compare ontology scope against source material scope
2. **Structural integrity:** Every entity has relationships, rules, and hierarchy position
3. **Causal completeness:** Every effect has a cause, no dangling links
4. **Archetype comparison:** What does the archetype have that we don't?
5. **Reflection probe:** "What does this domain's problem structure demand that I haven't represented?"

**Gap Classification and Routing:**

| Gap Type | Detection | Resolution | Autonomy |
|----------|-----------|------------|----------|
| Coverage (source has it, Neo missed) | Re-read source, extract | Fully autonomous |
| Source (source doesn't cover it) | Search supplementary sources | Semi-autonomous (flag user) |
| Structural (model can't represent it) | Revise commitments, restructure | Escalate to user |
| Temporal (knowledge may be outdated) | Check for newer sources | Semi-autonomous |

**Gap resolution statistics:** ~60% auto-resolve (missed extraction), ~25% synthesize+stage, ~15% escalate.

---

#### Operation 5: Abstraction Calibration

**Purpose:** Find the optimal level of abstraction for each ontology element.

**Test:** "If I give a downstream agent ONLY this description, can it execute its scenarios?"
- If no → too abstract
- If the agent has information it never uses → too concrete

**Goldilocks Scale:**
1. Too abstract (useless for decisions)
2. Slightly abstract (requires interpretation)
3. Right level (directly actionable)
4. Slightly concrete (over-specified)
5. Too concrete (locked to one implementation)

---

#### Operation 6: Contradiction Integration

**Purpose:** Represent contradictions honestly rather than silently resolving them.

**Resolution types:**
- **Factual contradiction** (one is wrong) → resolve with evidence
- **Perspective contradiction** (different valid viewpoints) → represent both
- **Context-dependent** (both true in different situations) → encode conditions
- **Genuine open question** (nobody knows) → mark as unresolved

**Produces:**
```yaml
contradiction_register:
  - id: TENSION-001
    type: "context-dependent"
    claim_a: "Central bank intervention prevents systemic collapse"
    claim_b: "Central bank backstop creates moral hazard"
    resolution: "Both simultaneously true — this IS the core tension"
    agent_guidance: "Present BOTH sides. This tension is the theory, not a bug."
```

---

#### Operation 7: Self-Aware Limitation

**Purpose:** Maintain honest assessment of what Neo knows, doesn't know, and what KIND of thing it doesn't know.

**Confidence tiers per element:**
- **HIGH:** Multiple sources, internally coherent, tested
- **MEDIUM:** Single source, Neo's interpretation, untested
- **LOW:** Synthesized by Neo, no source validation
- **GAP:** Known to be needed, not yet represented

**Model boundaries (first-class in executable ontology):**
```python
@property
def model_boundaries(self) -> list[ModelBoundary]:
    return [
        ModelBoundary("DeFi/crypto not covered", confidence=0.2),
        ModelBoundary("Quantitative predictions unreliable", confidence=0.1),
    ]
```

**Epistemic status progression:**
- `exploratory` → `draft` → `validated` → `production`
- Each transition has specific criteria (coverage %, PPT score, QA pass, expert validation)

---

### The Commitment Journal

Every ontological commitment recorded with full context:

```yaml
commitment_journal:
  - id: COMMIT-001
    timestamp: "2026-04-09T18:30:00Z"
    domain: "mehrling-money-view"
    decision: "Primary entity is 'monetary promise' rather than 'money'"
    alternatives_considered:
      - option: "Money as primary entity with subtypes"
        faithfulness_to_source: 0.4
        agent_utility: 0.7
      - option: "Monetary promise as primary entity"
        faithfulness_to_source: 0.95
        agent_utility: 0.8
    chosen: "monetary promise"
    rationale: "Mehrling's core insight is that relationships matter more than things"
    cost: "Quantity-based reasoning becomes harder"
    reversibility: "medium"
    confidence: 0.85
    outcome: null  # confirmed | weakened | refuted — set after DREA evaluation
    user_approved: true
```

---

### Operation Interaction Map

```
                    ┌─────────────────┐
     Input ───────►│   Ontological    │──── entities, relationships, assumptions
                    │   Listening      │
                    └────────┬────────┘
                             │ candidates
                             ▼
┌──────────────┐    ┌─────────────────┐    ┌──────────────────┐
│  Analogical  │───►│   Commitment    │◄───│   Abstraction    │
│  Transfer    │    │   Weighing      │    │   Calibration    │
└──────────────┘    └────────┬────────┘    └──────────────────┘
                             │ commitments
                             ▼
                    ┌─────────────────┐
                    │  Contradiction  │
                    │  Integration    │
                    └────────┬────────┘
                             │ tensions + resolved commitments
                             ▼
                    ┌─────────────────┐
                    │   Gap Sensing   │◄──── continuous background scan
                    └────────┬────────┘
                             │ gaps + coverage scores
                             ▼
                    ┌─────────────────┐
                    │   Self-Aware    │──── knowledge state model
                    │   Limitation    │──── epistemic status
                    └─────────────────┘──── model boundaries
```

---

## 4. Learning System

### 4.1 The DREA Loop

Every Neo action follows Do-Receive-Evaluate-Adapt.

#### Do
Neo performs an ontological action (extract, structure, generate, simulate). Each action logged with `action_id`, timestamp, input hash, phase.

#### Receive
Feedback from four sources:

| Source | Signal | Latency | Reliability |
|--------|--------|---------|-------------|
| Held-out test | Prediction accuracy (0-100%) | Minutes | HIGH |
| QA loop | Pass/Review/Fail + issues | Minutes | HIGH |
| Consumer agent | Gap logs, error traces | Hours-days | MEDIUM |
| Human review | Son's corrections | Hours-days | HIGHEST |

#### Evaluate
Classify errors into taxonomy:

| Error Type | Signal | Fix Target |
|------------|--------|------------|
| extraction_miss | Gap logged; found on re-read | Extraction pass |
| hallucinated_link | Critic flags UNSOURCED edge | Critic pass |
| wrong_abstraction | Consumer can't map ontology to task | Structuring + binding |
| causal_overclaim | Correlation presented as causation | Causal edge extraction |
| stale_knowledge | Newer source contradicts | Deprecation |
| meta_overgeneralization | Domain B worse than baseline | Immune system |

#### Adapt
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

### 4.2 Three Timescales

#### Within-Domain (minutes to hours)
- **Scope:** Single ontology extraction session
- **What changes:** The domain ontology itself
- **Governance:** Autonomous for extraction corrections, staged for new causal claims
- Analogous to SGD updates within one training epoch

#### Cross-Domain (days to weeks)
- **Scope:** Patterns across 2+ domains
- **What changes:** Meta-knowledge — patterns, anti-patterns, templates
- **Governance:** Proposed → validated across domains → graduated (or deprecated)
- Analogous to learning rate schedule adjustments

#### Lifetime (months to years)
- **Scope:** Neo's core capabilities and identity
- **What changes:** DREA parameters, extraction strategies, SKILL.md
- **Governance:** NEVER autonomous. Always requires Son's review.
- Analogous to architecture changes between model generations

---

### 4.3 Graduated Memory Model

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
├── core/                        # Tier 3: Foundational (Son-approved only)
│   ├── extraction-strategy.md
│   ├── critic-protocol.md
│   ├── structuring-rules.md
│   └── drea-parameters.md
│
└── identity/                    # Tier 4: Immutable
    └── SKILL.md                 # Changes only with Son
```

**Graduation Criteria:**

| From → To | Criteria |
|-----------|----------|
| Observation → Proposed | Auto (observed in 1 domain) |
| Proposed → Graduated | Validated across 2+ domains with >5% score improvement |
| Graduated → Core | Proven across 5+ domains, Son explicitly approves |
| Any → Deprecated | Not validated after 3 attempts, OR Son rejects, OR score regression >5% |

**Deprecation Sweeps:** Every 10 domains processed, Neo audits graduated rules. Stale or underperforming rules moved to `deprecated/` with full audit trail.

---

### 4.4 Immune System

#### Provenance Tracking
Every meta-knowledge carries: origin domain, evidence, corroboration history, application results, confidence, scope.

#### Validation-Before-Graduation
No meta-knowledge moves from `proposed/` to `graduated/` without:
1. Cross-domain test (2+ domains)
2. Score improvement test (>5% in validated domains)
3. Non-regression test (no domain scored worse >3%)
4. Phase gate (Phase 1 needs Son's approval; Phase 2+ auto-graduate if tests pass)

#### Periodic Forgetting
Every 10 domains:
- Last successfully applied >5 domains ago → flag for review
- Lifetime success rate <60% → flag for review
- Ever caused >5% regression → immediately deprecate

---

### 4.5 Held-Out Prediction Test

**The primary quantitative metric for ontology quality.**

#### Setup
1. Split source material 80/20 by content units (deterministic, hash-based, stratified)
2. Build ontology from 80%
3. Generate test questions from 20%:
   - FACTUAL (20% weight): "What is X?"
   - RELATIONAL (30%): "How does X relate to Y?"
   - CAUSAL (35%): "What happens when X?"
   - COUNTERFACTUAL (15%): "What if X didn't exist?"

#### Scoring
- CORRECT: 1.0 (matches held-out content)
- PARTIAL: 0.5 (captures main idea, misses detail)
- WRONG: 0.0 (contradicts held-out content)
- ABSTAIN: 0.3 (honest "I don't know" — better than wrong)

#### Interpretation
| Score | Meaning | Action |
|-------|---------|--------|
| >85% | Excellent | Ship it |
| 70-85% | Good | One more iteration |
| 50-70% | Mediocre | Review extraction strategy |
| <50% | Poor | Re-extract from scratch |

---

### 4.6 Compounding Skill Library

As Neo processes more domains, extraction speed and quality compound:

```
Domain 1: Baseline. No meta-knowledge. 5 iterations to reach 75%.
Domain 5: 3 meta-patterns applied. 3 iterations to reach 75%.
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

Each skill file has: id, name, type, confidence, scope, validated_in, failed_in, graduated date, lifetime success rate, and detailed procedure.

---

## 5. Implementation Architecture

### 5.1 Three Memory Systems

#### Episodic Memory (claude-mem MCP)

**Purpose:** Cross-session experiential learning.

**Tools:**
- `mcp__plugin_claude-mem_mcp-search__save_memory` — save a learning
- `mcp__plugin_claude-mem_mcp-search__search` — recall relevant learnings
- `mcp__plugin_claude-mem_mcp-search__get_observations` — fetch specific observations
- `mcp__plugin_claude-mem_mcp-search__timeline` — review chronology

**Write policy:** All phases write freely. This is Neo's private notebook.

#### Semantic Memory (Graphify Knowledge Graphs)

**Purpose:** Persistent, queryable domain knowledge.

**Tools:**
- `/graphify <path>` — build graph
- `/graphify <path> --mcp` — start MCP server for runtime queries
- `/graphify query "<question>"` — graph traversal

**Extended node schema:**
```json
{
  "id": "unique_string",
  "label": "human name",
  "type": "entity | relationship | rule | skill | gap | contradiction",
  "knowledge_type": "proprietary | domain_expertise | distilled",
  "confidence": "high | medium | low",
  "source_file": "path",
  "source_location": "page/line",
  "source_quote": "verbatim text or null",
  "temporal_validity": "always | 1873-present | 2008-2010"
}
```

**Extended edge schema:**
```json
{
  "source": "id_a",
  "target": "id_b",
  "relation": "is_a | causes | requires | contradicts | evolved_into",
  "confidence": "EXTRACTED | INFERRED | AMBIGUOUS",
  "source_quote": "verbatim text or null",
  "causal_direction": "forward | reverse | bidirectional | null"
}
```

#### Procedural Memory (Skill File + References)

**Purpose:** How Neo works.

```
~/.claude/skills/become-neo-ontologist/
├── SKILL.md                          # Identity + routing (~2K tokens)
├── neo-trust.yaml                    # Trust ledger
├── references/
│   ├── v2.1-structure.md             # Workspace templates
│   ├── discovery-patterns.md         # How to find domain knowledge
│   ├── learnings.md                  # Accumulated meta-learnings
│   ├── extraction-skills/            # Compounding skill library
│   └── heuristics.md                 # Generative meta-thinking patterns
```

---

### 5.2 Trust Ledger

**File:** `neo-trust.yaml` — read at session start, always.

```yaml
version: 1
phase: 1  # 1=co-creation, 2=propose+approve, 3=graduated

autonomous:
  - create_workspace_structure
  - discover_and_catalog_sources
  - propose_draft_rules
  - save_episodic_memory
  - run_qa_loop
  - generate_visualizations
  - auto_detect_knowledge_type

requires_approval:
  - add_new_entity_types
  - promote_draft_rules_to_active
  - modify_skill_file
  - generate_domain_agent_skill
  - restructure_existing_ontology

qa_mode: supervised  # autonomous | supervised | mandatory-review

domains_completed: 0
domains_list: []
last_review: null

default_knowledge_mode: proprietary  # fallback when auto-detect uncertain
max_autonomous_iterations: 5
```

---

### 5.3 Knowledge Type Auto-Detection

**User never chooses.** Neo detects automatically:

```
1. Check for ISBN, DOI, arXiv ID, public URL → domain_expertise mode
2. Check for known publisher/journal patterns → domain_expertise mode
3. Check if title returns web search results → domain_expertise mode
4. No match → DEFAULT: proprietary mode (strict extraction)
5. Mixed signals → proprietary mode (safer)
```

**Two pipelines:**

| Step | Proprietary (Extract-First) | Domain Expertise (Distill-First) |
|------|---------------------------|--------------------------------|
| 1 | Read source document | Neo dumps latent knowledge as draft |
| 2 | Extract with page citations | Read source to validate/extend draft |
| 3 | Mark everything EXTRACTED | Tag convergent/divergent claims |
| 4 | Confidence = source anchoring | Confidence = convergence scoring |
| 5 | Validation: spot-check citations | Validation: self-play + cross-reference |

---

### 5.4 Session Startup Protocol

```
1. Skill tool loads SKILL.md (~2K tokens)
2. Read neo-trust.yaml → current phase and permissions
3. claude-mem search → "what domains have I built?" + relevant memories
4. Check pending gaps in known workspaces
5. If gaps exist → prioritize gap resolution
6. Greet user with context
```

---

### 5.5 Neo.Architect ↔ Neo.Oracle Routing

```
INTENT DETECTION:

  BUILD signals: "build", "extract", "create", "process", [drops file]
  → Neo.Architect

  USE signals: "teach", "explain", "analyze", "what is", "why did"
  → Neo.Oracle → spawns consumer agent with ontology loaded

  VISUALIZE signals: "show", "visualize", "graph", "dashboard"
  → Open atlas.html

  META signals: "status", "what have you learned", "show gaps"
  → Respond from neo-trust.yaml + claude-mem

  AMBIGUOUS → one clarifying question
```

---

### 5.6 Error Attribution: Shadow Query System

When Neo.Oracle gives a wrong answer:

```
1. Run shadow query: /graphify query "[original question]"
2. Compare:
   - Shadow CORRECT + Oracle WRONG → Fix consumer agent
   - Shadow WRONG/EMPTY + Oracle WRONG → Fix ontology (write to gaps.md)
   - Shadow PARTIAL → Add relationship edges to connect existing knowledge
```

---

### 5.7 Consumer Feedback Loop

Consumer agents write to `ontology/docs/gaps.md`:

```markdown
## Gap: [title]
- **Reported by:** Neo.Oracle:perry
- **Query that failed:** "Why did repo rates spike in 2019?"
- **What was missing:** Temporal event chain
- **Priority:** HIGH
- **Status:** OPEN
```

**Resolution autonomy by phase:**

| Phase | Gap from existing sources | Gap needing new sources |
|-------|--------------------------|------------------------|
| 1 | Ask Son | Escalate |
| 2 | Fix autonomously, show diff | Escalate |
| 3 | Fix autonomously, log only | Escalate |

New source acquisition ALWAYS requires Son.

---

### 5.8 File System Layout

```
~/.claude/skills/become-neo-ontologist/
├── SKILL.md
├── neo-trust.yaml
├── references/
│   ├── v2.1-structure.md
│   ├── discovery-patterns.md
│   ├── learnings.md
│   ├── heuristics.md
│   └── extraction-skills/

~/neo-workspaces/{domain-name}/
├── agents/{agent-name}/
│   ├── AGENT.md
│   ├── spec/scenarios/
│   └── skills/
├── ontology/
│   ├── rules/*.yaml
│   ├── skills/*.md
│   ├── entities/*.yaml
│   └── docs/
│       ├── gaps.md
│       ├── contradictions.md
│       └── patterns.md
├── sources/{source-name}.md
├── graphify-out/
│   ├── graph.json
│   ├── galaxy.html
│   ├── dashboard.html
│   ├── playground.html
│   └── GRAPH_REPORT.md
├── QA_REPORT.md
└── iterations.tsv
```

---

### 5.9 Tool Chain Summary

| Tool | When Used | By Whom |
|------|-----------|---------|
| `Skill("become-neo-ontologist")` | Session start | User types `/neo` |
| `Read` (PDF) | Document ingestion | Neo.Architect |
| `claude-mem save_memory` | After every learning | Neo.Architect |
| `claude-mem search` | Session startup + recall | Neo.Architect |
| `/graphify <workspace>` | After ontology build | Neo.Architect |
| `/graphify query` | Shadow queries, gaps | Neo.Architect |
| `Agent(model="opus")` × 3 | QA loop | Neo.Architect |
| `Agent(model="opus")` × 2 | Self-play discovery | Neo.Architect |
| `Agent(model="opus")` | Consumer agent spawn | Neo.Oracle |
| `Write` / `Edit` | Create/update workspace | Neo.Architect |
| `Bash` | Run Python tests, Pyodide | Neo.Architect |

**Model:** Opus 4.6 for everything. No cost optimization.

---

## 6. Quality Assurance

### 6.1 Three-Agent QA Loop

**Trigger:** Automatically after Neo.Architect completes any ontology build.
**Execution:** Three Opus subagents run in PARALLEL.

#### Implementation Auditor
- Every entity cites source page/paragraph
- Cited quotes exist on cited pages (spot-check 20%)
- No EXTRACTED claims that are INFERRED
- No orphan entities
- No terminology inconsistencies
- Coverage: all source sections represented

#### Consistency Reviewer
- Internal contradictions
- Circular causality (not flagged as feedback loops)
- Hallucination detection (claims unsupported by source)
- Graph structure quality
- Statistical plausibility of relationships

#### Ontological Rigor Reviewer
- IS-A hierarchies clean
- Causal chains directional and non-trivial
- Missing intermediate entities
- Abstraction level consistency
- Rules vs. skills correctly separated
- Gaps explicitly documented

### 6.2 Consensus and Escalation

```
All three return results in parallel
  │
  ├─ 3/3 PASS → auto-approve
  ├─ 2/3 flag same claim → CRITICAL → escalate to Son
  ├─ 1/3 flags → rebuttal round → resolved or escalate
  └─ Any CRITICAL severity → escalate to Son
```

### 6.3 QA Mode (Trust Ledger)

| Mode | Behavior |
|------|----------|
| autonomous | Auto-approve if all pass. Son sees report after. |
| supervised | Son reviews report before finalization. |
| mandatory-review | Son approves each finding individually. |

---

## 7. Visualization

### 7.1 Galaxy View (`galaxy.html`)

**Tech:** 3d-force-graph (Three.js + WebGL)

- Nodes colored by knowledge type (proprietary=blue, domain=green, distilled=gold)
- Node opacity = confidence (high=1.0, medium=0.6, low=0.3)
- Animated particle streams along causal edges
- Gap voids as pulsing dark regions
- Click node → source quote, confidence, provenance
- Cluster zoom: click community → fly in

### 7.2 Dashboard View (`dashboard.html`)

**Tech:** D3.js + HTML

- Ontology health bars (coverage, sourced %, consistency)
- Confidence distribution
- Knowledge type breakdown
- Top N gaps (clickable)
- Causal chain explorer
- QA report summary

### 7.3 Playground View (`playground.html`)

**Tech:** HTML + Pyodide (Python in browser)

- Interactive entity cards with editable parameters
- What-if sliders
- Execute → runs Python ontology simulation
- Causal chain highlights
- Neo.Oracle narration panel

### 7.4 Commands

```
/neo visualize                → galaxy.html (default)
/neo visualize --dashboard    → dashboard.html
/neo visualize --playground   → playground.html
/neo visualize --present      → guided demo mode
```

---

## 8. Design Decisions Log

| Decision | Chosen | Alternatives Considered | Rationale |
|----------|--------|------------------------|-----------|
| Two agents (Architect + Oracle) | Yes | Single merged agent | Separation of concerns; context window; each agent loads only what it needs |
| Single `/neo` interface | Yes | Separate `/neo` + `/perry` + `/fraud` | UX: "it just works" — Son never manages complexity |
| Phased autonomy | Earned, not scheduled | Fixed timeline; full autonomy; always supervised | Mirrors training a junior ontologist; builds trust incrementally |
| Trust ledger (`neo-trust.yaml`) | File read at session start | Database; env vars; hardcoded | Simple, versionable, human-readable |
| Executable ontologies (Python) | Yes | YAML; OWL; JSON-LD | Testable, benchmarkable, autoresearch-compatible |
| Held-out prediction test | 80/20 split | Expert review only; QA loop only | Quantitative, repeatable, no domain expert needed |
| Three-agent QA loop | Parallel Opus reviewers | Single reviewer; Haiku reviewers | Maximum quality; cost not a concern |
| Auto-detect knowledge type | Yes | User selects | UX: user shouldn't care about internals |
| Default to proprietary mode | When uncertain | Default to expertise | Over-citing is annoying; hallucinating is dangerous |
| DREA loop | At every level | Ad-hoc improvement; no formal loop | Systematic; measurable; compounds learning |
| Autoresearch iteration | Max 5 per session | Unlimited; fixed 3 | Bounds cost while allowing meaningful improvement |
| Opus 4.6 everywhere | Yes | Haiku for QA, Sonnet for extraction | Quality over cost — Son's directive |
| Canonical ontology + views | Yes | Agent-specific ontologies | One truth, multiple projections; enables reuse |
| Consumer feedback via gaps.md | Yes | Direct API; shared memory | Simple, file-based, versionable, fits existing COSTAR workflow |
| Neo.Architect + Neo.Oracle naming | Yes | Neo.Builder/Neo.User; NeoX/NeoY | Matrix metaphor; clear in logs; unanimous team agreement |

---

---

## 9. Autonomous Iteration Loop (Autoresearch Pattern)

Neo adapts Karpathy's autoresearch loop for ontology refinement. The mapping is 1:1.

### 9.1 The Mapping

| autoresearch | Neo Equivalent |
|-------------|----------------|
| `train.py` (one modifiable file) | `ontology/` workspace (one modifiable directory) |
| `prepare.py` (fixed eval, read-only) | `eval/` — held-out test + structural checks (READ-ONLY) |
| `program.md` (human instructions) | `SKILL.md` (Neo's cognitive operations protocol) |
| `val_bpb` (single metric) | `neo_score` — weighted composite (see formula) |
| `results.tsv` | `iterations.tsv` (commit, score, status, description) |
| 5-minute budget | Fixed token budget per iteration (~30K tokens) |
| `NEVER STOP` | `NEVER STOP` — iterate until Son interrupts or plateau |

### 9.2 The Neo Score (Single Scalar)

```python
# eval/evaluate.py — READ-ONLY, never modified by Neo

def compute_neo_score(ontology, held_out_passages, source_text):
    ppt_score = passage_prediction_test(ontology, held_out_passages)  # 40%
    structural_score = structural_check(ontology)                      # 20%
    coverage_score = coverage_scan(ontology, source_text)              # 25%
    coherence_score = coherence_check(ontology)                        # 15%
    
    return ppt_score * 0.40 + structural_score * 0.20 + 
           coverage_score * 0.25 + coherence_score * 0.15
```

### 9.3 The Loop

```
SETUP:
1. Son provides source material
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
9. Plateau check: 10 consecutive reverts → pause, notify Son
10. NEVER STOP unless plateaued or Son interrupts
```

### 9.4 Simplicity Criterion (from autoresearch)

- 0.01 improvement + 20 lines of complexity? Probably not worth it.
- 0.01 improvement from DELETING code? Definitely keep.
- ~0 improvement but simpler? Keep.
- Threshold: complexity justified if neo_score improves >2 points.

### 9.5 iterations.tsv Format

```tsv
iteration	commit	neo_score	ppt	structural	coverage	coherence	loc	status	description
1	a3f2d1e	42.30	35	80	45	60	120	baseline	Initial extraction
2	b7c4e2f	48.50	40	85	50	65	135	kept	Added money hierarchy
3	c9d1f3a	47.20	38	85	52	60	142	reverted	Elasticity as entity (hurt PPT)
4	d2e5a4b	51.80	45	90	55	65	138	kept	Elasticity as property instead
```

### 9.6 NEVER STOP Policy

| Phase | Behavior |
|-------|----------|
| 1 | Loop DISABLED. One change at a time, Son approves. |
| 2 | Runs up to `max_autonomous_iterations` (default 5). Shows log to Son. |
| 3 | NEVER STOP. Runs until Son interrupts or context limit (80%). |

### 9.7 Overnight Example

```
22:00 — Son: "/neo process Mehrling, iterate overnight"
22:05 — Baseline: neo_score = 42.3
22:06 — Loop begins (~4-6 iterations/hour on Opus)
06:00 — 96 iterations complete. neo_score = 83.2
06:05 — QA loop runs. 2 findings (MEDIUM, LOW). Auto-fixed.
06:10 — Final: neo_score = 84.1, 94 entities, 168 edges, 3 gaps remaining

08:00 — Son reads iterations.tsv:
  "Started at 42.3, ended at 84.1. 47 kept, 49 reverted.
   Key wins: temporal chains (+5), hierarchy (+5), crisis counterfactuals (+5).
   Plateau at iter 88. 3 gaps need new sources."
```

---

## 10. Team Communication Architecture

### 10.1 Neo.Architect ↔ Neo.Oracle Communication

Two communication channels: **synchronous** (same session) and **asynchronous** (across sessions).

#### Synchronous (Same Session)

When Neo.Oracle encounters an issue during use:

```
Neo.Oracle:perry answers question
  → Gets it wrong
  → Runs shadow query against ontology
  → Determines: ontology gap
  → Writes to gaps.md immediately
  → If Neo.Architect is active in same session:
      Sends direct message: "Gap found: [description]. 
      Shadow query returned empty for [query]. 
      Priority: [HIGH/MEDIUM/LOW]"
  → Neo.Architect receives, prioritizes, may fix in real-time
```

#### Asynchronous (Across Sessions)

```
Session N: Neo.Oracle:perry logs gaps to gaps.md
Session N+1: Neo.Architect reads gaps.md at startup (step 4 of startup protocol)
  → Prioritizes gaps by severity
  → Fixes autonomous gaps before starting new work
  → Escalates structural gaps to Son
```

#### Shared Knowledge Contract

Both Architect and Oracle read from the same ontology workspace:

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

The `usage-log.md` is a new mechanism: Oracle tracks which ontology nodes it actually queries. Entities that Oracle NEVER uses are candidates for removal (simplification).

### 10.2 QA Reviewers: Persistent Roles

The three QA reviewers (Clark, Karpathy, ClaudeAIExpert) participate at THREE moments, not just post-build:

| Moment | Trigger | Reviewer Role |
|--------|---------|---------------|
| **Post-build QA** | Neo.Architect completes ontology or iteration loop converges | Full 3-reviewer audit (parallel Opus agents) |
| **Gap escalation** | Neo.Architect finds a structural gap it can't resolve | Clark-reviewer advises on commitment revision |
| **Cross-domain review** | Neo proposes graduating a meta-rule | All 3 validate: does this pattern generalize? |

#### Post-Build QA (Existing Design)

```
Neo.Architect completes ontology
  → Spawns 3 Opus reviewers in parallel
  → Each reviews from their perspective
  → Results merge into QA_REPORT.md
  → Consensus scoring → auto-approve or escalate
```

#### Gap Escalation (New)

```
Neo.Architect encounters structural gap (ontology can't represent something)
  → Spawns Clark-reviewer with specific question:
    "Current commitment: [X]. This prevents representing [Y].
     Options: (A) revise commitment, (B) add exception, (C) accept limitation.
     Which is best for this domain?"
  → Clark-reviewer analyzes and recommends
  → If Phase 1: recommendation goes to Son
  → If Phase 2+: Neo.Architect follows recommendation, logs in commitment journal
```

#### Cross-Domain Review (New)

```
Neo proposes graduating a meta-rule (validated in 2+ domains)
  → Spawns all 3 reviewers with:
    "Proposed meta-rule: [description].
     Evidence from domain A: [evidence].
     Evidence from domain B: [evidence].
     Should this graduate to permanent meta-knowledge?"
  → Each reviewer evaluates from their perspective:
    - Clark: Is this ontologically sound? Does it generalize?
    - Karpathy: Is the evidence statistically meaningful? Any confounders?
    - ClaudeAIExpert: Is this implementable? Any context window concerns?
  → 2/3 approve → graduate
  → 1/3 or fewer → stay in proposed/
```

### 10.3 Full Team Communication Map

```
┌─────────────────────────────────────────────────────────┐
│                        Son (Human)                       │
│  Reviews: commitment journal, QA reports, plateau msgs   │
│  Approves: phase promotions, new sources, structural     │
│            gap resolutions (Phase 1-2)                   │
└──────────┬────────────────────────┬──────────────────────┘
           │ escalations            │ approvals
           ▼                        ▼
┌─────────────────────┐    ┌─────────────────────┐
│   Neo.Architect      │◄──►│   Neo.Oracle         │
│                      │    │                      │
│  Builds ontology     │    │  Uses ontology       │
│  Runs iteration loop │    │  Spawns domain agents│
│  Fixes gaps          │    │  Logs gaps + usage   │
│                      │    │                      │
│  WRITES: ontology/*  │    │  WRITES: gaps.md     │
│  READS: gaps.md      │    │         usage-log.md │
│         usage-log.md │    │  READS: ontology/*   │
└──────────┬───────────┘    └──────────────────────┘
           │
           │ triggers QA
           ▼
┌─────────────────────────────────────────┐
│         QA Review Committee             │
│                                         │
│  🔵 Clark-Reviewer                      │
│     Ontological rigor, commitments      │
│     Also: gap escalation advisor        │
│     Also: cross-domain graduation judge │
│                                         │
│  🟡 Karpathy-Reviewer                   │
│     Consistency, hallucination, evidence │
│     Also: cross-domain graduation judge │
│                                         │
│  🟢 ClaudeAIExpert-Reviewer             │
│     Implementation, citations, structure│
│     Also: cross-domain graduation judge │
│                                         │
│  Triggered by:                          │
│  1. Post-build / iteration convergence  │
│  2. Structural gap escalation           │
│  3. Meta-rule graduation proposal       │
└─────────────────────────────────────────┘
```

### 10.4 Learning Flow (How the System Evolves)

```
WITHIN A SESSION:
  Oracle uses ontology → hits gap → writes gaps.md → Architect reads → fixes

ACROSS SESSIONS:
  Session N: Architect builds domain A, Oracle uses it
  Session N+1: Architect reads gaps.md from Oracle, fixes gaps, 
               proposes meta-learnings from domain A
  Session N+2: Architect builds domain B, applies meta-learnings,
               measures improvement → if improved, meta-rule graduates
  Session N+3: QA reviewers validate graduation proposal

ACROSS PHASES:
  Phase 1: All learning surfaces to Son. Dense feedback, slow but accurate.
  Phase 2: Tactical learning autonomous. Strategic surfaces to Son.
  Phase 3: All learning autonomous with audit log. 
           QA reviewers are the check, not Son.
```

---

*End of specification.*
