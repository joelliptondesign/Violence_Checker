import pytest
from pydantic import ValidationError

from src.models import Incident


def test_incident_is_the_only_domain_model_and_preserves_narrative():
    value = Incident(incident_id="INC-1", narrative=" raw narrative ")
    assert value.narrative == " raw narrative "


@pytest.mark.parametrize("field", ["incident_id", "narrative"])
def test_incident_rejects_empty_required_strings(field):
    values = {"incident_id": "INC-1", "narrative": "text"}
    values[field] = ""
    with pytest.raises(ValidationError):
        Incident(**values)


def test_transitional_global_models_are_removed():
    import src.models as models
    assert not hasattr(models, "ViolenceFinding")
    assert not hasattr(models, "ViolenceEventType")
