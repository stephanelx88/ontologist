# Source: MBBank Mobile App Loan Verification Packages

## Overview
- **Type:** PDF documents containing photographs
- **Count:** 2 packages
- **Access:** Local filesystem at `bank-statements/MBbank- mobile app/`
- **Knowledge type:** proprietary

## Package 1: LN2501104785157
- **Pages:** 5 photographs
- **VPBank employee:** Doãn Thùy Hằng, ID: 42589
- **Applicant account:** LE THI PHUONG
- **Bank:** MBBank, account 2020108285007
- **Balance:** 78,129,696 VND
- **Salary evidence:** 10,184,345 VND from 28 Hung Phu Joint Fund Company (kỳ 1, Jan 2025)
- **Background form:** VPBank credit card + e-banking registration, handwritten date "10/11/2025" (DD/MM/YYYY format = 10 Nov 2025 — future date relative to photos, possibly pre-dated or form preparation date)
- **Photo metadata:** None (no timestamps)
- **Phone:** iPhone (older model, home button visible)
- **Screenshot sequence:** Home → QR → Account list → Account detail → Transaction detail

## Package 2: LN2501134790716
- **Pages:** 5 photographs (+ 1 more not yet read)
- **VPBank employee:** Nguyễn Tuyết Mai, ID: 47223
- **Applicant account:** NGUYEN BICH HANH (TGTT label)
- **Bank:** MBBank, accounts: 0600100790006 (primary, 39,277,860 VND), 0989559269 (9,397 VND), 2065796126293 (overdraft)
- **Total balance:** 39,634,452 VND
- **Salary evidence 1:** 5,000,000 VND — "CUSTOMER Luong thang 11 24" (Nov salary), 02/01/2025
- **Salary evidence 2:** 11,000,000 VND — "CUSTOMER luong t12.24 vo thuong tet duong li ch" (Dec salary + Tet bonus), 02/01/2025
- **Photo metadata:** 7 Jan 2025, 18:03-18:06, Hà Nội
- **Phone:** Samsung Galaxy (no home button, punch-hole camera)
- **Screenshot sequence:** Home → Account list → Account detail → Transaction detail × 2

## Extraction Notes
- Both packages follow identical VPBank verification procedure
- Employee badge always placed to the left of phone
- VPBank application form sometimes visible as background document
- MBBank is the applicant's bank in both cases (not VPBank)
- Package 2 has richer metadata (timestamps + geolocation)

## Fraud Signals Observed
- Package 2: Both salary amounts are perfectly round (5M and 11M) — flagged as info
- Package 2: Account name "NGUYEN BICH HANH" — need to verify matches loan applicant
- Package 1: No photo timestamps — weaker evidence chain
