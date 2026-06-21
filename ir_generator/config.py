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
