# Scenario: Standard Package Verification

## Context
The most common case — a complete loan application package with all required
verification photos, badge visible, consistent data.

## Specification

**Given** a loan application package PDF with 4-6 verification photos showing
MBBank app screenshots and VPBank employee badge

**When** the fraud detector processes the package

**Then** it should:
1. Extract all structured data (names, accounts, balances, transactions)
2. Run all fraud detection rules
3. Produce a fraud assessment with risk score 0-100
4. List all triggered rules with severity and evidence
5. Provide a verdict: CLEAN, REVIEW, or SUSPICIOUS

## Edge Cases
- Missing badge in one photo: flag as CRITICAL, verdict SUSPICIOUS
- Name mismatch between app and form: flag as CRITICAL, verdict SUSPICIOUS
- No photo timestamps: flag as WARNING (weaker evidence), not CRITICAL
- Round salary amounts: flag as INFO only, not enough for REVIEW alone
- Multiple accounts visible: extract ALL, check each for consistency

## Validation Criteria
- [ ] All 10 fraud rules evaluated
- [ ] Risk score between 0-100
- [ ] Every finding cites specific photo page
- [ ] Verdict matches severity of findings (any CRITICAL → SUSPICIOUS)
- [ ] Salary summary extracted with period, amount, employer

---

# Scenario: Name Mismatch Detection

## Context
The account holder name in the bank app does not match the applicant name
on the loan application form.

## Specification

**Given** a package where bank app shows "NGUYEN BICH HANH" but loan applicant
is a different name

**When** the fraud detector processes the package

**Then** it should:
1. Flag `name-mismatch-check` as CRITICAL
2. Show both names side by side in the finding
3. Set verdict to SUSPICIOUS
4. Recommend manual verification of identity documents

## Validation Criteria
- [ ] Name mismatch detected
- [ ] CRITICAL severity assigned
- [ ] Verdict is SUSPICIOUS

---

# Scenario: Timestamp Manipulation

## Context
Photos have out-of-order timestamps or large gaps suggesting spliced evidence.

## Specification

**Given** a package where photo timestamps span more than 10 minutes or are
out of sequence

**When** the fraud detector processes the package

**Then** it should:
1. Flag `photo-timestamp-sequence` as WARNING
2. Show the timestamp sequence with gaps highlighted
3. Set verdict to at minimum REVIEW

## Validation Criteria
- [ ] Timestamp anomaly detected
- [ ] Time gap quantified in finding
- [ ] Verdict is REVIEW or higher
