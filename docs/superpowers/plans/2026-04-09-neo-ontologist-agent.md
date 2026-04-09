# Neo Ontologist Agent Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the `become-neo-ontologist` Claude Code skill — a persistent ontologist agent that extracts, organizes, and evolves domain ontologies with autoresearch-style iteration, 3-agent QA, and graduated autonomy.

**Architecture:** Single skill directory at `~/.claude/skills/become-neo-ontologist/` with a compact SKILL.md (~2K tokens) as entry point, routing to Neo.Architect (builds ontology) or Neo.Oracle (spawns consumer agents). Heavy cognitive operations, QA protocol, and DREA loop details live in `references/` files loaded on demand. Per-domain workspaces created at `~/neo-workspaces/{domain}/` with eval/, agents/, ontology/, graphify-out/.

**Tech Stack:** Claude Code Skill (Markdown + YAML), Python (eval system), Graphify (knowledge graphs), claude-mem MCP (episodic memory)

---

## File Map

```
~/.claude/skills/become-neo-ontologist/
├── SKILL.md                              # Task 1: Entry point + routing (~2K tokens)
├── neo-trust.yaml                        # Task 2: Trust ledger
├── references/
│   ├── cognitive-operations.md           # Task 3: 7 cognitive operations (full detail)
│   ├── drea-loop.md                      # Task 4: Learning system + iteration protocol
│   ├── qa-protocol.md                    # Task 5: 3-agent QA loop + consensus
│   ├── workspace-structure.md            # Task 6: Workspace templates + eval system
│   ├── heuristics.md                     # Task 7: Meta-thinking patterns
│   ├── discovery-patterns.md             # Task 8: Copied + extended from existing
│   ├── learnings.md                      # Task 8: Copied from existing
│   └── extraction-skills/                # Task 9: Compounding skill library seed
│       └── README.md
```

---

### Task 1: SKILL.md — Entry Point and Routing

**Files:**
- Create: `~/.claude/skills/become-neo-ontologist/SKILL.md`

This is the main skill file loaded when user types `/neo`. Must be ~2K tokens. Contains: identity, routing logic, session startup protocol, command table, and references to load on demand.

- [ ] **Step 1: Write SKILL.md**

```markdown
---
name: become-neo-ontologist
description: >
  Become Neo — a persistent ontologist agent that extracts, organizes, and evolves
  domain ontologies from any input (PDFs, code, data, conversations). Produces
  executable ontologies, interactive knowledge graph visualizations, and deployable
  domain agents. Trigger: "become neo", "neo mode", "/neo", "build ontology",
  "extract domain knowledge", "ontology from [source]", "domain agent from [source]".
---

# Neo — Persistent Ontologist Agent

You are **Neo** — a persistent ontologist agent. You extract, organize, and evolve
domain ontologies from any input. You produce executable ontologies as Python classes,
interactive knowledge graph visualizations, and deployable domain agents.

Two subsystems, one interface:
- **Neo.Architect** — builds, validates, and evolves domain ontologies
- **Neo.Oracle** — routes to domain-specific consumer agents with ontology loaded

---

## Session Startup

1. Read `neo-trust.yaml` → current phase and permissions
2. `claude-mem search` → "neo ontologist domains built" + relevant memories
3. Check pending `gaps.md` in known workspaces under `~/neo-workspaces/`
4. If gaps exist → prioritize gap resolution
5. Greet user with context: phase, domains completed, pending gaps

---

## Routing

```
User input → detect intent:
  BUILD: "build", "extract", "create", "process", [drops file]
    → Neo.Architect (read references/cognitive-operations.md)
  USE: "teach", "explain", "analyze", "what is", "why did"
    → Neo.Oracle → spawn consumer agent with ontology loaded
  VISUALIZE: "show", "visualize", "graph", "dashboard"
    → Open atlas.html / galaxy.html
  META: "status", "what have you learned", "show gaps"
    → Respond from neo-trust.yaml + claude-mem
  AMBIGUOUS → ask one clarifying question
```

---

## Commands

| Command | Action | Reference |
|---------|--------|-----------|
| `/neo` | Auto-detect intent, route | This file |
| `/neo build <source>` | Extract ontology from source | cognitive-operations.md |
| `/neo iterate` | Run autoresearch loop | drea-loop.md |
| `/neo qa` | Run 3-agent QA review | qa-protocol.md |
| `/neo init <domain>` | Create workspace | workspace-structure.md |
| `/neo status` | Show health metrics | neo-trust.yaml + workspace |
| `/neo visualize` | Open galaxy.html | workspace graphify-out/ |
| `/neo teach <topic>` | Spawn Oracle consumer agent | Neo.Oracle routing |
| `/neo gaps` | Show/prioritize knowledge gaps | workspace gaps.md |

---

## Neo.Architect Protocol

When building/iterating, read `references/cognitive-operations.md` for the 7 operations:
1. Ontological Listening — detect implicit structure
2. Commitment Weighing — make/record ontological commitments
3. Analogical Transfer — bootstrap from domain archetypes
4. Gap Sensing — detect structural holes
5. Abstraction Calibration — find optimal detail level
6. Contradiction Integration — represent tensions honestly
7. Self-Aware Limitation — maintain honest uncertainty

**Knowledge type auto-detection** (never ask user):
- ISBN, DOI, arXiv, public URL, known publisher → domain expertise mode
- No match → proprietary mode (strict extraction, page citations)

**After build:** Run QA automatically (see `references/qa-protocol.md`).

---

## Neo.Oracle Protocol

When user wants to USE an ontology:
1. Identify which domain workspace matches the request
2. Load the ontology from that workspace
3. Spawn a consumer agent (Opus) with AGENT.md + ontology loaded
4. Consumer agent answers using STAR loop (See, Think, Act, Reflect)
5. If answer fails → shadow query against graphify → write to gaps.md

---

## Autonomy Model

Read `neo-trust.yaml` for current phase:
- **Phase 1 (Co-creation):** All commitments surface to user. Socratic dialogue.
- **Phase 2 (Propose+Approve):** Structural auto-commit. Foundational need user.
- **Phase 3 (Graduated):** Most autonomous. Audit log always.
- **PERMANENT:** New domain ontological commitments + meta-reasoning changes always need user.

---

## Workspace

Domain workspaces live at `~/neo-workspaces/{domain-name}/`.
See `references/workspace-structure.md` for full template.

---

## Memory Systems

| System | Tool | Purpose |
|--------|------|---------|
| Episodic | claude-mem MCP | Cross-session learnings |
| Semantic | Graphify | Knowledge graphs |
| Procedural | This SKILL.md + references/ | How Neo works |

---

## Core Principles

1. One interface, smart routing — user never manages complexity
2. Phased autonomy — earned, not scheduled, permanent human veto
3. DREA loop — Do, Receive, Evaluate, Adapt — at every level
4. Honest uncertainty — every claim carries confidence + provenance
5. Auto-detect knowledge type — proprietary vs domain expertise
6. Executable ontologies — Python classes, not YAML
7. Quality over cost — Opus for everything
```

- [ ] **Step 2: Verify token count is ~2K**

Run: `wc -w ~/.claude/skills/become-neo-ontologist/SKILL.md`
Expected: ~500-600 words (roughly 2K tokens)

- [ ] **Step 3: Commit**

```bash
cd ~/.claude/skills/become-neo-ontologist && git init && git add SKILL.md
git commit -m "feat: add Neo ontologist SKILL.md entry point"
```

---

### Task 2: neo-trust.yaml — Trust Ledger

**Files:**
- Create: `~/.claude/skills/become-neo-ontologist/neo-trust.yaml`

- [ ] **Step 1: Write neo-trust.yaml**

```yaml
# Neo Trust Ledger — read at session start, always.
# Controls Neo's autonomy level and permissions.

version: 1
phase: 1  # 1=co-creation, 2=propose+approve, 3=graduated

# Phase graduation criteria:
# 1→2: >80% prediction accuracy across 3 consecutive domains
# 2→3: Ontologies pass validation without correction on first attempt
# PERMANENT: New domain commitments + meta-reasoning changes always need human sign-off

autonomous:
  - create_workspace_structure
  - discover_and_catalog_sources
  - propose_draft_rules
  - save_episodic_memory
  - run_qa_loop
  - generate_visualizations
  - auto_detect_knowledge_type
  - fix_coverage_gaps_from_existing_sources
  - run_held_out_prediction_test
  - log_iterations

requires_approval:
  - add_new_entity_types
  - promote_draft_rules_to_active
  - modify_skill_file
  - generate_domain_agent_skill
  - restructure_existing_ontology
  - acquire_new_sources
  - graduate_meta_rules
  - change_drea_parameters

qa_mode: supervised  # autonomous | supervised | mandatory-review
# autonomous: auto-approve if all 3 reviewers pass. User sees report after.
# supervised: user reviews report before finalization.
# mandatory-review: user approves each finding individually.

domains_completed: 0
domains_list: []
last_review: null

default_knowledge_mode: proprietary  # fallback when auto-detect uncertain
max_autonomous_iterations: 5  # Phase 1: ignored (1 at a time). Phase 2: this. Phase 3: unlimited.

# Iteration loop behavior per phase:
# Phase 1: Loop DISABLED. One change at a time, user approves.
# Phase 2: Runs up to max_autonomous_iterations. Shows log to user.
# Phase 3: NEVER STOP. Runs until user interrupts or context limit (80%).

# Plateau detection:
plateau_threshold: 10  # consecutive reverts before pausing
diminishing_returns_threshold: 2  # % improvement below which to stop

# Deprecation sweep interval:
deprecation_sweep_interval: 10  # every N domains, audit graduated rules
```

- [ ] **Step 2: Commit**

```bash
cd ~/.claude/skills/become-neo-ontologist && git add neo-trust.yaml
git commit -m "feat: add neo-trust.yaml trust ledger"
```

---

### Task 3: cognitive-operations.md — The Seven Cognitive Operations

**Files:**
- Create: `~/.claude/skills/become-neo-ontologist/references/cognitive-operations.md`

Contains the full detail of all 7 operations from spec sections 3.1-3.7, plus the commitment journal format and operation interaction map. This is loaded when Neo.Architect is active.

- [ ] **Step 1: Write cognitive-operations.md**

Include ALL of the following from the spec (reproduce fully, do not summarize):

1. **Operation 1: Ontological Listening** — triggers, process (5 steps), YAML output format (`listening_output` with explicit_entities, implicit_entities, assumed_relationships, terminology_flags, unstated_assumptions), knowledge type behavior (proprietary vs expertise mode)

2. **Operation 2: Commitment Weighing** — triggers, process (5 steps with faithfulness/utility/composability/reversibility/abstraction assessment), escalation rules per phase, PERMANENT rule

3. **Operation 3: Analogical Transfer** — triggers, process (5 steps with 5 archetype classifications: inspection, diagnostic, optimization, theoretical, operational), YAML output format (`analogical_transfer` with mappings, analogy_limits, modifications)

4. **Operation 4: Gap Sensing** — triggers, process (5-step scan), gap classification table (Coverage/Source/Structural/Temporal with detection, resolution, autonomy), resolution statistics (~60/25/15%)

5. **Operation 5: Abstraction Calibration** — the test ("If I give a downstream agent ONLY this description..."), Goldilocks scale (1-5)

6. **Operation 6: Contradiction Integration** — 4 resolution types (factual, perspective, context-dependent, genuine open question), YAML output format (`contradiction_register`)

7. **Operation 7: Self-Aware Limitation** — confidence tiers (HIGH/MEDIUM/LOW/GAP), model boundaries (Python property), epistemic status progression (exploratory→draft→validated→production)

8. **Commitment Journal** — full YAML format with id, timestamp, domain, decision, alternatives_considered (with scores), chosen, rationale, cost, reversibility, confidence, outcome, user_approved

9. **Operation Interaction Map** — ASCII diagram showing flow: Listening → Commitment Weighing (informed by Analogical Transfer + Abstraction Calibration) → Contradiction Integration → Gap Sensing → Self-Aware Limitation

- [ ] **Step 2: Commit**

```bash
cd ~/.claude/skills/become-neo-ontologist && git add references/cognitive-operations.md
git commit -m "feat: add 7 cognitive operations reference"
```

---

### Task 4: drea-loop.md — Learning System and Iteration Protocol

**Files:**
- Create: `~/.claude/skills/become-neo-ontologist/references/drea-loop.md`

Contains: DREA loop, 3 timescales, graduated memory model, immune system, held-out prediction test, compounding skill library, autoresearch iteration protocol, Neo score formula, NEVER STOP policy.

- [ ] **Step 1: Write drea-loop.md**

Include ALL of the following from spec sections 4 and 9:

1. **DREA Loop** — Do (action logging), Receive (4 feedback sources table), Evaluate (6 error types taxonomy), Adapt (6 adaptation actions table with writes-to destinations)

2. **Three Timescales** — Within-domain (minutes, ontology changes, autonomous for extraction), Cross-domain (days, meta-knowledge, proposed→validated→graduated), Lifetime (months, core capabilities, NEVER autonomous)

3. **Graduated Memory Model** — full directory structure:
   ```
   neo/meta-knowledge/
   ├── proposed/     (Tier 1: auto-write)
   ├── graduated/    (Tier 2: earned promotion)
   ├── core/         (Tier 3: Son-approved only)
   └── identity/     (Tier 4: immutable)
   ```
   Plus graduation criteria table (Observation→Proposed→Graduated→Core→Deprecated)

4. **Immune System** — provenance tracking fields, validation-before-graduation (4 checks), periodic forgetting rules (every 10 domains)

5. **Held-Out Prediction Test** — setup (80/20 split, hash-based, stratified), 4 question types with weights (FACTUAL 20%, RELATIONAL 30%, CAUSAL 35%, COUNTERFACTUAL 15%), scoring (CORRECT 1.0, PARTIAL 0.5, WRONG 0.0, ABSTAIN 0.3), interpretation table

6. **Autoresearch Mapping Table** — train.py↔ontology/, prepare.py↔eval/, program.md↔SKILL.md, val_bpb↔neo_score, results.tsv↔iterations.tsv

7. **Neo Score Formula** — Python code:
   ```python
   neo_score = ppt_score * 0.40 + structural_score * 0.20 + 
              coverage_score * 0.25 + coherence_score * 0.15
   ```

8. **Iteration Loop** — 10-step LOOP FOREVER protocol (read state, identify target, modify, commit, eval, decision keep/revert, log, plateau check)

9. **Simplicity Criterion** — 4 rules for when complexity is justified

10. **iterations.tsv format** — header row + example rows

11. **NEVER STOP Policy** — table by phase (1: disabled, 2: max N, 3: never stop)

12. **Overnight Example** — the 22:00→08:00 scenario from the spec

- [ ] **Step 2: Commit**

```bash
cd ~/.claude/skills/become-neo-ontologist && git add references/drea-loop.md
git commit -m "feat: add DREA loop and iteration protocol reference"
```

---

### Task 5: qa-protocol.md — Three-Agent QA Loop

**Files:**
- Create: `~/.claude/skills/become-neo-ontologist/references/qa-protocol.md`

Contains: 3 reviewer roles, consensus/escalation, QA modes, team communication, error attribution, consumer feedback loop.

- [ ] **Step 1: Write qa-protocol.md**

Include ALL of the following from spec sections 6 and 10:

1. **Three-Agent QA Loop** — trigger (auto after build), execution (3 Opus parallel)

2. **Implementation Auditor** — 6 checks: source citations, quote verification (spot-check 20%), no EXTRACTED-as-INFERRED, no orphan entities, terminology consistency, coverage

3. **Consistency Reviewer** — 5 checks: internal contradictions, circular causality, hallucination detection, graph structure quality, statistical plausibility

4. **Ontological Rigor Reviewer** — 6 checks: IS-A hierarchy clean, causal chains directional, missing intermediate entities, abstraction consistency, rules/skills separation, gaps documented

5. **Consensus and Escalation** — decision tree: 3/3 PASS→auto-approve, 2/3 same claim→CRITICAL→escalate, 1/3→rebuttal round, any CRITICAL→escalate

6. **QA Modes** — autonomous/supervised/mandatory-review table

7. **Reviewer Participation Points** — 3 moments table (post-build QA, gap escalation with Clark-reviewer, cross-domain graduation review with all 3)

8. **Gap Escalation Protocol** — flow: Architect encounters structural gap → spawns Clark-reviewer with specific question and 3 options → Phase 1: to user, Phase 2+: follow recommendation

9. **Cross-Domain Review** — flow: propose meta-rule → spawn all 3 → each evaluates from perspective (Clark: ontological, Karpathy: statistical, ClaudeAIExpert: implementation) → 2/3 approve → graduate

10. **Error Attribution: Shadow Query System** — 3 outcomes: Shadow CORRECT+Oracle WRONG→fix consumer, Shadow WRONG→fix ontology, Shadow PARTIAL→add edges

11. **Consumer Feedback Loop** — gaps.md format, resolution autonomy by phase table, usage-log.md mechanism

12. **Full Team Communication Map** — ASCII diagram showing Son↔Architect↔Oracle↔QA Committee

13. **Learning Flow** — within session, across sessions, across phases

- [ ] **Step 2: Commit**

```bash
cd ~/.claude/skills/become-neo-ontologist && git add references/qa-protocol.md
git commit -m "feat: add QA protocol and team communication reference"
```

---

### Task 6: workspace-structure.md — Workspace Templates + Eval System

**Files:**
- Create: `~/.claude/skills/become-neo-ontologist/references/workspace-structure.md`

Updated from existing v2.1-structure.md with Neo-specific additions: eval/, graphify-out/, iterations.tsv, sources/, QA_REPORT.md, neo/meta-knowledge/.

- [ ] **Step 1: Write workspace-structure.md**

Include:

1. **Design Principles** — same 5 from existing v2.1 plus: "Executable ontologies — Python classes, testable", "Autoresearch-compatible — one modifiable workspace, read-only eval"

2. **Full Directory Structure** — the Neo workspace from spec section 5.8:
   ```
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
   │       ├── usage-log.md
   │       └── patterns.md
   ├── sources/{source-name}.md
   ├── eval/                          # READ-ONLY after setup
   │   ├── held_out_passages.json     # 20% held-out content
   │   ├── evaluate.py                # Neo score computation
   │   └── run_eval.sh                # Eval runner
   ├── graphify-out/
   │   ├── graph.json
   │   ├── galaxy.html
   │   ├── dashboard.html
   │   ├── playground.html
   │   └── GRAPH_REPORT.md
   ├── neo/
   │   └── meta-knowledge/
   │       ├── proposed/
   │       ├── graduated/
   │       └── core/
   ├── QA_REPORT.md
   └── iterations.tsv
   ```

3. **File Templates** — include ALL templates from existing v2.1 (CLAUDE.md, AGENTS.md, AGENT.md, ONTOLOGY.md, INVENTORY.md, scenario format, test tiers, skills format, rules format)

4. **NEW: eval/evaluate.py template** — Python script implementing:
   ```python
   import json, sys, hashlib

   def split_passages(source_text: str, ratio: float = 0.8) -> tuple[list[str], list[str]]:
       """Deterministic hash-based 80/20 split."""
       paragraphs = [p.strip() for p in source_text.split('\n\n') if p.strip()]
       train, test = [], []
       for p in paragraphs:
           h = int(hashlib.sha256(p.encode()).hexdigest(), 16) % 100
           (train if h < ratio * 100 else test).append(p)
       return train, test

   def generate_test_questions(held_out: list[str]) -> list[dict]:
       """Generate weighted test questions from held-out passages."""
       # Question types with weights
       # FACTUAL: 20%, RELATIONAL: 30%, CAUSAL: 35%, COUNTERFACTUAL: 15%
       ...

   def score_predictions(predictions: list[dict], held_out: list[str]) -> dict:
       """Score: CORRECT=1.0, PARTIAL=0.5, WRONG=0.0, ABSTAIN=0.3"""
       ...

   def structural_check(ontology_path: str) -> float:
       """Check: no orphan entities, all edges valid, rules well-formed."""
       ...

   def coverage_scan(ontology_path: str, source_text: str) -> float:
       """Check: all source sections represented in ontology."""
       ...

   def coherence_check(ontology_path: str) -> float:
       """Check: no circular causality, consistent abstraction, no contradictions."""
       ...

   def compute_neo_score(ontology_path: str, held_out_path: str, source_path: str) -> float:
       ppt = score_predictions(...)
       structural = structural_check(ontology_path)
       coverage = coverage_scan(ontology_path, source_path)
       coherence = coherence_check(ontology_path)
       return ppt * 0.40 + structural * 0.20 + coverage * 0.25 + coherence * 0.15

   if __name__ == "__main__":
       score = compute_neo_score(sys.argv[1], sys.argv[2], sys.argv[3])
       print(f"neo_score={score:.2f}")
   ```

5. **NEW: eval/run_eval.sh template**:
   ```bash
   #!/usr/bin/env bash
   set -euo pipefail
   WORKSPACE="${1:-.}"
   python3 "$WORKSPACE/eval/evaluate.py" \
     "$WORKSPACE/ontology" \
     "$WORKSPACE/eval/held_out_passages.json" \
     "$WORKSPACE/sources"
   ```

6. **NEW: iterations.tsv template**:
   ```
   iteration	commit	neo_score	ppt	structural	coverage	coherence	loc	status	description
   ```

7. **NEW: gaps.md template**:
   ```markdown
   # Knowledge Gaps

   <!-- Reported by Neo.Oracle consumer agents and Neo.Architect gap sensing -->
   ```

8. **NEW: contradictions.md template**:
   ```markdown
   # Contradiction Register

   <!-- Tensions and contradictions detected during ontology construction -->
   ```

9. **NEW: usage-log.md template**:
   ```markdown
   # Ontology Usage Log

   <!-- Tracked by Neo.Oracle: which entities/rules are actually queried -->
   ```

- [ ] **Step 2: Commit**

```bash
cd ~/.claude/skills/become-neo-ontologist && git add references/workspace-structure.md
git commit -m "feat: add workspace structure with eval system templates"
```

---

### Task 7: heuristics.md — Generative Meta-Thinking Patterns

**Files:**
- Create: `~/.claude/skills/become-neo-ontologist/references/heuristics.md`

- [ ] **Step 1: Write heuristics.md**

This file captures Neo's generative meta-thinking patterns — heuristics for ontology construction that transcend any single domain. Structure:

1. **Domain Archetype Heuristics** — for each of the 5 archetypes (inspection, diagnostic, optimization, theoretical, operational), document:
   - Starter entity pattern
   - Typical relationship graph shape
   - Common causal chain patterns
   - Predictable gaps to pre-fill
   - Anti-patterns specific to this archetype

2. **Extraction Heuristics** — patterns for different input types:
   - PDF/textbook: chapter structure → hierarchy, definitions → entities, examples → counterfactuals
   - Code: classes → entities, methods → skills, tests → rules, config → thresholds
   - API schemas: endpoints → entities, query params → attributes, errors → rules
   - Interviews: "what if" answers → causalities, exceptions mentioned → counterfactuals
   - Data/CSV: columns → attributes, unique values → entity types, correlations → relationships

3. **Structuring Heuristics**:
   - "Nouns are entities, verbs are relationships" (with caveats)
   - "If it has a threshold, it's a rule. If it needs judgment, it's a skill."
   - "The first hierarchy you build is always wrong — plan for revision"
   - "Causal chains should be directional and falsifiable"
   - "When in doubt, add confidence scores, not certainty"

4. **Quality Heuristics**:
   - "If you can't write a test for it, it's too vague"
   - "If the ontology doesn't improve the agent's PPT score, remove it"
   - "Simplify until something breaks, then add back one thing"
   - "Every entity should be referenced by at least one rule or skill"

5. **Knowledge Type Detection Heuristics**:
   - ISBN/DOI/arXiv/public URL → domain expertise
   - No web results for title → likely proprietary
   - Mixed signals → default proprietary (safer)
   - Internal documents with "CONFIDENTIAL" → always proprietary

- [ ] **Step 2: Commit**

```bash
cd ~/.claude/skills/become-neo-ontologist && git add references/heuristics.md
git commit -m "feat: add meta-thinking heuristics reference"
```

---

### Task 8: Copy and Extend Existing References

**Files:**
- Create: `~/.claude/skills/become-neo-ontologist/references/discovery-patterns.md`
- Create: `~/.claude/skills/become-neo-ontologist/references/learnings.md`

- [ ] **Step 1: Copy discovery-patterns.md from existing skill**

Copy from `~/.claude/skills/become-ontologist/references/discovery-patterns.md` verbatim. This file is already complete and matches the spec.

```bash
cp ~/.claude/skills/become-ontologist/references/discovery-patterns.md \
   ~/.claude/skills/become-neo-ontologist/references/discovery-patterns.md
```

- [ ] **Step 2: Copy learnings.md from existing skill**

```bash
cp ~/.claude/skills/become-ontologist/references/learnings.md \
   ~/.claude/skills/become-neo-ontologist/references/learnings.md
```

- [ ] **Step 3: Commit**

```bash
cd ~/.claude/skills/become-neo-ontologist && git add references/discovery-patterns.md references/learnings.md
git commit -m "feat: copy existing discovery patterns and learnings references"
```

---

### Task 9: Extraction Skills Library Seed

**Files:**
- Create: `~/.claude/skills/become-neo-ontologist/references/extraction-skills/README.md`

- [ ] **Step 1: Write README.md for extraction-skills directory**

```markdown
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

Each skill file has:
- **id:** Unique identifier
- **name:** Human-readable name
- **type:** meta-pattern | anti-pattern | domain-template | extraction-strategy
- **confidence:** 0.0-1.0
- **scope:** Which domain archetypes this applies to
- **validated_in:** List of domains where this was validated
- **failed_in:** List of domains where this failed
- **graduated:** Date graduated from proposed/ to here (null if still proposed)
- **lifetime_success_rate:** Percentage of applications that improved scores
- **procedure:** Detailed steps

## Directory Structure

```
extraction-skills/
├── meta-patterns/           # "For hierarchical domains, start top-down"
├── anti-patterns/           # "Co-occurrence ≠ causation"
├── domain-templates/        # Starter structures per archetype
└── extraction-strategies/   # Per input type (PDF, code, interview)
```

Files appear here as Neo processes domains and graduates observations.
```

- [ ] **Step 2: Create subdirectories**

```bash
mkdir -p ~/.claude/skills/become-neo-ontologist/references/extraction-skills/{meta-patterns,anti-patterns,domain-templates,extraction-strategies}
```

- [ ] **Step 3: Commit**

```bash
cd ~/.claude/skills/become-neo-ontologist && git add references/extraction-skills/
git commit -m "feat: add extraction skills library seed structure"
```

---

### Task 10: Integration Test — Verify Skill Loads

**Files:**
- Verify: `~/.claude/skills/become-neo-ontologist/SKILL.md`
- Verify: `~/.claude/skills/become-neo-ontologist/neo-trust.yaml`
- Verify: all references/ files

- [ ] **Step 1: Verify all files exist**

```bash
find ~/.claude/skills/become-neo-ontologist -type f | sort
```

Expected output:
```
~/.claude/skills/become-neo-ontologist/SKILL.md
~/.claude/skills/become-neo-ontologist/neo-trust.yaml
~/.claude/skills/become-neo-ontologist/references/cognitive-operations.md
~/.claude/skills/become-neo-ontologist/references/discovery-patterns.md
~/.claude/skills/become-neo-ontologist/references/drea-loop.md
~/.claude/skills/become-neo-ontologist/references/extraction-skills/README.md
~/.claude/skills/become-neo-ontologist/references/heuristics.md
~/.claude/skills/become-neo-ontologist/references/learnings.md
~/.claude/skills/become-neo-ontologist/references/qa-protocol.md
~/.claude/skills/become-neo-ontologist/references/workspace-structure.md
```

- [ ] **Step 2: Verify SKILL.md is under 2500 words**

```bash
wc -w ~/.claude/skills/become-neo-ontologist/SKILL.md
```

Expected: < 2500 words

- [ ] **Step 3: Verify neo-trust.yaml is valid YAML**

```bash
python3 -c "import yaml; yaml.safe_load(open('$HOME/.claude/skills/become-neo-ontologist/neo-trust.yaml'))"
```

Expected: no error

- [ ] **Step 4: Verify no dangling references in SKILL.md**

Check that every reference file mentioned in SKILL.md exists:

```bash
grep -oP 'references/[a-z-]+\.md' ~/.claude/skills/become-neo-ontologist/SKILL.md | while read f; do
  test -f "$HOME/.claude/skills/become-neo-ontologist/$f" && echo "OK: $f" || echo "MISSING: $f"
done
```

Expected: all OK, no MISSING
