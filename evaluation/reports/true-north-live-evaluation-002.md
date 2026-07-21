# True North Live Provider Re-evaluation 002

## 1. Repository Identity and Starting State

Repository `/Users/joellipton/Desktop/Violence_Checker`, branch `main`, starting HEAD `73b5112d29b941c5afb58767748231d2ee351558`, upstream `origin/main`, initially clean and 0 ahead / 0 behind.

## 2. Evaluation Authority

Corpus `violence-checker-true-north-operational-evaluation` `3.0.0` at SHA-256 `79f696ab0acd19ca6f648a12ce52f9bbbf1a1f26f990b35ee8a4e26b0087c836`; 24 corpus cases and eight synthetic fixtures. Provider observations are evidence, not ground truth.

## 3. Preflight Verification

Complete suite: 226 passed. Corpus validation, `validate-all`, and `baseline-readiness` passed. No baseline was accepted.

## 4. Provider Execution Controls

Configured OpenAI model `gpt-5-mini`; SDK retries disabled; one separate-process request per narrative; hard 120-second alarm; 32 requests and zero retries.

## 5. Live Corpus Results

| Case | Expected outcome | Observed outcome | Status | Earliest failing stage | Severity |
|---|---|---|---|---|---|
| TN_001 | Violence Detected | Violence Detected | PASS | — | — |
| TN_002 | Violence Detected | Uncertain | SEMANTIC_MISMATCH | EVALUATION_COMPARISON | 1 |
| TN_003 | Violence Detected | Violence Detected | PASS | — | — |
| TN_004 | Violence Detected | Violence Detected | PASS | — | — |
| TN_005 | Violence Detected | Violence Detected | PASS | — | — |
| TN_006 | No Violence Detected | No Violence Detected | PASS | — | — |
| TN_007 | No Violence Detected | Unable to Determine | PROVIDER_TIMEOUT | PROVIDER_REQUEST | — |
| TN_008 | No Violence Detected | Unable to Determine | VALIDATION_FAILURE | EVIDENCE_INTEGRITY_VALIDATION | 1 |
| TN_009 | No Violence Detected | No Violence Detected | PASS | — | — |
| TN_010 | Violence Detected | Violence Detected | ACCEPTABLE_VARIATION | — | — |
| TN_011 | No Violence Detected | Unable to Determine | VALIDATION_FAILURE | EVIDENCE_INTEGRITY_VALIDATION | 1 |
| TN_012 | Uncertain | Unable to Determine | VALIDATION_FAILURE | EVIDENCE_INTEGRITY_VALIDATION | 2 |
| TN_013 | No Violence Detected | Unable to Determine | VALIDATION_FAILURE | EVIDENCE_INTEGRITY_VALIDATION | 2 |
| TN_014 | Uncertain | Uncertain | PASS | — | — |
| TN_015 | Violence Detected | Violence Detected | PASS | — | — |
| TN_016 | Violence Detected | Violence Detected | ACCEPTABLE_VARIATION | — | — |
| TN_017 | No Violence Detected | No Violence Detected | PASS | — | — |
| TN_018 | No Violence Detected | No Violence Detected | PASS | — | — |
| TN_019 | No Violence Detected | No Violence Detected | PASS | — | — |
| TN_020 | Violence Detected | Violence Detected | PASS | — | — |
| TN_021 | Violence Detected | Unable to Determine | PROVIDER_TIMEOUT | PROVIDER_REQUEST | — |
| TN_022 | Unable to Determine | Unable to Determine | PASS | — | — |
| TN_023 | Unable to Determine | Unable to Determine | PASS | — | — |
| TN_024 | Violence Detected | Violence Detected | SEMANTIC_MISMATCH | EVALUATION_COMPARISON | 1 |

## 6. Live Fixture Results

| Fixture | Expected outcome | Observed outcome | Status | Provider duration | Severity |
|---|---|---|---|---|---|
| CASE_001 | Violence Detected | Violence Detected | PASS | 29.936s | — |
| CASE_002 | Violence Detected | Unable to Determine | VALIDATION_FAILURE | 30.727s | 1 |
| CASE_003 | No Violence Detected | Unable to Determine | VALIDATION_FAILURE | 34.176s | 2 |
| CASE_004 | No Violence Detected | Unable to Determine | PROVIDER_FAILURE | 242.006s | — |
| CASE_005 | No Violence Detected | Unable to Determine | VALIDATION_FAILURE | 64.188s | 1 |
| CASE_006 | Violence Detected | Violence Detected | SEMANTIC_MISMATCH | 28.56s | 2 |
| CASE_007 | Violence Detected | Uncertain | SEMANTIC_MISMATCH | 77.153s | 1 |
| CASE_008 | Violence Detected | Violence Detected | PASS | 12.95s | — |

## 7. Adversarial Case Interpretation

`TN_017` through `TN_020` produced doctrine-valid live facts despite intentionally malformed injected corpus candidates and were evaluated against narrative truth. `TN_022` and `TN_023` correctly failed closed on the designed missing correction/contradiction relationships. `TN_021` timed out. `TN_024` preserved interpersonal violence but materially omitted property violence.

## 8. Aggregate Accuracy

Corpus exact passes: 14/24; acceptable variations: 2/24. Completed-response outcome accuracy: 17/22 (77.27%). Core operational-fact accuracy: 14/22 (63.64%).

## 9. Run 001 Versus Run 002

Exact passes changed by +12; outcome accuracy by +24.89 points; all-attempted core fact accuracy by +50.00 points; validation failures by -2; corpus timeouts by -1; Severity 1 by +1; Severity 2 by -8.

## 10. Evidence-Integrity Findings

Corpus validation failures: 4. Fixture validation failures: 3. Exact issue data and excerpts are recorded in the machine-readable artifacts.

## 11. Provider Availability Findings

`TN_007` and `TN_021` timed out at the case boundary. `CASE_004` returned an OpenAI request failure. None was retried; all other cases continued safely.

## 12. Severity 1 Findings

- `TN_002`: expected `Violence Detected`, observed `Uncertain`; stage `EVALUATION_COMPARISON`.
- `TN_008`: expected `No Violence Detected`, observed `Unable to Determine`; stage `EVIDENCE_INTEGRITY_VALIDATION`.
- `TN_011`: expected `No Violence Detected`, observed `Unable to Determine`; stage `EVIDENCE_INTEGRITY_VALIDATION`.
- `TN_024`: expected `Violence Detected`, observed `Violence Detected`; stage `EVALUATION_COMPARISON`.
- `CASE_002`: expected `Violence Detected`, observed `Unable to Determine`; stage `EVIDENCE_INTEGRITY_VALIDATION`.
- `CASE_005`: expected `No Violence Detected`, observed `Unable to Determine`; stage `EVIDENCE_INTEGRITY_VALIDATION`.
- `CASE_007`: expected `Violence Detected`, observed `Uncertain`; stage `EVALUATION_COMPARISON`.

## 13. Severity 2 Findings

- `TN_012`: material semantic or validation difference; stage `EVIDENCE_INTEGRITY_VALIDATION`.
- `TN_013`: material semantic or validation difference; stage `EVIDENCE_INTEGRITY_VALIDATION`.
- `CASE_003`: material semantic or validation difference; stage `EVIDENCE_INTEGRITY_VALIDATION`.
- `CASE_006`: material semantic or validation difference; stage `EVALUATION_COMPARISON`.

## 14. Severity 3 Findings

No Severity 3 failures. Equivalent evidence segmentation in otherwise exact cases was classified as `ACCEPTABLE_VARIATION`.

## 15. Artifacts Created

- `evaluation/runs/true-north-live-evaluation-002.json`
- `evaluation/reports/true-north-live-comparison-002.json`
- `evaluation/reports/true-north-live-fixtures-002.json`
- `evaluation/reports/true-north-live-evaluation-002.md`

## 16. Semantic Readiness Conclusion

`NOT_READY_SEMANTIC_FAILURES`

No baseline was accepted.

## 17. Provider Availability Conclusion

`PROVIDER_AVAILABILITY_NOT_ACCEPTABLE`

## 18. Governance and Verification Results

Post-evaluation verification is recorded by the executor heartbeat and commit evidence. No runtime, prompt, validation, policy, corpus, fixture, or test behavior was changed.

## 19. Heartbeat

Exactly one self-contained executor event will record preflight, execution controls, artifacts, conclusions, governance, and commit authorization.

## 20. Commit

One commit is authorized with subject `test: record true north live re-evaluation`; no amend and no push.

## 21. Repository End State

No baseline acceptance, deployment, hosted acceptance, or push occurred. Final repository identity and divergence are verified after commit.
