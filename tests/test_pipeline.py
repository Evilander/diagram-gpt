"""Tests for request validation and file safety."""

from src.generators.types import DiagramResult, DiagramType, OutputFormat
from src.pipeline import (
    DiagramRequest,
    DiagramRequestValidationError,
    sanitize_output_name,
    validate_request,
)
from src.renderers.render import normalize_d2_code, normalize_mermaid_code


def test_validate_request_rejects_unknown_style():
    request = DiagramRequest(description="user signup flow", style="unknown-style")

    try:
        validate_request(request)
    except DiagramRequestValidationError as exc:
        assert "Unknown style" in str(exc)
    else:
        raise AssertionError("validate_request should reject unknown styles")


def test_sanitize_output_name_strips_path_traversal():
    result = DiagramResult(
        source_code="graph TD\nstart --> finish",
        output_format=OutputFormat.MERMAID,
        diagram_type=DiagramType.FLOWCHART,
    )

    assert sanitize_output_name("../bad name?.mmd", result) == "bad-name-.mmd"


def test_normalize_mermaid_quotes_subgraph_and_labels():
    code = """graph TD
subgraph zone[Headquarters Zone]
    firewall[Firewall (HQ)]
end
"""

    normalized = normalize_mermaid_code(code)

    assert 'subgraph zone["Headquarters Zone"]' in normalized
    assert 'firewall["Firewall (HQ)"]' in normalized


def test_normalize_d2_converts_container_nodes_and_edges():
    code = """container apiService {
  apiGateway[API Gateway]
}
apiGateway --> worker[label: "sends events"]
"""

    normalized = normalize_d2_code(code)

    assert 'apiService: "Api Service" {' in normalized
    assert 'apiGateway: "API Gateway"' in normalized
    assert 'apiGateway -> worker: "sends events"' in normalized
