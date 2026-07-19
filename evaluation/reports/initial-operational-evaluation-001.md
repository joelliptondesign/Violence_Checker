# Evaluation Engineering Report

## 1. Run provenance

- Comparison: `INITIAL_OPERATIONAL_COMPARISON_001`
- Accepted baseline: `INITIAL_EVALUATION_BASELINE_001` from run `INITIAL_OPERATIONAL_EVALUATION_001`
- Current run: `INITIAL_OPERATIONAL_EVALUATION_001`
- Baseline repository commit: `e2d69b58dab7e6369a27805edea38950f4c5a32d`
- Current repository commit: `e2d69b58dab7e6369a27805edea38950f4c5a32d`
- Comparison timestamp: `2026-07-19T01:38:01+00:00`

## 2. Corpus identity

- Corpus: `violence-checker-synthetic-evaluation-corpus` version `1.0.0`
- Evaluation schema: `1.0.0`

## 3. Evaluation coverage

- Total compared cases: 48
- `accidental_contact`: 4
- `ambiguous_encounter`: 4
- `attempted_physical_assault`: 4
- `completed_physical_assault`: 4
- `conflicting_narrative`: 4
- `correction`: 4
- `historical_disclosure`: 4
- `incomplete_report`: 4
- `negated_event`: 4
- `object_directed_aggression`: 4
- `self_directed_violence`: 4
- `verbal_threat`: 4

## 4. Overall summary

- Improved: 0
- Degraded: 0
- Unchanged: 48
- Incomparable: 0
- Current provider failures: 0

## 5. Regression summary

- `accidental_contact`: unchanged=4
- `ambiguous_encounter`: unchanged=4
- `attempted_physical_assault`: unchanged=4
- `completed_physical_assault`: unchanged=4
- `conflicting_narrative`: unchanged=4
- `correction`: unchanged=4
- `historical_disclosure`: unchanged=4
- `incomplete_report`: unchanged=4
- `negated_event`: unchanged=4
- `object_directed_aggression`: unchanged=4
- `self_directed_violence`: unchanged=4
- `verbal_threat`: unchanged=4

## 6. Most frequent failure patterns

- `compatibility_failure`: 48
- `semantic_field_mismatch`: 34
- `unsupported_evidence`: 33
- `policy_mismatch`: 32
- `evidence_omission`: 31
- `excessive_uncertainty`: 17
- `validation_rejection`: 14
- `insufficient_uncertainty`: 5
- `self_directed_interpersonal_confusion`: 2
- `accidental_intentional_confusion`: 1
- `conflict_resolution_failure`: 1
- `negation_failure`: 1
- `threat_classification_failure`: 1

## 7. Validation observations

- `domain`: 14
- `none`: 34
- No validation-stage changes were observed.

## 8. Policy observations

- `WRITE_DETECTED`: 9
- `WRITE_FAILED`: 14
- `WRITE_NOT_DETECTED`: 3
- `WRITE_UNCERTAIN`: 22
- No policy-outcome changes were observed.

## 9. Representative difficult cases

- `EVAL_001` (completed_physical_assault): unchanged; current outcome=partial_mismatch; patterns=compatibility_failure, unsupported_evidence, evidence_omission, excessive_uncertainty, semantic_field_mismatch; introduced fields=none.
- `EVAL_002` (completed_physical_assault): unchanged; current outcome=partial_mismatch; patterns=compatibility_failure, unsupported_evidence, evidence_omission, excessive_uncertainty, semantic_field_mismatch; introduced fields=none.
- `EVAL_003` (completed_physical_assault): unchanged; current outcome=partial_mismatch; patterns=compatibility_failure, unsupported_evidence, evidence_omission, excessive_uncertainty, semantic_field_mismatch; introduced fields=none.
- `EVAL_004` (completed_physical_assault): unchanged; current outcome=partial_mismatch; patterns=compatibility_failure, unsupported_evidence, evidence_omission, semantic_field_mismatch; introduced fields=none.
- `EVAL_005` (attempted_physical_assault): unchanged; current outcome=failure; patterns=compatibility_failure, validation_rejection, policy_mismatch; introduced fields=none.

## 10. Engineering opportunities

- Review the observed `compatibility_failure` evidence recurring in 48 case(s): EVAL_001, EVAL_002, EVAL_003, EVAL_004, EVAL_005, EVAL_006, EVAL_007, EVAL_008, EVAL_009, EVAL_010, EVAL_011, EVAL_012, EVAL_013, EVAL_014, EVAL_015, EVAL_016, EVAL_017, EVAL_018, EVAL_019, EVAL_020, EVAL_021, EVAL_022, EVAL_023, EVAL_024, EVAL_025, EVAL_026, EVAL_027, EVAL_028, EVAL_029, EVAL_030, EVAL_031, EVAL_032, EVAL_033, EVAL_034, EVAL_035, EVAL_036, EVAL_037, EVAL_038, EVAL_039, EVAL_040, EVAL_041, EVAL_042, EVAL_043, EVAL_044, EVAL_045, EVAL_046, EVAL_047, EVAL_048.
- Review the observed `semantic_field_mismatch` evidence recurring in 34 case(s): EVAL_001, EVAL_002, EVAL_003, EVAL_004, EVAL_007, EVAL_008, EVAL_011, EVAL_012, EVAL_013, EVAL_014, EVAL_015, EVAL_016, EVAL_017, EVAL_018, EVAL_019, EVAL_020, EVAL_021, EVAL_022, EVAL_023, EVAL_024, EVAL_027, EVAL_028, EVAL_029, EVAL_030, EVAL_031, EVAL_032, EVAL_037, EVAL_038, EVAL_041, EVAL_042, EVAL_043, EVAL_045, EVAL_046, EVAL_048.
- Review the observed `unsupported_evidence` evidence recurring in 33 case(s): EVAL_001, EVAL_002, EVAL_003, EVAL_004, EVAL_007, EVAL_008, EVAL_011, EVAL_012, EVAL_013, EVAL_014, EVAL_015, EVAL_016, EVAL_017, EVAL_018, EVAL_019, EVAL_020, EVAL_021, EVAL_022, EVAL_023, EVAL_024, EVAL_027, EVAL_028, EVAL_029, EVAL_030, EVAL_031, EVAL_032, EVAL_037, EVAL_038, EVAL_041, EVAL_042, EVAL_043, EVAL_045, EVAL_048.
