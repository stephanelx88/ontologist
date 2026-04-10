# Neo Fraud Detection Pipeline — Design Spec

**Date:** 2026-04-09
**Status:** Design approved, ready for implementation

## Goal

User provides a Vietnamese bank statement PDF (loan verification package) → system autonomously extracts data → applies fraud rules → produces scored assessment + knowledge graph. Three interfaces: CLI, Claude Code skill, web app.

## Architecture

```
pipeline/                        # Python package — the shared engine
├── __init__.py
├── extract.py                   # PDF → pages → Gemini Vision → structured data
├── vision.py                    # Vision API abstraction (Gemini primary, Claude fallback)
├── models.py                    # Pydantic data models (PageData, PackageData, Finding, etc.)
├── rules.py                     # Load YAML rules, evaluate against extracted data
├── score.py                     # Compute fraud score (0-100) + verdict
├── report.py                    # Generate assessment (JSON + markdown)
├── graph.py                     # Generate graphify knowledge graph per package
├── server.py                    # FastAPI web app (drag & drop UI)
├── cli.py                       # CLI entry point
└── templates/
    └── index.html               # Single-page drag & drop UI
```

## Data Flow

```
PDF input
  │
  ├─ 1. Split PDF into page images (PyMuPDF/fitz, local, free)
  │
  ├─ 2. For each page → Gemini Vision API call (primary)
  │     If extraction confidence < 0.7 → Claude Vision API fallback
  │     Extract: badge info, account names, balances,
  │     transactions, timestamps, screen type, device model
  │     Returns: structured JSON per page
  │
  ├─ 3. Merge page extractions → PackageData (Pydantic model)
  │     (applicant, employee, accounts, transactions, photos metadata)
  │
  ├─ 4. Load rules from ontology/rules/fraud-detection-rules.yaml
  │     Evaluate each rule against PackageData
  │     Returns: list of triggered rules with severity
  │
  ├─ 5. Compute fraud score
  │     CRITICAL finding = 70 base score
  │     Each additional CRITICAL = +10
  │     Each WARNING = +10
  │     Each INFO = +3
  │     Cap at 100
  │     Verdict: 0-30 CLEAN, 31-60 REVIEW, 61-100 SUSPICIOUS
  │
  ├─ 6. Generate report (JSON + markdown)
  │
  ├─ 7. Generate knowledge graph (graphify integration)
  │
  └─ Output: FraudAssessment
       ├── assessment.json        # Machine-readable
       ├── assessment.md          # Human-readable
       └── graph.html             # Interactive knowledge graph
```

## Vision Extraction

### Provider Abstraction (vision.py)

```python
class VisionProvider(Protocol):
    async def extract_page(self, image: bytes, prompt: str) -> PageData: ...

class GeminiVision(VisionProvider):
    """Primary — better at degraded photos, Vietnamese text, angled screens."""

class ClaudeVision(VisionProvider):
    """Fallback — used when Gemini extraction confidence < 0.7."""
```

### Extraction Strategy

1. Send page image to Gemini with structured extraction prompt
2. Parse response into PageData model
3. Check confidence: if any critical field (badge name, account number, balance) is null or flagged uncertain → re-extract with Claude Vision
4. Merge: prefer Gemini result, fill gaps from Claude result

### Per-Page Extraction Prompt

Returns structured JSON:
```json
{
  "page_number": 1,
  "screen_type": "home | qr | account_list | account_detail | transaction_detail | unknown",
  "confidence": 0.92,
  "badge": {
    "name": "Doãn Thùy Hằng",
    "employee_id": "42589",
    "visible": true,
    "confidence": 0.95
  },
  "accounts": [{
    "number": "2020108285007",
    "holder_name": "LE THI PHUONG",
    "balance": 78129696,
    "currency": "VND",
    "type": "payment",
    "is_default": true
  }],
  "transactions": [{
    "amount": 10184345,
    "direction": "incoming",
    "counterparty": "28 HUNG PHU JOINT FUND COMPANY",
    "description": "Thanh toán lương kỳ 1 tháng 01 năm 2025",
    "timestamp": "2025-01-10T00:00:00",
    "reference": "T54544W919Y010059",
    "is_salary": true
  }],
  "device": {
    "type": "iphone",
    "model": "iPhone SE (older, home button visible)",
    "confidence": 0.8
  },
  "photo_metadata": {
    "timestamp": null,
    "location": null,
    "has_metadata": false
  },
  "background_document": {
    "visible": true,
    "type": "vpbank_application_form",
    "date": "10/11/2025",
    "notes": "DD/MM/YYYY format"
  }
}
```

## Data Models (models.py)

```python
@dataclass(frozen=True)
class BadgeData:
    name: str | None
    employee_id: str | None
    visible: bool
    confidence: float

@dataclass(frozen=True)
class AccountData:
    number: str
    holder_name: str | None
    balance: int  # VND
    currency: str
    type: str  # payment | overdraft | foreign_currency
    is_default: bool

@dataclass(frozen=True)
class TransactionData:
    amount: int  # VND
    direction: str  # incoming | outgoing
    counterparty: str | None
    description: str | None
    timestamp: str | None
    reference: str | None
    is_salary: bool

@dataclass(frozen=True)
class PageData:
    page_number: int
    screen_type: str
    confidence: float
    badge: BadgeData | None
    accounts: list[AccountData]
    transactions: list[TransactionData]
    device_type: str | None
    device_model: str | None
    photo_timestamp: str | None
    photo_location: str | None
    has_metadata: bool
    background_document_type: str | None

@dataclass(frozen=True)
class PackageData:
    loan_reference: str
    pages: list[PageData]
    applicant_name: str | None       # derived from account holder
    employee_name: str | None        # derived from badge
    employee_id: str | None          # derived from badge
    accounts: list[AccountData]      # merged from all pages
    transactions: list[TransactionData]  # merged from all pages
    total_balance: int               # sum of all account balances
    salary_transactions: list[TransactionData]  # filtered
    session_duration_seconds: float | None
    device_type: str | None
    device_model: str | None

@dataclass(frozen=True)
class Finding:
    rule_id: str
    rule_name: str
    severity: str  # critical | warning | info
    description: str
    evidence: str
    page_reference: str | None

@dataclass(frozen=True)
class FraudAssessment:
    loan_reference: str
    risk_score: int  # 0-100
    verdict: str  # CLEAN | REVIEW | SUSPICIOUS
    package: PackageData
    findings: list[Finding]
    extraction_provider: str  # gemini | claude | hybrid
    timestamp: str
```

## Rule Engine (rules.py)

Pure Python. Loads `ontology/rules/fraud-detection-rules.yaml`. Each rule has a condition that maps to a Python function:

```python
RULE_EVALUATORS = {
    "name-mismatch-check": evaluate_name_mismatch,
    "badge-present-check": evaluate_badge_present,
    "employee-consistency-check": evaluate_employee_consistency,
    "balance-consistency-check": evaluate_balance_consistency,
    "salary-regularity-check": evaluate_salary_regularity,
    "salary-description-format": evaluate_salary_description,
    "photo-timestamp-sequence": evaluate_timestamp_sequence,
    "screenshot-date-vs-photo-date": evaluate_screenshot_freshness,
    "round-number-deposit": evaluate_round_numbers,
    "balance-vs-salary-ratio": evaluate_balance_salary_ratio,
}
```

Each evaluator is a pure function: `(PackageData) -> Finding | None`. No LLM, no I/O.

## Scoring (score.py)

```python
def compute_score(findings: list[Finding]) -> tuple[int, str]:
    score = 0
    has_critical = False
    for f in findings:
        if f.severity == "critical":
            score += 70 if not has_critical else 10
            has_critical = True
        elif f.severity == "warning":
            score += 10
        elif f.severity == "info":
            score += 3
    score = min(score, 100)
    
    if score >= 61:
        verdict = "SUSPICIOUS"
    elif score >= 31:
        verdict = "REVIEW"
    else:
        verdict = "CLEAN"
    
    return score, verdict
```

## Three Interfaces

### CLI (cli.py)

```bash
# Single PDF
python -m pipeline.cli statement.pdf

# Custom output directory
python -m pipeline.cli statement.pdf --output-dir ./results

# Batch — process all PDFs in folder
python -m pipeline.cli bank-statements/ --batch

# JSON only (no markdown, no graph)
python -m pipeline.cli statement.pdf --json-only

# Verbose (show per-page extraction progress)
python -m pipeline.cli statement.pdf --verbose
```

Output:
```
Neo Fraud Detection — LN2501104785157
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Applicant:  LE THI PHUONG
Employee:   Doãn Thùy Hằng (ID: 42589)
Balance:    78,129,696 VND
Salary:     10,184,345 VND (kỳ 1, Jan 2025)

Risk Score: 8/100
Verdict:    CLEAN ✓

Findings:
  [INFO] round-number-deposit — not triggered
  [INFO] balance-vs-salary-ratio — 7.8x (within range)

Saved: results/LN2501104785157/assessment.json
       results/LN2501104785157/assessment.md
       results/LN2501104785157/graph.html
```

### Claude Code Skill (B)

`/neo build statement.pdf` invokes `python -m pipeline.cli` under the hood, reads the output, displays in chat.

Update SKILL.md routing: BUILD intent with a PDF → run pipeline CLI → display results.

### Web App (server.py)

```bash
python -m pipeline.server                # localhost:8000
python -m pipeline.server --port 3000
```

**Single-page UI:**
- Drag & drop zone for PDF
- Live progress bar (page 1/5... page 2/5... rules... scoring...)
- Assessment display: score gauge, verdict badge, findings table
- Knowledge graph embedded (graph.html iframe)
- Download buttons: JSON, markdown, graph

**API endpoints:**
```
POST /api/analyze          # multipart/form-data with PDF
GET  /api/status/{job_id}  # SSE stream for progress
GET  /api/results/{job_id} # completed assessment
GET  /api/graph/{job_id}   # graph.html for this assessment
```

**Tech:** FastAPI + vanilla HTML/CSS/JS. No React, no build step. Server-Sent Events for live progress.

## Dependencies

```
anthropic>=0.40.0      # Claude Vision fallback
google-genai>=1.0.0    # Gemini Vision primary
PyMuPDF>=1.24.0        # PDF → page images
fastapi>=0.115.0       # Web server
uvicorn>=0.32.0        # ASGI server
pyyaml>=6.0            # Rule loading
graphifyy>=0.1.0       # Knowledge graph
pydantic>=2.0          # Data models
python-multipart       # File upload handling
```

## Configuration

```yaml
# pipeline/config.yaml
vision:
  primary: gemini          # gemini | claude
  fallback: claude         # claude | none
  gemini_model: gemini-2.0-flash  # fast + cheap for vision
  claude_model: claude-sonnet-4-20250514
  confidence_threshold: 0.7  # below this → trigger fallback

rules:
  path: ontology/rules/fraud-detection-rules.yaml

scoring:
  critical_base: 70
  critical_additional: 10
  warning_weight: 10
  info_weight: 3
  thresholds:
    clean: 30
    review: 60
    # above 60 = suspicious

output:
  formats: [json, markdown, graph]
  graph_enabled: true
```

## Environment Variables

```
GEMINI_API_KEY=...         # Required for primary vision
ANTHROPIC_API_KEY=...      # Required for fallback vision
NEO_RULES_PATH=...         # Override default rules path
NEO_OUTPUT_DIR=...         # Override default output directory
```

## Cost per PDF

- ~5 pages × Gemini Vision (flash) = ~$0.005
- Fallback pages (if any) × Claude Sonnet = ~$0.01/page
- Typical total: **$0.005-0.02 per PDF**
- Rule engine + scoring + graph = free

## Deployment (Docker)

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY . .
RUN pip install -e .
EXPOSE 8000
CMD ["python", "-m", "pipeline.server"]
```

## File Layout in Repo

```
ontologist/
├── pipeline/                    # NEW — the engine
│   ├── __init__.py
│   ├── extract.py
│   ├── vision.py
│   ├── models.py
│   ├── rules.py
│   ├── score.py
│   ├── report.py
│   ├── graph.py
│   ├── server.py
│   ├── cli.py
│   ├── config.yaml
│   └── templates/
│       └── index.html
├── tests/                       # NEW — test suite
│   ├── test_rules.py
│   ├── test_score.py
│   ├── test_extract.py
│   └── test_models.py
├── Dockerfile                   # NEW
├── pyproject.toml               # NEW
├── workspaces/finance-and-banking/  # Existing ontology
├── bank-statements/             # Source PDFs
├── SKILL.md
├── specs.md
└── references/
```
