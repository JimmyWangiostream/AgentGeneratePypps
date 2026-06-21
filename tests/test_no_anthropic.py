from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def test_no_anthropic_imports_in_python_sources():
    offenders = []
    for py in list(REPO.glob("ir_generator/*.py")) + list(REPO.glob("pattern_generator/*.py")):
        text = py.read_text(encoding="utf-8")
        if "import anthropic" in text or "ANTHROPIC_API_KEY" in text:
            offenders.append(py.name)
    assert offenders == [], f"anthropic deps remain in: {offenders}"
