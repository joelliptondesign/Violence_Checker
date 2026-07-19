import ast
from pathlib import Path

from src.contracts import PipelineResult, ProviderStructuredResponse, ViolenceSemanticEnvelope
from src.provider_adapter import semantic_candidate_from_provider_response
from tests.successor_helpers import envelope


ACTIVE_FILES = [
    "app.py", "src/app_logic.py", "src/policy.py", "src/comparison.py",
    "src/salesforce_preview.py", "src/contract_adapters.py", "src/evaluation/runner.py",
]


def test_provider_shape_terminates_at_adapter():
    provider = envelope(provider=True)
    adapted = semantic_candidate_from_provider_response(provider)
    assert isinstance(provider, ProviderStructuredResponse)
    assert type(adapted) is ViolenceSemanticEnvelope


def test_current_pipeline_contains_no_transitional_global_authority():
    forbidden = {"ViolenceFinding", "SemanticFacts", "ValidatedSemanticFacts", "operational_finding", "compatibility_result"}
    for path in ACTIVE_FILES:
        source = Path(path).read_text()
        assert not forbidden.intersection({node.id for node in ast.walk(ast.parse(source)) if isinstance(node, ast.Name)})
        assert "operational_finding" not in source
        assert "compatibility_result" not in source
    assert "operational_finding" not in PipelineResult.model_fields


def test_compatibility_module_is_removed():
    assert not Path("src/compatibility_finding.py").exists()
