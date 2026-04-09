# Meta-Learnings About Building Ontologies

These are hard-won insights about the craft of ontology engineering itself —
patterns about the process, not about any specific domain.

---

## Table of Contents

1. [Self-Containment](#self-containment)
2. [Skills Architecture](#skills-architecture)
3. [Multi-Agent Communication](#multi-agent-communication)
4. [Test Structure](#test-structure)
5. [Common Pitfalls](#common-pitfalls)

---

## Self-Containment

An ontology must be portable. If you copy the workspace to a different machine,
everything should still make sense and work.

**Principles:**
- Transform external document references into inline skills or rules
- Don't reference file paths outside the workspace
- If a skill depends on an external tool, document the dependency explicitly
- Include example data, not just pointers to where data lives

**Anti-pattern:** "See the operations manual in the shared drive for details"
**Correct:** Extract the relevant procedures into skills within the ontology

---

## Skills Architecture

**Decision: Agent-specific skills with shared utilities**

```
ontology/
├── skills/                    # SHARED utilities only
│   ├── diagnose-issue.md
│   ├── execute-data-query.md
│   └── learn-and-update.md
│
└── agents/
    ├── facility-operator/
    │   └── skills/            # AGENT-SPECIFIC procedures
    │       ├── occupancy-response.md
    │       └── emergency-coordination.md
    │
    └── energy-manager/
        └── skills/            # AGENT-SPECIFIC procedures
            ├── grid-outage.md
            └── demand-response.md
```

**Rationale:**
- Clear ownership — agent owns its domain procedures
- Reduced noise — agent only reads relevant skills
- Shared utilities preserved — data query, messaging remain shared
- Independent evolution — energy skills evolve without affecting facility operator

**When to share vs. specialize:**
- Share: Generic operations (querying data, logging, learning feedback)
- Specialize: Domain-specific procedures (diagnosing HVAC vs. analyzing energy)

---

## Multi-Agent Communication

When multiple agents operate in the same ontology:

1. **AGENTS.md is the universal entry point** — every request starts there
2. **Each agent declares its scope** — what it owns, monitors, and ignores
3. **Skills need executable content** — not just documentation, but code blocks
   agents can copy and run
4. **Routing is intent-based** — match the request to the agent whose scope covers it

**Message passing (MVP):**
- SQLite message bus for simple inter-agent communication
- Agents write to a shared table, read from it on their next cycle
- No complex pub/sub needed until proven necessary

---

## Test Structure

**Three-layer test pyramid:**

```
        /  Semantic  \     ~$0.10/test, nightly
       / (LLM-judge)  \
      /________________\
     /   Structural    \    ~$0.01/test, every PR
    / (deterministic)   \
   /____________________\
  /       Unit          \   Free, every commit
 /   (pure logic)        \
/________________________\
```

**Key insight:** Rule definitions (YAML) → Spec test cases (YAML) → Executable
tests (Python). Each layer builds on the previous one.

**What each layer validates:**
- **Unit:** Do the rules compute correctly? (no LLM involved)
- **Structural:** Does the agent produce the right output shape? (agent runs, output checked deterministically)
- **Semantic:** Is the agent's reasoning correct? (LLM evaluates quality)

---

## Common Pitfalls

### 1. Ontology Without Agents
Building an elaborate knowledge graph with no agents to consume it. The ontology
becomes a documentation project, not an operational system.

**Fix:** Start with agents. Define what they need to do. Build only the ontology
that serves those agents.

### 2. Over-Abstracting
Creating a general-purpose ontology framework when you need to solve specific
problems. Premature abstraction kills momentum.

**Fix:** Start concrete. Build for one domain, one agent, one use case. Generalize
only when you see the same pattern three times.

### 3. Rules as Prose
Writing business rules as paragraphs of text instead of structured YAML. The agent
can't reliably extract thresholds from prose.

**Fix:** Every rule with a number, threshold, or decision point goes into YAML.
Prose explains the why; YAML encodes the what.

### 4. Skills Without Procedures
Documenting what a skill does but not how to do it. "Diagnose the problem" is
not a skill — it's a wish.

**Fix:** Every skill has numbered steps. Each step is concrete enough that
someone unfamiliar with the domain could follow it.

### 5. Ignoring the Learning Loop
Building the ontology once and never updating it. Domain knowledge evolves.
Agents discover gaps. The ontology must grow.

**Fix:** Include learn-and-update.md as a shared skill. Every agent interaction
is an opportunity to identify gaps and improvements.

### 6. Conflating Rules and Skills
Putting deterministic logic in markdown skills or judgment calls in YAML rules.

**Fix:**
- If a computer can evaluate it without reasoning → YAML rule
- If it requires interpretation, context, or judgment → Markdown skill

Examples:
- "Temperature must be between 21-25°C" → YAML rule
- "Determine if the occupant's complaint is justified" → Markdown skill
