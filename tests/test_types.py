"""Tests for diagram type detection."""

from src.generators.types import DiagramType, detect_diagram_type


def test_detect_flowchart():
    assert detect_diagram_type("show the user signup flow") == DiagramType.FLOWCHART


def test_detect_sequence():
    assert (
        detect_diagram_type("sequence of API request and response between client and server")
        == DiagramType.SEQUENCE
    )


def test_detect_network():
    assert (
        detect_diagram_type("network topology with router, switch, and firewall")
        == DiagramType.NETWORK
    )


def test_detect_architecture():
    assert (
        detect_diagram_type("microservice architecture with frontend, backend, and database")
        == DiagramType.ARCHITECTURE
    )


def test_detect_er():
    assert (
        detect_diagram_type("entity relationship diagram for the database schema")
        == DiagramType.ENTITY_RELATIONSHIP
    )


def test_detect_class():
    assert (
        detect_diagram_type("class diagram showing inheritance between Animal and Dog")
        == DiagramType.CLASS_DIAGRAM
    )


def test_detect_tree():
    assert detect_diagram_type("folder structure hierarchy of the project") == DiagramType.TREE


def test_detect_default():
    assert detect_diagram_type("something completely unrelated") == DiagramType.FLOWCHART


def test_detect_network_tree():
    assert (
        detect_diagram_type("network tree diagram showing all connected nodes")
        == DiagramType.NETWORK
    )


def test_detect_login_flow_prefers_flowchart():
    assert (
        detect_diagram_type("simple login flow from user to app to database")
        == DiagramType.FLOWCHART
    )
