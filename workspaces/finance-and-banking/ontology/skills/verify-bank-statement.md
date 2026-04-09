## Skill: Verify Bank Statement Package

**Purpose:** Systematically verify a VPBank loan application package containing mobile banking screenshots for fraud indicators.

**When to use:** When processing any loan application package with bank statement screenshots.

**Inputs:**
- verification_photos: List of photos in the package (ordered by page)
- loan_reference: The LN-prefixed loan reference number

**Procedure:**

1. **Identity extraction** — From each photo, extract:
   - Employee badge: name, ID number, photo match
   - Bank app account holder name (TGTT label)
   - Account numbers visible

2. **Consistency checks** (apply rules in order):
   - `badge-present-check`: Is the badge visible in ALL photos?
   - `employee-consistency-check`: Same badge in all photos?
   - `name-mismatch-check`: Account holder name matches applicant?
   - `balance-consistency-check`: Balance in list view = balance in detail view?

3. **Temporal checks:**
   - `photo-timestamp-sequence`: Are photo timestamps sequential within 10 min?
   - `screenshot-date-vs-photo-date`: Is the query date range current?

4. **Income verification:**
   - `salary-description-format`: Do salary descriptions contain standard keywords?
   - `salary-regularity-check`: Are salary deposits on regular dates/amounts?
   - `round-number-deposit`: Are salary amounts suspiciously round?

5. **Balance assessment:**
   - `balance-vs-salary-ratio`: Is balance plausible relative to income?

6. **Cross-reference** (if multiple packages available):
   - Same employee processing too many applications? (volume check)
   - Same phone device across different applicants? (device reuse)
   - Same background/location across different applicants?

7. **Verdict:** Classify as:
   - **CLEAN** — No flags triggered
   - **REVIEW** — Info/warning flags only, manual review recommended
   - **SUSPICIOUS** — Critical flag triggered, escalate to fraud team

**Outputs:**
- Fraud score (0-100)
- List of triggered rules with severity
- Extracted data summary (name, accounts, balances, salary)
- Recommendation (CLEAN / REVIEW / SUSPICIOUS)

**Rules applied:** All rules in fraud-detection-rules.yaml
**Data sources:** Verification photos in loan application package
