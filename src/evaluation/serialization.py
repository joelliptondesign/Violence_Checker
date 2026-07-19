"""Canonical serialization for evaluation contracts."""

from __future__ import annotations

import json

from pydantic import BaseModel


def canonical_json(value: BaseModel) -> str:
    """Serialize a typed artifact with stable keys, separators, and UTF-8 text."""

    return json.dumps(
        value.model_dump(mode="json"),
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )
