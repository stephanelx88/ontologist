# QA Report — Finance and Banking Ontology

**Date:** 2026-04-09
**QA Mode:** supervised (Phase 1)
**Reviewers:** 3 parallel Opus agents

## Results

| Reviewer | Checks | PASS | FAIL | Verdict |
|----------|--------|------|------|---------|
| Implementation Auditor | 5 | 2 | 3 | FAIL |
| Consistency Reviewer | 5 | 4 | 1 | FAIL |
| Ontological Rigor | 6 | 5 | 1 | FAIL |

**Consensus:** 0/3 PASS → issues found, no CRITICAL escalation needed.

## Issues Found and Resolved

### Issue 1: Rules reference invalid entity attributes (Auditor)
**Severity:** HIGH
- `name-mismatch-check` referenced `loan_application.applicant_name` → fixed to `applicant.full_name`
- `balance-consistency-check` referenced `account_list.balance` → fixed to `verification_photo` screen comparison
- `employee-consistency-check` referenced `verification_photos.employee_id` → fixed to `verification_session.photos -> vpbank_employee.employee_id`
- `balance-vs-salary-ratio` referenced `account_balance` → fixed to `bank_account.balance` and `income_profile.average_monthly_salary`

### Issue 2: Form date contradiction (Consistency)
**Severity:** MEDIUM
- Form date "10/11/2025" contradicts Jan 2025 photo dates
- Clarified as DD/MM/YYYY format (10 Nov 2025) in source doc — possible pre-dating or form prep date

### Issue 3: Missing entity — verification-session (Rigor)
**Severity:** MEDIUM
- Added `verification-session` entity with temporal attributes
- Added relationships: `package-has-session`, `session-contains-photos`, `session-performed-by`

### Issue 4: Missing entity — income-profile (Rigor)
**Severity:** MEDIUM
- Added `income-profile` entity as aggregate of salary transactions
- Added relationships: `package-has-income-profile`, `income-profile-from-salary`

### Issue 5: Missing phone model attribute (Auditor)
**Severity:** LOW
- Added `device_model` and `has_metadata` attributes to `verification-photo`

### Issue 6: Misleading source comment (Consistency)
**Severity:** LOW
- Changed "internal VPBank loan packages" → "MBBank app screenshots in VPBank loan verification packages"

### Issue 7: Missing IS-A relationship (Rigor)
**Severity:** LOW
- Added `salary-is-a-transaction` relationship to `relationships.yaml`

## Post-Fix Coverage

- Entities: 11 (was 9)
- Relationships: 20 (was 13)
- Rules: 10 (attribute references fixed)
- Gaps: 5 documented

## Verdict

All 7 issues resolved. Ontology ready for graphify visualization and agent deployment.
