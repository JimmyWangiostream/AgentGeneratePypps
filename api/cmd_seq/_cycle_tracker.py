from dataclasses import dataclass
from enum import Enum, auto

from Script.api.exception import PATTERN_ASSERT_CYCLE_TRACKER_FAIL_INVALID_TASKTAG_VALUE, PATTERN_ASSERT_CYCLE_TRACKER_FAIL_TASKTAG_SHALL_BE_NONE, PATTERN_ASSERT_CYCLE_TRACKER_FAIL_TASKTAG_SHALL_NOT_BE_NONE

class CmdSeqFuncType(Enum):
    CMD_UPIU = 0x0
    POWER_CYCLING = 0x1
    SWITCH_VOLTAGE = 0x2
    SWITCH_REFERENCE_CLOCK = 0x3
    SPEED_CHANGE = 0x4
    INITIAL_FLOW = 0x5
    GPIO_TRIGGER = 0x6
    HIBERNATE = 0x7
    TEST_UNIT_READY = 0x8
    POWER_CONTROL = 0x9
    READY_DEVICE_INIT_FLAG = 0xA
    PUSH_NOP_OUT_AND_POLLING_NOP_IN = 0xB
    DUMMY_RESPONSE_FOR_PREFETCH_HPB_WRITE_BUFFER = 0xFD
    DUMMY_RESPONSE_FOR_TASK_MGMT = 0xFE

@dataclass(frozen=True)
class CycleIndicator:
    cycle: int = -1
    func_type: CmdSeqFuncType = CmdSeqFuncType.CMD_UPIU
    tasktag: int = -1

class CycleTracker:
    def __init__(self) -> None:
        self.tasktag_cycle: list[int]
        self.cmdseq_func_cycle: list[int]
        self.reset()
    
    def get_cycle(self, cmdseq_func: CmdSeqFuncType, tasktag:int | None = None) -> CycleIndicator:
        if cmdseq_func == CmdSeqFuncType.CMD_UPIU:
            if tasktag is None:
                raise PATTERN_ASSERT_CYCLE_TRACKER_FAIL_TASKTAG_SHALL_NOT_BE_NONE
            if tasktag > 255 or tasktag < 0:
                raise PATTERN_ASSERT_CYCLE_TRACKER_FAIL_INVALID_TASKTAG_VALUE
            return CycleIndicator(self.tasktag_cycle[tasktag], CmdSeqFuncType.CMD_UPIU, tasktag)
        else:
            if tasktag is not None:
                raise PATTERN_ASSERT_CYCLE_TRACKER_FAIL_TASKTAG_SHALL_BE_NONE
            if cmdseq_func == CmdSeqFuncType.DUMMY_RESPONSE_FOR_PREFETCH_HPB_WRITE_BUFFER:
                return CycleIndicator(self.cmdseq_func_cycle[len(CmdSeqFuncType) - 2], cmdseq_func)
            elif cmdseq_func == CmdSeqFuncType.DUMMY_RESPONSE_FOR_TASK_MGMT:
                return CycleIndicator(self.cmdseq_func_cycle[len(CmdSeqFuncType) - 1], cmdseq_func)
            else:
                return CycleIndicator(self.cmdseq_func_cycle[cmdseq_func.value], cmdseq_func)
        
    def increment_cycle(self, cmdseq_func: CmdSeqFuncType, tasktag:int | None = None) -> CycleIndicator:
        if cmdseq_func == CmdSeqFuncType.CMD_UPIU:
            if tasktag is None:
                raise PATTERN_ASSERT_CYCLE_TRACKER_FAIL_TASKTAG_SHALL_NOT_BE_NONE
            if tasktag > 255 or tasktag < 0:
                raise PATTERN_ASSERT_CYCLE_TRACKER_FAIL_INVALID_TASKTAG_VALUE
            self.tasktag_cycle[tasktag] += 1
        else:
            if tasktag is not None:
                raise PATTERN_ASSERT_CYCLE_TRACKER_FAIL_TASKTAG_SHALL_BE_NONE
            if cmdseq_func == CmdSeqFuncType.DUMMY_RESPONSE_FOR_PREFETCH_HPB_WRITE_BUFFER:
                self.cmdseq_func_cycle[len(CmdSeqFuncType) - 2] += 1
            elif cmdseq_func == CmdSeqFuncType.DUMMY_RESPONSE_FOR_TASK_MGMT:
                self.cmdseq_func_cycle[len(CmdSeqFuncType) - 1] += 1
            else:
                self.cmdseq_func_cycle[cmdseq_func.value] += 1

        return self.get_cycle(cmdseq_func, tasktag)

    def reset(self) -> None:
        self.tasktag_cycle = [-1] * 256
        self.cmdseq_func_cycle = [-1] * len(CmdSeqFuncType)