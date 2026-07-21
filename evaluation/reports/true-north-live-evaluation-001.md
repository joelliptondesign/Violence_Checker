# True North Live Provider Operational Evaluation 001

## 1. Repository and Execution Identity

Repository `/Users/joellipton/Desktop/Violence_Checker`, branch `main`, starting commit `b735fdb994618463f2eb83de22766231c22f6c1a`. Live execution ran from `2026-07-21T11:23:50.600526Z` through `2026-07-21T11:38:06.631578Z` with 24 requests and zero retries.

## 2. Evaluation Authority

Corpus `violence-checker-true-north-operational-evaluation` version `3.0.0` at SHA-256 `79f696ab0acd19ca6f648a12ce52f9bbbf1a1f26f990b35ee8a4e26b0087c836` is authoritative. Evaluation schema `3.0.0` and semantic schema `violence-checker.true-north-incident-facts` `1.0.0` governed the run.

## 3. Provider Configuration

The configured repository OpenAI client used model `gpt-5-mini` with SDK retries disabled. Each case ran in a separate process under a 120-second alarm. Provider output is observed evidence, not ground truth.

## 4. Execution Summary

All 24 cases were attempted once. Results: 2 PASS, 13 SEMANTIC_MISMATCH, 6 VALIDATION_FAILURE, 0 PROVIDER_FAILURE, 3 PROVIDER_TIMEOUT, and 0 PIPELINE_FAILURE.

## 5. Outcome Accuracy

Observed pipeline outcomes matched 13/24 (54.17%). Among the 21 completed provider responses, 11/21 (52.38%) matched. Provider-timeout fallback outcomes are included only in the all-attempted measure.

## 6. Operational Fact Accuracy

Exact doctrine-authored operational facts matched 2/24 (8.33%). Derived direction matched 13/15 (86.67%) when derivation was available.

## 7. Evidence-Integrity Results

Evidence-integrity validation passed 15/21 completed responses (71.43%). Six responses failed closed at evidence-integrity validation.

## 8. Fixture Results

All eight fixture expectation records were verified by deterministic preflight. Zero fixture narratives were sent to the provider because explicit external-data approval was limited to the 24 active corpus narratives and no fixture narrative was byte-equivalent to an active case. This is an 8/8 expectation-authority verification result, not a live-provider fixture result.

## 9. Failures by Pipeline Stage

- `EVALUATION_COMPARISON`: 13
- `EVIDENCE_INTEGRITY_VALIDATION`: 6
- `PROVIDER_REQUEST`: 3

## 10. Severity 1 Findings

- `TN_010`: expected `Violence Detected`, observed `Unable to Determine`; earliest stage `EVIDENCE_INTEGRITY_VALIDATION`.
- `TN_020`: expected `Unable to Determine`, observed `Violence Detected`; earliest stage `EVALUATION_COMPARISON`.
- `TN_021`: expected `Unable to Determine`, observed `Violence Detected`; earliest stage `EVALUATION_COMPARISON`.

## 11. Severity 2 Findings

- `TN_008`: material fact, uncertainty, validation, direction, or non-binary outcome difference; earliest stage `EVIDENCE_INTEGRITY_VALIDATION`.
- `TN_009`: material fact, uncertainty, validation, direction, or non-binary outcome difference; earliest stage `EVIDENCE_INTEGRITY_VALIDATION`.
- `TN_011`: material fact, uncertainty, validation, direction, or non-binary outcome difference; earliest stage `EVALUATION_COMPARISON`.
- `TN_012`: material fact, uncertainty, validation, direction, or non-binary outcome difference; earliest stage `EVIDENCE_INTEGRITY_VALIDATION`.
- `TN_013`: material fact, uncertainty, validation, direction, or non-binary outcome difference; earliest stage `EVIDENCE_INTEGRITY_VALIDATION`.
- `TN_014`: material fact, uncertainty, validation, direction, or non-binary outcome difference; earliest stage `EVALUATION_COMPARISON`.
- `TN_017`: material fact, uncertainty, validation, direction, or non-binary outcome difference; earliest stage `EVIDENCE_INTEGRITY_VALIDATION`.
- `TN_019`: material fact, uncertainty, validation, direction, or non-binary outcome difference; earliest stage `EVALUATION_COMPARISON`.
- `TN_022`: material fact, uncertainty, validation, direction, or non-binary outcome difference; earliest stage `EVALUATION_COMPARISON`.
- `TN_024`: material fact, uncertainty, validation, direction, or non-binary outcome difference; earliest stage `EVALUATION_COMPARISON`.

## 12. Severity 3 Findings

- `TN_002`: outcome and material facts matched; evidence-support selection included the additional `resolution_status` label.
- `TN_003`: outcome and material facts matched; evidence-support selection included the additional `resolution_status` label.
- `TN_004`: outcome and material facts matched; evidence-support selection included the additional `resolution_status` label.
- `TN_005`: outcome and material facts matched; evidence-support selection included the additional `resolution_status` label.
- `TN_006`: outcome and material facts matched; evidence-support selection included the additional `resolution_status` label.
- `TN_016`: outcome and material facts matched; evidence-support selection included the additional `resolution_status` label.

## 13. Provider Availability Findings

`TN_001`, `TN_018`, and `TN_023` exceeded 120 seconds. Each containing process was terminated by the alarm, recorded as `PROVIDER_TIMEOUT`, and was not retried. Safe case-level continuation completed the remaining cases.

## 14. Case-by-Case Results

| Case | Expected outcome | Observed outcome | Status | Earliest stage | Severity |
|---|---|---|---|---|---|
| TN_001 | Violence Detected | Unable to Determine | PROVIDER_TIMEOUT | PROVIDER_REQUEST | — |
| TN_002 | Violence Detected | Violence Detected | SEMANTIC_MISMATCH | EVALUATION_COMPARISON | 3 |
| TN_003 | Violence Detected | Violence Detected | SEMANTIC_MISMATCH | EVALUATION_COMPARISON | 3 |
| TN_004 | Violence Detected | Violence Detected | SEMANTIC_MISMATCH | EVALUATION_COMPARISON | 3 |
| TN_005 | Violence Detected | Violence Detected | SEMANTIC_MISMATCH | EVALUATION_COMPARISON | 3 |
| TN_006 | No Violence Detected | No Violence Detected | SEMANTIC_MISMATCH | EVALUATION_COMPARISON | 3 |
| TN_007 | No Violence Detected | No Violence Detected | PASS | — | — |
| TN_008 | No Violence Detected | Unable to Determine | VALIDATION_FAILURE | EVIDENCE_INTEGRITY_VALIDATION | 2 |
| TN_009 | No Violence Detected | Unable to Determine | VALIDATION_FAILURE | EVIDENCE_INTEGRITY_VALIDATION | 2 |
| TN_010 | Violence Detected | Unable to Determine | VALIDATION_FAILURE | EVIDENCE_INTEGRITY_VALIDATION | 1 |
| TN_011 | No Violence Detected | No Violence Detected | SEMANTIC_MISMATCH | EVALUATION_COMPARISON | 2 |
| TN_012 | Uncertain | Unable to Determine | VALIDATION_FAILURE | EVIDENCE_INTEGRITY_VALIDATION | 2 |
| TN_013 | No Violence Detected | Unable to Determine | VALIDATION_FAILURE | EVIDENCE_INTEGRITY_VALIDATION | 2 |
| TN_014 | Uncertain | No Violence Detected | SEMANTIC_MISMATCH | EVALUATION_COMPARISON | 2 |
| TN_015 | Violence Detected | Violence Detected | PASS | — | — |
| TN_016 | Violence Detected | Violence Detected | SEMANTIC_MISMATCH | EVALUATION_COMPARISON | 3 |
| TN_017 | Unable to Determine | Unable to Determine | VALIDATION_FAILURE | EVIDENCE_INTEGRITY_VALIDATION | 2 |
| TN_018 | Unable to Determine | Unable to Determine | PROVIDER_TIMEOUT | PROVIDER_REQUEST | — |
| TN_019 | Unable to Determine | No Violence Detected | SEMANTIC_MISMATCH | EVALUATION_COMPARISON | 2 |
| TN_020 | Unable to Determine | Violence Detected | SEMANTIC_MISMATCH | EVALUATION_COMPARISON | 1 |
| TN_021 | Unable to Determine | Violence Detected | SEMANTIC_MISMATCH | EVALUATION_COMPARISON | 1 |
| TN_022 | Unable to Determine | No Violence Detected | SEMANTIC_MISMATCH | EVALUATION_COMPARISON | 2 |
| TN_023 | Unable to Determine | Unable to Determine | PROVIDER_TIMEOUT | PROVIDER_REQUEST | — |
| TN_024 | Violence Detected | Violence Detected | SEMANTIC_MISMATCH | EVALUATION_COMPARISON | 2 |

Exact narratives, evidence excerpts, expected and observed facts, validation results, and field-level differences are preserved in the machine-readable comparison artifact.

## 15. Baseline Readiness Conclusion

`NOT_READY_SEMANTIC_FAILURES`

This is an assessment only. No baseline was accepted.

## 16. Artifact Paths

- `evaluation/runs/true-north-live-evaluation-001.json`
- `evaluation/reports/true-north-live-comparison-001.json`
- `evaluation/reports/true-north-live-evaluation-001.md`

## 17. Prohibited Operations Confirmation

No runtime, prompt, adapter, schema, validation, derivation, policy, presentation, corpus, test, baseline, deployment, or hosted-acceptance behavior was changed. No request was retried. No baseline was accepted. No deployment or push occurred.
