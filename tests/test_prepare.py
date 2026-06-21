import json
from pathlib import Path
import pytest
from pattern_generator.config import PGConfig
from pattern_generator.prepare import prepare_pattern

# IR with two phases connected by a dependency edge: phase_0 -> phase_1.
# phase_1 is listed FIRST in the phases array so we can confirm topo order
# overrides natural list order (phase_0 must still come first).
IR_WITH_DEPS = {
    "pattern_id": "PFTEST_0001",
    "title": "Topo Test",
    "description": "Tests that phase_0 steps precede phase_1 steps",
    "tags": [],
    "phases": [
        {
            "phase_id": "phase_1",
            "name": "Second Phase",
            "type": "sequential",
            "loop_type": None,
            "loop_count": None,
            "steps": [
                {"step_id": "s2", "scsi_cmd": "READ(10)", "ufs_query": None,
                 "opcode": "0x28", "query_opcode": None, "idn": None, "expected": "GOOD"}
            ],
            "inputs": ["lun"],
            "outputs": [],
        },
        {
            "phase_id": "phase_0",
            "name": "First Phase",
            "type": "sequential",
            "loop_type": None,
            "loop_count": None,
            "steps": [
                {"step_id": "s1", "scsi_cmd": "WRITE(10)", "ufs_query": None,
                 "opcode": "0x2A", "query_opcode": None, "idn": None, "expected": "GOOD"}
            ],
            "inputs": [],
            "outputs": ["lun"],
        },
    ],
    "dependency_graph": {
        "nodes": ["phase_0", "phase_1"],
        "edges": [{"from": "phase_0", "to": "phase_1"}],
    },
}


def test_prepare_writes_steps_and_prompt(tmp_path):
    """prepare_pattern must write 1_steps.json and generation_prompt.txt."""
    ir_path = tmp_path / "pftest-0001-ir.json"
    ir_path.write_text(json.dumps(IR_WITH_DEPS), encoding="utf-8")
    cfg = PGConfig(generated_dir=tmp_path / "generated")
    out = prepare_pattern(ir_path, cfg)
    run = Path(out["run_dir"])
    assert (run / "1_steps.json").exists(), "1_steps.json must be written"
    assert (run / "generation_prompt.txt").exists(), "generation_prompt.txt must be written"


def test_prepare_returns_steps_and_prompt(tmp_path):
    """Return dict must contain steps list and generation_prompt string."""
    ir_path = tmp_path / "pftest-0001-ir.json"
    ir_path.write_text(json.dumps(IR_WITH_DEPS), encoding="utf-8")
    cfg = PGConfig(generated_dir=tmp_path / "generated")
    out = prepare_pattern(ir_path, cfg)
    assert isinstance(out["steps"], list)
    assert len(out["steps"]) == 2
    assert isinstance(out["generation_prompt"], str)
    assert "run_dir" in out


def test_steps_have_sequential_method_names(tmp_path):
    """Steps must be named step1, step2, ... in order."""
    ir_path = tmp_path / "pftest-0001-ir.json"
    ir_path.write_text(json.dumps(IR_WITH_DEPS), encoding="utf-8")
    cfg = PGConfig(generated_dir=tmp_path / "generated")
    out = prepare_pattern(ir_path, cfg)
    methods = [s["method"] for s in out["steps"]]
    assert methods == ["step1", "step2"]


def test_topological_order_respected(tmp_path):
    """phase_0 has no dependencies; phase_1 depends on phase_0.
    Despite phase_1 appearing first in the IR phases list, phase_0's step
    must appear as step1 (seq=1) and phase_1's step as step2 (seq=2)."""
    ir_path = tmp_path / "pftest-0001-ir.json"
    ir_path.write_text(json.dumps(IR_WITH_DEPS), encoding="utf-8")
    cfg = PGConfig(generated_dir=tmp_path / "generated")
    out = prepare_pattern(ir_path, cfg)
    steps = out["steps"]
    assert steps[0]["phase_id"] == "phase_0", (
        f"Expected phase_0 first but got {steps[0]['phase_id']}"
    )
    assert steps[1]["phase_id"] == "phase_1", (
        f"Expected phase_1 second but got {steps[1]['phase_id']}"
    )


def test_steps_json_on_disk_matches_return(tmp_path):
    """1_steps.json content must equal out['steps']."""
    ir_path = tmp_path / "pftest-0001-ir.json"
    ir_path.write_text(json.dumps(IR_WITH_DEPS), encoding="utf-8")
    cfg = PGConfig(generated_dir=tmp_path / "generated")
    out = prepare_pattern(ir_path, cfg)
    run = Path(out["run_dir"])
    on_disk = json.loads((run / "1_steps.json").read_text(encoding="utf-8"))
    assert on_disk == out["steps"]
