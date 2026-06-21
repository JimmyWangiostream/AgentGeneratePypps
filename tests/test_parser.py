from pathlib import Path
from ir_generator.parser import parse_tc

FIXTURE = Path("tests/fixtures/pf002-0098-normalized-test-flow.md")


def test_parse_metadata():
    result = parse_tc(FIXTURE)
    assert result["pattern_id"] == "PF002_0098"
    assert "boot-lun" in result["tags"]
    assert result["description"] != ""


def test_parse_phase_count():
    result = parse_tc(FIXTURE)
    assert len(result["phases"]) == 3


def test_phase_0_is_sequential():
    result = parse_tc(FIXTURE)
    phase_0 = result["phases"][0]
    assert phase_0["phase_id"] == "phase_0"
    assert phase_0["type"] == "sequential"
    assert len(phase_0["steps"]) == 6


def test_loop_phase_detected():
    result = parse_tc(FIXTURE)
    loop = next(p for p in result["phases"] if p["type"] == "loop")
    assert loop["loop_type"] == "count"
    assert loop["loop_count"] == 100


def test_step_scsi_cmd_extracted():
    result = parse_tc(FIXTURE)
    step_0_1 = result["phases"][0]["steps"][0]
    assert step_0_1["step_id"] == "step_0_1"
    assert "TEST UNIT READY" in step_0_1["scsi_cmd"]
    assert step_0_1["opcode"] == "0x00"


def test_step_ufs_query_extracted():
    result = parse_tc(FIXTURE)
    step_0_2 = result["phases"][0]["steps"][1]
    assert step_0_2["ufs_query"] is not None
    assert step_0_2["scsi_cmd"] is None


def test_fail_condition_detected_on_condition_step():
    result = parse_tc(FIXTURE)
    phase_0 = result["phases"][0]
    step_0_5 = phase_0["steps"][4]
    assert step_0_5["fail_condition"] is not None
    assert step_0_5["on_fail"] == "abort"


def test_no_fail_condition_on_plain_step():
    result = parse_tc(FIXTURE)
    step_0_1 = result["phases"][0]["steps"][0]
    assert step_0_1["fail_condition"] is None
