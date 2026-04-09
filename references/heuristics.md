# Generative Meta-Thinking Patterns

Heuristics for ontology construction that transcend any single domain. These are
Neo's accumulated wisdom about HOW to build ontologies effectively.

---

## 1. Domain Archetype Heuristics

### Inspection Domain (fraud, QA, audit)
- **Starter entities:** Artifact, Rule, Anomaly, Inspector, Evidence
- **Graph shape:** Star — artifact at center, rules radiate outward, anomalies cluster at rule violations
- **Causal pattern:** artifact_property → rule_violation → anomaly_flag → investigation_trigger
- **Predictable gaps:** Temporal patterns (sequence matters), baseline definitions (what's "normal"?)
- **Anti-patterns:** Treating all anomalies as equal severity; missing the "who benefits" entity

### Diagnostic Domain (HVAC, medical, debugging)
- **Starter entities:** System, Component, Symptom, Cause, Intervention
- **Graph shape:** Tree — system at root, components branch, symptoms are leaves
- **Causal pattern:** root_cause → cascading_effects → observable_symptoms → diagnostic_path
- **Predictable gaps:** Cascade effects (A fails → B overloads → C shows symptom), intermittent faults
- **Anti-patterns:** Flat symptom lists without causal chains; confusing correlation with causation

### Optimization Domain (energy, logistics, finance)
- **Starter entities:** Variable, Constraint, Objective, Decision, Tradeoff
- **Graph shape:** Bipartite — variables on one side, constraints on other, edges are relationships
- **Causal pattern:** variable_change → constraint_impact → objective_shift → decision_required
- **Predictable gaps:** Multi-objective tradeoffs, constraint interactions, sensitivity analysis
- **Anti-patterns:** Single-objective optimization ignoring side effects; missing feedback loops

### Theoretical Framework (academic, philosophical)
- **Starter entities:** Construct, Tension, Regime, Agent, Mechanism
- **Graph shape:** Network — constructs linked by tensions, regimes as clusters
- **Causal pattern:** mechanism → regime_state → tension_resolution_or_escalation
- **Predictable gaps:** Historical context, boundary conditions, competing theories
- **Anti-patterns:** Oversimplifying dialectics into binary choices; losing the "both true" tensions

### Operational Domain (manufacturing, service delivery)
- **Starter entities:** Process, Step, Input, Output, Exception, Role
- **Graph shape:** DAG — steps flow left to right, exceptions branch off
- **Causal pattern:** input → process_step → output (or exception → recovery_path)
- **Predictable gaps:** Exception handling, handoff points, timing constraints
- **Anti-patterns:** Happy path only; ignoring the 20% of cases that take 80% of effort

---

## 2. Extraction Heuristics by Input Type

### PDF / Textbook
- Chapter structure → hierarchy (chapters = top-level entities, sections = sub-entities)
- Definitions → entity definitions (verbatim quotes with page numbers)
- Examples → counterfactuals and edge cases
- Diagrams → relationship maps (use ai-multimodal for complex visuals)
- Index/glossary → terminology flags
- Bibliography → related domains for analogical transfer

### Code
- Classes/structs → entities
- Methods → skills (procedures)
- Tests → rules (encoded expected behavior)
- Config files → thresholds and parameters
- Error handling → counterfactuals and edge cases
- Inheritance → IS-A hierarchy
- Composition → HAS-A relationships

### API Schemas
- Endpoints → entities (each resource is an entity)
- Query parameters → entity attributes
- Nested resources → relationships (parent/child)
- Enums → entity type classifications
- Error codes → business rules
- Rate limits → operational constraints

### Interviews / Conversations
- "What if..." answers → causalities
- "Except when..." → counterfactuals
- "We usually..." → skills (procedures)
- "The rule is..." → YAML rules
- "That depends on..." → decision trees
- Hesitation/uncertainty → knowledge gaps

### Data / CSV / Spreadsheets
- Columns → entity attributes
- Unique values → entity type enumerations
- Foreign keys → relationships
- Correlations → candidate causal edges (flag as correlates, not causes)
- Missing data patterns → knowledge gaps
- Outliers → counterfactuals or anomalies

---

## 3. Structuring Heuristics

- "Nouns are entities, verbs are relationships" — but watch for nominalized verbs
  ("a transfer" is an event, not a thing) and verbal nouns ("running" can be a process entity)
- "If it has a threshold, it's a rule. If it needs judgment, it's a skill." — no exceptions
- "The first hierarchy you build is always wrong — plan for revision" — commit but
  keep reversibility cost low
- "Causal chains should be directional and falsifiable" — if you can't imagine evidence
  that would break the chain, it's too vague
- "When in doubt, add confidence scores, not certainty" — MEDIUM confidence with evidence
  beats HIGH confidence without
- "Three mentions across sources = core entity" — frequency of reference signals importance
- "If two entities always appear together, one might be an attribute of the other" —
  test by asking "can entity A exist without entity B?"
- "Relationship labels should be verbs, not nouns" — "causes" not "causation",
  "contains" not "containment"

---

## 4. Quality Heuristics

- "If you can't write a test for it, it's too vague" — every entity/rule/skill should be testable
- "If the ontology doesn't improve the agent's PPT score, remove it" — ruthless simplification
- "Simplify until something breaks, then add back one thing" — minimum viable ontology
- "Every entity should be referenced by at least one rule or skill" — orphan entities are waste
- "Measure twice, commit once" — enumerate alternatives before committing (Operation 2)
- "An honest gap is more valuable than a hallucinated fill" — ABSTAIN scores 0.3, WRONG scores 0.0
- "The best ontology is the smallest one that passes all tests" — complexity is cost

---

## 5. Knowledge Type Detection Heuristics

### Signals for Domain Expertise Mode
- ISBN, DOI, arXiv ID present in document
- Public URL that returns search results
- Known publisher/journal (Springer, IEEE, Nature, etc.)
- Academic citation format
- Author with public profile
- Published before current year

### Signals for Proprietary Mode
- No web results for document title
- Internal document markings (CONFIDENTIAL, INTERNAL, DRAFT)
- Company-specific terminology with no public definition
- References to internal systems by name
- No ISBN/DOI/arXiv
- Shared via private channel

### Decision Rules
- Any proprietary signal → proprietary mode (strict extraction, page citations required)
- All expertise signals → domain expertise mode (can infer, cross-reference with training knowledge)
- Mixed signals → proprietary mode (safer default)
- Uncertain → proprietary mode (over-citing is annoying; hallucinating is dangerous)

---

## 6. Iteration Heuristics

- "Fix structural failures first — they're free points" — broken YAML, orphan entities,
  missing fields
- "Coverage gaps before prediction improvements" — re-read source for missed concepts
  before revising existing ones
- "One change per iteration, always" — never batch changes; you can't attribute improvement
- "If 3 iterations don't improve score, step back and rethink the approach" — don't grind
- "Deletion that maintains score = success" — simpler is better
- "When the score plateaus, look at what the held-out test is actually asking" —
  understand the eval before optimizing against it
