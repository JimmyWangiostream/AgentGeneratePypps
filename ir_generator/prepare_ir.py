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
