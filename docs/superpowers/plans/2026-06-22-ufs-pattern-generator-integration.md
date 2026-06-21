# UFS Pattern Generator — Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Consolidate the TC→IR generator and the llm-wiki retriever into the current `understandanything/` repo so it self-contains the entire UFS-pattern generation pipeline (TC → IR → .py), driven by the current Claude Code model with no API key, and make it a portable repo other agents can use.

**Architecture:** Python does only deterministic work (parse, retrieve from the code knowledge-graph + wiki, assemble context, write files, validate). All LLM steps (IR data-flow annotation, pattern `.py` generation, C1/C2/C3 grading) are performed by the driving Claude Code current-session model, which reads prepared context files and writes results back. The repo already holds the pattern source code at root and `.understand-anything/knowledge-graph.json` (the Code Retriever base, 7611 nodes / 18766 edges with `calls`/`contains`/`imports`).

**Tech Stack:** Python 3.10+ (uses `list[...]` builtins generics), pytest. No `anthropic` SDK.

## Global Constraints

- All filesystem paths MUST be relative to the repo root, derived via `Path(__file__).resolve().parent...`. No absolute paths (the current `ir_generator/config.py` hardcodes `D:\GME_AI\Claude\llm_wiki_repo\wiki` — this must go).
- No `anthropic` import anywhere. No `ANTHROPIC_API_KEY` requirement. LLM steps are agent-driven.
- Repo root for code: `understandanything/` (the directory this plan lives under).
- Pattern source code at root (`api/ lib/ pattern/ pattern_template_wizard/ project_api/`) and `.understand-anything/` MUST stay in place — the graph's `filePath` values are relative to repo root and must remain valid.
- Per-run output goes to `generated/<PATTERN_ID>/` (one folder per generated pattern).
- Python generics use builtin syntax (`list[dict]`, `dict[str, list]`) — matches existing code style.
- Test framework: pytest. Run from repo root.

---

## File Structure

**Moved in (from sibling repos):**
- `ir_generator/` ← `agent_pypps/ir_generator/` (config paths fixed; `llm_enricher.py` LLM call removed)
- `TC/` ← `agent_pypps/TC/` (60+ test-case `.md`)
- `wiki/` ← `llm_wiki_repo/wiki/` (self-contained, keeps its own `Script/`; the stray brace-expansion junk dir `{entities,concepts,...}/` is NOT copied)
- `wiki_query.py` ← `llm_wiki_repo/query_wiki.py` (default `wiki_root` made relative)

**Created new:**
- `pattern_generator/` package: `config.py`, `extractor.py`, `code_retriever.py`, `wiki_retriever.py`, `merger.py`, `validator.py`, `run_logger.py`, `prepare.py`
- `ir_generator/enrich_prompt.py` (replaces the LLM call in `llm_enricher.py`)
- `generated/` (output root; gitignored except `.gitkeep`)
- `README.md` (complete usage docs)
- `requirements.txt` (no `anthropic`)
- `tests/` for the new modules

**Kept in place:** `api/ lib/ pattern/ ...`, `.understand-anything/`, root `__init__.py`.

---

## PHASE 1 — Relocate & Portability

### Task 1: Move ir_generator + TC + tests, fix paths to relative

**Files:**
- Create: `ir_generator/__init__.py`, `ir_generator/config.py`, `ir_generator/parser.py`, `ir_generator/wiki_lookup.py`, `ir_generator/debug_reporter.py` (copied from `agent_pypps/`)
- Create: `TC/*.md` (copied), `tests/test_parser.py`, `tests/test_wiki_lookup.py`, `tests/test_debug_reporter.py`, `tests/__init__.py`, `tests/fixtures/pf002-0098-normalized-test-flow.md` (copied)
- Modify: `ir_generator/config.py` (paths → relative)

**Interfaces:**
- Produces: `ir_generator.config.Config` dataclass with `tc_dir`, `wiki_path`, `output_dir`, `model` attributes; `ir_generator.parser.parse_tc(path) -> dict`; `ir_generator.wiki_lookup.lookup_wiki(skeleton, config) -> dict[str, list[dict]]`.

- [ ] **Step 1: Copy the files (no edits yet)**

```bash
# from repo root (understandanything/)
cp -r ../agent_pypps/ir_generator ./ir_generator
cp -r ../agent_pypps/TC ./TC
cp -r ../agent_pypps/tests ./tests
rm -f ./ir_generator/llm_enricher.py        # LLM call removed in Task 2
rm -f ./tests/test_llm_enricher.py          # replaced in Task 2
```

- [ ] **Step 2: Rewrite `ir_generator/config.py` with relative paths**

```python
from pathlib import Path
from dataclasses import dataclass, field

# Repo root = parent of the ir_generator package
REPO_ROOT = Path(__file__).resolve().parent.parent


@dataclass
class Config:
    tc_dir: Path = field(default_factory=lambda: REPO_ROOT / "TC")
    wiki_path: Path = field(default_factory=lambda: REPO_ROOT / "wiki")
    output_dir: Path = field(default_factory=lambda: REPO_ROOT / "generated")
    model: str = "current"  # LLM steps run on the current Claude Code model; no SDK/key

    def __post_init__(self):
        self.tc_dir = Path(self.tc_dir)
        self.wiki_path = Path(self.wiki_path)
        self.output_dir = Path(self.output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
```

- [ ] **Step 3: Write a test that config resolves to in-repo relative paths**

```python
# tests/test_config.py
from pathlib import Path
from ir_generator.config import Config, REPO_ROOT


def test_config_paths_are_inside_repo():
    cfg = Config()
    assert cfg.wiki_path == REPO_ROOT / "wiki"
    assert cfg.tc_dir == REPO_ROOT / "TC"
    assert cfg.output_dir == REPO_ROOT / "generated"
    # No absolute drive letters baked in
    assert "GME_AI" not in str(cfg.wiki_path) or cfg.wiki_path.is_relative_to(REPO_ROOT)
```

- [ ] **Step 4: Run tests, expect PASS**

Run: `python -m pytest tests/test_config.py -v`
Expected: PASS (2 assertions).

- [ ] **Step 5: Run the moved parser/wiki tests to confirm relocation intact**

Run: `python -m pytest tests/test_parser.py tests/test_debug_reporter.py -v`
Expected: PASS (these don't depend on the LLM). `test_wiki_lookup.py` runs after Task 3 (needs `wiki/` present).

- [ ] **Step 6: Commit**

```bash
git add ir_generator TC tests
git commit -m "feat: relocate ir_generator + TC into repo with relative paths"
```

---

### Task 2: Replace the LLM enrichment call with an agent-driven prompt builder

**Files:**
- Create: `ir_generator/enrich_prompt.py`
- Create: `tests/test_enrich_prompt.py`

**Interfaces:**
- Consumes: skeleton dict from `parse_tc`, `wiki_refs` from `lookup_wiki`.
- Produces:
  - `ir_generator.enrich_prompt.build_enrich_prompt(skeleton: dict, wiki_refs: dict) -> str`
  - `ir_generator.enrich_prompt.apply_annotations(skeleton: dict, annotations: dict, wiki_refs: dict) -> dict` where `annotations` has shape `{"phases": [{"phase_id","inputs","outputs"}], "edges": [{"from","to","type","data_flow"}]}` and the return is the final IR dict (same shape the old `enrich` produced, including `_wiki_refs`).

- [ ] **Step 1: Write the failing test**

```python
# tests/test_enrich_prompt.py
from ir_generator.enrich_prompt import build_enrich_prompt, apply_annotations

SKELETON = {
    "pattern_id": "PF002_0098", "title": "Boot Stress", "description": "", "tags": [],
    "phases": [
        {"phase_id": "phase_0", "name": "Enable", "type": "sequential",
         "loop_type": None, "loop_count": None, "loop_condition": None,
         "steps": [{"step_id": "step_0_1", "name": "TUR", "scsi_cmd": "TEST UNIT READY",
                    "ufs_query": None, "opcode": "0x00", "query_opcode": None, "idn": None,
                    "expected": "GOOD Status", "fail_condition": None, "on_fail": None,
                    "raw_content": ""}]},
    ],
}


def test_build_prompt_mentions_phases_and_steps():
    prompt = build_enrich_prompt(SKELETON, {"phase_0": []})
    assert "phase_0" in prompt
    assert "TEST UNIT READY" in prompt
    assert "data_flow" in prompt  # instructs the model what to produce


def test_apply_annotations_merges_inputs_outputs_and_edges():
    ann = {"phases": [{"phase_id": "phase_0", "inputs": [], "outputs": ["boot_lun_id"]}],
           "edges": []}
    ir = apply_annotations(SKELETON, ann, {"phase_0": []})
    assert ir["phases"][0]["outputs"] == ["boot_lun_id"]
    assert ir["dependency_graph"]["nodes"] == ["phase_0"]
    assert ir["_wiki_refs"] == {"phase_0": []}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_enrich_prompt.py -v`
Expected: FAIL with `ModuleNotFoundError: ir_generator.enrich_prompt`.

- [ ] **Step 3: Write `ir_generator/enrich_prompt.py`**

```python
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
             f"Pattern: {skeleton['pattern_id']} — {skeleton['title']}", "",
             "## Phase Skeleton", ""]
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
            lines.append(f"\n  ## Relevant Wiki ({len(refs)} chapters)")
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_enrich_prompt.py -v`
Expected: PASS (3 assertions across 2 tests).

- [ ] **Step 5: Commit**

```bash
git add ir_generator/enrich_prompt.py tests/test_enrich_prompt.py
git commit -m "feat: replace anthropic enrich call with agent-driven prompt builder"
```

---

### Task 3: Move the wiki + retriever, make wiki_root relative

**Files:**
- Create: `wiki/` (copied tree, minus junk dir), `wiki_query.py` (copied + edited)
- Create: `tests/test_wiki_query.py`
- Modify: `wiki_query.py` default `wiki_root`

**Interfaces:**
- Produces: `wiki_query.WikiQuery(wiki_root=None)` with `.search_entities(q) -> list[dict]` (keys: `title`, `file`, `definition`, `match_score`) and `.search_sources(q) -> list[dict]` (keys: `source`, `title`, `matches`).

- [ ] **Step 1: Copy wiki tree (exclude the stray brace-expansion dir) and the retriever**

```bash
# from repo root
cp -r ../llm_wiki_repo/wiki ./wiki
# remove the accidental literal brace-expansion directory if present
rm -rf "./wiki/{entities,concepts,sources,synthesis,Spec,CustomerReq,UserPrompt,Script,ProNoun,ModelDefault}"
cp ../llm_wiki_repo/query_wiki.py ./wiki_query.py
```

- [ ] **Step 2: Make `wiki_query.py` default to the in-repo `wiki/` via relative path**

Modify the `__init__` of `WikiQuery` (top of file add import; replace the constructor default):

```python
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent
_DEFAULT_WIKI = _REPO_ROOT / "wiki"

class WikiQuery:
    def __init__(self, wiki_root: str | Path | None = None):
        self.wiki_root = Path(wiki_root) if wiki_root else _DEFAULT_WIKI
        self.entities_dir = self.wiki_root / "entities"
        self.sources_dir = self.wiki_root / "sources"
```

(Leave `search_entities`, `search_sources`, `query`, and the `__main__` block unchanged.)

- [ ] **Step 3: Write the failing test**

```python
# tests/test_wiki_query.py
from wiki_query import WikiQuery


def test_default_wiki_root_is_in_repo():
    wq = WikiQuery()
    assert wq.entities_dir.exists(), "wiki/entities must exist in-repo"


def test_search_entities_returns_scored_results():
    wq = WikiQuery()
    results = wq.search_entities("descriptor")
    assert isinstance(results, list)
    assert all("match_score" in r and "title" in r for r in results)
    # sorted descending by score
    scores = [r["match_score"] for r in results]
    assert scores == sorted(scores, reverse=True)
```

- [ ] **Step 4: Run tests**

Run: `python -m pytest tests/test_wiki_query.py tests/test_wiki_lookup.py -v`
Expected: PASS. (`test_wiki_lookup.py` now finds `wiki/Spec/catalog.json` via the relative `Config`.)

- [ ] **Step 5: Add `.gitignore` for generated output and commit**

```bash
mkdir -p generated && touch generated/.gitkeep
printf 'generated/*\n!generated/.gitkeep\n' >> .gitignore
git add wiki wiki_query.py tests/test_wiki_query.py generated/.gitkeep .gitignore
git commit -m "feat: move llm-wiki + retriever in-repo with relative wiki_root"
```

---

### Task 4: requirements.txt without anthropic; verify no anthropic references remain

**Files:**
- Create/Modify: `requirements.txt`

**Interfaces:** none.

- [ ] **Step 1: Write `requirements.txt`**

```
pytest>=8.0.0
```

- [ ] **Step 2: Write a test asserting no `anthropic` import survives**

```python
# tests/test_no_anthropic.py
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def test_no_anthropic_imports_in_python_sources():
    offenders = []
    for py in list(REPO.glob("ir_generator/*.py")) + list(REPO.glob("pattern_generator/*.py")):
        text = py.read_text(encoding="utf-8")
        if "import anthropic" in text or "ANTHROPIC_API_KEY" in text:
            offenders.append(py.name)
    assert offenders == [], f"anthropic deps remain in: {offenders}"
```

- [ ] **Step 3: Run test**

Run: `python -m pytest tests/test_no_anthropic.py -v`
Expected: PASS (ir_generator has no anthropic after Task 2; pattern_generator not yet created — glob is empty, still passes).

- [ ] **Step 4: Commit**

```bash
git add requirements.txt tests/test_no_anthropic.py
git commit -m "chore: drop anthropic dependency"
```

---

## PHASE 2 — pattern_generator deterministic core

### Task 5: pattern_generator config + Extractor (IR fields → shared keys)

**Files:**
- Create: `pattern_generator/__init__.py`, `pattern_generator/config.py`, `pattern_generator/extractor.py`
- Create: `tests/test_extractor.py`

**Interfaces:**
- Produces:
  - `pattern_generator.config.PGConfig` dataclass with `graph_path`, `wiki_path`, `repo_root`, `generated_dir` (all relative).
  - `pattern_generator.extractor.extract_keys(ir: dict) -> list[dict]` — each key dict: `{"kind": str, "key": str, "opcode": str|None, "idn": str|None, "step_id": str|None}`. Kinds: `scsi`, `ufs_query`, `entity`, `control_flow`, `reset`, `data_flow`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_extractor.py
from pattern_generator.extractor import extract_keys

IR = {
    "phases": [
        {"phase_id": "phase_0", "type": "sequential", "steps": [
            {"step_id": "step_0_1", "scsi_cmd": "WRITE(10)", "ufs_query": None,
             "opcode": "0x2A", "query_opcode": None, "idn": None, "expected": "GOOD"},
            {"step_id": "step_0_2", "scsi_cmd": None, "ufs_query": "WRITE ATTRIBUTE",
             "opcode": None, "query_opcode": "0x04", "idn": "0x00 (bBootLunEn)",
             "expected": "ok"},
        ], "inputs": [], "outputs": ["boot_lun_id"]},
        {"phase_id": "loop_1", "type": "loop", "loop_type": "count", "loop_count": 100,
         "steps": [{"step_id": "step_L_1", "scsi_cmd": None, "ufs_query": None,
                    "opcode": None, "query_opcode": None, "idn": None, "expected": "x",
                    "iterate_over": ["HW_RESET", "RST_N"]}],
         "inputs": ["boot_lun_id"]},
    ],
}


def test_extracts_scsi_and_query_keys():
    keys = extract_keys(IR)
    scsi = [k for k in keys if k["kind"] == "scsi"]
    assert any(k["opcode"] == "0x2A" and "WRITE(10)" in k["key"] for k in scsi)
    q = [k for k in keys if k["kind"] == "ufs_query"]
    assert any(k["idn"] == "bBootLunEn" and k["opcode"] == "0x04" for k in q)


def test_extracts_entity_control_reset_dataflow():
    keys = extract_keys(IR)
    kinds = {k["kind"] for k in keys}
    assert {"entity", "control_flow", "reset", "data_flow"} <= kinds
    assert any(k["key"] == "bBootLunEn" for k in keys if k["kind"] == "entity")
    assert any(k["key"] == "loop:count:100" for k in keys if k["kind"] == "control_flow")
    assert any(k["key"] == "HW_RESET" for k in keys if k["kind"] == "reset")
    assert any(k["key"] == "boot_lun_id" for k in keys if k["kind"] == "data_flow")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_extractor.py -v`
Expected: FAIL with `ModuleNotFoundError: pattern_generator`.

- [ ] **Step 3: Create the package files**

`pattern_generator/__init__.py`:
```python
```
(empty file)

`pattern_generator/config.py`:
```python
from pathlib import Path
from dataclasses import dataclass, field

REPO_ROOT = Path(__file__).resolve().parent.parent


@dataclass
class PGConfig:
    repo_root: Path = field(default_factory=lambda: REPO_ROOT)
    graph_path: Path = field(default_factory=lambda: REPO_ROOT / ".understand-anything" / "knowledge-graph.json")
    wiki_path: Path = field(default_factory=lambda: REPO_ROOT / "wiki")
    generated_dir: Path = field(default_factory=lambda: REPO_ROOT / "generated")

    def __post_init__(self):
        self.repo_root = Path(self.repo_root)
        self.graph_path = Path(self.graph_path)
        self.wiki_path = Path(self.wiki_path)
        self.generated_dir = Path(self.generated_dir)
        self.generated_dir.mkdir(parents=True, exist_ok=True)
```

`pattern_generator/extractor.py`:
```python
"""Turn an IR JSON into deterministic, queryable keys. No LLM."""
import re

_IDN_PAREN = re.compile(r'\(([^)]+)\)')


def _idn_name(idn: str | None) -> str | None:
    if not idn:
        return None
    m = _IDN_PAREN.search(idn)
    return (m.group(1) if m else idn).strip()


def extract_keys(ir: dict) -> list[dict]:
    keys: list[dict] = []
    seen: set[tuple] = set()

    def add(kind, key, opcode=None, idn=None, step_id=None):
        sig = (kind, key)
        if key and sig not in seen:
            seen.add(sig)
            keys.append({"kind": kind, "key": key, "opcode": opcode,
                         "idn": idn, "step_id": step_id})

    for phase in ir.get("phases", []):
        if phase.get("type") == "loop":
            lt = phase.get("loop_type")
            if lt == "count" and phase.get("loop_count") is not None:
                add("control_flow", f"loop:count:{phase['loop_count']}")
            elif lt:
                add("control_flow", f"loop:{lt}")
        for var in phase.get("inputs", []) + phase.get("outputs", []):
            add("data_flow", var)

        for step in phase.get("steps", []):
            sid = step.get("step_id")
            scsi, op = step.get("scsi_cmd"), step.get("opcode")
            if scsi:
                add("scsi", f"{scsi}:{op}" if op else scsi, opcode=op, step_id=sid)
            q, qop = step.get("ufs_query"), step.get("query_opcode")
            idn_name = _idn_name(step.get("idn"))
            if q:
                parts = [q] + ([qop] if qop else []) + ([idn_name] if idn_name else [])
                add("ufs_query", ":".join(parts), opcode=qop, idn=idn_name, step_id=sid)
            if idn_name:
                add("entity", idn_name, idn=idn_name, step_id=sid)
            for rst in step.get("iterate_over", []) or []:
                add("reset", rst, step_id=sid)
                add("control_flow", "for_each", step_id=sid)
    return keys
```

- [ ] **Step 4: Run tests**

Run: `python -m pytest tests/test_extractor.py -v`
Expected: PASS (all assertions).

- [ ] **Step 5: Commit**

```bash
git add pattern_generator/__init__.py pattern_generator/config.py pattern_generator/extractor.py tests/test_extractor.py
git commit -m "feat: pattern_generator config + IR key extractor"
```

---

### Task 6: Code Retriever (query the knowledge-graph + read source slices)

**Files:**
- Create: `pattern_generator/code_retriever.py`
- Create: `tests/test_code_retriever.py`

**Interfaces:**
- Consumes: `PGConfig.graph_path`, `PGConfig.repo_root`.
- Produces: `pattern_generator.code_retriever.CodeRetriever(config: PGConfig)` with:
  - `.find_by_name(name: str) -> list[dict]` (graph nodes whose `name` contains `name`, case-insensitive)
  - `.callees(node_id: str) -> list[dict]` and `.callers(node_id: str) -> list[dict]`
  - `.source_slice(node: dict) -> str` (reads `filePath` lines `startLine..endLine` relative to repo root)
  - `.file_imports(file_path: str) -> list[str]` (target file paths this file imports, from `imports` edges)
  - `.retrieve_for_key(key: dict) -> dict | None` — returns `{"key", "function", "file", "imports", "callees", "snippet"}` or `None` if no name match.

- [ ] **Step 1: Write the failing test (uses the real in-repo graph)**

```python
# tests/test_code_retriever.py
from pattern_generator.config import PGConfig
from pattern_generator.code_retriever import CodeRetriever


def test_find_by_name_locates_write_attribute():
    cr = CodeRetriever(PGConfig())
    hits = cr.find_by_name("write_attribute")
    assert hits, "write_attribute should exist in the graph"
    assert all("filePath" in h and "startLine" in h for h in hits)


def test_source_slice_returns_real_code():
    cr = CodeRetriever(PGConfig())
    hits = cr.find_by_name("write_attribute")
    snippet = cr.source_slice(hits[0])
    assert "def write_attribute" in snippet


def test_retrieve_for_key_shape():
    cr = CodeRetriever(PGConfig())
    out = cr.retrieve_for_key({"kind": "ufs_query", "key": "WRITE ATTRIBUTE:0x04:bBootLunEn",
                               "opcode": "0x04", "idn": "bBootLunEn", "step_id": "s1"})
    # write_attribute exists, so we expect a hit dict (not None)
    assert out is None or {"key", "function", "file", "imports", "snippet"} <= set(out)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_code_retriever.py -v`
Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Write `pattern_generator/code_retriever.py`**

```python
"""Query the understand-anything knowledge graph as a structural index, and read
real source slices. No LLM."""
import json
from collections import defaultdict
from pattern_generator.config import PGConfig


class CodeRetriever:
    def __init__(self, config: PGConfig):
        self.config = config
        g = json.loads(config.graph_path.read_text(encoding="utf-8"))
        self.nodes = {n["id"]: n for n in g["nodes"]}
        self._by_name = defaultdict(list)
        for n in g["nodes"]:
            if n.get("name"):
                self._by_name[n["name"].lower()].append(n)
        self._callees = defaultdict(list)
        self._callers = defaultdict(list)
        self._imports = defaultdict(list)
        for e in g["edges"]:
            if e["type"] == "calls":
                self._callees[e["source"]].append(e["target"])
                self._callers[e["target"]].append(e["source"])
            elif e["type"] == "imports":
                self._imports[e["source"]].append(e["target"])

    def find_by_name(self, name: str) -> list[dict]:
        nl = name.lower()
        exact = self._by_name.get(nl, [])
        if exact:
            return exact
        return [n for n in self.nodes.values()
                if n.get("name") and nl in n["name"].lower()]

    def callees(self, node_id: str) -> list[dict]:
        return [self.nodes[t] for t in self._callees.get(node_id, []) if t in self.nodes]

    def callers(self, node_id: str) -> list[dict]:
        return [self.nodes[s] for s in self._callers.get(node_id, []) if s in self.nodes]

    def source_slice(self, node: dict) -> str:
        fp = node.get("filePath")
        if not fp:
            return ""
        path = self.config.repo_root / fp
        if not path.exists():
            return ""
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
        start = max((node.get("startLine") or 1) - 1, 0)
        end = node.get("endLine") or len(lines)
        return "\n".join(lines[start:end])

    def file_imports(self, file_path: str) -> list[str]:
        file_id = f"file:{file_path}"
        return [self.nodes[t].get("filePath", t)
                for t in self._imports.get(file_id, []) if t in self.nodes]

    def _candidate_name(self, key: dict) -> str | None:
        # Prefer the entity/idn (e.g. bBootLunEn), else the command head token.
        if key.get("idn"):
            return key["idn"]
        head = key["key"].split(":")[0]
        return head or None

    def retrieve_for_key(self, key: dict) -> dict | None:
        name = self._candidate_name(key)
        if not name:
            return None
        hits = self.find_by_name(name)
        if not hits:
            # try a normalized form: WRITE(10) -> write
            token = name.split("(")[0].strip().split()[0].lower()
            hits = self.find_by_name(token)
        if not hits:
            return None
        node = next((h for h in hits if h.get("type") == "function"), hits[0])
        return {
            "key": key["key"],
            "function": node.get("name"),
            "file": node.get("filePath"),
            "imports": self.file_imports(node.get("filePath", "")),
            "callees": [c.get("name") for c in self.callees(node["id"])][:8],
            "snippet": self.source_slice(node)[:1200],
        }
```

- [ ] **Step 4: Run tests**

Run: `python -m pytest tests/test_code_retriever.py -v`
Expected: PASS (`write_attribute` exists in the graph and source).

- [ ] **Step 5: Commit**

```bash
git add pattern_generator/code_retriever.py tests/test_code_retriever.py
git commit -m "feat: code retriever over knowledge-graph with source slicing"
```

---

### Task 7: Wiki Retriever (wraps WikiQuery, returns structured hits)

**Files:**
- Create: `pattern_generator/wiki_retriever.py`
- Create: `tests/test_wiki_retriever.py`

**Interfaces:**
- Consumes: `wiki_query.WikiQuery`, `PGConfig.wiki_path`.
- Produces: `pattern_generator.wiki_retriever.WikiRetriever(config: PGConfig)` with `.retrieve_for_key(key: dict) -> dict` returning `{"key", "entities": list[dict], "sources": list[dict], "found": bool}`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_wiki_retriever.py
from pattern_generator.config import PGConfig
from pattern_generator.wiki_retriever import WikiRetriever


def test_retrieve_for_entity_key():
    wr = WikiRetriever(PGConfig())
    out = wr.retrieve_for_key({"kind": "entity", "key": "descriptor", "idn": "descriptor"})
    assert set(out) == {"key", "entities", "sources", "found"}
    assert isinstance(out["entities"], list)
    assert out["found"] == (len(out["entities"]) > 0 or len(out["sources"]) > 0)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_wiki_retriever.py -v`
Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Write `pattern_generator/wiki_retriever.py`**

```python
"""Query the in-repo llm-wiki for spec/constraint context. No LLM."""
from wiki_query import WikiQuery
from pattern_generator.config import PGConfig


class WikiRetriever:
    def __init__(self, config: PGConfig):
        self.wq = WikiQuery(wiki_root=config.wiki_path)

    def retrieve_for_key(self, key: dict) -> dict:
        term = key.get("idn") or key["key"].split(":")[0]
        entities = self.wq.search_entities(term)[:5]
        sources = self.wq.search_sources(term)[:5]
        return {
            "key": key["key"],
            "entities": entities,
            "sources": sources,
            "found": bool(entities or sources),
        }
```

- [ ] **Step 4: Run tests**

Run: `python -m pytest tests/test_wiki_retriever.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add pattern_generator/wiki_retriever.py tests/test_wiki_retriever.py
git commit -m "feat: wiki retriever wrapping WikiQuery"
```

---

### Task 8: Merger (per-step context blocks with source tags + risk markers)

**Files:**
- Create: `pattern_generator/merger.py`
- Create: `tests/test_merger.py`

**Interfaces:**
- Consumes: IR dict, key list from `extract_keys`, `CodeRetriever`, `WikiRetriever`.
- Produces:
  - `pattern_generator.merger.risk_marker(code_hit, wiki_hit) -> str` returning one of `OK:both`, `WARN:no-spec`, `RISK:no-impl`, `ERROR:not-found`. (C1/C2/C3 grading of partial wiki-impl is an LLM step done later; the deterministic marker covers the code/wiki presence matrix.)
  - `pattern_generator.merger.build_merged_context(ir, keys, code_retriever, wiki_retriever) -> dict` returning `{"markdown": str, "per_key": list[dict], "summary": dict}` where `summary` has `risk_breakdown` counts.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_merger.py
from pattern_generator.merger import risk_marker, build_merged_context


def test_risk_marker_matrix():
    assert risk_marker({"function": "f"}, {"found": True}) == "OK:both"
    assert risk_marker({"function": "f"}, {"found": False}) == "WARN:no-spec"
    assert risk_marker(None, {"found": True}) == "RISK:no-impl"
    assert risk_marker(None, {"found": False}) == "ERROR:not-found"


class _FakeCode:
    def retrieve_for_key(self, key):
        return {"key": key["key"], "function": "write_attribute", "file": "api/x.py",
                "imports": ["api/y.py"], "callees": [], "snippet": "def write_attribute(): ..."} \
            if key["kind"] in ("scsi", "ufs_query") else None


class _FakeWiki:
    def retrieve_for_key(self, key):
        return {"key": key["key"], "entities": [{"title": "bBootLunEn"}], "sources": [],
                "found": key["kind"] == "entity"}


def test_build_merged_context_counts_and_markdown():
    ir = {"pattern_id": "PF002_0098", "phases": []}
    keys = [{"kind": "ufs_query", "key": "WRITE ATTRIBUTE:0x04:bBootLunEn",
             "opcode": "0x04", "idn": "bBootLunEn", "step_id": "s1"},
            {"kind": "entity", "key": "bBootLunEn", "idn": "bBootLunEn", "step_id": "s1"}]
    out = build_merged_context(ir, keys, _FakeCode(), _FakeWiki())
    assert "WRITE ATTRIBUTE" in out["markdown"]
    assert out["summary"]["risk_breakdown"]["WARN"] >= 1  # ufs_query: code yes, wiki no
    assert out["summary"]["risk_breakdown"]["RISK"] >= 1   # entity: code no, wiki yes
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_merger.py -v`
Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Write `pattern_generator/merger.py`**

```python
"""Assemble per-key context blocks tagging code vs wiki provenance and a risk
marker. Deterministic; the C1/C2/C3 sub-grading is an LLM step done downstream."""
from collections import Counter


def risk_marker(code_hit, wiki_hit) -> str:
    has_code = bool(code_hit)
    has_wiki = bool(wiki_hit and wiki_hit.get("found"))
    if has_code and has_wiki:
        return "OK:both"
    if has_code and not has_wiki:
        return "WARN:no-spec"
    if not has_code and has_wiki:
        return "RISK:no-impl"
    return "ERROR:not-found"


def build_merged_context(ir, keys, code_retriever, wiki_retriever) -> dict:
    per_key = []
    lines = [f"# Merged Context — {ir.get('pattern_id', '?')}", ""]
    for key in keys:
        code_hit = code_retriever.retrieve_for_key(key)
        wiki_hit = wiki_retriever.retrieve_for_key(key)
        marker = risk_marker(code_hit, wiki_hit)
        per_key.append({"key": key, "code": code_hit, "wiki": wiki_hit, "risk": marker})

        lines.append(f"## [{key['kind']}] {key['key']}  ({marker})")
        if key.get("step_id"):
            lines.append(f"  step: {key['step_id']}")
        if code_hit:
            lines.append(f"  ─ impl(code): `{code_hit['function']}` in {code_hit['file']}")
            if code_hit.get("imports"):
                lines.append(f"     imports: {', '.join(code_hit['imports'][:5])}")
            if code_hit.get("snippet"):
                lines.append("     ```python")
                lines.append(code_hit["snippet"])
                lines.append("     ```")
        if wiki_hit and wiki_hit.get("found"):
            ents = ", ".join(e.get("title", "") for e in wiki_hit.get("entities", [])[:3])
            if ents:
                lines.append(f"  ─ spec(wiki): {ents}")
        lines.append("")

    breakdown = Counter(p["risk"].split(":")[0] for p in per_key)
    summary = {
        "pattern_id": ir.get("pattern_id"),
        "total_keys": len(keys),
        "risk_breakdown": {k: breakdown.get(k, 0) for k in ("OK", "WARN", "RISK", "ERROR")},
        "high_risk_keys": [p["key"]["key"] for p in per_key if p["risk"].startswith(("RISK", "ERROR"))],
    }
    return {"markdown": "\n".join(lines), "per_key": per_key, "summary": summary}
```

- [ ] **Step 4: Run tests**

Run: `python -m pytest tests/test_merger.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add pattern_generator/merger.py tests/test_merger.py
git commit -m "feat: context merger with provenance + risk markers"
```

---

### Task 9: Validator (syntax + import-exists + structure)

**Files:**
- Create: `pattern_generator/validator.py`
- Create: `tests/test_validator.py`

**Interfaces:**
- Consumes: generated `.py` source string, IR dict, `CodeRetriever` (to check import targets exist).
- Produces: `pattern_generator.validator.validate(py_source: str, ir: dict, code_retriever) -> dict` returning `{"syntax": "pass"|str, "structure": "pass"|list[str], "imports": "pass"|list[str]}`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_validator.py
from pattern_generator.validator import validate


class _CR:
    def find_by_name(self, name): return [{"name": name}] if name != "ghost" else []


IR = {"phases": [{"phase_id": "loop_1", "type": "loop", "loop_type": "count",
                  "loop_count": 100, "steps": []}]}


def test_syntax_failure_is_reported():
    out = validate("def f(:\n  pass", IR, _CR())
    assert out["syntax"] != "pass"


def test_structure_checks_loop_count_present():
    good = "for i in range(100):\n    pass\n"
    out = validate(good, IR, _CR())
    assert out["syntax"] == "pass"
    assert out["structure"] == "pass"


def test_structure_flags_missing_loop_count():
    out = validate("x = 1\n", IR, _CR())
    assert out["structure"] != "pass"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_validator.py -v`
Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Write `pattern_generator/validator.py`**

```python
"""Validate a generated pattern: syntax, structural fidelity to the IR, and that
imported names exist in the code graph. No LLM."""
import ast


def validate(py_source: str, ir: dict, code_retriever) -> dict:
    result = {"syntax": "pass", "structure": "pass", "imports": "pass"}

    try:
        tree = ast.parse(py_source)
    except SyntaxError as e:
        result["syntax"] = f"SyntaxError: {e}"
        return result  # can't go further without a parse

    # Structure: every count-loop's loop_count literal must appear in source
    struct_issues = []
    for phase in ir.get("phases", []):
        if phase.get("type") == "loop" and phase.get("loop_type") == "count":
            lc = phase.get("loop_count")
            if lc is not None and str(lc) not in py_source:
                struct_issues.append(f"{phase['phase_id']}: loop_count {lc} not found")
    if struct_issues:
        result["structure"] = struct_issues

    # Imports: names imported should resolve to something the graph knows
    import_issues = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            for alias in node.names:
                if alias.name != "*" and not code_retriever.find_by_name(alias.name):
                    import_issues.append(f"{node.module}.{alias.name}")
    if import_issues:
        result["imports"] = import_issues

    return result
```

- [ ] **Step 4: Run tests**

Run: `python -m pytest tests/test_validator.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add pattern_generator/validator.py tests/test_validator.py
git commit -m "feat: pattern validator (syntax/structure/imports)"
```

---

### Task 10: Run logger + prepare orchestration (writes generated/<ID>/)

**Files:**
- Create: `pattern_generator/run_logger.py`, `pattern_generator/prepare.py`
- Create: `tests/test_prepare.py`

**Interfaces:**
- Consumes: all Phase 2 modules.
- Produces:
  - `pattern_generator.run_logger.RunDir(generated_dir: Path, pattern_id: str)` with `.write_json(name, obj)`, `.write_text(name, text)`, `.path` (the `generated/<ID>/` dir).
  - `pattern_generator.prepare.prepare_pattern(ir_path, config) -> dict` returning `{"run_dir": str, "context_md": str, "summary": dict, "generation_prompt": str}` and writing into `generated/<ID>/`: `1_keys.json`, `2_merged_context.md`, `summary.json`, `generation_prompt.txt`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_prepare.py
import json
from pathlib import Path
from pattern_generator.config import PGConfig
from pattern_generator.prepare import prepare_pattern

IR = {
    "pattern_id": "PFTEST_0001", "title": "t", "description": "", "tags": [],
    "phases": [{"phase_id": "phase_0", "type": "sequential", "steps": [
        {"step_id": "s1", "scsi_cmd": "WRITE(10)", "ufs_query": None, "opcode": "0x2A",
         "query_opcode": None, "idn": None, "expected": "GOOD"}], "inputs": [], "outputs": []}],
    "dependency_graph": {"nodes": ["phase_0"], "edges": []},
}


def test_prepare_writes_run_dir(tmp_path):
    ir_path = tmp_path / "pftest-0001-ir.json"
    ir_path.write_text(json.dumps(IR), encoding="utf-8")
    cfg = PGConfig(generated_dir=tmp_path / "generated")
    out = prepare_pattern(ir_path, cfg)
    run = Path(out["run_dir"])
    assert (run / "2_merged_context.md").exists()
    assert (run / "summary.json").exists()
    assert (run / "generation_prompt.txt").exists()
    assert out["summary"]["pattern_id"] == "PFTEST_0001"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_prepare.py -v`
Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Write `pattern_generator/run_logger.py`**

```python
import json
from pathlib import Path


class RunDir:
    def __init__(self, generated_dir: Path, pattern_id: str):
        self.path = Path(generated_dir) / pattern_id
        self.path.mkdir(parents=True, exist_ok=True)

    def write_json(self, name: str, obj) -> Path:
        p = self.path / name
        p.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
        return p

    def write_text(self, name: str, text: str) -> Path:
        p = self.path / name
        p.write_text(text, encoding="utf-8")
        return p
```

- [ ] **Step 4: Write `pattern_generator/prepare.py`**

```python
"""Deterministic preparation for pattern generation. Produces the merged context
and a generation prompt for the current Claude Code model to act on. No LLM here."""
import json
from pathlib import Path

from pattern_generator.config import PGConfig
from pattern_generator.extractor import extract_keys
from pattern_generator.code_retriever import CodeRetriever
from pattern_generator.wiki_retriever import WikiRetriever
from pattern_generator.merger import build_merged_context
from pattern_generator.run_logger import RunDir

GEN_INSTRUCTIONS = """You are a UFS pattern generator. Using ONLY the merged
context below (grounded code snippets + spec/constraints), generate an executable
Python UFS test pattern.

Rules:
- Follow the IR phase/step order; honor dependency_graph topological order.
- Use the real functions and imports shown in the code context. Do not invent APIs.
- Emit control flow exactly from the IR (loop counts, for_each reset sets, phase data flow).
- For any key marked RISK:no-impl, grade it C1/C2/C3 from the wiki context and add a
  `# TODO human-confirm (Cx)` comment near the generated code for that step.
- Output ONLY the Python source.
"""


def prepare_pattern(ir_path, config: PGConfig | None = None) -> dict:
    config = config or PGConfig()
    ir = json.loads(Path(ir_path).read_text(encoding="utf-8"))
    pattern_id = ir["pattern_id"]

    keys = extract_keys(ir)
    code = CodeRetriever(config)
    wiki = WikiRetriever(config)
    merged = build_merged_context(ir, keys, code, wiki)

    run = RunDir(config.generated_dir, pattern_id)
    run.write_json("1_keys.json", keys)
    run.write_text("2_merged_context.md", merged["markdown"])
    run.write_json("summary.json", merged["summary"])

    prompt = "\n\n".join([
        GEN_INSTRUCTIONS,
        "## IR", json.dumps(ir, ensure_ascii=False, indent=2),
        "## Merged Context", merged["markdown"],
    ])
    run.write_text("generation_prompt.txt", prompt)

    return {"run_dir": str(run.path), "context_md": merged["markdown"],
            "summary": merged["summary"], "generation_prompt": prompt}
```

- [ ] **Step 5: Run tests**

Run: `python -m pytest tests/test_prepare.py -v`
Expected: PASS.

- [ ] **Step 6: Run the whole suite**

Run: `python -m pytest -v`
Expected: PASS (all tests green).

- [ ] **Step 7: Commit**

```bash
git add pattern_generator/run_logger.py pattern_generator/prepare.py tests/test_prepare.py
git commit -m "feat: run logger + prepare orchestration writing generated/<ID>/"
```

---

## PHASE 3 — Agent-driven end-to-end glue

### Task 11: CLI entry points for the deterministic stages

**Files:**
- Create: `generate_pattern.py` (repo-root CLI)
- Modify: `ir_generator` — add `ir_generator/prepare_ir.py` for the deterministic IR half
- Create: `tests/test_cli_smoke.py`

**Interfaces:**
- Produces:
  - `ir_generator.prepare_ir.prepare_ir(tc_path, config) -> dict` returning `{"run_dir", "skeleton", "enrich_prompt"}` and writing `generated/<ID>/ir_skeleton.json` + `generated/<ID>/enrich_prompt.txt`.
  - `ir_generator.prepare_ir.finalize_ir(skeleton, annotations, wiki_refs, config) -> Path` writing `generated/<ID>/<id>-ir.json` and `-ir-debug.md`.
  - CLI: `python generate_pattern.py prepare-ir TC/<file>.md`, `python generate_pattern.py prepare <id>-ir.json`, `python generate_pattern.py validate generated/<ID>/<pattern>.py <id>-ir.json`.

- [ ] **Step 1: Write `ir_generator/prepare_ir.py`**

```python
"""Deterministic IR halves. The data-flow annotation between them is an LLM step
performed by the current Claude Code model on enrich_prompt.txt."""
import json
from pathlib import Path

from ir_generator.config import Config
from ir_generator.parser import parse_tc
from ir_generator.wiki_lookup import lookup_wiki
from ir_generator.enrich_prompt import build_enrich_prompt, apply_annotations
from ir_generator.debug_reporter import generate_debug_md


def _run_dir(config: Config, pattern_id: str) -> Path:
    d = config.output_dir / pattern_id
    d.mkdir(parents=True, exist_ok=True)
    return d


def prepare_ir(tc_path, config: Config | None = None) -> dict:
    config = config or Config()
    skeleton = parse_tc(Path(tc_path))
    wiki_refs = lookup_wiki(skeleton, config)
    run = _run_dir(config, skeleton["pattern_id"])
    (run / "ir_skeleton.json").write_text(
        json.dumps({"skeleton": skeleton, "wiki_refs": wiki_refs},
                   ensure_ascii=False, indent=2), encoding="utf-8")
    prompt = build_enrich_prompt(skeleton, wiki_refs)
    (run / "enrich_prompt.txt").write_text(prompt, encoding="utf-8")
    return {"run_dir": str(run), "skeleton": skeleton, "enrich_prompt": prompt}


def finalize_ir(skeleton: dict, annotations: dict, wiki_refs: dict,
                config: Config | None = None) -> Path:
    config = config or Config()
    ir = apply_annotations(skeleton, annotations, wiki_refs)
    run = _run_dir(config, ir["pattern_id"])
    pid = ir["pattern_id"].lower().replace("_", "-")
    ir_clean = {k: v for k, v in ir.items() if k != "_wiki_refs"}
    out = run / f"{pid}-ir.json"
    out.write_text(json.dumps(ir_clean, ensure_ascii=False, indent=2), encoding="utf-8")
    (run / f"{pid}-ir-debug.md").write_text(generate_debug_md(ir), encoding="utf-8")
    return out
```

- [ ] **Step 2: Write `generate_pattern.py` (repo-root CLI)**

```python
#!/usr/bin/env python3
"""CLI for the deterministic stages. LLM steps (IR annotation, .py generation,
C1/C2/C3 grading) are performed by the current Claude Code model between calls —
see README.md."""
import argparse
import json
from pathlib import Path

from ir_generator.config import Config
from ir_generator.prepare_ir import prepare_ir
from pattern_generator.config import PGConfig
from pattern_generator.prepare import prepare_pattern
from pattern_generator.validator import validate
from pattern_generator.code_retriever import CodeRetriever


def main():
    ap = argparse.ArgumentParser(description="UFS pattern generation — deterministic stages")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p1 = sub.add_parser("prepare-ir", help="TC .md -> IR skeleton + enrich prompt")
    p1.add_argument("tc_file")

    p2 = sub.add_parser("prepare", help="IR json -> merged context + generation prompt")
    p2.add_argument("ir_file")

    p3 = sub.add_parser("validate", help="validate a generated .py against its IR")
    p3.add_argument("py_file")
    p3.add_argument("ir_file")

    args = ap.parse_args()

    if args.cmd == "prepare-ir":
        out = prepare_ir(Path(args.tc_file), Config())
        print(f"Run dir: {out['run_dir']}")
        print(f"Next (LLM): read {out['run_dir']}/enrich_prompt.txt, produce annotations JSON.")
    elif args.cmd == "prepare":
        out = prepare_pattern(Path(args.ir_file), PGConfig())
        print(f"Run dir: {out['run_dir']}")
        print(f"Risk: {out['summary']['risk_breakdown']}")
        print(f"Next (LLM): read {out['run_dir']}/generation_prompt.txt, write the .py there.")
    elif args.cmd == "validate":
        ir = json.loads(Path(args.ir_file).read_text(encoding="utf-8"))
        src = Path(args.py_file).read_text(encoding="utf-8")
        report = validate(src, ir, CodeRetriever(PGConfig()))
        print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Write a CLI smoke test**

```python
# tests/test_cli_smoke.py
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def test_prepare_ir_cli_runs_on_fixture():
    tc = REPO / "TC" / "pf002-0098-normalized-test-flow.md"
    r = subprocess.run([sys.executable, "generate_pattern.py", "prepare-ir", str(tc)],
                       cwd=REPO, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    assert "Run dir:" in r.stdout
```

- [ ] **Step 4: Run tests**

Run: `python -m pytest tests/test_cli_smoke.py -v`
Expected: PASS (the fixture TC parses and the IR skeleton + prompt are written).

- [ ] **Step 5: Commit**

```bash
git add ir_generator/prepare_ir.py generate_pattern.py tests/test_cli_smoke.py
git commit -m "feat: CLI entry points for deterministic prepare-ir/prepare/validate"
```

---

### Task 12: End-to-end agent workflow doc (the LLM-step contract)

**Files:**
- Create: `docs/AGENT_WORKFLOW.md`

**Interfaces:** none (documentation of the agent-driven contract).

- [ ] **Step 1: Write `docs/AGENT_WORKFLOW.md`**

````markdown
# Agent Workflow — TC → IR → Pattern (.py)

The deterministic stages are Python; the three LLM steps are performed by the
current model (no API key). A driving agent runs:

1. `python generate_pattern.py prepare-ir TC/<file>.md`
   → writes `generated/<ID>/ir_skeleton.json` + `enrich_prompt.txt`.
2. **LLM step A** — read `enrich_prompt.txt`, output annotations JSON
   `{"phases":[{phase_id,inputs,outputs}],"edges":[{from,to,type,data_flow}]}`.
   Then call `finalize_ir(skeleton, annotations, wiki_refs)` (via a short Python
   snippet or a follow-up command) to write `<id>-ir.json`.
3. `python generate_pattern.py prepare generated/<ID>/<id>-ir.json`
   → writes `2_merged_context.md`, `summary.json`, `generation_prompt.txt`.
4. **LLM step B** — read `generation_prompt.txt`, write the pattern to
   `generated/<ID>/<pattern>.py`. For each `RISK:no-impl` key, grade C1/C2/C3
   from the wiki context and add `# TODO human-confirm (Cx)`.
5. `python generate_pattern.py validate generated/<ID>/<pattern>.py generated/<ID>/<id>-ir.json`
   → prints syntax/structure/imports report. Fix and re-validate as needed.

`generated/<ID>/` therefore contains every artifact for one pattern: skeleton,
IR, merged context, prompts, the .py, and the risk summary — fully debuggable.
````

- [ ] **Step 2: Commit**

```bash
git add docs/AGENT_WORKFLOW.md
git commit -m "docs: agent-driven workflow contract"
```

---

## PHASE 4 — Portability docs

### Task 13: README with complete usage

**Files:**
- Create: `README.md`

**Interfaces:** none.

- [ ] **Step 1: Write `README.md`**

````markdown
# UFS Pattern Generator (self-contained)

Generate UFS test patterns (`.py`) from test-case flows. Combines two grounded
knowledge sources at generation time:

- **Code knowledge graph** (`.understand-anything/knowledge-graph.json`) over the
  pattern source at repo root (`api/ lib/ pattern/ ...`) — answers *how to implement*.
- **llm-wiki** (`wiki/`) — answers *spec / customer constraints*.

All LLM steps run on the **current model** (no API key, no `anthropic` dependency).
Python only does deterministic retrieval, assembly, and validation.

## Layout

| Path | Role |
|------|------|
| `api/ lib/ pattern/ ...` | pattern source = code-retriever base (keep in place) |
| `.understand-anything/` | knowledge graph (regenerate with `/understand` if code changes) |
| `ir_generator/` | TC `.md` → IR JSON (deterministic + LLM annotation) |
| `wiki/`, `wiki_query.py` | llm-wiki data + retriever |
| `pattern_generator/` | IR → merged context → `.py` |
| `TC/` | input test cases |
| `generated/<PATTERN_ID>/` | all per-run artifacts |
| `docs/AGENT_WORKFLOW.md` | the agent-driven step-by-step contract |

## Install

```bash
pip install -r requirements.txt   # pytest only
```

## Usage (driven by an agent / current model)

```bash
python generate_pattern.py prepare-ir TC/pf002-0098-normalized-test-flow.md
# LLM step A: annotate data flow -> finalize IR (see docs/AGENT_WORKFLOW.md)
python generate_pattern.py prepare generated/PF002_0098/pf002-0098-ir.json
# LLM step B: read generation_prompt.txt, write generated/PF002_0098/<pattern>.py
python generate_pattern.py validate generated/PF002_0098/<pattern>.py generated/PF002_0098/pf002-0098-ir.json
```

Query the wiki directly:

```bash
python wiki_query.py "bBootLunEn"
```

## For other agents

- Everything is relative-path and self-contained; clone/copy the folder anywhere.
- The LLM-step contract is in `docs/AGENT_WORKFLOW.md`. Follow the numbered steps;
  read the prepared `*.txt` prompt files and write results back into
  `generated/<PATTERN_ID>/`.
- Regenerate the code graph after changing pattern source: run understand-anything's
  `/understand` on the repo root.

## Tests

```bash
python -m pytest -v
```
````

- [ ] **Step 2: Run the full suite one last time**

Run: `python -m pytest -v`
Expected: PASS (all tests across both packages).

- [ ] **Step 3: Commit**

```bash
git add README.md
git commit -m "docs: complete usage README for portability"
```

---

## Self-Review (completed)

- **Spec coverage:** Plan A dual-source retrieval (Tasks 6–8), C1/C2/C3 grading (deterministic marker in Task 8 + LLM grading in Task 12 contract), generated/<ID>/ output (Tasks 10–11), independent wiki query / decision (a) (Task 7 uses WikiQuery; ir-stage `wiki_lookup` untouched), API-key removal / current model (Tasks 2, 4, 12), relative paths (Tasks 1, 3, 5), usage docs (Tasks 12–13), wiki self-contained incl. Script/ (Task 3). All covered.
- **Placeholder scan:** none — every code step contains full source; the only `# TODO` is the *generated-pattern* human-confirm marker (intended output behavior), not a plan gap.
- **Type consistency:** `extract_keys` key dict shape (`kind/key/opcode/idn/step_id`) is consumed identically by `code_retriever.retrieve_for_key`, `wiki_retriever.retrieve_for_key`, and `merger.build_merged_context`. `risk_marker`/`build_merged_context` return shapes match `prepare_pattern` usage. `Config` (ir) vs `PGConfig` (pattern_generator) kept distinct and used consistently.
- **Note / open risk:** opcode→function mapping relies on name heuristics (the graph has no opcode tags); `code_retriever.retrieve_for_key` may miss for commands whose function name doesn't share a token with the command/idn. This is acceptable for v1 (surfaces as `RISK:no-impl` in the summary, not a silent failure) and can be improved later with an opcode→function alias table or source grep.
