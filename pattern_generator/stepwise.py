"""Walk an IR into an ordered, phase-aware step plan and a generation prompt.
No LLM, no code retrieval — grounding is done on demand by the generating model."""
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TEMPLATE_REL = "pattern/pattern_template.py"


def topo_order_phases(ir: dict) -> list[str]:
    """Return phase_ids in dependency (topological) order. Falls back to the
    phases' natural order if the dependency_graph is missing/empty."""
    phases = [p["phase_id"] for p in ir.get("phases", [])]
    dg = ir.get("dependency_graph") or {}
    edges = dg.get("edges") or []
    if not edges:
        return phases
    incoming = {pid: 0 for pid in phases}
    adj = {pid: [] for pid in phases}
    for e in edges:
        f, t = e.get("from"), e.get("to")
        if f in adj and t in incoming:
            adj[f].append(t)
            incoming[t] += 1
    queue = [pid for pid in phases if incoming[pid] == 0]
    order = []
    while queue:
        n = queue.pop(0)
        order.append(n)
        for m in adj[n]:
            incoming[m] -= 1
            if incoming[m] == 0:
                queue.append(m)
    # Append any leftover (cycle safety) preserving natural order
    for pid in phases:
        if pid not in order:
            order.append(pid)
    return order


def ordered_steps(ir: dict) -> list[dict]:
    """Flatten phases (in topological order) into a flat ordered step list.
    Each entry carries its phase context so generation respects dependencies."""
    by_id = {p["phase_id"]: p for p in ir.get("phases", [])}
    steps = []
    n = 0
    for pid in topo_order_phases(ir):
        phase = by_id[pid]
        for s in phase.get("steps", []):
            n += 1
            steps.append({
                "seq": n,
                "method": f"step{n}",
                "phase_id": pid,
                "phase_name": phase.get("name"),
                "phase_type": phase.get("type"),
                "loop_type": phase.get("loop_type"),
                "loop_count": phase.get("loop_count"),
                "phase_inputs": phase.get("inputs", []),
                "phase_outputs": phase.get("outputs", []),
                "step": s,
            })
    return steps


GEN_INSTRUCTIONS = """You are a UFS pattern generator. Generate ONE executable
Python UFS test pattern from the step plan below.

STRUCTURE — follow pattern/pattern_template.py EXACTLY:
- The VERY FIRST line of the file MUST be `import package_root` (path bootstrap;
  it must precede every other import).
- Subclass `UFSTC` (from the template) and implement `pre_process()` and
  `post_process()`.
- Each plan step becomes a method named step1, step2, ... (process() auto-runs
  them in number order). Keep the given `method` name for each step.
- Carry phase data_flow across steps as `self.<var>` attributes (a phase's
  `outputs` become self attributes that later phases' `inputs` read).
- A loop phase becomes a step method containing `for _ in range(loop_count):`
  with the for_each set iterated inside.
- Use the real imports the template uses: `import Script`, `from Script import api`,
  `from Script.lib import sdk_lib as lib`, `from Script.pattern.pattern_logger import logger`,
  `import Script.api.cmd_seq as ExecuteCMD`.

GROUNDING — do NOT invent APIs. For EACH step you MUST consult BOTH sources
using their PROPER mechanism (not ad-hoc text search):
  • CODE = understand-anything knowledge graph. Use `python graph_query.py <symbol>`
    to look up real functions/classes in `.understand-anything/knowledge-graph.json`
    (returns file:line + call edges), THEN read the real source at that location.
    This is structural lookup, not grep. Search by DOMAIN KEYWORD; do NOT assume a
    naming prefix (e.g. `StartStopUnit` vs `CmdSeqTestUnitReady`). Prefer real
    usages in `pattern/` for the calling idiom.
  • WIKI = llm-wiki, an INGESTED Karpathy LLM-Wiki with conflict resolution — NOT a
    keyword DB. Do NOT use wiki_query.py keyword search and do NOT guess filenames.
    Instead READ the ingested pages:
      1. `wiki/conflicts.md` FIRST — conflict-resolved overrides (highest authority).
      2. relevant `wiki/entities/*.md` and `wiki/concepts/*.md` (synthesized knowledge).
    APPLY the priority rules: CustomerReq > Spec (Rule 1), UserPrompt > ModelDefault
    (Rule 2); any other conflict keeps both. The resolved value WINS over raw Spec
    (e.g. default LUN = MaxCapacity Enabled LUN, not 0; WriteBooster flag LUN must be
    Normal non-Boot 0-7).
If you cannot ground a call, emit `# TODO human-confirm` with what is missing.

PROVENANCE — every grounded fact MUST be traceable to its source:
- Inline: tag each grounded element with `# src[code]: <file>:<line>` or
  `# src[wiki]: <wiki file>` next to where it is used.
- Sidecar: also write `provenance.json` into the run dir. Shape:
    { "<method>": {
        "code": [{"claim": "...", "ref": "api/...py:NN"}],
        "wiki": [{"claim": "...", "ref": "wiki/entities/x.md"}]   // or "none relevant found"
    }, ... }
  Record BOTH sources for every step. If a source yielded nothing, write the
  string "none relevant found" (NOT an empty list) so "didn't check" is
  distinguishable from "checked, nothing there".

CONTROL FLOW — emit loop counts, for_each sets, and phase order EXACTLY as the
IR/step plan specifies.

Output ONLY the Python source for the pattern file (then write provenance.json).
"""


def build_generation_prompt(ir: dict, steps: list[dict]) -> str:
    return "\n\n".join([
        GEN_INSTRUCTIONS,
        f"Template to follow: {TEMPLATE_REL}",
        f"Pattern: {ir.get('pattern_id')} — {ir.get('title', '')}",
        f"Description: {ir.get('description', '')}",
        "## Step Plan (topological, phase-aware)",
        json.dumps(steps, ensure_ascii=False, indent=2),
        "## Full IR",
        json.dumps(ir, ensure_ascii=False, indent=2),
    ])
