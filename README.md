# UFS Pattern Generator (self-contained)

Generate UFS test patterns (`.py`) from test-case flows (`TC/*.md`).

The pipeline is **TC → IR → pattern.py**. Deterministic work is Python; the
reasoning steps run on the **current model** (no API key, no `anthropic`
dependency — `pip install` only needs pytest). Every step grounds itself in two
real sources:

- **Code** — the understand-anything **knowledge graph**
  (`.understand-anything/knowledge-graph.json`) over the pattern source at repo
  root (`api/ lib/ pattern/ ...`). Answers *how to implement* (real functions,
  call chains, imports).
- **Wiki** — the **ingested llm-wiki** (`wiki/`), a Karpathy LLM-Wiki built by
  ingesting 6 sources with conflict resolution. Answers *spec / customer
  constraints*. Conflict rules: **CustomerReq > Spec**, **UserPrompt >
  ModelDefault**.

## Layout

| Path | Role |
|------|------|
| `api/ lib/ pattern/ project_api/ ...` | pattern source = code-grounding base (keep in place) |
| `.understand-anything/knowledge-graph.json` | code knowledge graph (rebuild with `/understand` if source changes) |
| `graph_query.py` | query the code graph (code grounding tool) |
| `wiki/` | ingested llm-wiki (entities/ concepts/ conflicts.md + raw sources) |
| `wiki_query.py` | basic wiki keyword lookup (utility; not the primary grounding path) |
| `ir_generator/` | TC `.md` → IR JSON (parser + ingested-wiki lookup + agent annotation) |
| `pattern_generator/` | IR → step plan → generation prompt → validate |
| `TC/` | input test cases |
| `generated/<PATTERN_ID>/` | all per-run artifacts (see docs/AGENT_WORKFLOW.md) |
| `generate_pattern.py` | CLI for the deterministic stages |
| `docs/AGENT_WORKFLOW.md` | step-by-step contract + output-file reference |

## Install

```bash
pip install -r requirements.txt   # pytest only — no API key, no anthropic SDK
```

## How it works — 6 steps

Python CLI steps alternate with two LLM steps (done by the current model).
All artifacts land in `generated/<PATTERN_ID>/`.

```bash
# 1. TC -> IR skeleton + enrich prompt (Python)
python generate_pattern.py prepare-ir TC/pf002-0098-normalized-test-flow.md

# 2. LLM step A: read generated/PF002_0098/enrich_prompt.txt, write
#    generated/PF002_0098/annotations.json  (phase inputs/outputs + edges)

# 3. annotations -> final IR (Python)
python generate_pattern.py finalize-ir \
    generated/PF002_0098/ir_skeleton.json generated/PF002_0098/annotations.json

# 4. IR -> topological step plan + generation prompt (Python)
python generate_pattern.py prepare generated/PF002_0098/pf002-0098-ir.json

# 5. LLM step B: read generated/PF002_0098/generation_prompt.txt, write
#    generated/PF002_0098/<PatternName>.py  +  provenance.json  (grounding rules below)

# 6. validate the generated pattern (Python)
python generate_pattern.py validate \
    generated/PF002_0098/<PatternName>.py generated/PF002_0098/pf002-0098-ir.json
```

## Grounding rules (MANDATORY for the LLM generation step)

For **every** step, consult BOTH sources using their proper mechanism — never
ad-hoc text search:

- **Code** → `python graph_query.py <symbol>` to locate the real function/class
  in the knowledge graph (file:line + call edges), then read the real source
  there. Search by domain keyword; do **not** assume a naming prefix
  (e.g. `StartStopUnit` vs `CmdSeqTestUnitReady`). Prefer real `pattern/` usages.
- **Wiki** → read `wiki/conflicts.md` FIRST (conflict-resolved overrides, highest
  authority), then the relevant `wiki/entities/*.md` / `wiki/concepts/*.md`.
  Apply CustomerReq > Spec and UserPrompt > ModelDefault. Do **not** rely on
  `wiki_query.py` keyword search or guess filenames.
  (e.g. default LUN = MaxCapacity Enabled LUN, not 0; WriteBooster flag LUN must
  be Normal non-Boot index 0–7.)

Record provenance: tag each grounded element inline `# src[code]: file:line` or
`# src[wiki]: file`, and write `generated/<ID>/provenance.json` with both sources
per step (use `"none relevant found"` when a source was checked but empty).

## Querying the llm-wiki (how, for any agent)

The wiki is a **Karpathy LLM-Wiki**: you *query* it by **navigating and reading**
markdown — NOT by keyword search. The intelligence is the model reading the
ingested, conflict-resolved pages. Steps:

1. Open **`wiki/index.md`** — the navigation entry point. It lists every page
   (sources / entities / concepts / conflicts) with a one-line description and
   `[[wikilink]]` names.
2. Find the page whose description matches your term (e.g. for `bBootLunEn` →
   `[[attributes]]`; for LUN selection → `[[lun]]`; for WriteBooster →
   `[[write-booster]]`).
3. Read that page: `wiki/entities/<name>.md` or `wiki/concepts/<name>.md`
   (a `[[name]]` wikilink maps to `entities/name.md` or `concepts/name.md`).
   Follow further `[[wikilinks]]` inside as needed.
4. Read **`wiki/conflicts.md`** for any conflict-resolved overrides — these WIN.
5. Apply the priority rules: **CustomerReq > Spec**, **UserPrompt > ModelDefault**
   (the resolved value beats the raw Spec value).

> `wiki_query.py` is only a basic keyword helper for quick lookups — it is NOT
> the proper query mechanism and must not be used for grounding decisions.

## Generated pattern rules

- **First line MUST be `import package_root`** (path bootstrap), before the
  docstring and all other imports.
- Follow `pattern/pattern_template.py`: subclass `UFSTC`; implement
  `pre_process()` / `post_process()`; test steps are methods `step1`, `step2`, …
  (auto-run in order by `process()`).
- Carry phase data flow across steps as `self.<var>` attributes.
- A loop phase becomes one step method with an internal loop.
- Emit `# TODO human-confirm` for anything that cannot be grounded.

## Quick reference

```bash
python graph_query.py write_attribute        # find a symbol in the code graph
python graph_query.py StartStopUnit --src     # ... and print its source
python wiki_query.py "bBootLunEn"             # basic wiki keyword lookup
python -m pytest -q                            # run the test suite
```

## For other agents / users

- **This README is the single entry point — it is enough to use the system.**
  At each step you read the prepared prompt file in `generated/<ID>/`
  (`enrich_prompt.txt`, `generation_prompt.txt`); those are **self-describing** —
  they embed the exact JSON schemas (annotations, provenance) and the grounding
  rules. So you do not need any other doc to operate.
- Optional deeper reference: **`docs/AGENT_WORKFLOW.md`** has a table of every
  output file (order, producer, meaning) — useful for debugging, not required.
- Self-contained and relative-path; copy the folder anywhere.
- After changing the pattern source under `api/ lib/ pattern/ ...`, rebuild the
  code graph by running understand-anything's `/understand` on the repo root.
- The wiki is ingested; if you add CustomerReq/UserPrompt/Spec etc., re-ingest
  via the llm-wiki tooling so `conflicts.md` and `entities/concepts` stay current.
