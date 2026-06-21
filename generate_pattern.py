#!/usr/bin/env python3
"""CLI for the deterministic stages. LLM steps (IR annotation, .py generation,
C1/C2/C3 grading) are performed by the current Claude Code model between calls —
see README.md."""
import argparse
import json
from pathlib import Path

from ir_generator.config import Config
from ir_generator.prepare_ir import prepare_ir, finalize_ir
from pattern_generator.config import PGConfig
from pattern_generator.prepare import prepare_pattern
from pattern_generator.validator import validate


def main():
    ap = argparse.ArgumentParser(description="UFS pattern generation — deterministic stages")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p1 = sub.add_parser("prepare-ir", help="TC .md -> IR skeleton + enrich prompt")
    p1.add_argument("tc_file")

    pf = sub.add_parser("finalize-ir",
                        help="ir_skeleton.json + annotations.json -> final <id>-ir.json (in folder)")
    pf.add_argument("skeleton_file", help="generated/<ID>/ir_skeleton.json from prepare-ir")
    pf.add_argument("annotations_file", help="annotations JSON produced by the LLM step")

    p2 = sub.add_parser("prepare", help="IR json -> step plan + generation prompt")
    p2.add_argument("ir_file")

    p3 = sub.add_parser("validate", help="validate a generated .py against its IR")
    p3.add_argument("py_file")
    p3.add_argument("ir_file")

    args = ap.parse_args()

    if args.cmd == "prepare-ir":
        out = prepare_ir(Path(args.tc_file), Config())
        print(f"Run dir: {out['run_dir']}")
        print(f"Next (LLM): read {out['run_dir']}/enrich_prompt.txt, produce annotations JSON.")
    elif args.cmd == "finalize-ir":
        bundle = json.loads(Path(args.skeleton_file).read_text(encoding="utf-8"))
        annotations = json.loads(Path(args.annotations_file).read_text(encoding="utf-8"))
        out = finalize_ir(bundle["skeleton"], annotations, bundle["wiki_refs"], Config())
        print(f"Final IR: {out}")
    elif args.cmd == "prepare":
        out = prepare_pattern(Path(args.ir_file), PGConfig())
        print(f"Run dir: {out['run_dir']}")
        print(f"Steps: {len(out['steps'])}")
        print(f"Next (LLM): read {out['run_dir']}/generation_prompt.txt, write the .py there.")
    elif args.cmd == "validate":
        ir = json.loads(Path(args.ir_file).read_text(encoding="utf-8"))
        src = Path(args.py_file).read_text(encoding="utf-8")
        # code_retriever=None skips import resolution (no code graph required)
        report = validate(src, ir, code_retriever=None)
        print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
