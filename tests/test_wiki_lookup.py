from ir_generator.config import Config
from ir_generator.wiki_lookup import lookup_wiki, extract_commands

FIXTURE_SKELETON = {
    "pattern_id": "PF002_0098",
    "phases": [
        {
            "phase_id": "phase_0",
            "type": "sequential",
            "steps": [
                {"scsi_cmd": "TEST UNIT READY", "ufs_query": None, "opcode": "0x00",
                 "query_opcode": None, "idn": None},
                {"scsi_cmd": None, "ufs_query": "READ DESCRIPTOR", "opcode": None,
                 "query_opcode": "0x07", "idn": "0x00 (Device Descriptor)"},
                {"scsi_cmd": None, "ufs_query": "READ ATTRIBUTE", "opcode": None,
                 "query_opcode": "0x03", "idn": "0x00 (bBootLunEn)"},
            ]
        }
    ]
}


def test_extract_commands_from_phase():
    phase = FIXTURE_SKELETON["phases"][0]
    terms = extract_commands(phase)
    assert any("test" in t or "ready" in t for t in terms)
    assert any("descriptor" in t or "read" in t for t in terms)


def test_lookup_returns_refs_per_phase():
    cfg = Config()
    refs = lookup_wiki(FIXTURE_SKELETON, cfg)
    assert "phase_0" in refs
    assert len(refs["phase_0"]) > 0


def test_lookup_ref_has_required_fields():
    cfg = Config()
    refs = lookup_wiki(FIXTURE_SKELETON, cfg)
    for ref in refs["phase_0"]:
        assert "title" in ref
        assert "file" in ref
        assert "excerpt" in ref


def test_read_attribute_matches_attributes_chapter():
    cfg = Config()
    refs = lookup_wiki(FIXTURE_SKELETON, cfg)
    files = [r["file"] for r in refs["phase_0"]]
    assert any("attribute" in f.lower() for f in files)


def test_uses_ingested_pages_not_spec_chapters():
    refs = lookup_wiki(FIXTURE_SKELETON, Config())
    files = [r["file"] for r in refs["phase_0"]]
    assert files, "phase_0 should match ingested pages"
    assert all(f.startswith(("entities/", "concepts/")) for f in files), files


def test_includes_conflict_resolved_overrides():
    refs = lookup_wiki(FIXTURE_SKELETON, Config())
    assert "__conflicts__" in refs
    assert "CustomerReq" in refs["__conflicts__"][0]["excerpt"]
