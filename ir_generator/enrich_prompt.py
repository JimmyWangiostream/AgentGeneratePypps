"""Agent-driven IR enrichment: build the prompt (deterministic) and apply the
model's annotations back into the IR. No LLM SDK call — the current Claude Code
model reads the prompt and returns annotations."""

ENRICH_INSTRUCTIONS = """You are a UFS test architecture expert. Given a UFS test
pattern skeleton and relevant UFS spec excerpts, identify:
1. What data variables each phase produces as outputs
2. What data variables each phase needs as inputs
3. The data_flow on each sequential edge between phases

Rules:
- Variables are snake_case (e.g. boot_lun_id, max_lba, write_pattern)
- Only include variables explicitly passed between phases
- Respond with ONLY valid JSON of this exact shape:
{
  "phases": [{"phase_id": "...", "inputs": [...], "outputs": [...]}],
  "edges": [{"from": "...", "to": "...", "type": "sequential", "data_flow": [...]}]
}"""


def build_enrich_prompt(skeleton: dict, wiki_refs: dict) -> str:
    lines = [ENRICH_INSTRUCTIONS, "",
             f"Pattern: {skeleton['pattern_id']} — {skeleton['title']}", ""]
    # Conflict-resolved overrides from the ingested llm-wiki (highest authority), shown once.
    for ref in wiki_refs.get("__conflicts__", []):
        lines += [f"## {ref['title']}", ref["excerpt"], ""]
    lines += ["## Phase Skeleton", ""]
    for phase in skeleton["phases"]:
        lines.append(f"### {phase['phase_id']}: {phase['name']} (type={phase['type']})")
        if phase.get("loop_count"):
            lines.append(f"  loop_count: {phase['loop_count']}")
        for step in phase["steps"]:
            cmd = step.get("scsi_cmd") or step.get("ufs_query") or "—"
            lines.append(f"  - {step['step_id']}: {step['name']} [{cmd}]")
            lines.append(f"    expected: {step['expected']}")
        refs = wiki_refs.get(phase["phase_id"], [])
        if refs:
            lines.append(f"\n  ## Relevant Wiki ({len(refs)} ingested pages)")
            for ref in refs[:3]:
                lines.append(f"  ### {ref['title']}")
                lines.append(ref["excerpt"][:800])
        lines.append("")
    return "\n".join(lines)


def apply_annotations(skeleton: dict, annotations: dict, wiki_refs: dict) -> dict:
    annotated = {p["phase_id"]: p for p in annotations.get("phases", [])}
    phases = [
        {**phase,
         "inputs":  annotated.get(phase["phase_id"], {}).get("inputs", []),
         "outputs": annotated.get(phase["phase_id"], {}).get("outputs", [])}
        for phase in skeleton["phases"]
    ]
    return {
        **skeleton,
        "phases": phases,
        "dependency_graph": {
            "nodes": [p["phase_id"] for p in phases],
            "edges": annotations.get("edges", []),
        },
        "_wiki_refs": wiki_refs,
    }
