"""Tests for pattern_generator.stepwise: topo_order_phases and ordered_steps."""
import pytest
from pattern_generator.stepwise import topo_order_phases, ordered_steps


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_phase(phase_id, steps=1, loop_type=None, loop_count=None,
                inputs=None, outputs=None, name=None, ptype="sequential"):
    return {
        "phase_id": phase_id,
        "name": name or phase_id,
        "type": ptype,
        "loop_type": loop_type,
        "loop_count": loop_count,
        "inputs": inputs or [],
        "outputs": outputs or [],
        "steps": [{"step_id": f"{phase_id}_s{i}"} for i in range(steps)],
    }


def _make_ir(phases, edges=None):
    return {
        "pattern_id": "TEST",
        "title": "test",
        "description": "",
        "phases": phases,
        "dependency_graph": {
            "nodes": [p["phase_id"] for p in phases],
            "edges": edges or [],
        },
    }


# ---------------------------------------------------------------------------
# topo_order_phases
# ---------------------------------------------------------------------------

class TestTopoOrderPhases:

    def test_no_edges_returns_natural_order(self):
        """With no dependency edges, phases come back in IR list order."""
        ir = _make_ir([_make_phase("a"), _make_phase("b"), _make_phase("c")])
        assert topo_order_phases(ir) == ["a", "b", "c"]

    def test_missing_dependency_graph_falls_back(self):
        """IR with no dependency_graph key returns natural order."""
        ir = {
            "pattern_id": "X",
            "phases": [_make_phase("x"), _make_phase("y")],
        }
        assert topo_order_phases(ir) == ["x", "y"]

    def test_empty_phases_returns_empty(self):
        ir = _make_ir([])
        assert topo_order_phases(ir) == []

    def test_single_edge_orders_dependency_first(self):
        """a -> b means a must come before b."""
        # Present b first in the list to prove topo overrides list order.
        ir = _make_ir(
            [_make_phase("b"), _make_phase("a")],
            edges=[{"from": "a", "to": "b"}],
        )
        order = topo_order_phases(ir)
        assert order.index("a") < order.index("b")

    def test_chain_a_b_c(self):
        """a -> b -> c: must come out [a, b, c]."""
        ir = _make_ir(
            [_make_phase("c"), _make_phase("b"), _make_phase("a")],
            edges=[{"from": "a", "to": "b"}, {"from": "b", "to": "c"}],
        )
        assert topo_order_phases(ir) == ["a", "b", "c"]

    def test_two_roots_converge(self):
        """a -> c and b -> c: a and b come before c (order between a/b not fixed)."""
        ir = _make_ir(
            [_make_phase("c"), _make_phase("b"), _make_phase("a")],
            edges=[{"from": "a", "to": "c"}, {"from": "b", "to": "c"}],
        )
        order = topo_order_phases(ir)
        assert order.index("a") < order.index("c")
        assert order.index("b") < order.index("c")

    def test_cycle_safety_all_phases_present(self):
        """Even with a cycle (a->b, b->a), all phase_ids appear in output."""
        ir = _make_ir(
            [_make_phase("a"), _make_phase("b")],
            edges=[{"from": "a", "to": "b"}, {"from": "b", "to": "a"}],
        )
        order = topo_order_phases(ir)
        assert set(order) == {"a", "b"}


# ---------------------------------------------------------------------------
# ordered_steps
# ---------------------------------------------------------------------------

class TestOrderedSteps:

    def test_empty_ir_returns_empty(self):
        ir = _make_ir([])
        assert ordered_steps(ir) == []

    def test_single_phase_single_step(self):
        ir = _make_ir([_make_phase("p0", steps=1)])
        steps = ordered_steps(ir)
        assert len(steps) == 1
        s = steps[0]
        assert s["seq"] == 1
        assert s["method"] == "step1"
        assert s["phase_id"] == "p0"

    def test_sequential_method_naming(self):
        """Three phases with 1 step each: method names step1, step2, step3."""
        ir = _make_ir([
            _make_phase("a", steps=1),
            _make_phase("b", steps=1),
            _make_phase("c", steps=1),
        ])
        steps = ordered_steps(ir)
        assert [s["method"] for s in steps] == ["step1", "step2", "step3"]
        assert [s["seq"] for s in steps] == [1, 2, 3]

    def test_multi_step_phase_flattens_correctly(self):
        """A phase with 3 steps produces 3 entries with consecutive seqs."""
        ir = _make_ir([_make_phase("p", steps=3)])
        steps = ordered_steps(ir)
        assert len(steps) == 3
        assert [s["method"] for s in steps] == ["step1", "step2", "step3"]
        assert all(s["phase_id"] == "p" for s in steps)

    def test_phase_context_carried_on_each_step(self):
        """Every step carries phase_name, phase_type, loop_type, loop_count,
        phase_inputs, phase_outputs."""
        ir = _make_ir([
            _make_phase("loop_ph", steps=2, ptype="loop",
                        loop_type="count", loop_count=50,
                        inputs=["lun"], outputs=["result"],
                        name="Stress Loop"),
        ])
        steps = ordered_steps(ir)
        for s in steps:
            assert s["phase_name"] == "Stress Loop"
            assert s["phase_type"] == "loop"
            assert s["loop_type"] == "count"
            assert s["loop_count"] == 50
            assert s["phase_inputs"] == ["lun"]
            assert s["phase_outputs"] == ["result"]

    def test_topological_order_in_ordered_steps(self):
        """phase_0 -> phase_1: phase_0's steps come before phase_1's steps
        even when phase_1 appears first in the phases list."""
        ir = _make_ir(
            [_make_phase("phase_1", steps=1), _make_phase("phase_0", steps=1)],
            edges=[{"from": "phase_0", "to": "phase_1"}],
        )
        steps = ordered_steps(ir)
        assert steps[0]["phase_id"] == "phase_0"
        assert steps[1]["phase_id"] == "phase_1"
        # method names must still be step1/step2 in emission order
        assert steps[0]["method"] == "step1"
        assert steps[1]["method"] == "step2"

    def test_step_payload_is_preserved(self):
        """The raw step dict from the IR must appear as steps[i]['step']."""
        raw_step = {"step_id": "s99", "scsi_cmd": "INQUIRY", "opcode": "0x12"}
        ir = _make_ir([{
            "phase_id": "p",
            "name": "p",
            "type": "sequential",
            "loop_type": None,
            "loop_count": None,
            "inputs": [],
            "outputs": [],
            "steps": [raw_step],
        }])
        steps = ordered_steps(ir)
        assert steps[0]["step"] == raw_step
