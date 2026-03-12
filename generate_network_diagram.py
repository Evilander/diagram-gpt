"""Parse network switch CSV and generate a Mermaid network topology diagram."""

import csv
import subprocess
import shutil
import tempfile
from pathlib import Path
from collections import defaultdict

CSV_PATH = Path(__file__).parent / "NetworkSwitches_1772647968042 - Copy(in).csv"
OUTPUT_DIR = Path(__file__).parent / "diagrams"
OUTPUT_DIR.mkdir(exist_ok=True)


def parse_switches(csv_path: Path) -> dict:
    """Parse CSV into parent switches with their stack members."""
    switches = {}
    current_parent = None

    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row["switchName"].strip()
            ip = row["ipAddress"].strip()
            model = row["model"].strip()
            status = row["status"].strip()
            ports = row["ports"].strip()
            poe = row["poe"].strip()

            if ip:
                current_parent = name
                switches[name] = {
                    "ip": ip,
                    "model": model,
                    "status": status,
                    "ports": int(ports) if ports else 0,
                    "poe": poe,
                    "stack_members": [],
                }
            else:
                if current_parent and current_parent in switches:
                    role = ""
                    if "(Active)" in name:
                        role = "Active"
                    elif "(Standby)" in name:
                        role = "Standby"
                    elif "(Member)" in name:
                        role = "Member"
                    switches[current_parent]["stack_members"].append({
                        "name": name,
                        "model": model,
                        "role": role,
                        "status": status,
                    })
    return switches


def classify_location(name: str) -> str:
    """Classify a switch into a building/location group."""
    n = name.upper()
    if n in ("COURTHOUSE_CORE",):
        return "CORE"
    if n in ("MENDON_CORE",):
        return "MENDON"
    if n in ("911_CORE",):
        return "911_CENTER"
    if "911" in n or "RADIO_ROOM" in n:
        return "911_CENTER"
    if "HEALTH" in n:
        return "HEALTH_DEPT"
    if "EMS" in n:
        return "EMS_STATIONS"
    if "DATA_CENTER" in n or "DATA CENTER" in n or "45DRIVES" in n or n == "SERVERROOM":
        return "DATA_CENTER"
    if "IDF" in n or "PHONEROOM" in n or "UNDERSTAIRS" in n:
        return "COURTHOUSE_IDF"
    if "IT_OFFICE" in n:
        return "IT_OFFICES"
    if n in ("JUVENILE", "JUV_CONTROL_ROOM", "JAIL_EAST_CORRIDOR", "OLD-JAIL",
             "PROBATION", "ACSO_TASKFORCE"):
        return "JUSTICE"
    if "HIGHWAY" in n:
        return "HIGHWAY_DEPT"
    if n in ("BOARD_AV", "ELECTION_ROOM", "RECORDING_ROOM", "ROE", "ROE_CFC"):
        return "COURTHOUSE_OFFICES"
    if n in ("SOA_DESK", "CIR_DESK", "TR-DESK"):
        return "COURTHOUSE_DESKS"
    if n in ("PDO_REMOTE_OFFICE", "VAC"):
        return "REMOTE"
    return "OTHER"


LOCATION_META = {
    "CORE": {"label": "Core", "order": 0},
    "DATA_CENTER": {"label": "Data Center", "order": 1},
    "COURTHOUSE_IDF": {"label": "Courthouse IDFs", "order": 2},
    "COURTHOUSE_OFFICES": {"label": "Courthouse Offices", "order": 3},
    "COURTHOUSE_DESKS": {"label": "Desk Switches", "order": 4},
    "IT_OFFICES": {"label": "IT Department", "order": 5},
    "JUSTICE": {"label": "Justice / Law Enforcement", "order": 6},
    "911_CENTER": {"label": "911 Emergency Center", "order": 7},
    "HEALTH_DEPT": {"label": "Health Department", "order": 8},
    "EMS_STATIONS": {"label": "EMS Stations", "order": 9},
    "HIGHWAY_DEPT": {"label": "Highway Department", "order": 10},
    "REMOTE": {"label": "Remote Offices", "order": 11},
    "MENDON": {"label": "Mendon Campus", "order": 12},
    "OTHER": {"label": "Other", "order": 99},
}


def safe_id(name: str) -> str:
    """Convert switch name to valid Mermaid node ID."""
    s = name.replace("-", "_").replace(" ", "_").replace(".", "_")
    if s and s[0].isdigit():
        s = "sw_" + s
    if s.lower() in ("end", "graph", "subgraph", "class", "style", "default"):
        s = s + "_sw"
    return s


def node_label(name: str, info: dict) -> str:
    """Compact label: name, model, IP, stack info."""
    stack = len(info["stack_members"])
    parts = [f"<b>{name}</b>"]
    parts.append(info["model"])
    parts.append(info["ip"])
    if stack > 0:
        parts.append(f"Stack: {stack + 1} units | {info['ports']} ports")
    else:
        parts.append(f"{info['ports']} ports")
    return "<br/>".join(parts)


def generate_mermaid(switches: dict) -> str:
    """Generate Mermaid flowchart with 3-tier hierarchy: Core → Campus/Remote → Groups → Switches."""
    groups = defaultdict(list)
    for name, info in switches.items():
        loc = classify_location(name)
        groups[loc].append((name, info))

    lines = []
    lines.append("graph LR")
    lines.append("")

    # Styles
    lines.append("    classDef coreNode fill:#e94560,stroke:#ff6b6b,stroke-width:3px,color:#fff,font-weight:bold")
    lines.append("    classDef campusNode fill:#7c3aed,stroke:#a78bfa,stroke-width:2px,color:#fff,font-weight:bold")
    lines.append("    classDef hubNode fill:#6366f1,stroke:#818cf8,stroke-width:2px,color:#fff,font-weight:bold")
    lines.append("    classDef aggNode fill:#0f3460,stroke:#22d3ee,stroke-width:2px,color:#e4e4ef")
    lines.append("    classDef stackNode fill:#1a1a2e,stroke:#533483,stroke-width:1.5px,color:#e4e4ef")
    lines.append("    classDef singleNode fill:#1a1a2e,stroke:#2a2a3a,stroke-width:1px,color:#8888a0")
    lines.append("    classDef offNode fill:#2d1117,stroke:#f87171,stroke-width:2px,color:#f87171,stroke-dasharray:5")
    lines.append("")

    # === CORE NODE ===
    core = switches["COURTHOUSE_CORE"]
    lines.append(f'    CORE["{node_label("COURTHOUSE_CORE", core)}"]')
    lines.append("    class CORE coreNode")
    lines.append("")

    # === SUPER-GROUPS (tier 1 from core) ===
    # Courthouse Campus: IDFs + Offices + Desks + IT
    # Public Safety: 911 + Justice
    # Field Sites: EMS + Highway + Remote
    # Direct: Data Center, Health (has own AGG), Mendon

    SUPER_GROUPS = {
        "courthouse": {
            "label": "Courthouse Campus",
            "locations": ["COURTHOUSE_IDF", "COURTHOUSE_OFFICES", "COURTHOUSE_DESKS", "IT_OFFICES"],
        },
        "public_safety": {
            "label": "Public Safety",
            "locations": ["911_CENTER", "JUSTICE"],
        },
        "field_sites": {
            "label": "Field Sites",
            "locations": ["EMS_STATIONS", "HIGHWAY_DEPT", "REMOTE"],
        },
    }

    # Direct connections (don't go through super-groups)
    DIRECT = ["DATA_CENTER", "HEALTH_DEPT", "MENDON"]

    AGG_SWITCHES = {
        "911_CENTER": "911_CORE",
        "HEALTH_DEPT": "HEALTH_DEPT_AGG",
    }

    def emit_switch(name, info):
        nid = safe_id(name)
        # All switches are online per network admin
        style = "stackNode" if info["stack_members"] else "singleNode"
        lines.append(f'    {nid}["{node_label(name, info)}"]')
        lines.append(f"    class {nid} {style}")
        return nid

    def emit_group(loc, parent_id):
        meta = LOCATION_META.get(loc, {"label": loc})
        switch_list = groups.get(loc, [])
        if not switch_list:
            return

        agg_switch = AGG_SWITCHES.get(loc)

        if agg_switch and agg_switch in switches:
            agg_info = switches[agg_switch]
            agg_nid = safe_id(agg_switch)
            lines.append(f'    {agg_nid}["{node_label(agg_switch, agg_info)}"]')
            lines.append(f"    class {agg_nid} aggNode")
            lines.append(f"    {parent_id} --> {agg_nid}")
            for name, info in sorted(switch_list, key=lambda x: x[0]):
                if name == agg_switch:
                    continue
                nid = emit_switch(name, info)
                lines.append(f"    {agg_nid} --> {nid}")
        else:
            hub_id = f"hub_{loc}"
            count = len(switch_list)
            total_ports = sum(info["ports"] for _, info in switch_list)
            lines.append(f'    {hub_id}{{"<b>{meta["label"]}</b><br/>{count} switches | {total_ports} ports"}}')
            lines.append(f"    class {hub_id} hubNode")
            lines.append(f"    {parent_id} --> {hub_id}")
            for name, info in sorted(switch_list, key=lambda x: x[0]):
                nid = emit_switch(name, info)
                lines.append(f"    {hub_id} --> {nid}")

        lines.append("")

    # Super-groups
    for sg_key, sg_meta in SUPER_GROUPS.items():
        sg_id = f"sg_{sg_key}"
        # Count total switches in super-group
        total = sum(len(groups.get(loc, [])) for loc in sg_meta["locations"])
        if total == 0:
            continue
        sg_label = sg_meta["label"]
        lines.append(f'    {sg_id}{{{{"<b>{sg_label}</b><br/>{total} switches"}}}}')
        lines.append(f"    class {sg_id} campusNode")
        lines.append(f"    CORE --> {sg_id}")
        lines.append("")

        for loc in sg_meta["locations"]:
            emit_group(loc, sg_id)

    # Direct connections
    for loc in DIRECT:
        if loc == "MENDON":
            for name, info in groups.get("MENDON", []):
                nid = safe_id(name)
                lines.append(f'    {nid}["{node_label(name, info)}"]')
                lines.append(f"    class {nid} aggNode")
                lines.append(f"    CORE -->|downstream| {nid}")
            lines.append("")
        else:
            emit_group(loc, "CORE")

    return "\n".join(lines)


def render_mermaid(code: str, output_path: Path, width: int = 3000, height: int = 4000):
    """Render Mermaid code to SVG using mmdc CLI."""
    tmp = Path(tempfile.mktemp(suffix=".mmd"))
    tmp.write_text(code, encoding="utf-8")

    config = Path(tempfile.mktemp(suffix=".json"))
    config.write_text('''{
  "theme": "dark",
  "themeVariables": {
    "primaryColor": "#1a1a2e",
    "primaryTextColor": "#e4e4ef",
    "primaryBorderColor": "#6366f1",
    "lineColor": "#533483",
    "secondaryColor": "#16213e",
    "tertiaryColor": "#0f3460",
    "background": "#0a0a0f",
    "mainBkg": "#1a1a2e",
    "nodeBorder": "#6366f1",
    "clusterBkg": "#13131a",
    "clusterBorder": "#2a2a3a",
    "titleColor": "#e4e4ef",
    "edgeLabelBackground": "#0a0a0f",
    "fontSize": "13px"
  },
  "flowchart": {
    "htmlLabels": true,
    "curve": "basis",
    "rankSpacing": 80,
    "nodeSpacing": 25,
    "padding": 20,
    "useMaxWidth": false
  }
}''', encoding="utf-8")

    mmdc = shutil.which("mmdc") or shutil.which("mmdc.cmd")
    if not mmdc:
        print("ERROR: mmdc not found")
        return False

    svg_path = output_path.with_suffix(".svg")
    cmd = [mmdc, "-i", str(tmp), "-o", str(svg_path), "-w", str(width),
           "-H", str(height), "-c", str(config), "-b", "#0a0a0f"]

    print(f"Rendering: {svg_path.name}")
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

    tmp.unlink(missing_ok=True)
    config.unlink(missing_ok=True)

    if result.returncode != 0:
        print(f"ERROR: {result.stderr[:500]}")
        return False

    print(f"SVG saved: {svg_path} ({svg_path.stat().st_size // 1024}KB)")
    return True


def main():
    print("Parsing network switch CSV...")
    switches = parse_switches(CSV_PATH)
    print(f"Found {len(switches)} parent switches\n")

    # Summary
    groups = defaultdict(list)
    for name, info in switches.items():
        groups[classify_location(name)].append(name)

    for loc in sorted(groups, key=lambda x: LOCATION_META.get(x, {}).get("order", 99)):
        meta = LOCATION_META.get(loc, {"label": loc})
        print(f"  {meta['label']:25s} ({len(groups[loc])} switches): {', '.join(sorted(groups[loc]))}")

    print("\nGenerating Mermaid code...")
    mermaid_code = generate_mermaid(switches)

    mmd_path = OUTPUT_DIR / "network_topology.mmd"
    mmd_path.write_text(mermaid_code, encoding="utf-8")
    print(f"Source: {mmd_path} ({len(mermaid_code.splitlines())} lines)")

    print("\nRendering SVG...")
    success = render_mermaid(mermaid_code, OUTPUT_DIR / "network_topology")

    if success:
        print("\nDone!")
    else:
        print("\nRender failed — check .mmd file or paste into mermaid.live")


if __name__ == "__main__":
    main()
