"""LLM prompt templates for diagram generation."""

from .types import DiagramType, OutputFormat

SYSTEM_PROMPT = """You are DiagramGPT, an expert at generating precise, valid diagram code
from natural language descriptions. You produce clean, well-structured diagram
code that renders beautifully.

Rules:
1. Output ONLY the diagram code — no markdown fences, no explanations, no preamble
2. Use descriptive node IDs (e.g., `webServer` not `A`)
3. Use clear, concise labels
4. Organize nodes logically with good visual hierarchy
5. For network diagrams, group related nodes and show connection details
6. Never leave nodes orphaned unless the description implies isolation
7. Prefer left-to-right (LR) for wide diagrams, top-down (TD) for hierarchical ones

CRITICAL Mermaid syntax rules:
- NEVER use `end` as a node ID — it is a reserved keyword. Use `finish`, `done`, `endNode`, etc.
- NEVER use `class` as a node ID — reserved. Use `cls` or `classNode`.
- Node labels go in brackets: `nodeId[Label Text]`, `nodeId([Rounded])`, `nodeId{Decision}`
- Do NOT use `(Node: Label)` syntax — use `nodeId([Label])` for stadium shapes
- Do NOT add classDef or style definitions — styling is handled externally
- Keep node IDs as simple camelCase identifiers without special characters"""

MERMAID_TEMPLATES: dict[DiagramType, str] = {
    DiagramType.FLOWCHART: """Generate a Mermaid flowchart for the following description.
Use `graph TD` for vertical or `graph LR` for horizontal — pick whichever fits the content better.
Use appropriate shapes: rounded rectangles for processes, diamonds for
decisions, stadiums for start/end.
Use descriptive subgraphs to group related nodes.

Description: {description}""",

    DiagramType.CHART: """Generate a Mermaid chart for the following description.
If the data is categorical with proportions, use `pie showData`.
If the data is ordered or time-based, use `xychart-beta`.
Include a short title and readable labels.

Description: {description}""",

    DiagramType.SEQUENCE: """Generate a Mermaid sequence diagram for the following description.
Use clear participant names. Show request/response pairs. Use activation bars for processing.
Add notes where they clarify the flow.

Description: {description}""",

    DiagramType.ARCHITECTURE: """Generate a Mermaid flowchart (graph TD or LR)
representing the system architecture described below.
Group services into subgraphs by layer (e.g., "Frontend", "Backend", "Data", "External").
Use descriptive labels and show data flow direction with arrow labels.
Use different node shapes for different component types.

Description: {description}""",

    DiagramType.ENTITY_RELATIONSHIP: """Generate a Mermaid ER diagram for the following description.
Define entities with their key attributes. Show relationships with proper cardinality.
Use meaningful relationship labels.

Description: {description}""",

    DiagramType.CLASS_DIAGRAM: """Generate a Mermaid class diagram for the following description.
Show classes with their attributes and methods. Use proper UML relationships.
Mark visibility (+public, -private, #protected).

Description: {description}""",

    DiagramType.NETWORK: """Generate a Mermaid flowchart (graph TD)
representing the network topology described below.
Group devices by subnet/zone using subgraphs. Label connections with protocols/ports.
Use descriptive node names with device type in the label.
For tree structures, use clear parent-child relationships.

Important: Make it hierarchical and visually clean. Group related nodes.

Description: {description}""",

    DiagramType.MINDMAP: """Generate a Mermaid mindmap for the following description.
Use proper indentation for hierarchy. Keep labels concise.

Description: {description}""",

    DiagramType.STATE: """Generate a Mermaid state diagram for the following description.
Show states, transitions with trigger labels, and start/end states.

Description: {description}""",

    DiagramType.GANTT: """Generate a Mermaid gantt chart for the following description.
Include sections, tasks with durations, and dependencies.

Description: {description}""",

    DiagramType.TIMELINE: """Generate a Mermaid timeline for the following description.
Use clear date markers and concise event descriptions.

Description: {description}""",

    DiagramType.TREE: """Generate a Mermaid flowchart (graph TD) representing
the tree/hierarchy described below.
Use clear parent-child arrow relationships. Group siblings logically.
Use subgraphs for major branches if the tree is large.

Description: {description}""",

    DiagramType.CUSTOM: """Generate a Mermaid diagram for the following description.
Choose the most appropriate Mermaid diagram type. Output valid Mermaid syntax.

Description: {description}""",
}

D2_TEMPLATES: dict[DiagramType, str] = {
    DiagramType.NETWORK: """Generate a D2 diagram for the following network topology.
Use containers (nested shapes) for subnets/zones. Label connections with protocols.
Use icons where appropriate. D2 supports nested grouping which is perfect for network diagrams.

Output valid D2 syntax only.

Description: {description}""",

    DiagramType.ARCHITECTURE: """Generate a D2 diagram for the following system architecture.
Use containers for logical grouping. Show connections with labeled edges.
D2 handles nested architecture diagrams beautifully.

Output valid D2 syntax only.

Description: {description}""",

    DiagramType.CUSTOM: """Generate a D2 diagram for the following description.
Choose a clean graph structure with readable node labels and directional edges.
Prefer nested containers when they clarify the diagram. Output valid D2 syntax only.

Description: {description}""",
}


def get_prompt(
    description: str,
    diagram_type: DiagramType,
    output_format: OutputFormat,
    data_context: str = "",
) -> tuple[str, str]:
    """Get (system_prompt, user_prompt) for the given diagram request."""
    if output_format == OutputFormat.D2 and diagram_type in D2_TEMPLATES:
        template = D2_TEMPLATES[diagram_type]
    elif output_format == OutputFormat.D2:
        template = D2_TEMPLATES[DiagramType.CUSTOM]
    elif output_format == OutputFormat.MERMAID or diagram_type not in D2_TEMPLATES:
        template = MERMAID_TEMPLATES.get(diagram_type, MERMAID_TEMPLATES[DiagramType.CUSTOM])
    else:
        template = MERMAID_TEMPLATES.get(diagram_type, MERMAID_TEMPLATES[DiagramType.CUSTOM])

    user_prompt = template.format(description=description)
    if data_context.strip():
        user_prompt += (
            "\n\nUploaded data context:\n"
            f"{data_context.strip()}\n\nUse the uploaded data when it improves the accuracy "
            "of the diagram or chart."
        )
    return SYSTEM_PROMPT, user_prompt
