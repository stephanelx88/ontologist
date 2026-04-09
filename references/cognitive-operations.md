# Neo's Seven Cognitive Operations

## Overview

Neo's cognitive architecture consists of seven ontological operations that work as
**concurrent cognitive processes** activated by input context. Multiple operations fire
simultaneously during any extraction or reasoning task.

Inspired by dual-process cognitive theory:
- **Fast/pattern-based:** Ontological Listening, Gap Sensing, Analogical Transfer
- **Slow/deliberative:** Commitment Weighing, Abstraction Calibration, Contradiction Integration, Self-Aware Limitation

---

## Operation 1: Ontological Listening

**Purpose:** Detect implicit ontological structure in domain input — entities,
relationships, and causal models that are assumed but never stated.

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

**Output format:**

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
- **Proprietary mode:** Listen for structure but NEVER infer beyond what's stated. Flag implicit entities as "requires confirmation from source owner."
- **Expertise mode:** Actively infer implicit structure. Cross-reference with Claude's training knowledge to validate inferences.

---

## Operation 2: Commitment Weighing

**Purpose:** Make and record ontological commitments — decisions about what entities,
relationships, and structures are "real" in the domain model. Every commitment
constrains future modeling options.

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
- **Phase 1:** ALL commitments surface to user for approval
- **Phase 2:** Structural commitments auto-commit. Foundational commitments surface to user.
- **Phase 3:** All auto-commit. User reviews commitment journal asynchronously.
- **PERMANENT:** Ontological commitments about what's "real" in a NEW domain always require human ratification, regardless of phase.

---

## Operation 3: Analogical Transfer

**Purpose:** Bootstrap ontological structure in unfamiliar domains by pattern-matching
against known domain archetypes and previously built ontologies.

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

**Output format:**

```yaml
analogical_transfer:
  source_domain: "Vietnamese banking fraud detection"
  target_domain: "insurance claims fraud"
  archetype: "inspection"
  mappings:
    - source: "bank statement"
      target: "insurance claim form"
      confidence: 0.9
    - source: "transaction"
      target: "claim line item"
      confidence: 0.85
  analogy_limits:
    - "Banking fraud has running balances; insurance claims do not have cumulative state"
  archetype_modifications_needed:
    - "Add 'assessor' entity type not present in banking archetype"
```

---

## Operation 4: Gap Sensing

**Purpose:** Detect structural holes in the ontology — missing entities, unrepresented
relationships, absent causal chains.

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

## Operation 5: Abstraction Calibration

**Purpose:** Find the optimal level of abstraction for each ontology element.

**Test:** "If I give a downstream agent ONLY this description, can it execute its scenarios?"
- If no → too abstract
- If the agent has information it never uses → too concrete

**Goldilocks Scale:**
1. Too abstract (useless for decisions)
2. Slightly abstract (requires interpretation)
3. **Right level (directly actionable)**
4. Slightly concrete (over-specified)
5. Too concrete (locked to one implementation)

---

## Operation 6: Contradiction Integration

**Purpose:** Represent contradictions honestly rather than silently resolving them.

**Resolution types:**
- **Factual contradiction** (one is wrong) → resolve with evidence
- **Perspective contradiction** (different valid viewpoints) → represent both
- **Context-dependent** (both true in different situations) → encode conditions
- **Genuine open question** (nobody knows) → mark as unresolved

**Output format:**

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

## Operation 7: Self-Aware Limitation

**Purpose:** Maintain honest assessment of what Neo knows, doesn't know, and what
KIND of thing it doesn't know.

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
`exploratory` → `draft` → `validated` → `production`

Each transition has specific criteria (coverage %, PPT score, QA pass, expert validation).

---

## The Commitment Journal

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

## Operation Interaction Map

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

**Flow description:**
1. Input enters through **Ontological Listening**, which produces candidate entities and relationships
2. **Analogical Transfer** provides archetype patterns; **Abstraction Calibration** adjusts granularity
3. Both inform **Commitment Weighing**, which decides what becomes part of the ontology
4. Committed elements pass through **Contradiction Integration** to handle tensions
5. **Gap Sensing** continuously scans for holes in the resulting ontology
6. **Self-Aware Limitation** maintains the overall knowledge state model and epistemic status
7. Gap Sensing feeds back to Ontological Listening (re-read source) and Commitment Weighing (revise)
