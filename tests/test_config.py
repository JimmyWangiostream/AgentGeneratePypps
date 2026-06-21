from pathlib import Path
from ir_generator.config import Config, REPO_ROOT


def test_config_paths_are_inside_repo():
    cfg = Config()
    assert cfg.wiki_path == REPO_ROOT / "wiki"
    assert cfg.tc_dir == REPO_ROOT / "TC"
    assert cfg.output_dir == REPO_ROOT / "generated"
    # No absolute drive letters baked in
    assert "GME_AI" not in str(cfg.wiki_path) or cfg.wiki_path.is_relative_to(REPO_ROOT)
