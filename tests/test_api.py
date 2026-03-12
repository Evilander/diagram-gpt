"""Tests for API status and request validation."""

from fastapi.testclient import TestClient

from src.api.server import app

client = TestClient(app)


def test_status_exposes_runtime_shape(monkeypatch):
    monkeypatch.setattr(
        "src.api.server.build_runtime_status",
        lambda: {
            "ready": True,
            "version": "0.2.0",
            "llm": {"ready": True},
            "renderers": {},
            "available_formats": ["mermaid"],
            "styles": ["professional"],
            "fonts": ["clean"],
            "types": ["flowchart"],
        },
    )

    response = client.get("/api/status")

    assert response.status_code == 200
    payload = response.json()
    assert payload["ready"] is True
    assert payload["available_formats"] == ["mermaid"]


def test_ready_uses_503_for_unready_runtime(monkeypatch):
    monkeypatch.setattr("src.api.server.build_runtime_status", lambda: {"ready": False})

    response = client.get("/ready")

    assert response.status_code == 503
    assert response.json()["ready"] is False


def test_generate_rejects_unknown_style():
    response = client.post(
        "/api/generate",
        json={
            "description": "user signup flow",
            "style": "unknown-style",
        },
    )

    assert response.status_code == 422


def test_upload_context_accepts_csv():
    response = client.post(
        "/api/context/upload",
        files={
            "files": ("metrics.csv", b"month,revenue\nJan,10\nFeb,12\n", "text/csv"),
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["files"][0]["filename"] == "metrics.csv"
    assert "chart" in payload["suggested_diagram_types"]
