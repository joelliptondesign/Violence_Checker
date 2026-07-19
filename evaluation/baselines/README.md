# Accepted Evaluation Baselines

A current baseline is an explicit immutable snapshot of one complete successor run, including ordered observations, comparisons, summary, semantic schema provenance, and acceptance provenance. Existing files cannot be overwritten; replacement requires a new identity and a retained predecessor reference.

Creation-time schema `1.0.0` baselines remain byte-immutable and readable. They cannot be used as successor baselines or silently upgraded.
