# Agent Workflow — TC → IR → Pattern (.py)

The deterministic stages are Python; the LLM steps are performed by the current
model (no API key). Every artifact for one pattern lands in `generated/<PATTERN_ID>/`.

1. `python generate_pattern.py prepare-ir TC/<file>.md`
   → writes `generated/<ID>/ir_skeleton.json` + `enrich_prompt.txt`.

2. **LLM step A — annotate data flow.** Read `enrich_prompt.txt`, write the
   annotations to `generated/<ID>/annotations.json`:
   `{"phases":[{phase_id,inputs,outputs}],"edges":[{from,to,type,data_flow}]}`.

3. `python generate_pattern.py finalize-ir generated/<ID>/ir_skeleton.json generated/<ID>/annotations.json`
   → writes `<id>-ir.json` + `<id>-ir-debug.md` in the folder.

4. `python generate_pattern.py prepare generated/<ID>/<id>-ir.json`
   → writes `1_steps.json` (topological, phase-aware step plan) + `generation_prompt.txt`.

5. **LLM step B — generate the pattern.** Read `generation_prompt.txt` and write
   `generated/<ID>/<pattern>.py`, following `pattern/pattern_template.py`
   (subclass `UFSTC`; steps become `step1..stepN`; data flow via `self.*`; loop
   phase = a step with an internal `for` loop). Ground each step against BOTH
   sources and record provenance:
   - **code** (understand-anything graph): `python graph_query.py <symbol>` →
     file:line + call edges from `.understand-anything/knowledge-graph.json`, then
     read the real source there. Domain-keyword search; no naming-prefix
     assumptions; prefer real `pattern/` usages. NOT plain grep.
   - **wiki** (llm-wiki, ingested + conflict-resolved): navigate via
     `wiki/index.md` (entry point with `[[wikilinks]]`), read `wiki/conflicts.md`
     FIRST (overrides), then the relevant `wiki/entities/*.md` /
     `wiki/concepts/*.md`. Apply CustomerReq > Spec and UserPrompt > ModelDefault.
     Do NOT use `wiki_query.py` keyword search or guess filenames. Full how-to:
     README "Querying the llm-wiki".
   - Tag each grounded element inline `# src[code]: file:line` / `# src[wiki]: file`.
   - Write `generated/<ID>/provenance.json` with both sources per step; use the
     string `"none relevant found"` where a source had nothing (so "checked but
     empty" is distinct from "not checked"). Emit `# TODO human-confirm` for any
     ungrounded call.

6. `python generate_pattern.py validate generated/<ID>/<pattern>.py generated/<ID>/<id>-ir.json`
   → prints syntax/structure/imports report. Fix and re-validate as needed.

`generated/<ID>/` then contains every artifact for one pattern: ir_skeleton,
annotations, IR (+debug), step plan, prompts, the .py, and provenance — fully
debuggable, with each grounded fact traceable to code or wiki.

## Output files — order, producer, meaning

Files in `generated/<PATTERN_ID>/`, in creation order. Steps alternate between
deterministic Python (CLI) and LLM (current model):

| # | File | Produced by | Kind | What it is |
|---|------|-------------|------|-----------|
| 1 | `ir_skeleton.json` | `prepare-ir` | Python | Parsed TC skeleton (phases/steps) + wiki chapter refs. No data flow yet. |
| 2 | `enrich_prompt.txt` | `prepare-ir` | Python | Prompt asking the model for each phase's inputs/outputs/data_flow. |
| 3 | `annotations.json` | **LLM step A** | LLM | Data-flow annotation the model produces from (2). |
| 4 | `<id>-ir.json` | `finalize-ir` | Python | **Final IR** = skeleton (1) + annotations (3). The input to generation. |
| 5 | `<id>-ir-debug.md` | `finalize-ir` | Python | Human-readable IR report (phase table, loop/fail_condition, data flow). |
| 6 | `1_steps.json` | `prepare` | Python | IR flattened in topological order into an ordered step list + phase context. |
| 7 | `generation_prompt.txt` | `prepare` | Python | Generation prompt: rules (template, both-sources, provenance) + step plan + IR. |
| 8 | `<PatternName>.py` | **LLM step B** | LLM | The generated pattern, grounded by on-demand code/wiki search. |
| 9 | `provenance.json` | **LLM step B** | LLM | Per-step source record (code / wiki / "none relevant found"). Written with (8). |

Three groups: **IR stage** (1-5, "what the pattern must do") · **generation
stage** (6-8, "how to build it from real code") · **traceability** (5 debug + 9
provenance, "why these decisions, where grounding came from").

Debug entry points: wrong API in a step → `provenance.json` + inline `# src[...]`
in the .py; IR data-flow/loop wrong → `<id>-ir-debug.md`; step order/phase deps →
`1_steps.json`; what the model actually saw → `generation_prompt.txt`.
