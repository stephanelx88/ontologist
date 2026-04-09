# Finance and Banking Ontology — Bank Statement Verification for Fraud Detection

## Purpose
This ontology encodes Vietnamese bank statement verification expertise so that
AI agents can detect fraud in loan application packages submitted to VPBank.

## Domain
Vietnamese consumer lending — specifically the verification step where VPBank
employees photograph applicants' mobile banking app screens as income/balance evidence.

## Entities
- **loan-application-package** — the bundle of evidence for one loan
- **applicant** — the person applying for credit
- **bank-account** — financial account (payment, overdraft, foreign currency)
- **transaction** — a financial event in the account
- **salary-transaction** — income transfer from employer
- **vpbank-employee** — the loan officer who captures verification
- **verification-photo** — a single evidence photograph
- **bank-application-form** — the physical VPBank form
- **employer** — the company paying the applicant's salary

## Key Relationships
```
applicant --holds--> bank-account --contains--> transaction
applicant --employed_by--> employer --originates--> salary-transaction
applicant --submits--> loan-application-package
vpbank-employee --verifies--> loan-application-package
vpbank-employee --captures--> verification-photo --evidences--> bank-account
salary-transaction --proves_income_for--> loan-application-package
```

## Data Sources
See INVENTORY.md — currently 2 MBBank loan verification packages.

## Coverage
- Entities: 11 defined (9 original + verification-session + income-profile)
- Relationships: 20 mapped
- Rules: 10 encoded (fraud detection)
- Skills: 2 documented (learn-and-update, verify-bank-statement)
- Known gaps: See docs/gaps.md (5 open)

## Epistemic Status
draft — extracted from 2 packages, QA loop complete (7 issues found, all fixed)
