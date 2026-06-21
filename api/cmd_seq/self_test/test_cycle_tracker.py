
from dataclasses import FrozenInstanceError
from Script.api.self_test.base import ApiTestBase
from Script import api
from Script.api import shared
import Script.api.cmd_seq as ExecuteCMD

from Script.api.cmd_seq._cycle_tracker import (
    CmdSeqFuncType,
    CycleIndicator,
    CycleTracker,
    PATTERN_ASSERT_CYCLE_TRACKER_FAIL_TASKTAG_SHALL_NOT_BE_NONE,
    PATTERN_ASSERT_CYCLE_TRACKER_FAIL_INVALID_TASKTAG_VALUE,
    PATTERN_ASSERT_CYCLE_TRACKER_FAIL_TASKTAG_SHALL_BE_NONE,
)


class TestCycleTracker(ApiTestBase):

    def setUp(self) -> None:
        self.tracker = CycleTracker()

    # -----------------------------
    # reset() 行為與初始狀態
    # -----------------------------
    def test_reset_initial_state(self) -> None:
        # 256 個 tasktag，初始為 -1
        self.assertEqual(len(self.tracker.tasktag_cycle), 256)
        self.assertTrue(all(v == -1 for v in self.tracker.tasktag_cycle))

        # cmdseq_func_cycle 長度為枚舉長度，初始為 -1
        self.assertEqual(len(self.tracker.cmdseq_func_cycle), len(CmdSeqFuncType))
        self.assertTrue(all(v == -1 for v in self.tracker.cmdseq_func_cycle))

    # -----------------------------
    # CycleIndicator frozen & 相等性
    # -----------------------------
    def test_cycle_indicator_frozen_and_equality(self) -> None:
        ind1 = CycleIndicator(cycle=0, func_type=CmdSeqFuncType.CMD_UPIU, tasktag=7)
        ind2 = CycleIndicator(cycle=0, func_type=CmdSeqFuncType.CMD_UPIU, tasktag=7)
        self.assertEqual(ind1, ind2)

        # frozen dataclass: 嘗試修改屬性應拋出 FrozenInstanceError
        with self.assertRaises(FrozenInstanceError):
            ind1.cycle = 5 # type: ignore

    # -----------------------------
    # get_cycle() 在 CMD_UPIU
    # -----------------------------
    def test_get_cycle_cmd_upiu_requires_tasktag(self) -> None:
        # 未提供 tasktag 應拋出「tasktag 不可為 None」
        with self.assertRaises(PATTERN_ASSERT_CYCLE_TRACKER_FAIL_TASKTAG_SHALL_NOT_BE_NONE):
            self.tracker.get_cycle(CmdSeqFuncType.CMD_UPIU, tasktag=None)

    def test_get_cycle_cmd_upiu_invalid_tasktag_value(self) -> None:
        # tasktag 負值
        with self.assertRaises(PATTERN_ASSERT_CYCLE_TRACKER_FAIL_INVALID_TASKTAG_VALUE):
            self.tracker.get_cycle(CmdSeqFuncType.CMD_UPIU, tasktag=-1)

        # tasktag 超過 255
        with self.assertRaises(PATTERN_ASSERT_CYCLE_TRACKER_FAIL_INVALID_TASKTAG_VALUE):
            self.tracker.get_cycle(CmdSeqFuncType.CMD_UPIU, tasktag=256)

    def test_get_cycle_cmd_upiu_initial_minus_one(self) -> None:
        ind = self.tracker.get_cycle(CmdSeqFuncType.CMD_UPIU, tasktag=0)
        self.assertEqual(ind.cycle, -1)
        self.assertEqual(ind.func_type, CmdSeqFuncType.CMD_UPIU)
        self.assertEqual(ind.tasktag, 0)

    # -----------------------------
    # get_cycle() 在非 CMD_UPIU
    # -----------------------------
    def test_get_cycle_non_cmd_upiu_requires_tasktag_none(self) -> None:
        # 提供 tasktag 應拋出「tasktag 應為 None」
        with self.assertRaises(PATTERN_ASSERT_CYCLE_TRACKER_FAIL_TASKTAG_SHALL_BE_NONE):
            self.tracker.get_cycle(CmdSeqFuncType.POWER_CYCLING, tasktag=3)

    def test_get_cycle_regular_enum_indexing(self) -> None:
        # 一般枚舉用 value 當索引
        ind = self.tracker.get_cycle(CmdSeqFuncType.POWER_CYCLING)
        self.assertEqual(ind.cycle, -1)
        self.assertEqual(ind.func_type, CmdSeqFuncType.POWER_CYCLING)
        self.assertEqual(ind.tasktag, -1)

    def test_get_cycle_dummy_response_indices(self) -> None:
        # DUMMY_RESPONSE_FOR_PREFETCH_HPB_WRITE_BUFFER -> len(Enum)-2
        ind_prefetch = self.tracker.get_cycle(
            CmdSeqFuncType.DUMMY_RESPONSE_FOR_PREFETCH_HPB_WRITE_BUFFER
        )
        self.assertEqual(ind_prefetch.cycle, -1)
        self.assertEqual(ind_prefetch.func_type, CmdSeqFuncType.DUMMY_RESPONSE_FOR_PREFETCH_HPB_WRITE_BUFFER)

        # DUMMY_RESPONSE_FOR_TASK_MGMT -> len(Enum)-1
        ind_taskmgmt = self.tracker.get_cycle(
            CmdSeqFuncType.DUMMY_RESPONSE_FOR_TASK_MGMT
        )
        self.assertEqual(ind_taskmgmt.cycle, -1)
        self.assertEqual(ind_taskmgmt.func_type, CmdSeqFuncType.DUMMY_RESPONSE_FOR_TASK_MGMT)

    # -----------------------------
    # increment_cycle() 在 CMD_UPIU
    # -----------------------------
    def test_increment_cycle_cmd_upiu_and_get_cycle(self) -> None:
        # 初始為 -1，呼叫 increment 後應為 0
        ind0 = self.tracker.increment_cycle(CmdSeqFuncType.CMD_UPIU, tasktag=10)
        self.assertEqual(ind0.cycle, 0)
        self.assertEqual(self.tracker.get_cycle(CmdSeqFuncType.CMD_UPIU, tasktag=10).cycle, 0)

        # 再次呼叫 increment，應為 1
        ind1 = self.tracker.increment_cycle(CmdSeqFuncType.CMD_UPIU, tasktag=10)
        self.assertEqual(ind1.cycle, 1)

    def test_increment_cycle_cmd_upiu_invalid_tasktag(self) -> None:
        with self.assertRaises(PATTERN_ASSERT_CYCLE_TRACKER_FAIL_INVALID_TASKTAG_VALUE):
            self.tracker.increment_cycle(CmdSeqFuncType.CMD_UPIU, tasktag=300)

    def test_increment_cycle_cmd_upiu_missing_tasktag(self) -> None:
        with self.assertRaises(PATTERN_ASSERT_CYCLE_TRACKER_FAIL_TASKTAG_SHALL_NOT_BE_NONE):
            self.tracker.increment_cycle(CmdSeqFuncType.CMD_UPIU, tasktag=None)

    # -----------------------------
    # increment_cycle() 在非 CMD_UPIU
    # -----------------------------
    def test_increment_cycle_non_cmd_upiu_requires_tasktag_none(self) -> None:
        with self.assertRaises(PATTERN_ASSERT_CYCLE_TRACKER_FAIL_TASKTAG_SHALL_BE_NONE):
            self.tracker.increment_cycle(CmdSeqFuncType.SWITCH_VOLTAGE, tasktag=1)

    def test_increment_cycle_regular_enum_indexing(self) -> None:
        # 初始 -1，increment 後應為 0
        ind0 = self.tracker.increment_cycle(CmdSeqFuncType.SWITCH_VOLTAGE)
        self.assertEqual(ind0.cycle, 0)
        # 再取一次，應為 0
        got = self.tracker.get_cycle(CmdSeqFuncType.SWITCH_VOLTAGE)
        self.assertEqual(got.cycle, 0)

        # 再 increment，應為 1
        ind1 = self.tracker.increment_cycle(CmdSeqFuncType.SWITCH_VOLTAGE)
        self.assertEqual(ind1.cycle, 1)

    def test_increment_cycle_dummy_response_indices(self) -> None:
        # len(Enum)-2 的 Prefetch Dummy
        ind_prefetch_0 = self.tracker.increment_cycle(
            CmdSeqFuncType.DUMMY_RESPONSE_FOR_PREFETCH_HPB_WRITE_BUFFER
        )
        self.assertEqual(ind_prefetch_0.cycle, 0)
        ind_prefetch_1 = self.tracker.increment_cycle(
            CmdSeqFuncType.DUMMY_RESPONSE_FOR_PREFETCH_HPB_WRITE_BUFFER
        )
        self.assertEqual(ind_prefetch_1.cycle, 1)

        # len(Enum)-1 的 TaskMgmt Dummy
        ind_task_0 = self.tracker.increment_cycle(
            CmdSeqFuncType.DUMMY_RESPONSE_FOR_TASK_MGMT
        )
        self.assertEqual(ind_task_0.cycle, 0)
        ind_task_1 = self.tracker.increment_cycle(
            CmdSeqFuncType.DUMMY_RESPONSE_FOR_TASK_MGMT
        )
        self.assertEqual(ind_task_1.cycle, 1)

    # -----------------------------
    # 多 tasktag 與多 func 的相互獨立性
    # -----------------------------
    def test_independent_counters_between_tasktags_and_funcs(self) -> None:
        # 兩個不同 tasktag 應互不影響
        self.tracker.increment_cycle(CmdSeqFuncType.CMD_UPIU, tasktag=1)  # -> 0
        self.tracker.increment_cycle(CmdSeqFuncType.CMD_UPIU, tasktag=2)  # -> 0
        self.tracker.increment_cycle(CmdSeqFuncType.CMD_UPIU, tasktag=1)  # -> 1

        self.assertEqual(self.tracker.get_cycle(CmdSeqFuncType.CMD_UPIU, tasktag=1).cycle, 1)
        self.assertEqual(self.tracker.get_cycle(CmdSeqFuncType.CMD_UPIU, tasktag=2).cycle, 0)

        # 不同 func 應互不影響
        self.tracker.increment_cycle(CmdSeqFuncType.SPEED_CHANGE)  # -> 0
        self.tracker.increment_cycle(CmdSeqFuncType.SWITCH_REFERENCE_CLOCK)  # -> 0
        self.tracker.increment_cycle(CmdSeqFuncType.SPEED_CHANGE)  # -> 1

        self.assertEqual(self.tracker.get_cycle(CmdSeqFuncType.SPEED_CHANGE).cycle, 1)
        self.assertEqual(self.tracker.get_cycle(CmdSeqFuncType.SWITCH_REFERENCE_CLOCK).cycle, 0)

    # -----------------------------
    # reset() 會把所有計數歸回 -1
    # -----------------------------
    def test_reset_after_increments(self) -> None:
        # 先做一些遞增
        self.tracker.increment_cycle(CmdSeqFuncType.CMD_UPIU, tasktag=5)
        self.tracker.increment_cycle(CmdSeqFuncType.SWITCH_VOLTAGE)
        self.tracker.increment_cycle(CmdSeqFuncType.DUMMY_RESPONSE_FOR_TASK_MGMT)

        self.tracker.reset()

        # 檢查全部回到 -1
        self.assertTrue(all(v == -1 for v in self.tracker.tasktag_cycle))
        self.assertTrue(all(v == -1 for v in self.tracker.cmdseq_func_cycle))
