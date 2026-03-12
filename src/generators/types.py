"""Diagram type definitions and detection."""

from dataclasses import dataclass
from enum import Enum


class DiagramType(str, Enum):
    FLOWCHART = "flowchart"
    CHART = "chart"
    SEQUENCE = "sequence"
    ARCHITECTURE = "architecture"
    ENTITY_RELATIONSHIP = "er"
    CLASS_DIAGRAM = "class"
    NETWORK = "network"
    MINDMAP = "mindmap"
    TIMELINE = "timeline"
    STATE = "state"
    GANTT = "gantt"
    TREE = "tree"
    CUSTOM = "custom"


class OutputFormat(str, Enum):
    MERMAID = "mermaid"
    D2 = "d2"
    SVG = "svg"


@dataclass
class DiagramRequest:
    description: str
    diagram_type: DiagramType | None = None  # auto-detect if None
    data_context: str = ""
    style: str = "professional"
    font: str = "clean"
    output_format: OutputFormat = OutputFormat.MERMAID
    width: int = 1200
    height: int = 800


@dataclass
class DiagramResult:
    source_code: str
    output_format: OutputFormat
    diagram_type: DiagramType
    svg: str | None = None
    png_bytes: bytes | None = None
    metadata: dict | None = None


# Weighted keywords that hint at diagram type.
TYPE_HINTS: dict[DiagramType, dict[str, int]] = {
    DiagramType.FLOWCHART: {
        "flow": 4,
        "workflow": 4,
        "process": 3,
        "step": 2,
        "decision": 2,
        "approval": 2,
        "login": 4,
        "signup": 4,
        "onboarding": 3,
        "journey": 2,
        "pipeline": 2,
    },
    DiagramType.CHART: {
        "chart": 5,
        "bar chart": 5,
        "line chart": 5,
        "pie chart": 5,
        "trend": 3,
        "timeseries": 3,
        "time series": 3,
        "dataset": 2,
        "metrics": 2,
    },
    DiagramType.SEQUENCE: {
        "sequence": 5,
        "interaction": 3,
        "message": 2,
        "request": 2,
        "response": 2,
        "api call": 4,
        "handshake": 3,
    },
    DiagramType.ARCHITECTURE: {
        "architecture": 5,
        "system": 2,
        "service": 3,
        "microservice": 4,
        "component": 3,
        "layer": 2,
        "frontend": 3,
        "backend": 3,
        "database": 2,
    },
    DiagramType.ENTITY_RELATIONSHIP: {
        "entity": 5,
        "relationship": 5,
        "schema": 4,
        "table": 4,
        "cardinality": 4,
        "foreign key": 4,
        "erd": 5,
        "database": 1,
        "sql": 2,
    },
    DiagramType.CLASS_DIAGRAM: {
        "class": 5,
        "inheritance": 4,
        "interface": 4,
        "method": 2,
        "object": 2,
        "uml": 3,
    },
    DiagramType.NETWORK: {
        "network": 5,
        "topology": 4,
        "router": 4,
        "switch": 4,
        "firewall": 4,
        "subnet": 3,
        "vlan": 3,
        "server": 1,
        "node": 1,
        "tree": 1,
    },
    DiagramType.MINDMAP: {"mindmap": 5, "brainstorm": 4, "concept": 3, "idea map": 4},
    DiagramType.TIMELINE: {"timeline": 5, "history": 4, "chronolog": 3, "milestone": 3},
    DiagramType.STATE: {"state": 4, "transition": 4, "fsm": 5, "state machine": 5},
    DiagramType.GANTT: {"gantt": 5, "schedule": 3, "project plan": 3, "sprint": 3},
    DiagramType.TREE: {
        "tree": 4,
        "hierarchy": 4,
        "org chart": 4,
        "folder structure": 4,
        "taxonomy": 4,
    },
}


def detect_diagram_type(description: str) -> DiagramType:
    """Auto-detect diagram type from natural language description."""
    desc_lower = description.lower()
    scores = {diagram_type: 0 for diagram_type in TYPE_HINTS}

    for diagram_type, keywords in TYPE_HINTS.items():
        for keyword, weight in keywords.items():
            if keyword in desc_lower:
                scores[diagram_type] += weight

    if scores[DiagramType.NETWORK] and "network" in desc_lower:
        scores[DiagramType.NETWORK] += 2

    if scores[DiagramType.FLOWCHART] and any(
        keyword in desc_lower for keyword in ("flow", "workflow", "login", "signup", "onboarding")
    ):
        scores[DiagramType.FLOWCHART] += 2

    best_type = max(scores, key=scores.get)
    if scores[best_type] == 0:
        return DiagramType.FLOWCHART
    return best_type
