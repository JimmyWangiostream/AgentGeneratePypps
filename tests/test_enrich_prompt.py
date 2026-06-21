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
