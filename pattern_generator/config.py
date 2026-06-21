from pathlib import Path
from dataclasses import dataclass, field

REPO_ROOT = Path(__file__).resolve().parent.parent


@dataclass
class PGConfig:
    repo_root: Path = field(default_factory=lambda: REPO_ROOT)
    graph_path: Path = field(default_factory=lambda: REPO_ROOT / ".understand-anything" / "knowledge-graph.json")
    wiki_path: Path = field(default_factory=lambda: REPO_ROOT / "wiki")
    generated_dir: Path = field(default_factory=lambda: REPO_ROOT / "generated")

    def __post_init__(self):
        self.repo_root = Path(self.repo_root)
        self.graph_path = Path(self.graph_path)
        self.wiki_path = Path(self.wiki_path)
        self.generated_dir = Path(self.generated_dir)
        self.generated_dir.mkdir(parents=True, exist_ok=True)
