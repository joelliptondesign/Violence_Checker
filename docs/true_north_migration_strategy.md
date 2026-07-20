# True North Migration Strategy

## Purpose

This document defines the planned boundary and dependency order for replacing the current proposition-oriented semantic architecture with the incident-fact contract in `true_north_semantic_contract_specification.md`. It authorizes no runtime, prompt, test, evaluation, provider, deployment, baseline, commit, or publication change.

## Current-State Summary

The active runtime uses `ViolenceSemanticEnvelope` (`violence-checker.proposition-semantics` version `1.0.0`) as its sole semantic authority. It contains entities, propositions, typed relationships, separate uncertainty records, evidence excerpts, evidence-support links, and extraction metadata. Repository code derives `DerivedSemanticView` and `PolicyCandidateView`; deterministic policy currently focuses on active current interpersonal candidates. Operator communication receives a proposition-based bounded projection. Evaluation schema `2.0.0` stores proposition-oriented expected and observed contracts.

That architecture remains repository runtime truth until verified cutover. Its current policy and vocabularies do not implement the complete approved doctrine: the target expressly qualifies self-directed and intentional property-directed violence, requires affirmed intentionality for completed contact, adds incident direction `multiple`, and standardizes `Violence Detected`, `No Violence Detected`, `Uncertain`, and `Unable to Determine` around the new evidence-integrity rules.

The existing `docs/semantic_design_basis.md`, `docs/successor_semantic_contract_specification.md`, and `docs/opord_004_verification_authority.md` continue to document and protect the currently implemented proposition successor until cutover. After cutover they remain historical design and verification provenance for that architecture; they do not override the newly approved doctrine for future implementation.

## Target-State Summary

The target has one validated incident-fact contract with the smallest fields needed for conduct, direction, intentionality, temporal scope, assertion, resolution, fact-level evidence, and uncertainty. Corrections use a narrow supersession reference; unresolved contradictions use a narrow group identifier. Repository-owned processing and analysis-completeness status remains outside operational facts and cannot assert that violence is absent. Deterministic derivation builds the active set, incident direction, and material-uncertainty state. Deterministic policy evaluates validated facts and repository-owned analysis status directly and alone returns the four doctrinal outcomes. Communication receives a validated presentation-only projection.

## Component Disposition Matrix

| Current component | Disposition | Planned target treatment |
| --- | --- | --- |
| `ViolenceSemanticEnvelope` | REPLACE | Replace with one versioned true-north incident-fact contract; never keep both as current authority. |
| Provider candidate contracts | REPLACE | Use candidate facts, exact excerpts, attribute-level supports, uncertainty, and temporary narrow correction/conflict references only. |
| Entities | REMOVE | Actor/target entity modeling is not required by approved doctrine; retain no entity graph solely for compatibility. |
| Propositions | REPLACE | Replace multi-axis proposition objects with minimal evidence-linked conduct facts. |
| Relationships | REMOVE | Replace the general relationship collection with optional `supersedes_fact_id` and `contradiction_group`. |
| Uncertainty records | SIMPLIFY | Inline bounded unresolved material dimensions on the affected fact. |
| Evidence excerpts | RETAIN | Preserve exact narrative excerpts as the evidence primitive, with stricter material-support rules. |
| Evidence supports | SIMPLIFY | Link excerpts directly to each fact and the specific attributes supported; no generic subject graph. |
| `DerivedSemanticView` | REPLACE | Derive only active facts, incident direction, material uncertainty, and other explicitly consumed views. |
| `PolicyCandidateView` | REMOVE | Deterministic policy evaluates validated target facts and repository-owned processing/completeness status directly; local indexes are non-authoritative implementation details only. |
| Deterministic policy | RETAIN | Retain sole deterministic authority and total/fail-closed behavior; replace logic and vocabulary to implement the approved doctrine. |
| Operator communication projection | SIMPLIFY | Project only validated facts and deterministic result needed for Incident Summary, Key Findings, and Why This Result. |
| Evaluation contracts | REPLACE | Introduce a distinct evaluation schema with true-north semantic expectations and doctrinal outcomes. |
| Compatibility and serialization adapters | REMOVE | Permit only temporary, one-way boundary adapters during migration; remove them before target authority becomes active. Never translate historical evidence into new truth. |

## Migration Principles

- Preserve one current semantic authority at every repository state.
- Build and verify the target behind an explicit schema boundary before cutover.
- Do not dual-write current semantic truth or compare schemas as though they were equivalent.
- Do not retain legacy concepts merely for compatibility.
- Preserve raw narratives and historical artifacts byte-for-byte.
- Fail closed on unsupported identity, version, fields, evidence, or combinations.
- Make each package independently reviewable and deterministic before enabling the next consumer.
- Treat provider output as candidates and repository validation/derivation/policy as authority.
- Do not permit provider-authored negative conclusions or treat an empty provider fact list as proof of `No Violence Detected`.
- Do not introduce a renamed policy-candidate aggregate; policy reads validated target facts directly.
- Do not accept a target baseline until all deterministic and authorized live gates pass.

## Dependency Sequence

1. Freeze the approved doctrine and target specification as documentation authority.
2. Define the new semantic and extraction identities, provider candidate contract, prompt boundary, adapter, and evidence validation.
3. Build strict schema/domain validation and adversarial evidence-integrity coverage before any target fact can reach policy.
4. Build deterministic active-set, incident-direction, correction, contradiction, and material-uncertainty derivations without a policy-candidate contract.
5. Implement the four-outcome deterministic policy directly over validated facts and repository-owned processing/completeness status.
6. Replace communication and downstream projections with the new bounded truth projection and deterministic fallback checks.
7. Reconstruct evaluation contracts and corpus expectations under a distinct evaluation schema; do not translate old expected envelopes.
8. Consolidate tests and pass local acceptance for the entire target path.
9. Run separately authorized live-provider validation and analyze evidence without accepting a baseline.
10. Accept a new baseline only through a separate explicit authority after all gates pass.
11. Cut over the runtime atomically, declare the target contract the sole active semantic authority, and remove superseded runtime components/adapters.
12. Perform separately authorized hosted deployment and hosted acceptance.

Steps 2–12 are planned work, not authorized by this document.

## Schema Transition

The target semantic identity is distinct from `violence-checker.proposition-semantics`; the planned identity is `violence-checker.true-north-incident-facts` version `1.0.0`. The target extraction contract requires a distinct identity. Deterministic policy has no separately serialized policy-input schema; it consumes the validated target contract and repository-owned processing/completeness status directly. Consumers must route semantic content by exact identity and version and fail closed on unsupported content.

Temporary coexistence is allowed only in development and evaluation scaffolding when:

- one explicitly selected path owns the request and result;
- target output cannot feed current policy or current output as current truth;
- current output cannot be silently adapted into target truth;
- artifacts state their schema family;
- no UI, aggregate, report, or baseline presents both as coequal authority; and
- the temporary path has named removal criteria.

At cutover, application orchestration must select the target path atomically. Any compatibility or serialization adapter must terminate before the sole semantic-authority boundary and must be removed before target authority is declared active.

## Evaluation Transition

Evaluation reconstruction requires a new schema identity/version, repository-authored true-north expected facts, derived values, validation outcomes, and policy outcomes. Each narrative must be independently annotated under the approved doctrine, including self-directed violence, property violence, accidental contact, historical-only facts, corrections, denials, contradictions, evidence-entailment adversaries, unknown direction, and mixed direction.

Current evaluation schema `2.0.0`, its corpus, runs, baselines, comparisons, and reports remain within the proposition-semantic family. They are not upgraded in place, rewritten, or promoted. Cross-family metrics may be reported only as explicitly non-comparable observations; they cannot establish regression or acceptance.

Live-provider evaluation is a later separately authorized gate. Generated output is evidence, never ground truth. Baseline acceptance is a later distinct operator decision.

## Historical Artifact Preservation

Existing design documents, archived SITRECs, corpus files, runs, baselines, comparisons, reports, and protected hashes remain immutable historical provenance. Readers may route recognized historical identities for display or audit only. No adapter may invent missing fact-level evidence, reinterpret a historical proposition as a true-north fact, or relabel a historical policy outcome.

The active SITREC must distinguish the implemented proposition runtime from planned true-north authority until cutover. After cutover, it must still preserve clear historical provenance rather than claim the target was always active.

## Verification Gates

Target authority cannot become active until all of these gates pass:

1. **Doctrine traceability:** every contract value, derivation, policy branch, and communication field traces to approved doctrine.
2. **Contract strictness:** exact schemas, bounded vocabularies, required fields, extra-field rejection, canonical references, and version routing pass.
3. **Evidence integrity:** fact/attribute coverage and explicit denial, accident, historical, no-contact, property-direction, correction, and contradiction adversaries pass.
4. **Correction and contradiction:** supersession order/acyclicity, copied-forward correction, denial/confirmation, and unresolved witness conflict pass.
5. **Deterministic derivation:** active set, incident direction including `multiple`, unknown-direction handling, and material uncertainty pass exhaustive partitions.
6. **Deterministic policy:** direct evaluation of validated facts and repository-owned analysis status passes all four outcomes and their precedence, including self-harm, intentional property violence, empty-fact handling, and absence of a policy-candidate aggregate.
7. **Communication consistency:** projection completeness, prohibited invention, factual checks, and deterministic fallback pass.
8. **Evaluation authority:** a new independently authored corpus and schema pass coverage, admissibility, stable serialization, and artifact lifecycle checks.
9. **Local acceptance:** focused tests, the complete deterministic suite, governance, link, scope, and generated-artifact freshness checks pass.
10. **Live-provider validation:** separately authorized representative and adversarial live cases pass with preserved request boundaries.
11. **Baseline acceptance:** separately authorized baseline review confirms no unresolved critical semantic or evidence-integrity failure.
12. **Cutover readiness:** all legacy runtime consumers are replaced or retired, no dual semantic authority remains, rollback state is identified, and current documentation/SITREC match runtime truth.

## Rollback Boundary

Before baseline acceptance and atomic cutover, the current proposition runtime remains the rollback target and sole active implementation. Target development may be removed or disabled without rewriting current artifacts. No target artifact may be accepted as current baseline during this period.

After baseline acceptance but before hosted acceptance, rollback may restore the last accepted proposition runtime only through an explicit repository change that also restores matching schema routing, evaluation authority, documentation, and SITREC truth. Mixing target provider output with legacy policy, or legacy semantics with target communication, is never a valid rollback.

## Removal Criteria

Superseded runtime components and temporary adapters are removed when:

- target schema, evidence validation, derivation, policy, communication, evaluation, and local acceptance gates pass;
- authorized live validation and baseline acceptance pass;
- every runtime and downstream consumer reads the target identity/version;
- no persisted current artifact requires a legacy writer;
- historical readers are isolated from current policy;
- rollback is available as a repository-level version transition rather than a live dual path; and
- active documentation and SITREC can truthfully declare one target semantic authority.

## Prohibited Migration Patterns

- Dual current semantic authorities or permanent dual-write.
- Using provider-selected outcomes or prose as policy input.
- Allowing a provider-authored negative conclusion or treating empty provider facts alone as a negative result.
- Replacing `PolicyCandidateView` with a renamed or separately serialized aggregate.
- Translating legacy evidence or outcomes into true-north ground truth.
- Retaining entities, relationship graphs, or proposition fields without demonstrated target value.
- Silent defaults, semantic repair, or conversion of unsupported facts into affirmed truth.
- Enabling target policy before evidence and contract validation pass.
- Mixing schema families in one baseline or regression claim.
- Rewriting historical artifacts or archived SITRECs.
- Declaring implementation, baseline, deployment, or hosted acceptance complete from documentation alone.

## Planned Execution Packages

### 1. Provider contract, prompt, adapter, and evidence validation

Define the new provider candidate schema and prompt; terminate provider objects; assign repository bookkeeping; enforce fact/attribute evidence, correction, contradiction, and fail-closed validation. No policy cutover occurs in this package.

### 2. Deterministic derivation and policy

Implement active-set, incident-direction, material-uncertainty, correction, and contradiction derivations; remove `PolicyCandidateView`; evaluate validated facts and repository-owned processing/completeness status directly; implement and exhaustively test the four doctrinal outcomes. Mechanical policy indexes may exist only as local non-serialized implementation details.

### 3. Communication and downstream projections

Replace proposition projections with the minimal validated fact projection; enforce prohibited-invention and factual-consistency checks; update deterministic fallback and downstream illustrative views without adding semantic authority.

### 4. Evaluation reconstruction

Create a new schema family and independently annotate a synthetic corpus against the approved doctrine. Add adversarial evidence-integrity and all direction/conduct/outcome cases. Preserve existing artifacts unchanged.

### 5. Test consolidation and local acceptance

Trace permanent tests to migration gates, remove obsolete runtime tests only after equivalent target authority exists, run the complete deterministic suite and governance checks, and document remaining risk.

### 6. Live-provider validation

Under separate authorization, run bounded representative and adversarial provider cases with explicit request counts. Treat results as evidence only and correct implementation before any baseline decision.

### 7. Baseline acceptance

Under separate authority, review deterministic and live evidence, accept a new target-family baseline, and record the exact repository state. Baseline acceptance must not occur implicitly during evaluation.

### 8. Hosted deployment and acceptance

After cutover and baseline acceptance, separately authorize deployment, verify the hosted target path and presentation, and record hosted acceptance. Deployment is not evidence that semantic gates passed.
