import json
from pathlib import Path


class RunDir:
    def __init__(self, generated_dir: Path, pattern_id: str):
        self.path = Path(generated_dir) / pattern_id
        self.path.mkdir(parents=True, exist_ok=True)

    def write_json(self, name: str, obj) -> Path:
        p = self.path / name
        p.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
        return p

    def write_text(self, name: str, text: str) -> Path:
        p = self.path / name
        p.write_text(text, encoding="utf-8")
        return p
