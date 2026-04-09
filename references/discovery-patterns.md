# Discovery Patterns

Recurring patterns for finding and extracting domain knowledge. Use these
during the `/discover` phase to systematically uncover hidden knowledge.

---

## Table of Contents

1. [Document Repository Pattern](#1-document-repository-pattern)
2. [Control Hierarchy Pattern](#2-control-hierarchy-pattern)
3. [Test-as-Knowledge Pattern](#3-test-as-knowledge-pattern)
4. [API-as-Ontology Pattern](#4-api-as-ontology-pattern)
5. [Configuration Signal Pattern](#5-configuration-signal-pattern)
6. [Schema Documentation Mismatch](#6-schema-documentation-mismatch)
7. [Tribal Knowledge Extraction](#7-tribal-knowledge-extraction)
8. [Cross-Reference Validation](#8-cross-reference-validation)

---

## 1. Document Repository Pattern

**Problem:** Teams point to a folder of PDFs/docs and say "the knowledge is in there."

**Detection:** User mentions document repositories, shared drives, wikis, Confluence spaces.

**Response:**
1. Catalog every document — title, type, date, author, topic coverage
2. For each document, extract: entities mentioned, rules stated, procedures described
3. Cross-reference: which entities appear in multiple docs? Those are core entities.
4. Identify contradictions between documents (common in evolving domains)
5. Note which documents are current vs. outdated

**Why this matters:** Referencing a repository is not discovering knowledge. The ontology
needs the extracted content, not pointers to where content lives.

---

## 2. Control Hierarchy Pattern

**Problem:** Systems with controllers (HVAC, manufacturing, process control) have implicit
hierarchies that aren't documented but are critical for diagnosis.

**Detection:** Domain mentions controllers, setpoints, loops, PID, cascades, overrides.

**Response:**
1. Map the hierarchy: which controller controls which?
2. For each controller, document:
   - What it optimizes for (control variable)
   - What constrains it (cascade constraints from parent)
   - When it saturates (can't do more)
   - What its saturation signals to the parent
3. Document the override/priority logic

**Example (HVAC):**
```
Chiller Plant → AHU → VAV → Zone
  |                |       |       |
  optimizes:       optimizes: optimizes: measures:
  CW temp          SA temp   airflow   zone temp
  |                |       |
  saturates:       saturates: saturates:
  max capacity     valve 100% damper 100%
```

---

## 3. Test-as-Knowledge Pattern

**Problem:** Existing test suites encode implicit domain knowledge that nobody thinks
to extract into the ontology.

**Detection:** Project has test files, QA docs, acceptance criteria, validation scripts.

**Response:**
1. Read test files — each assertion encodes an expected behavior
2. Extract: what entity is being tested? What rule does the test enforce?
3. Edge case tests often reveal domain exceptions (counterfactuals)
4. Integration tests reveal entity relationships
5. Performance tests reveal operational constraints

**What to capture:**
- Threshold values from assertions → YAML rules
- Expected behaviors → spec scenarios
- Error conditions tested → counterfactuals
- Workflow tests → skills/procedures

---

## 4. API-as-Ontology Pattern

**Problem:** REST/GraphQL APIs already encode a domain model, but it's implicit in
endpoints, schemas, and response shapes.

**Detection:** Domain has APIs, microservices, data endpoints.

**Response:**
1. Map API resources to entities
2. Map nested resources to relationships (e.g., `/buildings/{id}/floors` = Building has Floors)
3. Extract enums as entity types/categories
4. Map query parameters as entity attributes
5. Note which endpoints are read vs. write (implies agent capabilities)
6. Document error codes as business rules

---

## 5. Configuration Signal Pattern

**Problem:** Configuration files encode domain decisions that aren't documented elsewhere.

**Detection:** .yaml, .json, .toml, .env, .ini files with domain-specific values.

**Response:**
1. Catalog every configurable parameter
2. For each: what does the default value mean? Who decided it? Why?
3. Which parameters are environment-specific vs. universal?
4. Empty/commented-out config values signal "this was considered but not needed"
5. Config file proliferation signals architectural complexity

---

## 6. Schema Documentation Mismatch

**Problem:** The documented schema doesn't match the actual data.

**Detection:** Compare declared schemas with real data samples.

**Response:**
1. Identify fields present in data but missing from docs
2. Identify documented fields that don't appear in data
3. Check for null/empty patterns that reveal optional vs. required
4. Document the actual schema as the source of truth
5. Note discrepancies as knowledge gaps

---

## 7. Tribal Knowledge Extraction

**Problem:** The most critical domain knowledge lives in experts' heads, not in documents.

**Detection:** User says "our senior engineer knows this" or "we just know to do it this way."

**Response:**
1. Interview using specific scenarios, not abstract questions
2. Ask "what would happen if...?" to uncover causalities
3. Ask "what's the exception to that rule?" to find counterfactuals
4. Ask "how do you know when something is wrong?" to find diagnostic procedures
5. Record the expert's decision process, not just their conclusions

**Interview techniques:**
- Walk through a recent incident: what did you see, think, do?
- Present a hypothetical failure: what would you check first?
- Ask about edge cases: "does this rule always apply?"

---

## 8. Cross-Reference Validation

**Problem:** Knowledge from different sources may contradict or complement each other.

**Detection:** Multiple documents/sources cover the same entities or rules.

**Response:**
1. For each entity, collect all descriptions from all sources
2. Identify contradictions — which source is authoritative?
3. Identify complements — Source A has attributes, Source B has relationships
4. Merge into a single canonical definition in the ontology
5. Document provenance: which source contributed what

---

## General Discovery Principles

- **Exhaustive before selective** — scan everything first, then prioritize
- **Structure reveals knowledge** — how information is organized tells you what matters
- **Absence is information** — what's NOT documented is often the most critical gap
- **Ask "why" five times** — surface root causes, not symptoms
- **Prefer concrete over abstract** — "the threshold is 25°C" beats "appropriate temperature"
