# True North Post-refactor Live Provider Evaluation 003

## 1. Repository Identity and Starting State

Repository `/Users/joellipton/Desktop/Violence_Checker`, branch `main`, starting HEAD `1377c1bd985f75f89618631e05b2c078888cdbd3`, remote `origin` (`git@github.com:joelliptondesign/Violence_Checker.git`), upstream `origin/main`, initially clean and 2 ahead / 0 behind. Python 3.9.6 with the repository `.venv`; configured provider OpenAI model `gpt-5-mini`.

## 2. Semantic Refactor Verification

Provider output is limited to semantic facts, exact evidence, uncertainty, and temporary references. Repository code derives final identifiers, canonical ordering, correction targets, contradiction groups, and active/superseded bookkeeping. Extraction contract `violence-checker.true-north-fact-extraction@2.0.0`; semantic schema `violence-checker.true-north-incident-facts` `1.0.0`. Policy and corpus authority are unchanged.

## 3. Preflight Verification

Complete suite: 226 passed. Corpus validation, `validate-all`, and `baseline-readiness` passed. No baseline was accepted.

## 4. Provider Execution Controls

Configured OpenAI model `gpt-5-mini`; SDK retries disabled; one separate-process request per narrative; hard 120-second alarm; 32 requests and zero retries. Case failures did not prevent later cases from running.

## 5. Live Corpus Results

| Case | Expected outcome | Observed outcome | Status | Earliest failing stage | Severity |
|---|---|---|---|---|---|
| TN_001 | Violence Detected | Unable to Determine | PROVIDER_TIMEOUT | PROVIDER_REQUEST | — |
| TN_002 | Violence Detected | Violence Detected | PASS | — | — |
| TN_003 | Violence Detected | Violence Detected | PASS | — | — |
| TN_004 | Violence Detected | Violence Detected | PASS | — | — |
| TN_005 | Violence Detected | Violence Detected | PASS | — | — |
| TN_006 | No Violence Detected | Unable to Determine | PROVIDER_TIMEOUT | PROVIDER_REQUEST | — |
| TN_007 | No Violence Detected | No Violence Detected | PASS | — | — |
| TN_008 | No Violence Detected | Unable to Determine | PROVIDER_TIMEOUT | PROVIDER_REQUEST | — |
| TN_009 | No Violence Detected | No Violence Detected | PASS | — | — |
| TN_010 | Violence Detected | Unable to Determine | VALIDATION_FAILURE | EVIDENCE_INTEGRITY_VALIDATION | 1 |
| TN_011 | No Violence Detected | Unable to Determine | VALIDATION_FAILURE | EVIDENCE_INTEGRITY_VALIDATION | 1 |
| TN_012 | Uncertain | Uncertain | SEMANTIC_MISMATCH | EVALUATION_COMPARISON | 2 |
| TN_013 | No Violence Detected | No Violence Detected | SEMANTIC_MISMATCH | EVALUATION_COMPARISON | 2 |
| TN_014 | Uncertain | Uncertain | PASS | — | — |
| TN_015 | Violence Detected | Violence Detected | PASS | — | — |
| TN_016 | Violence Detected | Violence Detected | ACCEPTABLE_VARIATION | — | — |
| TN_017 | No Violence Detected | No Violence Detected | PASS | — | — |
| TN_018 | No Violence Detected | No Violence Detected | PASS | — | — |
| TN_019 | No Violence Detected | No Violence Detected | PASS | — | — |
| TN_020 | Violence Detected | Violence Detected | PASS | — | — |
| TN_021 | Violence Detected | Violence Detected | PASS | — | — |
| TN_022 | Unable to Determine | Unable to Determine | PROVIDER_TIMEOUT | PROVIDER_REQUEST | — |
| TN_023 | Unable to Determine | Unable to Determine | PASS | — | — |
| TN_024 | Violence Detected | Violence Detected | SEMANTIC_MISMATCH | EVALUATION_COMPARISON | 1 |

## 6. Live Fixture Results

| Fixture | Expected outcome | Observed outcome | Status | Provider duration | Severity |
|---|---|---|---|---|---|
| CASE_001 | Violence Detected | Violence Detected | PASS | 39.396s | — |
| CASE_002 | Violence Detected | Unable to Determine | VALIDATION_FAILURE | 27.494s | 1 |
| CASE_003 | No Violence Detected | No Violence Detected | PASS | 20.372s | — |
| CASE_004 | No Violence Detected | No Violence Detected | PASS | 32.412s | — |
| CASE_005 | No Violence Detected | Unable to Determine | VALIDATION_FAILURE | 60.943s | 1 |
| CASE_006 | Violence Detected | Unable to Determine | VALIDATION_FAILURE | 30.264s | 1 |
| CASE_007 | Violence Detected | Violence Detected | PASS | 24.767s | — |
| CASE_008 | Violence Detected | Violence Detected | PASS | 9.059s | — |

## 7. Prior Run Comparison

Against completed run `002`: exact passes +0; completed-response outcome accuracy +12.73 points; semantic mismatches +1; validation failures -2; corpus timeouts +2; Severity 1 -1; Severity 2 -2. Corrected cases: TN_002, TN_007, TN_021. Persistent failures: TN_008, TN_011, TN_012, TN_013, TN_024. New regressions or availability losses: TN_001, TN_006, TN_010, TN_022.

## 8. Severity 1 Findings

- `TN_010`: expected `Violence Detected`, observed `Unable to Determine`; stage `EVIDENCE_INTEGRITY_VALIDATION`.
- `TN_011`: expected `No Violence Detected`, observed `Unable to Determine`; stage `EVIDENCE_INTEGRITY_VALIDATION`.
- `TN_024`: expected `Violence Detected`, observed `Violence Detected`; stage `EVALUATION_COMPARISON`.
- `CASE_002`: expected `Violence Detected`, observed `Unable to Determine`; stage `EVIDENCE_INTEGRITY_VALIDATION`.
- `CASE_005`: expected `No Violence Detected`, observed `Unable to Determine`; stage `EVIDENCE_INTEGRITY_VALIDATION`.
- `CASE_006`: expected `Violence Detected`, observed `Unable to Determine`; stage `EVIDENCE_INTEGRITY_VALIDATION`.

## 9. Severity 2 Findings

- `TN_012`: material semantic or validation difference; stage `EVALUATION_COMPARISON`.
- `TN_013`: material semantic or validation difference; stage `EVALUATION_COMPARISON`.

## 10. Severity 3 Findings

No Severity 3 failures. Equivalent evidence segmentation in otherwise exact cases was classified as `ACCEPTABLE_VARIATION`.

## 11. Provider Availability Findings

Corpus provider timeouts: TN_001, TN_006, TN_008, TN_022. Fixture provider failures or timeouts: none. No case was retried, and later cases continued safely.

## 12. Artifacts Created

- `evaluation/runs/true-north-live-evaluation-003.json`
- `evaluation/reports/true-north-live-comparison-003.json`
- `evaluation/reports/true-north-live-fixtures-003.json`
- `evaluation/reports/true-north-live-evaluation-003.md`

## 13. Semantic Readiness Conclusion

`NOT_READY_SEMANTIC_FAILURES`

No baseline was accepted.

## 14. Provider Availability Conclusion

`PROVIDER_AVAILABILITY_NOT_ACCEPTABLE`

## 15. Governance and Verification Results

Post-evaluation verification covers the full deterministic suite, corpus and artifact validation, SITREC validation, `validate-all`, `baseline-readiness`, and Git whitespace checks. Runtime, prompt, validation, policy, corpus, fixtures, and tests remain unchanged.

## 16. Heartbeat

Exactly one self-contained executor event records repository inspection, preflight, refactor verification, all 32 bounded requests, comparison, conclusions, artifacts, prohibited operations avoided, and commit authorization.

## 17. Commit

One commit is authorized with subject `test: record post-refactor live evaluation`; no amend and no push.

## 18. Repository End State

No baseline acceptance, deployment, communication-provider request, or push occurred. Final repository identity, clean status, and divergence are verified after commit.
