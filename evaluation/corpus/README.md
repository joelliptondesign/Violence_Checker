# Synthetic Corpus and Ground Truth

`successor_corpus.json` is the only authoritative current corpus. It contains 48 synthetic cases, stable IDs `EVAL_001` through `EVAL_048`, preserved raw narrative bytes, and manually authored proposition-oriented ground truth. Corpus, corpus-schema, and evaluation-schema versions are `2.0.0`; semantic schema is `violence-checker.proposition-semantics` version `1.0.0`.

Ground truth includes typed expected envelopes, deterministic derived semantic views, validation expectations, policy expectations, and explicitly unasserted optional fields. Provider output, regex output, app results, previous runs, and external systems cannot create, repair, or approve it. Metadata and expectations never enter the analyzed narrative.

`corpus.json` is the immutable creation-time corpus under schema `1.0.0`. It remains available only for historical readability and stable-case migration evidence; it is not accepted by the current corpus loader and is not current semantic authority.

```sh
.venv/bin/python -m src.evaluation.corpus validate
.venv/bin/python -m src.evaluation.corpus coverage
```

Both commands are deterministic and make no provider request.
