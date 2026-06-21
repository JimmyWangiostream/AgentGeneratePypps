"""Deterministic preparation for pattern generation. Walks the IR in topological
phase order, builds a per-step context plan, and produces a generation prompt for
the Claude Code model to act on. No LLM, no key extraction, no code retrieval."""
import json
from pathlib import Path

from pattern_generator.config import PGConfig
from pattern_generator.run_logger import RunDir
from pattern_generator.stepwise import ordered_steps, build_generation_prompt


def prepare_pattern(ir_path, config: PGConfig | None = None) -> dict:
    config = config or PGConfig()
    ir = json.loads(Path(ir_path).read_text(encoding="utf-8"))
    pattern_id = ir["pattern_id"]

    steps = ordered_steps(ir)
    prompt = build_generation_prompt(ir, steps)

    run = RunDir(config.generated_dir, pattern_id)
    run.write_json("1_steps.json", steps)
    run.write_text("generation_prompt.txt", prompt)

    return {"run_dir": str(run.path), "steps": steps, "generation_prompt": prompt}
