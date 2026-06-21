def generate_debug_md(ir: dict) -> str:
    pid       = ir["pattern_id"]
    wiki_refs = ir.get("_wiki_refs", {})
    lines = [
        f"# {pid} IR Debug Report",
        "",
        f"**Pattern**: {ir['title']}",
        f"**Pattern ID**: {pid}",
        "",
        "---",
        "",
        "## Stage 1 — Rule-based 解析結果",
        "",
        "| Phase | Type | Steps | Loop Info |",
        "|-------|------|-------|-----------|",
    ]

    for phase in ir["phases"]:
        loop_info = ""
        if phase["type"] == "loop":
            loop_info = (f"count={phase['loop_count']}" if phase.get("loop_count")
                         else f"until: {phase.get('loop_condition', '')}")
        lines.append(f"| {phase['phase_id']} | {phase['type']} | {len(phase['steps'])} | {loop_info} |")

    lines += ["", "**Fail Condition 識別**:", ""]
    for phase in ir["phases"]:
        for step in phase["steps"]:
            if step.get("fail_condition"):
                lines.append(
                    f"- `{step['step_id']}`: Expected `{step['expected']}` "
                    f"→ 含條件式關鍵字 → `fail_condition` 加入"
                )

    lines += ["", "---", "", "## Stage 2 — Wiki 查詢結果", ""]
    for phase in ir["phases"]:
        pid_s = phase["phase_id"]
        refs  = wiki_refs.get(pid_s, [])
        lines.append(f"### {pid_s} — {phase['name']}")
        if refs:
            lines += ["", "| 參考 Wiki Chapter | 標題 |", "|------------------|------|"]
            for ref in refs:
                lines.append(f"| `{ref['file']}` | {ref['title']} |")
        else:
            lines.append("_(no wiki chapters matched)_")
        lines.append("")

    lines += ["---", "", "## Stage 3 — LLM 標注決策", ""]

    edges = ir.get("dependency_graph", {}).get("edges", [])
    lines += ["### 資料流 (data_flow per edge)", ""]
    if edges:
        lines += ["| Edge | data_flow |", "|------|-----------|"]
        for edge in edges:
            flows = ", ".join(edge.get("data_flow", []))
            lines.append(f"| {edge['from']} → {edge['to']} | {flows} |")
    else:
        lines.append("_(no edges)_")

    lines += ["", "### Phase inputs / outputs", "",
              "| Phase | inputs | outputs |",
              "|-------|--------|---------|"]
    for phase in ir["phases"]:
        inp = ", ".join(phase.get("inputs", []))
        out = ", ".join(phase.get("outputs", []))
        lines.append(f"| {phase['phase_id']} | {inp or '—'} | {out or '—'} |")

    return "\n".join(lines)
