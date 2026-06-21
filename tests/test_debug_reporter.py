from ir_generator.debug_reporter import generate_debug_md

ENRICHED_IR = {
    "pattern_id": "PF002_0098",
    "title": "Boot Stress Test",
    "description": "...",
    "tags": [],
    "phases": [
        {
            "phase_id": "phase_0", "name": "Boot LU 配置", "type": "sequential",
            "loop_type": None, "loop_count": None, "loop_condition": None,
            "inputs": [], "outputs": ["boot_lun_id"],
            "steps": [
                {"step_id": "step_0_5", "name": "確認已啟用",
                 "scsi_cmd": None, "ufs_query": "READ ATTRIBUTE",
                 "expected": "bBootLunEn != 0x00",
                 "fail_condition": "NOT (bBootLunEn != 0x00)", "on_fail": "abort",
                 "raw_content": ""}
            ]
        }
    ],
    "dependency_graph": {"nodes": ["phase_0"], "edges": []},
    "_wiki_refs": {
        "phase_0": [
            {"title": "14.3 Attributes", "file": "70_143_attributes.md",
             "excerpt": "Attributes define configurable parameters..."}
        ]
    }
}


def test_debug_md_contains_pattern_id():
    md = generate_debug_md(ENRICHED_IR)
    assert "PF002_0098" in md


def test_debug_md_contains_wiki_reference():
    md = generate_debug_md(ENRICHED_IR)
    assert "70_143_attributes.md" in md or "14.3 Attributes" in md


def test_debug_md_contains_fail_condition_section():
    md = generate_debug_md(ENRICHED_IR)
    assert "step_0_5" in md


def test_debug_md_contains_data_flow_section():
    md = generate_debug_md(ENRICHED_IR)
    assert "boot_lun_id" in md


def test_debug_md_is_valid_markdown():
    md = generate_debug_md(ENRICHED_IR)
    assert md.startswith("#")
    assert "##" in md
