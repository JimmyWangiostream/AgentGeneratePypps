from pattern_generator.validator import validate


class _CR:
    def find_by_name(self, name): return [{"name": name}] if name != "ghost" else []


IR = {"phases": [{"phase_id": "loop_1", "type": "loop", "loop_type": "count",
                  "loop_count": 100, "steps": []}]}


def test_syntax_failure_is_reported():
    out = validate("def f(:\n  pass", IR, _CR())
    assert out["syntax"] != "pass"


def test_structure_checks_loop_count_present():
    good = "for i in range(100):\n    pass\n"
    out = validate(good, IR, _CR())
    assert out["syntax"] == "pass"
    assert out["structure"] == "pass"


def test_structure_flags_missing_loop_count():
    out = validate("x = 1\n", IR, _CR())
    assert out["structure"] != "pass"
