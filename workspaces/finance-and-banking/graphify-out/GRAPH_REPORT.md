# Graph Report - ~/neo-workspaces/finance-and-banking  (2026-04-09)

## Corpus Check
- Corpus is ~2,312 words - fits in a single context window. You may not need a graph.

## Summary
- 51 nodes · 62 edges · 7 communities detected
- Extraction: 85% EXTRACTED · 15% INFERRED · 0% AMBIGUOUS · INFERRED: 9 edges (avg confidence: 0.82)
- Token cost: 0 input · 0 output

## God Nodes (most connected - your core abstractions)
1. `Skill: Verify Bank Statement Package` - 16 edges
2. `Fraud Detector Agent` - 10 edges
3. `Finance and Banking Ontology` - 8 edges
4. `Applicant Entity` - 5 edges
5. `Finance and Banking Neo Workspace` - 4 edges
6. `VPBank Employee Entity` - 4 edges
7. `MBBank Loan Package 1 (LN2501104785157)` - 4 edges
8. `MBBank Loan Package 2 (LN2501134790716)` - 4 edges
9. `Risk Classification (CLEAN/REVIEW/SUSPICIOUS)` - 3 edges
10. `Loan Application Package Entity` - 3 edges

## Surprising Connections (you probably didn't know these)
- `VPBank Verification Procedure` --semantically_similar_to--> `Skill: Verify Bank Statement Package`  [INFERRED] [semantically similar]
  sources/mbbank-loan-packages.md → ontology/skills/verify-bank-statement.md
- `Name Mismatch Detection Scenario` --semantically_similar_to--> `Applicant: Nguyen Bich Hanh (Package 2)`  [INFERRED] [semantically similar]
  agents/fraud-detector/spec/scenarios/core-workflow.md → sources/mbbank-loan-packages.md
- `Applicant: Le Thi Phuong (Package 1)` --implements--> `Applicant Entity`  [INFERRED]
  sources/mbbank-loan-packages.md → ontology/ONTOLOGY.md
- `Fraud Detector Agent` --references--> `Skill: Verify Bank Statement Package`  [INFERRED]
  agents/fraud-detector/AGENT.md → ontology/skills/verify-bank-statement.md
- `Applicant: Nguyen Bich Hanh (Package 2)` --implements--> `Applicant Entity`  [INFERRED]
  sources/mbbank-loan-packages.md → ontology/ONTOLOGY.md

## Hyperedges (group relationships)
- **Fraud Detection Pipeline** — agent_md_fraud_detector, verify_bank_statement_skill, agent_md_risk_classification, agent_md_fraud_assessment_output, learn_and_update_skill [EXTRACTED 0.95]
- **Loan Application Entity Relationship Graph** — ontology_md_applicant, ontology_md_bank_account, ontology_md_transaction, ontology_md_salary_transaction, ontology_md_vpbank_employee, ontology_md_verification_photo, ontology_md_loan_application_package, ontology_md_employer [EXTRACTED 1.00]
- **COSTAR Architecture Flow** — claude_md_costar_architecture, agents_md_costar_co, agents_md_costar_star, agents_md_neo_architect, agent_md_fraud_detector [EXTRACTED 1.00]

## Communities

### Community 0 - "Verification Skills & Gaps"
Cohesion: 0.17
Nodes (12): Gap: Cross-Applicant Device Reuse Detection, Gap: VPBank Employee Volume Thresholds, VPBank Verification Procedure, Skill: Verify Bank Statement Package, Rule: badge-present-check, Rule: balance-consistency-check, Rule: balance-vs-salary-ratio, Rule: employee-consistency-check (+4 more)

### Community 1 - "COSTAR Architecture"
Cohesion: 0.2
Nodes (10): Agents Registry, COSTAR CO - Curate and Organize, COSTAR STAR - See Think Act Reflect, Neo.Architect, COSTAR Cognitive Architecture, Finance and Banking Neo Workspace, Gap: Other Bank App Layouts, Rationale: Epistemic Status Draft (+2 more)

### Community 2 - "Source Data & Packages"
Cohesion: 0.22
Nodes (9): Name Mismatch Detection Scenario, MBBank Loan Package 1 (LN2501104785157), MBBank Loan Package 2 (LN2501134790716), VPBank Employee: Doan Thuy Hang (ID 42589), Applicant: Le Thi Phuong (Package 1), MBBank Mobile App Loan Verification Source, Applicant: Nguyen Bich Hanh (Package 2), VPBank Employee: Nguyen Tuyet Mai (ID 47223) (+1 more)

### Community 3 - "Fraud Detection Agent"
Cohesion: 0.32
Nodes (8): Fraud Assessment Output Format, Fraud Detector Agent, Rationale: Minimize False Positives, Rationale: Out of Scope Boundaries, Risk Classification (CLEAN/REVIEW/SUSPICIOUS), Standard Package Verification Scenario, Gap: Photo Manipulation Detection Rules, Skill: Learn and Update

### Community 4 - "Domain Entity Model"
Cohesion: 0.32
Nodes (8): Applicant Entity, Bank Account Entity, Employer Entity, Loan Application Package Entity, Salary Transaction Entity, Transaction Entity, Verification Photo Entity, VPBank Employee Entity

### Community 5 - "Form Extraction Gap"
Cohesion: 1.0
Nodes (2): Gap: Loan Application Form Field Extraction, Bank Application Form Entity

### Community 6 - "Timestamp Rules"
Cohesion: 1.0
Nodes (2): Timestamp Manipulation Scenario, Rule: photo-timestamp-sequence

## Knowledge Gaps
- **23 isolated node(s):** `COSTAR Cognitive Architecture`, `Agents Registry`, `Fraud Assessment Output Format`, `Timestamp Manipulation Scenario`, `Transaction Entity` (+18 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `Form Extraction Gap`** (2 nodes): `Gap: Loan Application Form Field Extraction`, `Bank Application Form Entity`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Timestamp Rules`** (2 nodes): `Timestamp Manipulation Scenario`, `Rule: photo-timestamp-sequence`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Skill: Verify Bank Statement Package` connect `Verification Skills & Gaps` to `Source Data & Packages`, `Fraud Detection Agent`, `Timestamp Rules`?**
  _High betweenness centrality (0.461) - this node is a cross-community bridge._
- **Why does `Finance and Banking Ontology` connect `COSTAR Architecture` to `Source Data & Packages`, `Fraud Detection Agent`?**
  _High betweenness centrality (0.457) - this node is a cross-community bridge._
- **Why does `Fraud Detector Agent` connect `Fraud Detection Agent` to `Verification Skills & Gaps`, `COSTAR Architecture`?**
  _High betweenness centrality (0.410) - this node is a cross-community bridge._
- **Are the 3 inferred relationships involving `Skill: Verify Bank Statement Package` (e.g. with `Fraud Detector Agent` and `VPBank Verification Procedure`) actually correct?**
  _`Skill: Verify Bank Statement Package` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Are the 2 inferred relationships involving `Applicant Entity` (e.g. with `Applicant: Le Thi Phuong (Package 1)` and `Applicant: Nguyen Bich Hanh (Package 2)`) actually correct?**
  _`Applicant Entity` has 2 INFERRED edges - model-reasoned connections that need verification._
- **What connects `COSTAR Cognitive Architecture`, `Agents Registry`, `Fraud Assessment Output Format` to the rest of the system?**
  _23 weakly-connected nodes found - possible documentation gaps or missing edges._