import package_root
import time
from Script import api
from Script.api import cmd_seq as ExecuteCMD
from Script.api.util.functions import dumpfile
from Script.api.ufs_api.defines.enum_define import QueryResponseCode
from Script.pattern.pattern_template import UFSTC
from Script.pattern.pattern_logger import logger
from Script import project_api
from Script.api import shared
from Script.lib import sdk_lib as lib
import random

from Script.api.ufs_api import *
from Script.api.exception import *
from Script.api.ufs_api.rpmb.rpmb import RPMB
from Script.api.ufs_api.vendor_cmd.functions import *
from typing import cast
from Script.project_api.custom_vu.structs import get_nand_feature_format, set_nand_feature_format
from Script.project_api.custom_vu.mdwlsv_vu.structs import MDWLSV_format
import copy
from dataclasses import is_dataclass, asdict, fields
from Script.api.struct_helper import *
from typing import Any, Mapping, cast, List, Final
from typing import Any, Protocol, runtime_checkable, cast, TypeGuard
from typing import Any, cast, Mapping as TMapping, List, Final

#_sdk = shared.sdk
g_dict: Mapping[str, Any] = {}
OpenVBchangeList : dict[str, dict[str, Any]] = {}
diffopenvb_dict: dict[str, dict[str, Any]] = {}
RESET_COMMANDS: Final[Mapping[int, str]] = {
    0:      "hw_reset",      # Hardware Reset
    1:       "reset_n",       # Reset‑N
    2:  "endpoint_rst",  # Endpoint Reset
    3:    "unipro_rst",    # UniPro Reset
}
@runtime_checkable
class _HasValue(Protocol):
    value: Any
@runtime_checkable               # 讓 isinstance(obj, _DataclassLike) 在執行時成立

@runtime_checkable               # 讓 isinstance(obj, _DataclassLike) 在執行時成立
class _DataclassLike(Protocol):
    """
    只要物件有 ``__dataclass_fields__`` 屬性就算是 *dataclass‑like*。
    ``__dataclass_fields__`` 由 @dataclass 產生，型別是
    ``dict[str, dataclasses.Field]``，但我們只需要知道它是個字典，
    所以使用 ``dict[str, Any]`` 來描述即可。
    """
    __dataclass_fields__: dict[str, Any] 
class Pattern(UFSTC):
    def show_diff_open_vb_p2(
    self,
    open_vb_1: Any,
    open_vb_2: Any,
    lastclassname: str,
) -> bool:
        """
        比較兩個 *OpenVB* 物件（或任意結構）之間的差異。

        參數
        ----
        open_vb_1 / open_vb_2 : 任意物件
            只要能被 ``self._to_mapping`` 轉成 ``Mapping[str, Any]`` 即可。
        lastclassname : str
            用來在 log 中顯示「目前遞迴的類別名稱」。
            若傳入空字串，會先清空全域 ``OpenVBchangeList``。

        回傳值
        -------
        bool
            ``True`` 代表兩側完全相同，``False`` 代表至少有一處差異。
        """
        # -------------------------------------------------------------
        # 1️⃣ 重新初始化全域差異清單（只在最外層呼叫時執行）
        # -------------------------------------------------------------
        if lastclassname == "":
            OpenVBchangeList.clear()            # 這是您原本的全域 dict

        # -------------------------------------------------------------
        # 2️⃣ 把兩個物件都轉成 Mapping（key → value）
        # -------------------------------------------------------------
        dict1: Mapping[str, Any] = self._to_mapping(open_vb_1)
        dict2: Mapping[str, Any] = self._to_mapping(open_vb_2)

        # -------------------------------------------------------------
        # 3️⃣ 取得所有 key 的聯集，確保「只在其中一側」的情形也能被偵測
        # -------------------------------------------------------------
        all_keys = set(dict1) | set(dict2)

        all_equal = True   # 預設兩邊完全相同

        for key in all_keys:
            val1 = dict1.get(key)
            val2 = dict2.get(key)

            # ---------------------------------------------------------
            # a) 任一側缺少此 key → 視為差異
            # ---------------------------------------------------------
            if val1 is None or val2 is None:
                all_equal = False
                logger.info(
                    f"OpenVB change -> {lastclassname}.{key}: missing in one side"
                )
                continue

            # ---------------------------------------------------------
            # b) 兩側都是「BaseField」(或類似) 只比較 .value
            # ---------------------------------------------------------
            if isinstance(val1, _HasValue) and isinstance(val2, _HasValue):
                if val1.value != val2.value:
                    all_equal = False
                    logger.info(
                        f"OpenVB change -> {lastclassname}.{key}: "
                        f"0x{val1.value:x} != 0x{val2.value:x}"
                    )
                    # 把差異存到全域變數（保持您原有的行為）
                    OpenVBchangeList.setdefault(lastclassname, {})[key] = val2
                continue

            # ---------------------------------------------------------
            # c) 兩側皆為 Mapping（巢狀結構） → 使用遞迴比較
            # ---------------------------------------------------------
            #if isinstance(val1, Mapping) and isinstance(val2, Mapping):
            if isinstance(val1, OpenVBInfoUnit) and isinstance(val2, OpenVBInfoUnit):
                # 直接把 Mapping 傳下去，省去再一次 _to_mapping 的動作
                sub_equal = self.show_diff_open_vb_p2(val1, val2, key)
                if not sub_equal:
                    all_equal = False
                continue

            # ---------------------------------------------------------
            # d) 其他類型（純量、List、bytes、bool …）直接比較
            #    注意：若 key 為 'payload'（整段 bytearray），
            #    只要不相等就直接列印十六進位差異
            # ---------------------------------------------------------
            if key != "payload" and val1 != val2:
                all_equal = False
                # 把可能不是 int 的值安全轉成十六進位字串
                try:
                    hex1 = f"{int(val1):x}"
                    hex2 = f"{int(val2):x}"
                    logger.info(
                        f"OpenVB change -> {lastclassname}.{key}: 0x{hex1} != 0x{hex2}"
                    )
                except Exception:
                    logger.info(
                        f"OpenVB change -> {lastclassname}.{key}: {val1!r} != {val2!r}"
                    )
                OpenVBchangeList.setdefault(lastclassname, {})[key] = val2
                continue

            # 若是 key == "payload" 且值相同，就不需要再做任何事

        # -------------------------------------------------------------
        # 5️⃣ 回傳結果
        # -------------------------------------------------------------
        return all_equal

    def _hex_repr(self, data: bytes | bytearray) -> List[str]:
        """
        把 bytes/bytearray 轉成每個位元組的 2 位十六進位字串列表。
        例如 b'\x01\x0A' → ['01', '0A']
        """
        return [f"{b:02X}" for b in data]

    def show_diff_open_vb_p(self,
        vb1: "OpenVBInfo",
        vb2: "OpenVBInfo",
        title: str = "",
    ) -> bool:
        """
        顯示兩筆 OpenVBInfo (payload) 的差異。

        參數
        ----
        vb1, vb2 : OpenVBInfo
            需要比較的兩個物件。只要它們擁有 ``payload`` 屬性即可（bytearray）。
        title : str
            額外的說明文字，會放在最上方的 log 行，方便辨識是哪一次的比較。
        """
        # 取得 payload，若物件沒有 payload 則直接回報錯誤
        result = True
        if not hasattr(vb1, "payload") or not hasattr(vb2, "payload"):
            logger.error("show_diff_open_vb_p: 兩個物件皆必須有 'payload' 屬性")
            return False

        payload1: bytearray = vb1.payload.copy()
        payload2: bytearray = vb2.payload.copy()

        # 兩個 payload 長度不同會先補齊較短的，以免 IndexError
        max_len = max(len(payload1), len(payload2))
        p1 = payload1 + bytearray([0] * (max_len - len(payload1)))
        p2 = payload2 + bytearray([0] * (max_len - len(payload2)))

        # 產生十六進位字串列表，方便比對
        hex1 = self._hex_repr(p1)
        hex2 = self._hex_repr(p2)

        # 收集差異資訊
        diffs: List[Tuple[int, str, str]] = []   # (index, hex1, hex2)
        for idx, (h1, h2) in enumerate(zip(hex1, hex2)):
            if h1 != h2:
                diffs.append((idx, h1, h2))

        # ---- 輸出結果 -------------------------------------------------
        header = f"=== Diff OpenVBInfo ==="
        if title:
            header += f"  [{title}]"
        logger.info(header)

        if not diffs:
            logger.info("兩筆 payload 完全相同")
            return result

        logger.info(
            f"共找到 {len(diffs)} 個不相同的位元組 (index, vb1, vb2):"
        )
        # 為了不一次印太長，我們每 16 個位元組分段顯示
        for idx, h1, h2 in diffs:
            logger.info(f"  [{idx:04d}] {h1} != {h2}")
            result = False
        return result

        # 若需要一次把全部十六進位字串全部印出，可自行取消下列註解
        # logger.debug(f"vb1 payload (hex) : {' '.join(hex1)}")
        # logger.debug(f"vb2 payload (hex) : {' '.join(hex2)}")

    # def show_diff_open_vb_phison(self,open_vb_1: OpenVBInfo,open_vb_2: OpenVBInfo,) -> bool:
    #     # 清空前一次的差異紀錄
    #     diffopenvb_dict.clear()
    #     status = True


    #     units1 = self._collect_units(open_vb_1)
    #     units2 = self._collect_units(open_vb_2)

    #     # 逐一比較子單元 (key 為單元名稱，如 "SLC_L2")
    #     for unit_name in set(units1) | set(units2):
    #         unit1 = units1.get(unit_name)
    #         unit2 = units2.get(unit_name)

    #         # 若只有其中一個出現，直接視為不同
    #         if unit1 is None or unit2 is None:
    #             logger.info(f"OpenVBInfo change -> 單元缺失: {unit_name}")
    #             status = False
    #             continue

    #         # 兩個單元皆為 OpenVBInfoUnit，取得其欄位字典
    #         def _fields(obj: Any) -> Mapping[str, Any]:
    #             if is_dataclass(obj):
    #                 return cast(Mapping[str, Any], asdict(obj))
    #             return cast(Mapping[str, Any], vars(obj))

    #         fields1 = _fields(unit1)
    #         fields2 = _fields(unit2)

    #         # 比較欄位 (使用兩個單元的欄位聯集)
    #         for field_name in set(fields1) | set(fields2):
    #             f1 = fields1.get(field_name)
    #             f2 = fields2.get(field_name)

    #             # 若只有其中一個出現，同樣直接視為差異
    #             if f1 is None or f2 is None:
    #                 logger.info(
    #                     f"OpenVBInfo change -> {unit_name}.{field_name} 單側缺失"
    #                 )
    #                 status = False
    #                 continue

    #             # 只比較我們的 BaseField (具有 value、start_offset 等屬性)
    #             if isinstance(f1, BaseField) and isinstance(f2, BaseField):
    #                 if f1.value != f2.value:
    #                     logger.info(
    #                         f"OpenVB change -> {unit_name}.{field_name}: "
    #                         f"0x{hex(f1.value)!r} != 0x{hex(f2.value)!r}"
    #                     )
    #                     status = False
    #                     # 以 second 物件的值寫入 diff dict，鍵名保留「單元.欄位」的形式
    #                     diffopenvb_dict[f"{unit_name}.{field_name}"] = f2.value
    #             else:
    #                 # 若欄位不是 BaseField (可能是一般屬性) 直接使用等號比較
    #                 if f1 != f2:
    #                     logger.info(
    #                         f"OpenVB change -> {unit_name}.{field_name}: {f1!r} != {f2!r}"
    #                     )
    #                     status = False
    #                     diffopenvb_dict[f"{unit_name}.{field_name}"] = f2

    #     return status
    def debug_dataclass(self,obj: Any) -> Mapping[str, Any]:
        # 1️⃣ 確認 is_dataclass 判斷結果
        logger.info(f"is_dataclass? {is_dataclass(obj)}")

        # 2️⃣ 看看 __dataclass_fields__（若有的話）
        if hasattr(obj, '__dataclass_fields__'):
            logger.info(f"__dataclass_fields__: {obj.__dataclass_fields__}")

        # 3️⃣ 用 fields() 取得正式的 field list
        try:
            logger.info(f"dataclass fields (fields()): {[f.name for f in fields(obj)]}")
        except TypeError:
            logger.info("fields() 呼叫失敗（可能不是 dataclass）")

        # 4️⃣ 顯示 __dict__（若有的話）
        if hasattr(obj, '__dict__'):
            logger.info(f"__dict__: {obj.__dict__}")

        # 5️⃣ 顯示 __slots__（若有的話）
        if hasattr(obj, '__slots__'):
            logger.info(f"__slots__: {obj.__slots__}")

        # 6️⃣ 真正執行 asdict 並回傳
        return cast(Mapping[str, Any], asdict(obj))
    def _from_slots(self,obj: Any) -> dict[str, Any]:
        
        slot_names = getattr(obj, "__slots__", ())
        # __slots__ 可能是單一字串，統一轉成 tuple
        if isinstance(slot_names, str):
            slot_names = (slot_names,)

        result: dict[str, Any] = {}
        for name in slot_names:
            # 有的 slot 可能在實例化時根本沒被建立
            if hasattr(obj, name):
                result[name] = getattr(obj, name)
        return result
    def _parse_24_bytes(self,payload: bytes | bytearray) -> dict[str, int]:

        # 欄位名稱與在 payload 中的起始 offset
        fields = (
            ("logical_vb", 0),
            ("physical_vb", 4),
            ("first_empty_CE", 8),
            ("first_empty_plane", 12),
            ("first_empty_physical_page", 16),
            ("first_empty_node", 20),
        )
        return {
            name: int.from_bytes(payload[offset : offset + 4], "little")
            for name, offset in fields
        }
    def _parse_240_bytes(self, payload: bytes | bytearray) -> dict[str, dict[str, int]]:
       
        unit_names = (
            "SLC_L2",
            "WB",
            "TLC_L2",
            "TLC_L1",
            "SLC_GC",
            "TLC_GC",
            "PTE",
            "LOG",
            "SWAP",
            "SWAP_for_RAID",
        )

        result: dict[str, dict[str, int]] = {}
        for idx, name in enumerate(unit_names):
            start = idx * 24
            unit_payload = payload[start : start + 24]
            # 使用剛才的 24‑byte 解析函式
            result[name] = self._parse_24_bytes(unit_payload)

        return result
    @staticmethod
    def _is_dataclass_instance(obj: Any) -> TypeGuard[_DataclassLike]:
        """
        True → obj 被視為 dataclass‑instance（排除類別本身）。
        這樣 MyPy 會把 obj 縮減為 _DataclassLike，asdict 就能匹配。
        """
        return is_dataclass(obj) and not isinstance(obj, type)

    def _to_mapping(self, obj: Any) -> Mapping[str, Any]:
        """
        把任意物件轉成 Mapping[str, Any]（類似 dict）。
       處理順序：
            1️⃣ dataclass 實例 → asdict
            2️⃣ 已是 Mapping（dict、OrderedDict …） → 直接拷貝
            3️⃣ 有 __slots__ → 依 slots 產生 dict
            4️⃣ 有 __dict__ → 使用 vars()
        若全部不符合則拋 TypeError。
        """
        # 1️⃣ dataclass 實例（排除類別本身）
        if is_dataclass(obj) and not isinstance(obj, type):
            # asdict 只接受「實例」；此時 MyPy 能正確推斷型別
            return cast(TMapping[str, Any], asdict(obj))

        # 2️⃣ 已經是 Mapping（dict、OrderedDict …）
        if isinstance(obj, Mapping):
           return dict(obj)                     # -> dict[str, Any]

        # 4️⃣ 有 __dict__（最常見的普通類別）
        if hasattr(obj, "__dict__"):
            return dict(vars(obj))
        
        # 3️⃣ 有 __slots__ 的普通物件
        if hasattr(obj, "__slots__"):
            slots = getattr(obj, "__slots__")
            if isinstance(slots, str):
                slots = (slots,)
            return {slot: getattr(obj, slot) for slot in slots if hasattr(obj, slot)}


        # 5️⃣ 其餘類型無法轉成 Mapping
        raise TypeError(
            f"Object of type {type(obj)!r} cannot be converted to a Mapping."
        )
    # def _to_mapping(self, obj: Any) -> Mapping[str, Any]:
    #     """
    #     把任意物件轉成 Mapping[str, Any]（類似 dict）。
    #     依序嘗試:
    #         1. dataclass‑like → asdict
    #         2. 已是 Mapping（dict、OrderedDict…） → 直接拷貝
    #         3. 有 __slots__ → 依 slots 產生 dict
    #         4. 有 __dict__ → 使用 vars(obj)
    #     若全部不符合則拋 TypeError。
    #     """
    #     # 1️⃣ dataclass‑like（如果有此需求）
    #     if isinstance(obj, _DataclassLike):
    #         return cast(Mapping[str, Any], asdict(obj))

    #     # 2️⃣ 已經是 Mapping（dict 等）
    #     if isinstance(obj, Mapping):
    #         return dict(obj)                     # -> dict[str, Any]

    #     # 3️⃣ 有 __slots__ 的普通物件
    #     if hasattr(obj, "__slots__"):
    #         slots = getattr(obj, "__slots__")
    #         if isinstance(slots, str):
    #             slots = (slots,)
    #         return {slot: getattr(obj, slot) for slot in slots if hasattr(obj, slot)}

    #     # 4️⃣ 有 __dict__（最常見的普通類別）
    #     if hasattr(obj, "__dict__"):
    #         return dict(vars(obj))

    #     # 5️⃣ 其他類型無法轉成 Mapping
    #     raise TypeError(f"Object of type {type(obj)!r} cannot be converted to a Mapping.")

    # def _to_mapping_old(self, obj: Any) -> Mapping[str, Any]:
    #     result: dict[str, Any] = {}

    #     # 先取得 dataclass 欄位（即使是空的也沒關係）
    #     if is_dataclass(obj):
    #         result.update(cast(Mapping[str, Any], asdict(obj)))

    #     # 再看有沒有 payload，需要的話再把解析結果 merge 進去
    #     # if hasattr(obj, "payload"):
    #     #     payload = getattr(obj, "payload")
    #     #     if isinstance(payload, (bytes, bytearray)):
    #     #         if len(payload) == 24:
    #     #             result.update(self._parse_24_bytes(payload))
    #     #         elif len(payload) == 240:
    #     #             result.update(self._parse_240_bytes(payload))

    #     # 若 result 仍然是空，走其他 fallback（dict、__slots__、__dict__）
    #     if not result:
    #         if isinstance(obj, Mapping):
    #             result = dict(obj)
    #         if hasattr(obj, "__slots__"):
    #             result = dict(self._from_slots(obj))
    #         if hasattr(obj, "__dict__"):
    #             result = dict(vars(obj))

    #     return result

#     def show_diff_open_vb_p_old(
#     self,
#     open_vb_1: Any,   # 允許任意物件，內部會安全轉成 Mapping
#     open_vb_2: Any,
#     lastclassname: str,
# ) -> bool:
#         # 1️⃣ 先重置差異紀錄容器
#         #print(type(diffopenvb_dict))
#         if lastclassname == "":
#             OpenVBchangeList.clear()
#         dict1 = self._to_mapping(open_vb_1)
#         dict2 = self._to_mapping(open_vb_2)
#         # dict1: Mapping[str, Any] = _to_mapping(open_vb_1)
#         # dict2: Mapping[str, Any] = _to_mapping(open_vb_2)

#         # -------------------------------------------------------------
#         # 3️⃣ 取得所有鍵的聯集，確保「只在其中一側」的情形也能被偵測
#         # -------------------------------------------------------------
#         all_keys = set(dict1) | set(dict2)

#         all_equal = True  # 預設兩邊完全相同

#         for key in all_keys:
#             val1 = dict1.get(key)
#             val2 = dict2.get(key)

#             # ---------------------------------------------------------
#             #   a) 任一側缺少此鍵 → 直接視為差異
#             # ---------------------------------------------------------
#             if val1 is None or val2 is None:
#                 all_equal = False
#                 #diffopenvb_dict[key] = val2
#                 logger.info(f"OpenVB change -> {key}: missing in one side")
#                 continue

#             # ---------------------------------------------------------
#             #   b) BaseField（或其子類）直接比較 .value
#             # ---------------------------------------------------------
#             if isinstance(val1, BaseField) and isinstance(val2, BaseField):
#                 if val1.value != val2.value:
#                     all_equal = False
#                     logger.info(f"OpenVB change ->{lastclassname}.{key}: 0x{val1.value:x} != 0x{val2.value:x}")
#                     OpenVBchangeList.setdefault(lastclassname, {}).update({key: val2})
#                     # logger.info(
#                     #     f"OpenVB change -> {key}: 0x{val1.value:x} != 0x{val2.value:x}"
#                     # )
#                 continue

#             # ---------------------------------------------------------
#             #   c) 其他類型（可能是巢狀的 dataclass / object）遞迴比較
#             # ---------------------------------------------------------
#             if (is_dataclass(val1) and is_dataclass(val2)) or (
#                 isinstance(val1, Mapping) and isinstance(val2, Mapping)
#             ):
#                 sub_equal = self.show_diff_open_vb_p(val1, val2, key)
#                 if not sub_equal:
#                     all_equal = False
#                 continue

#             # ---------------------------------------------------------
#             #   d) 純量直接比較（int、str、bytes、bool …）
#             # ---------------------------------------------------------
#             if key != 'payload' and val1 != val2:
#                 all_equal = False
#                 logger.info(f"OpenVB change ->{lastclassname}.{key}: 0x{val1:x} != 0x{val2:x}")
#                 OpenVBchangeList.setdefault(lastclassname, {}).update({key: val2})

#         # ``all_equal`` 為 True 時表示 *沒有* 差異；若有差異則回傳 False
#         return all_equal
    # def show_diff_open_vb_p(self, open_vb_1: Any, open_vb_2: Any) -> bool:
    #     diffopenvb_dict.clear()
    #     status = True
    #     if is_dataclass(open_vb_1):
    #         dict1: Mapping[str, Any] = cast(Mapping[str, Any], asdict(open_vb_1))
    #     else:
    #         dict1 = cast(Mapping[str, Any], vars(open_vb_1))
    #     g_dict = dict1
    #     if is_dataclass(open_vb_2):
    #         dict2: Mapping[str, Any] = cast(Mapping[str, Any], asdict(open_vb_2))
    #     else:
    #         dict2 = cast(Mapping[str, Any], vars(open_vb_2))
    #     diff: List[str] = []
    #     # 取兩個 dict 的所有鍵的聯集，確保把「只在其中一個出現」的情況也列出
    #     for key in set(dict1) | set(dict2):
    #         print(type(dict1))
    #         print(type(key))
    #         print((key))
    #         print(type(dict1[key]))
    #         val1_obj = dict1.get(key)
    #         val2_obj = dict2.get(key)
    #         if(val1_obj is None or val2_obj is None):
    #             return True
    #         if isinstance(dict1[key], BaseField):
    #             if dict1[key].value != dict2[key].value:
    #                 logger.info(f"OpenVB change -> {key}: 0x{hex(dict1[key].value)!r} != 0x{hex(dict2[key].value)!r}")
    #                 status = False
    #                 diffopenvb_dict[key] = dict2[key].value
    #         else:
    #             self.show_diff_open_vb_p(dict1[key],dict2[key])


    #     return status

    # def show_diff_open_vb(self, open_vb_1: project_api.OpenVBInformation, open_vb_2: project_api.OpenVBInformation) -> bool:
    #     diffopenvb_dict.clear()
    #     status = True
    #     if is_dataclass(open_vb_1):
    #         dict1: Mapping[str, Any] = cast(Mapping[str, Any], asdict(open_vb_1))
    #     else:
    #         dict1 = cast(Mapping[str, Any], vars(open_vb_1))
    #     g_dict = dict1
    #     if is_dataclass(open_vb_2):
    #         dict2: Mapping[str, Any] = cast(Mapping[str, Any], asdict(open_vb_2))
    #     else:
    #         dict2 = cast(Mapping[str, Any], vars(open_vb_2))
    #     diff: List[str] = []
    #     # 取兩個 dict 的所有鍵的聯集，確保把「只在其中一個出現」的情況也列出
    #     for key in set(dict1) | set(dict2):
    #         val1_obj = dict1.get(key)
    #         val2_obj = dict2.get(key)
    #         if(val1_obj is None or val2_obj is None):
    #             return True
    #         if isinstance(dict1[key], BaseField):
    #             if dict1[key].value != dict2[key].value:
    #                 logger.info(f"OpenVB change -> {key}: 0x{hex(dict1[key].value)!r} != 0x{hex(dict2[key].value)!r}")
    #                 status = False
    #                 diffopenvb_dict[key] = dict2[key].value

    #     return status
    def tables_equal(self, tbl1: MDWLSV_format, tbl2: MDWLSV_format) -> bool:
        # if tbl1.Die0_MDWLSV_MM_OPEN_BLOCK_EM1_HOST_offset.value != tbl2.Die0_MDWLSV_MM_OPEN_BLOCK_EM1_HOST_offset.value:
        #     return False
        status = True
        # if is_dataclass(tbl1):
        #     dict1: Mapping[str, Any] = cast(Mapping[str, Any], asdict(tbl1))
        # else:
        #     dict1 = cast(Mapping[str, Any], vars(tbl1))

        # if is_dataclass(tbl2):
        #     dict2: Mapping[str, Any] = cast(Mapping[str, Any], asdict(tbl2))
        # else:
        #     dict2 = cast(Mapping[str, Any], vars(tbl2))

        # if is_dataclass(tbl1) and not isinstance(tbl1, type):
        #     dict1: TMapping[str, Any] = cast(TMapping[str, Any], asdict(tbl1))
        # else:
        #     # vars() 會回傳 obj.__dict__，對於非 dataclass 仍能得到屬性字典
        #     dict1 = cast(TMapping[str, Any], vars(tbl1))

        # if is_dataclass(tbl2) and not isinstance(tbl2, type):
        #     dict2: TMapping[str, Any] = cast(TMapping[str, Any], asdict(tbl2))
        # else:
        #     dict2 = cast(TMapping[str, Any], vars(tbl2))
        dict1 = cast(Mapping[str, Any], vars(tbl1))
        dict2 = cast(Mapping[str, Any], vars(tbl2))

        diff: List[str] = []
        # 取兩個 dict 的所有鍵的聯集，確保把「只在其中一個出現」的情況也列出
        for key in set(dict1) | set(dict2):
            print(type(dict1))
            print(type(key))
            print((key))
            print(type(dict1[key]))
            val1_obj = dict1.get(key)
            val2_obj = dict2.get(key)
            if(val1_obj is None or val2_obj is None):
                return True
            #if type(dict1[key]) not BaseField:
            if isinstance(dict1[key], BaseField):
                if dict1[key].value != dict2[key].value:
                    return False

            # val1 = dict1.get(key)
            # val2 = dict2.get(key)
            # if val1.value != val2.value:
            #     logger.info(f"{key}: {val1.value!r} != {val2!r}")
            #     diff.append(f"{key}: {val1!r} != {val2!r}")

        return True

    def pre_process(self) -> None:
        self.disableMDWLSV = 1
        self.EnableMDWLSV = 0
        self.write_record = api.get_empty_write_record()
        self.geometry_desc = api.get_geometry_descriptor()
        self.fw_geometry = api.get_fw_geometry()
        self.flash_setting = api.get_flash_setting()
        self.slc_vb_size = (self.fw_geometry.l84_vb_size_u0 * 512 // 4096)
        self.tlc_vb_size = (self.fw_geometry.l88_vb_size_u1 * 512 // 4096)
        self.TestNormalLun = 0
        self.TestBootA = 1
        self.TestBootB = 2
        self.TestEM1Lun = 3
        self.Total_AU_Count = self.geometry_desc.q4_total_raw_device_capacity / (self.geometry_desc.l13_segment_size * self.geometry_desc.b17_allocation_unit_size);
        #self.diffopenvb_dict: dict[str, Any]
        


    def step1(self) -> None:
        MDWLSV_SLC_L2 =0
        MDWLSV_TLC_L2 =1
        MDWLSV_PTE =2
        MDWLSV_LOG =3
        MDWLSV_EM1 =4
        MDWLSV_L1 =5
        MDWLSV_SLC_GC =6
        MDWLSV_TLC_GC =7
        MDWLSV_RAID_SWAP_SLC_L2_SLC =8
        MDWLSV_RAID_SWAP_TLC_L2_SLC =9
        MDWLSV_RAID_SWAP_TLC_L2_TLC =10
        MDWLSV_MODULE_CNT =11
        MDWLSV_INVALID =0xFF
        #disable media scan
        hw_setting = api.HwSetting.get_instance()
        hw_setting.update_from_device()
        medium_scan_setting_bk = hw_setting.get_local_val(api.HwSettingField.MEDIUM_SCAN_TRIGGER_TIME)
        hw_setting.set_to_device(field = api.HwSettingField.MEDIUM_SCAN_TRIGGER_TIME, val= 0x80)
        
        logger.flow(1, 'config lun and WB ,disable wb and wb flush')
        self.config_lun()
        _, open_vb_info = get_open_vb_info()
        self.print_open_vb_information_phison(open_vb_info)
        open_vb_1: OpenVBInfo = OpenVBInfo(open_vb_info.payload.copy())
        _, open_vb_info = get_open_vb_info()
        self.print_open_vb_information_phison(open_vb_info)
        open_vb_2: OpenVBInfo = OpenVBInfo(open_vb_info.payload.copy())
        self.show_diff_open_vb_p2(open_vb_1,open_vb_2,"")
        # logger.flow(9, 'Power Off')
        # cmd = ExecuteCMD.CmdSeqPowerCycle()
        # cmd.set_option(api.PowerCycleMode.ALL_POWER_DOWN)
        # idx = cmd.enqueue()
        # ExecuteCMD.send(clear_on_success=True) 

        # logger.flow(10, 'Power on')
        # cmd = ExecuteCMD.CmdSeqPowerControl()
        # cmd.set_option(mode=1, channel=1, spendtime=0, ramptime=0, delay_time=100)
        # idx = cmd.enqueue()
        # ExecuteCMD.send(clear_on_success=True)
        # cmd = ExecuteCMD.CmdSeqPowerControl()
        # cmd.set_option(mode=1, channel=2, spendtime=0, ramptime=0, delay_time=100)
        # idx = cmd.enqueue()
        # ExecuteCMD.send(clear_on_success=True)
        # cmd = ExecuteCMD.CmdSeqPowerControl()
        # cmd.set_option(mode=1, channel=3, spendtime=0, ramptime=0, delay_time=100)
        # idx = cmd.enqueue()
        # ExecuteCMD.send(clear_on_success=True)
        # logger.flow(11, 'link start up')
        # cmd = ExecuteCMD.CmdSeqPowerCycle()
        # cmd.set_option(api.PowerCycleMode.LINK_START_UP)
        # idx = cmd.enqueue()
        # ExecuteCMD.send(clear_on_success=True) 
        # cmd = ExecuteCMD.CmdSeqPushNopOutPollNopIn()
        # cmd.set_option(timeout=10000000)
        # idx = cmd.enqueue()
        # ExecuteCMD.send(clear_on_success=True)

        
        api.clear_flag(idn=api.FlagIDN.WRITEBOOSTER_EN)
        api.clear_flag(idn=api.FlagIDN.WRITEBOOSTER_BUFFER_FLUSH_EN)
        api.clear_flag(idn=api.FlagIDN.WRITEBOOSTER_BUFFER_FLUSH_DURING_HIBERNATE)

        # logger.flow(1-1, 'Host issue VU 0xD0FD with value 0x00-disable all the background operations')
        # project_api.issue_D0FD_en_disable_BKOPS(bValue = 0x00)
        wlsv_default = 0
        write10 = ExecuteCMD.Write10()
        cur_lba = 0
        tlc_ce_page = self.flash_setting.Plane_Per_Die * 4 * 3
        logger.info(f'tlc_ce_page = {tlc_ce_page}')
        write_len = 1
        logger.flow(2, 'write 1 tlc CE page size on normal LUN')
        write10.assign(lun=self.TestNormalLun, lba=cur_lba, length=tlc_ce_page, fua=1)
        ExecuteCMD.enqueue(write10)
        ExecuteCMD.send(clear_on_success=True)
        response, data_payload = project_api.issue_4022_to_get_NAND_feature(0,0x7F)
        project_api.print_array_tohex(data_payload,60, 4)
        get_nand_feature = self.assign_get_nand_feature_info(data_payload)
        tlcL2_get_nand_feature: get_nand_feature_format = get_nand_feature_format(get_nand_feature.payload.copy())
        rsp, previos_payload = get_previous_info()
        project_api.print_array_tohex(previos_payload,60, 4)
        if previos_payload[0] == MDWLSV_TLC_L2:
            check_tlcl2 = True
        else:
            check_tlcl2 = False
        logger.flow(3, 'write 1 lba size on EM1 LUN')
        write10.assign(lun=self.TestEM1Lun, lba=cur_lba, length=write_len, fua=1)
        ExecuteCMD.enqueue(write10)
        ExecuteCMD.send(clear_on_success=True)

        response, data_payload = project_api.issue_4022_to_get_NAND_feature(0,0x7F)
        project_api.print_array_tohex(data_payload,60, 4)
        get_nand_feature = self.assign_get_nand_feature_info(data_payload)
        EM1_get_nand_feature: get_nand_feature_format = get_nand_feature_format(get_nand_feature.payload.copy())
        rsp, previos_payload = get_previous_info()
        project_api.print_array_tohex(previos_payload,60, 4)
        if previos_payload[0] == MDWLSV_EM1:
            check_EM1 = True
        else:
            check_EM1 = False
        logger.info('VU 0x4029 get MDWLSV Offset')
        response, data_payload = project_api.issue_4029_to_get_MDWLSV_offset_information()  
        project_api.print_array_tohex(data_payload,60, 4)
        MDWLSV_info = self.assign_MDWLSV_info(data_payload)
        logger.info(f'Die0_MDWLSV_SM_OPEN_BLOCK_NOMAL_HOST_TLC_offset = {MDWLSV_info.Die0_MDWLSV_SM_OPEN_BLOCK_NOMAL_HOST_TLC_offset.value}')
        if check_tlcl2 is True:
            if MDWLSV_info.Die0_MDWLSV_SM_OPEN_BLOCK_NOMAL_HOST_TLC_offset.value == wlsv_default or MDWLSV_info.Die0_MDWLSV_SM_OPEN_BLOCK_NOMAL_HOST_TLC_offset.value != tlcL2_get_nand_feature.P3.value:
                logger.error_lb(f'write tlc l2 , then write em1 l2')
                logger.error_fp(f'expect tlc l2 has wlsv offset and equal to P3 ={tlcL2_get_nand_feature.P3.value}, result Fail!')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        else:
            logger.error_fp(f'expect tlc l2 has wlsv offset, result Fail, due to internal program!')
        # response, data_payload = project_api.issue_4022_to_get_NAND_feature(0,0x7F)
        # project_api.print_array_tohex(data_payload,60, 4)
        # get_nand_feature = self.assign_get_nand_feature_info(data_payload)
        
        _, open_vb_info = get_open_vb_info()
        logger.flow(4, 'write 1 lba size on normal LUN (L1)')
        write10.assign(lun=self.TestNormalLun, lba=cur_lba, length=write_len, fua=1)
        ExecuteCMD.enqueue(write10)
        ExecuteCMD.send(clear_on_success=True)
        
        
        response, data_payload = project_api.issue_4022_to_get_NAND_feature(0,0x7F)
        project_api.print_array_tohex(data_payload,60, 4)
        get_nand_feature = self.assign_get_nand_feature_info(data_payload)
        L1_get_nand_feature: get_nand_feature_format = get_nand_feature_format(get_nand_feature.payload.copy())
        rsp, previos_payload = get_previous_info()
        project_api.print_array_tohex(previos_payload,60, 4)
        if previos_payload[0] == MDWLSV_L1:
            check_L1 = True
        else:
            check_L1 = False
        logger.info('VU 0x4029 get MDWLSV Offset')
        response, data_payload = project_api.issue_4029_to_get_MDWLSV_offset_information()  
        project_api.print_array_tohex(data_payload,60, 4)
        MDWLSV_info = self.assign_MDWLSV_info(data_payload)
        logger.info(f'Die0_MDWLSV_MM_OPEN_BLOCK_EM1_HOST_offset = {MDWLSV_info.Die0_MDWLSV_MM_OPEN_BLOCK_EM1_HOST_offset.value}')
        if check_EM1 is True:
            if MDWLSV_info.Die0_MDWLSV_MM_OPEN_BLOCK_EM1_HOST_offset.value == wlsv_default or EM1_get_nand_feature.P3.value != MDWLSV_info.Die0_MDWLSV_MM_OPEN_BLOCK_EM1_HOST_offset.value:
                logger.error_lb(f'write EM1 l2 , then write L1')
                logger.error_fp(f'expect EM1 l2 has wlsv offset and equal to P3 {EM1_get_nand_feature.P3.value}, result Fail!')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        else:
            logger.error_fp(f'expect EM1 l2 has wlsv offset, result Fail, due to internal program!')
        
        _, open_vb_info2 = get_open_vb_info()

        logger.flow(5, 'enable WB and write 1 lba size on normal lun')
        api.set_flag(idn=api.FlagIDN.WRITEBOOSTER_EN)
        write10.assign(lun=self.TestNormalLun, lba=cur_lba, length=write_len, fua=1)
        ExecuteCMD.enqueue(write10)
        ExecuteCMD.send(clear_on_success=True)
        rsp, previos_payload = get_previous_info()
        project_api.print_array_tohex(previos_payload,60, 4)
        logger.info(f'last program vb type is {previos_payload[0]}')
        if previos_payload[0] == MDWLSV_SLC_L2:
            check_WB = True
        else:
            check_WB = False
        logger.info('VU 0x4029 get MDWLSV Offset as table1')
        response, data_payload = project_api.issue_4029_to_get_MDWLSV_offset_information()  
        project_api.print_array_tohex(data_payload,60, 4)
        MDWLSV_info = self.assign_MDWLSV_info(data_payload)
        table1 :MDWLSV_format = MDWLSV_format(MDWLSV_info.payload.copy())
        logger.info(f'Die0_MDWLSV_MM_OPEN_BLOCK_NOMAL_HOST_SLC_offset = {MDWLSV_info.Die0_MDWLSV_MM_OPEN_BLOCK_NOMAL_HOST_SLC_offset.value}')
        if check_L1 is True:
            if MDWLSV_info.Die0_MDWLSV_MM_OPEN_BLOCK_NOMAL_HOST_SLC_offset.value == wlsv_default or L1_get_nand_feature.P3.value != MDWLSV_info.Die0_MDWLSV_MM_OPEN_BLOCK_NOMAL_HOST_SLC_offset.value:
                logger.error_lb(f'write L1 , then write wb')
                logger.error_fp(f'expect L1 has wlsv offset {MDWLSV_info.Die0_MDWLSV_MM_OPEN_BLOCK_NOMAL_HOST_SLC_offset.value} and equal P3 {L1_get_nand_feature.P3.value}, result Fail!')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        else:
            logger.error_fp(f'expect L1 has wlsv offset, result Fail, due to internal program!')
        
        #test SSU 
        _, open_vb_info = get_open_vb_info()
        self.print_open_vb_information_phison(open_vb_info)
        open_vb_1: OpenVBInfo = OpenVBInfo(open_vb_info.payload.copy())
        # get_open_vb = self.get_and_print_open_vb_information()
        #open_vb_1: project_api.OpenVBInformation = project_api.OpenVBInformation(get_open_vb.payload.copy())
        logger.flow(6, 'issue SSU sleep and active')
        ExecuteCMD.StartStopUnit().assign(lun=api.WellKnownLUN.UFS_DEVICE, immed=0, power_condition=0x02, no_flush=0, start=0).set_option(wait_queue_empty=True).enqueue()
        ExecuteCMD.StartStopUnit().assign(lun=api.WellKnownLUN.UFS_DEVICE, immed=0, power_condition=0x01, no_flush=0, start=0).set_option(wait_queue_empty=True).enqueue()
        logger.info('VU 0x4029 get MDWLSV Offset as table2') 
        response, data_payload = project_api.issue_4029_to_get_MDWLSV_offset_information()  
        project_api.print_array_tohex(data_payload,60, 4)
        MDWLSV_info = self.assign_MDWLSV_info(data_payload)
        table2 :MDWLSV_format = MDWLSV_format(MDWLSV_info.payload.copy())
        
        _, open_vb_info = get_open_vb_info()
        self.print_open_vb_information_phison(open_vb_info)
        open_vb_2: OpenVBInfo = OpenVBInfo(open_vb_info.payload.copy())
        # get_open_vb = self.get_and_print_open_vb_information()
        #open_vb_2: project_api.OpenVBInformation = project_api.OpenVBInformation(get_open_vb.payload.copy())
        diff = self.show_diff_open_vb_p2(open_vb_1,open_vb_2,"")
        if diff is True:
            logger.info('compare table1 and table2 should same')
            same: bool = self.tables_equal(table1, table2)
            if same is False:
                logger.error_lb(f'SSU sleep and active')
                logger.error_fp(f'expect wlsv table same, result Fail!')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        #test ATS
        logger.info('VU 0x4029 get MDWLSV Offset as table1')
        response, data_payload = project_api.issue_4029_to_get_MDWLSV_offset_information()  
        project_api.print_array_tohex(data_payload,60, 4)
        MDWLSV_info = self.assign_MDWLSV_info(data_payload)
        table1 :MDWLSV_format = MDWLSV_format(MDWLSV_info.payload.copy())
        logger.flow(7, 'idle 2s to enter ATS')
        time.sleep(2)
        rsp, previos_payload = get_previous_info()
        project_api.print_array_tohex(previos_payload,60, 4)
        logger.info(f'last program vb type is {previos_payload[0]}')

        logger.info('VU 0x4029 get MDWLSV Offset as table2') 
        response, data_payload = project_api.issue_4029_to_get_MDWLSV_offset_information()  
        project_api.print_array_tohex(data_payload,60, 4)
        MDWLSV_info = self.assign_MDWLSV_info(data_payload)
        table2 :MDWLSV_format = MDWLSV_format(MDWLSV_info.payload.copy())
        
        logger.info('compare table1 and table2 should same')
        same = self.tables_equal(table1, table2)
        if same is False:
            logger.error_lb(f'SSU sleep and active')
            logger.error_fp(f'expect wlsv table same, result Fail!')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        
        logger.flow(8, 'H8 enter and exit')
        f = ExecuteCMD.CmdSeqHibernate() 
        f.set_option(
            hibernate_enter=1,
            hibernate_exit=1,
            loopcount=10,
            delayafterenter=500,
            delayafterexit=1000,
            wait_queue_empty=True,
            delay_time=100
        )
        
        ExecuteCMD.enqueue(f)
        ExecuteCMD.send(clear_on_success=True)

        logger.info('VU 0x4029 get MDWLSV Offset as table3')
        response, data_payload = project_api.issue_4029_to_get_MDWLSV_offset_information()  
        project_api.print_array_tohex(data_payload,60, 4)
        MDWLSV_info = self.assign_MDWLSV_info(data_payload)
        table3 :MDWLSV_format = MDWLSV_format(MDWLSV_info.payload.copy())
        logger.info('compare table1 and table3 should same')
        same = self.tables_equal(table1, table3)    

        reset_type = api.Dcmd5ResetType.HW_RESET
        logger.flow(9, f'reset event = {RESET_COMMANDS.get(reset_type)}')
        api.init_tester_to_unit_ready(resetmode = api.Dcmd5ResetType(api.Dcmd5ResetType.HW_RESET), powerdown = True)

        logger.info('VU 0x4029 get MDWLSV Offset as table3')
        response, data_payload = project_api.issue_4029_to_get_MDWLSV_offset_information()  
        project_api.print_array_tohex(data_payload,60, 4)
        MDWLSV_info = self.assign_MDWLSV_info(data_payload)
        self.check_all_zero(data_payload)
        hw_setting.set_to_device(field = api.HwSettingField.MEDIUM_SCAN_TRIGGER_TIME, val= medium_scan_setting_bk)
        pass

    def post_process(self) -> None:
        pass
    def assign_MDWLSV_info(self, data_payload:bytearray) -> MDWLSV_format:
        self.MDWLSV_info = MDWLSV_format()
        self.MDWLSV_info.Die0_MDWLSV_MM_OPEN_BLOCK_EM1_HOST_offset.value=data_payload[2]            
        self.MDWLSV_info.Die0_MDWLSV_MM_OPEN_BLOCK_EM1_HOST_SB0_offset.value=data_payload[3]        
        self.MDWLSV_info.Die0_MDWLSV_MM_OPEN_BLOCK_TABLE_PTE_offset.value=data_payload[6]          
        self.MDWLSV_info.Die0_MDWLSV_MM_OPEN_BLOCK_TABLE_PTE_SB0_offset.value=data_payload[7]      
        self.MDWLSV_info.Die0_MDWLSV_MM_OPEN_BLOCK_TEMP_RAIN_offset.value=data_payload[10]        
        self.MDWLSV_info.Die0_MDWLSV_MM_OPEN_BLOCK_TEMP_RAIN_SB0_offset.value=data_payload[11]    
        self.MDWLSV_info.Die0_MDWLSV_MM_OPEN_BLOCK_NOMAL_HOST_SLC_offset.value=data_payload[14]    
        self.MDWLSV_info.Die0_MDWLSV_MM_OPEN_BLOCK_NOMAL_HOST_SLC_SB0_offset.value=data_payload[15]
        self.MDWLSV_info.Die0_MDWLSV_MM_OPEN_BLOCK_WRITE_BOOSTER_offset.value=data_payload[18]    
        self.MDWLSV_info.Die0_MDWLSV_MM_OPEN_BLOCK_WRITE_BOOSTER_SB0_offset.value=data_payload[19]
        self.MDWLSV_info.Die0_MDWLSV_MM_OPEN_BLOCK_RPMB_HOST_offset.value=data_payload[22]        
        self.MDWLSV_info.Die0_MDWLSV_MM_OPEN_BLOCK_RPMB_HOST_SB0_offset.value=data_payload[23]    
        self.MDWLSV_info.Die0_MDWLSV_MM_OPEN_BLOCK_RPMB_GC_offset.value=data_payload[26]          
        self.MDWLSV_info.Die0_MDWLSV_MM_OPEN_BLOCK_RPMB_GC_SB0_offset.value=data_payload[27]      
        self.MDWLSV_info.Die0_MDWLSV_MM_OPEN_BLOCK_SWAPRAIN_WB_offset.value=data_payload[30]      
        self.MDWLSV_info.Die0_MDWLSV_MM_OPEN_BLOCK_SWAPRAIN_WB_SB0_offset.value=data_payload[31]  
        self.MDWLSV_info.Die0_MDWLSV_MM_OPEN_BLOCK_SWAPRAIN_EM1_offset.value=data_payload[34]      
        self.MDWLSV_info.Die0_MDWLSV_MM_OPEN_BLOCK_SWAPRAIN_EM1_SB0_offset.value=data_payload[35]  
        self.MDWLSV_info.Die0_MDWLSV_SM_OPEN_BLOCK_FTL_SUB_offset.value=data_payload[38]          
        self.MDWLSV_info.Die0_MDWLSV_SM_OPEN_BLOCK_FTL_SUB_SB0_offset.value=data_payload[39]      
        self.MDWLSV_info.Die0_MDWLSV_SM_OPEN_BLOCK_EM1_GC_offset.value=data_payload[42]            
        self.MDWLSV_info.Die0_MDWLSV_SM_OPEN_BLOCK_EM1_GC_SB0_offset.value=data_payload[43]        
        self.MDWLSV_info.Die0_MDWLSV_SM_OPEN_BLOCK_NOMAL_HOST_TLC_offset.value=data_payload[46]    
        self.MDWLSV_info.Die0_MDWLSV_SM_OPEN_BLOCK_NOMAL_HOST_TLC_SB0_offset.value=data_payload[47]
        self.MDWLSV_info.Die0_MDWLSV_SM_OPEN_BLOCK_NORMAL_GC_offset.value=data_payload[50]        
        self.MDWLSV_info.Die0_MDWLSV_SM_OPEN_BLOCK_NORMAL_GC_SB0_offset.value=data_payload[51]    
        self.MDWLSV_info.Die0_MDWLSV_SM_OPEN_BLOCK_SWAPRAIN_HOST_offset.value=data_payload[54]    
        self.MDWLSV_info.Die0_MDWLSV_SM_OPEN_BLOCK_SWAPRAIN_HOST_SB0_offset.value=data_payload[55]
        self.MDWLSV_info.Die0_MDWLSV_MM_OPEN_BLOCK_TABLE_LOG_offset.value=data_payload[58]        
        self.MDWLSV_info.Die0_MDWLSV_MM_OPEN_BLOCK_TABLE_LOG_SB0_offset.value=data_payload[59]
        self.MDWLSV_info.Die1_MDWLSV_MM_OPEN_BLOCK_EM1_HOST_offset.value=data_payload[2+1*60]            
        self.MDWLSV_info.Die1_MDWLSV_MM_OPEN_BLOCK_EM1_HOST_SB0_offset.value=data_payload[3+1*60]        
        self.MDWLSV_info.Die1_MDWLSV_MM_OPEN_BLOCK_TABLE_PTE_offset.value=data_payload[6+1*60]          
        self.MDWLSV_info.Die1_MDWLSV_MM_OPEN_BLOCK_TABLE_PTE_SB0_offset.value=data_payload[7+1*60]      
        self.MDWLSV_info.Die1_MDWLSV_MM_OPEN_BLOCK_TEMP_RAIN_offset.value=data_payload[10+1*60]        
        self.MDWLSV_info.Die1_MDWLSV_MM_OPEN_BLOCK_TEMP_RAIN_SB0_offset.value=data_payload[11+1*60]    
        self.MDWLSV_info.Die1_MDWLSV_MM_OPEN_BLOCK_NOMAL_HOST_SLC_offset.value=data_payload[14+1*60]    
        self.MDWLSV_info.Die1_MDWLSV_MM_OPEN_BLOCK_NOMAL_HOST_SLC_SB0_offset.value=data_payload[15+1*60]
        self.MDWLSV_info.Die1_MDWLSV_MM_OPEN_BLOCK_WRITE_BOOSTER_offset.value=data_payload[18+1*60]    
        self.MDWLSV_info.Die1_MDWLSV_MM_OPEN_BLOCK_WRITE_BOOSTER_SB0_offset.value=data_payload[19+1*60]
        self.MDWLSV_info.Die1_MDWLSV_MM_OPEN_BLOCK_RPMB_HOST_offset.value=data_payload[22+1*60]        
        self.MDWLSV_info.Die1_MDWLSV_MM_OPEN_BLOCK_RPMB_HOST_SB0_offset.value=data_payload[23+1*60]    
        self.MDWLSV_info.Die1_MDWLSV_MM_OPEN_BLOCK_RPMB_GC_offset.value=data_payload[26+1*60]          
        self.MDWLSV_info.Die1_MDWLSV_MM_OPEN_BLOCK_RPMB_GC_SB0_offset.value=data_payload[27+1*60]      
        self.MDWLSV_info.Die1_MDWLSV_MM_OPEN_BLOCK_SWAPRAIN_WB_offset.value=data_payload[30+1*60]      
        self.MDWLSV_info.Die1_MDWLSV_MM_OPEN_BLOCK_SWAPRAIN_WB_SB0_offset.value=data_payload[31+1*60]  
        self.MDWLSV_info.Die1_MDWLSV_MM_OPEN_BLOCK_SWAPRAIN_EM1_offset.value=data_payload[34+1*60]      
        self.MDWLSV_info.Die1_MDWLSV_MM_OPEN_BLOCK_SWAPRAIN_EM1_SB0_offset.value=data_payload[35+1*60]  
        self.MDWLSV_info.Die1_MDWLSV_SM_OPEN_BLOCK_FTL_SUB_offset.value=data_payload[38+1*60]          
        self.MDWLSV_info.Die1_MDWLSV_SM_OPEN_BLOCK_FTL_SUB_SB0_offset.value=data_payload[39+1*60]      
        self.MDWLSV_info.Die1_MDWLSV_SM_OPEN_BLOCK_EM1_GC_offset.value=data_payload[42+1*60]            
        self.MDWLSV_info.Die1_MDWLSV_SM_OPEN_BLOCK_EM1_GC_SB0_offset.value=data_payload[43+1*60]        
        self.MDWLSV_info.Die1_MDWLSV_SM_OPEN_BLOCK_NOMAL_HOST_TLC_offset.value=data_payload[46+1*60]    
        self.MDWLSV_info.Die1_MDWLSV_SM_OPEN_BLOCK_NOMAL_HOST_TLC_SB0_offset.value=data_payload[47+1*60]
        self.MDWLSV_info.Die1_MDWLSV_SM_OPEN_BLOCK_NORMAL_GC_offset.value=data_payload[50+1*60]        
        self.MDWLSV_info.Die1_MDWLSV_SM_OPEN_BLOCK_NORMAL_GC_SB0_offset.value=data_payload[51+1*60]    
        self.MDWLSV_info.Die1_MDWLSV_SM_OPEN_BLOCK_SWAPRAIN_HOST_offset.value=data_payload[54+1*60]    
        self.MDWLSV_info.Die1_MDWLSV_SM_OPEN_BLOCK_SWAPRAIN_HOST_SB0_offset.value=data_payload[55+1*60]
        self.MDWLSV_info.Die1_MDWLSV_MM_OPEN_BLOCK_TABLE_LOG_offset.value=data_payload[58+1*60]        
        self.MDWLSV_info.Die1_MDWLSV_MM_OPEN_BLOCK_TABLE_LOG_SB0_offset.value=data_payload[59+1*60]  
        self.MDWLSV_info.Die2_MDWLSV_MM_OPEN_BLOCK_EM1_HOST_offset.value=data_payload[2+2*60]            
        self.MDWLSV_info.Die2_MDWLSV_MM_OPEN_BLOCK_EM1_HOST_SB0_offset.value=data_payload[3+2*60]        
        self.MDWLSV_info.Die2_MDWLSV_MM_OPEN_BLOCK_TABLE_PTE_offset.value=data_payload[6+2*60]          
        self.MDWLSV_info.Die2_MDWLSV_MM_OPEN_BLOCK_TABLE_PTE_SB0_offset.value=data_payload[7+2*60]      
        self.MDWLSV_info.Die2_MDWLSV_MM_OPEN_BLOCK_TEMP_RAIN_offset.value=data_payload[10+2*60]        
        self.MDWLSV_info.Die2_MDWLSV_MM_OPEN_BLOCK_TEMP_RAIN_SB0_offset.value=data_payload[11+2*60]    
        self.MDWLSV_info.Die2_MDWLSV_MM_OPEN_BLOCK_NOMAL_HOST_SLC_offset.value=data_payload[14+2*60]    
        self.MDWLSV_info.Die2_MDWLSV_MM_OPEN_BLOCK_NOMAL_HOST_SLC_SB0_offset.value=data_payload[15+2*60]
        self.MDWLSV_info.Die2_MDWLSV_MM_OPEN_BLOCK_WRITE_BOOSTER_offset.value=data_payload[18+2*60]    
        self.MDWLSV_info.Die2_MDWLSV_MM_OPEN_BLOCK_WRITE_BOOSTER_SB0_offset.value=data_payload[19+2*60]
        self.MDWLSV_info.Die2_MDWLSV_MM_OPEN_BLOCK_RPMB_HOST_offset.value=data_payload[22+2*60]        
        self.MDWLSV_info.Die2_MDWLSV_MM_OPEN_BLOCK_RPMB_HOST_SB0_offset.value=data_payload[23+2*60]    
        self.MDWLSV_info.Die2_MDWLSV_MM_OPEN_BLOCK_RPMB_GC_offset.value=data_payload[26+2*60]          
        self.MDWLSV_info.Die2_MDWLSV_MM_OPEN_BLOCK_RPMB_GC_SB0_offset.value=data_payload[27+2*60]      
        self.MDWLSV_info.Die2_MDWLSV_MM_OPEN_BLOCK_SWAPRAIN_WB_offset.value=data_payload[30+2*60]      
        self.MDWLSV_info.Die2_MDWLSV_MM_OPEN_BLOCK_SWAPRAIN_WB_SB0_offset.value=data_payload[31+2*60]  
        self.MDWLSV_info.Die2_MDWLSV_MM_OPEN_BLOCK_SWAPRAIN_EM1_offset.value=data_payload[34+2*60]      
        self.MDWLSV_info.Die2_MDWLSV_MM_OPEN_BLOCK_SWAPRAIN_EM1_SB0_offset.value=data_payload[35+2*60]  
        self.MDWLSV_info.Die2_MDWLSV_SM_OPEN_BLOCK_FTL_SUB_offset.value=data_payload[38+2*60]          
        self.MDWLSV_info.Die2_MDWLSV_SM_OPEN_BLOCK_FTL_SUB_SB0_offset.value=data_payload[39+2*60]      
        self.MDWLSV_info.Die2_MDWLSV_SM_OPEN_BLOCK_EM1_GC_offset.value=data_payload[42+2*60]            
        self.MDWLSV_info.Die2_MDWLSV_SM_OPEN_BLOCK_EM1_GC_SB0_offset.value=data_payload[43+2*60]        
        self.MDWLSV_info.Die2_MDWLSV_SM_OPEN_BLOCK_NOMAL_HOST_TLC_offset.value=data_payload[46+2*60]    
        self.MDWLSV_info.Die2_MDWLSV_SM_OPEN_BLOCK_NOMAL_HOST_TLC_SB0_offset.value=data_payload[47+2*60]
        self.MDWLSV_info.Die2_MDWLSV_SM_OPEN_BLOCK_NORMAL_GC_offset.value=data_payload[50+2*60]        
        self.MDWLSV_info.Die2_MDWLSV_SM_OPEN_BLOCK_NORMAL_GC_SB0_offset.value=data_payload[51+2*60]    
        self.MDWLSV_info.Die2_MDWLSV_SM_OPEN_BLOCK_SWAPRAIN_HOST_offset.value=data_payload[54+2*60]    
        self.MDWLSV_info.Die2_MDWLSV_SM_OPEN_BLOCK_SWAPRAIN_HOST_SB0_offset.value=data_payload[55+2*60]
        self.MDWLSV_info.Die2_MDWLSV_MM_OPEN_BLOCK_TABLE_LOG_offset.value=data_payload[58+2*60]        
        self.MDWLSV_info.Die2_MDWLSV_MM_OPEN_BLOCK_TABLE_LOG_SB0_offset.value=data_payload[59+2*60]
        self.MDWLSV_info.Die3_MDWLSV_MM_OPEN_BLOCK_EM1_HOST_offset.value=data_payload[2+3*60]            
        self.MDWLSV_info.Die3_MDWLSV_MM_OPEN_BLOCK_EM1_HOST_SB0_offset.value=data_payload[3+3*60]        
        self.MDWLSV_info.Die3_MDWLSV_MM_OPEN_BLOCK_TABLE_PTE_offset.value=data_payload[6+3*60]          
        self.MDWLSV_info.Die3_MDWLSV_MM_OPEN_BLOCK_TABLE_PTE_SB0_offset.value=data_payload[7+3*60]      
        self.MDWLSV_info.Die3_MDWLSV_MM_OPEN_BLOCK_TEMP_RAIN_offset.value=data_payload[10+3*60]        
        self.MDWLSV_info.Die3_MDWLSV_MM_OPEN_BLOCK_TEMP_RAIN_SB0_offset.value=data_payload[11+3*60]    
        self.MDWLSV_info.Die3_MDWLSV_MM_OPEN_BLOCK_NOMAL_HOST_SLC_offset.value=data_payload[14+3*60]    
        self.MDWLSV_info.Die3_MDWLSV_MM_OPEN_BLOCK_NOMAL_HOST_SLC_SB0_offset.value=data_payload[15+3*60]
        self.MDWLSV_info.Die3_MDWLSV_MM_OPEN_BLOCK_WRITE_BOOSTER_offset.value=data_payload[18+3*60]    
        self.MDWLSV_info.Die3_MDWLSV_MM_OPEN_BLOCK_WRITE_BOOSTER_SB0_offset.value=data_payload[19+3*60]
        self.MDWLSV_info.Die3_MDWLSV_MM_OPEN_BLOCK_RPMB_HOST_offset.value=data_payload[22+3*60]        
        self.MDWLSV_info.Die3_MDWLSV_MM_OPEN_BLOCK_RPMB_HOST_SB0_offset.value=data_payload[23+3*60]    
        self.MDWLSV_info.Die3_MDWLSV_MM_OPEN_BLOCK_RPMB_GC_offset.value=data_payload[26+3*60]          
        self.MDWLSV_info.Die3_MDWLSV_MM_OPEN_BLOCK_RPMB_GC_SB0_offset.value=data_payload[27+3*60]      
        self.MDWLSV_info.Die3_MDWLSV_MM_OPEN_BLOCK_SWAPRAIN_WB_offset.value=data_payload[30+3*60]      
        self.MDWLSV_info.Die3_MDWLSV_MM_OPEN_BLOCK_SWAPRAIN_WB_SB0_offset.value=data_payload[31+3*60]  
        self.MDWLSV_info.Die3_MDWLSV_MM_OPEN_BLOCK_SWAPRAIN_EM1_offset.value=data_payload[34+3*60]      
        self.MDWLSV_info.Die3_MDWLSV_MM_OPEN_BLOCK_SWAPRAIN_EM1_SB0_offset.value=data_payload[35+3*60]  
        self.MDWLSV_info.Die3_MDWLSV_SM_OPEN_BLOCK_FTL_SUB_offset.value=data_payload[38+3*60]          
        self.MDWLSV_info.Die3_MDWLSV_SM_OPEN_BLOCK_FTL_SUB_SB0_offset.value=data_payload[39+3*60]      
        self.MDWLSV_info.Die3_MDWLSV_SM_OPEN_BLOCK_EM1_GC_offset.value=data_payload[42+3*60]            
        self.MDWLSV_info.Die3_MDWLSV_SM_OPEN_BLOCK_EM1_GC_SB0_offset.value=data_payload[43+3*60]        
        self.MDWLSV_info.Die3_MDWLSV_SM_OPEN_BLOCK_NOMAL_HOST_TLC_offset.value=data_payload[46+3*60]    
        self.MDWLSV_info.Die3_MDWLSV_SM_OPEN_BLOCK_NOMAL_HOST_TLC_SB0_offset.value=data_payload[47+3*60]
        self.MDWLSV_info.Die3_MDWLSV_SM_OPEN_BLOCK_NORMAL_GC_offset.value=data_payload[50+3*60]        
        self.MDWLSV_info.Die3_MDWLSV_SM_OPEN_BLOCK_NORMAL_GC_SB0_offset.value=data_payload[51+3*60]    
        self.MDWLSV_info.Die3_MDWLSV_SM_OPEN_BLOCK_SWAPRAIN_HOST_offset.value=data_payload[54+3*60]    
        self.MDWLSV_info.Die3_MDWLSV_SM_OPEN_BLOCK_SWAPRAIN_HOST_SB0_offset.value=data_payload[55+3*60]
        self.MDWLSV_info.Die3_MDWLSV_MM_OPEN_BLOCK_TABLE_LOG_offset.value=data_payload[58+3*60]        
        self.MDWLSV_info.Die3_MDWLSV_MM_OPEN_BLOCK_TABLE_LOG_SB0_offset.value=data_payload[59+3*60]
        return self.MDWLSV_info
    def assign_get_nand_feature_info(self, data_payload:bytearray) -> get_nand_feature_format:
        get_nand_info_format = get_nand_feature_format()
        #testbytes = data_payload[0:4]
        # print(type(testbytes))
        # print(type(data_payload[0:4]))
        get_nand_info_format.result.value = int.from_bytes(data_payload[0:4], byteorder='little')
        get_nand_info_format.die.value = int.from_bytes(data_payload[4:8], byteorder='little')
        get_nand_info_format.P1.value = int.from_bytes(data_payload[8:12], byteorder='little')
        get_nand_info_format.P2.value = int.from_bytes(data_payload[12:16], byteorder='little')
        get_nand_info_format.P3.value = int.from_bytes(data_payload[16:20], byteorder='little')
        get_nand_info_format.P4.value = int.from_bytes(data_payload[20:24], byteorder='little')
        
        logger.info(f'get_nand_info_format.P3.value = {get_nand_info_format.P3.value}')
        return get_nand_info_format       
    # def assign_set_nand_feature_info(self, data_payload:bytearray) -> set_nand_feature_format:
    #     self.set_nand_info_format = set_nand_feature_format()
    #     testbytes = data_payload[0:4]
    #     print(type(testbytes))
    #     print(type(data_payload[0:4]))
    #     self.get_nand_info_format.result.value = int.from_bytes(data_payload[0:4], byteorder='little')
    #     return self.set_nand_info_format      
    def config_lun(self) -> None:
        _param = shared.param
        selector = 0x00
        length = 0xE6
        self.unit_desc_idxes:List[int] = []
        for index in range(4):
            cmd = ExecuteCMD.WriteDescriptor()
            cmd.assign(api.DescriptorIDN.CONFIGURATION, index, selector, length)

            desc = api.ConfigDescriptor310()
            desc.header.b2_conf_desc_continue = api.ConfDescContinue.DISABLE if index == 3 else api.ConfDescContinue.ENABLE
            desc.header.b3_boot_enable = api.BootEnable.BOOT_DISABLE
            desc.header.b4_descr_access_en = api.DescrAccessEn.DISABLE
            desc.header.b5_init_power_mode = api.InitPowerMode.ACTIVE
            desc.header.b6_high_priority_lun = api.HighPriorityLUN.ALL_LUN_SAME_PRIORITY
            desc.header.b7_secure_removal_type = api.SecureRemovalType.BY_PHYSICAL_ERASE
            desc.header.b8_init_active_icc_level = api.InitActiveICCLevel.LVL_00
            desc.header.w9_periodic_rtc_update = 0
            desc.header.b11_hpb_control = 0
            desc.header.b16_write_booster_buffer_preserve_user_space_en = api.WriteBoosterBufferPreserveUserSpaceEn.DISABLE
            desc.header.b17_write_booster_buffer_type = api.WriteBoosterBufferType.SHARED
            desc.header.l18_num_shared_write_booster_buffer_alloc_units = self.geometry_desc.l79_write_booster_buffer_max_n_alloc_units
            desc.header.l18_num_shared_write_booster_buffer_alloc_units = 0x1000

            for unit_idx in range(8):
                if index == 0 and unit_idx == self.TestNormalLun:
                    desc.units[unit_idx].b0_lu_enable = api.LUNEnable.ENABLE
                    desc.units[unit_idx].b1_boot_lun_id = api.BootLUNID.NOT_BOOTABLE
                    desc.units[unit_idx].b2_lu_write_protect = api.LUNWriteProtect.NOT_WRITE_PROTECTED
                    desc.units[unit_idx].b3_memory_type = api.MemoryType.NORMAL
                    desc.units[unit_idx].l4_num_alloc_units = int(self.Total_AU_Count /4)
                    #desc.units[unit_idx].l4_num_alloc_units = 8092
                    desc.units[unit_idx].b8_data_reliability = api.DataReliability.LUN_NOT_PROTECTED
                    desc.units[unit_idx].b9_logical_block_size = api.LogicalBlockSize.SIZE_4KB
                    desc.units[unit_idx].b10_provisioning_type = api.ProvisioningType.THIN_PROVISIONING_ERASE
                elif index == 0 and unit_idx == self.TestBootA:
                    desc.units[unit_idx].b0_lu_enable = api.LUNEnable.ENABLE
                    desc.units[unit_idx].b1_boot_lun_id = api.BootLUNID.BOOT_LUN_A
                    desc.units[unit_idx].b2_lu_write_protect = api.LUNWriteProtect.NOT_WRITE_PROTECTED
                    desc.units[unit_idx].b3_memory_type = api.MemoryType.ENHANCED_1
                    desc.units[unit_idx].l4_num_alloc_units = int(self.Total_AU_Count /4)
                    desc.units[unit_idx].b8_data_reliability = api.DataReliability.LUN_NOT_PROTECTED
                    desc.units[unit_idx].b9_logical_block_size = api.LogicalBlockSize.SIZE_4KB
                    desc.units[unit_idx].b10_provisioning_type = api.ProvisioningType.THIN_PROVISIONING_ERASE
                elif index == 0 and unit_idx == self.TestBootB:
                    desc.units[unit_idx].b0_lu_enable = api.LUNEnable.ENABLE
                    desc.units[unit_idx].b1_boot_lun_id = api.BootLUNID.BOOT_LUN_B
                    desc.units[unit_idx].b2_lu_write_protect = api.LUNWriteProtect.NOT_WRITE_PROTECTED
                    desc.units[unit_idx].b3_memory_type = api.MemoryType.ENHANCED_1
                    desc.units[unit_idx].l4_num_alloc_units = int(self.Total_AU_Count /4)
                    desc.units[unit_idx].b8_data_reliability = api.DataReliability.LUN_NOT_PROTECTED
                    desc.units[unit_idx].b9_logical_block_size = api.LogicalBlockSize.SIZE_4KB
                    desc.units[unit_idx].b10_provisioning_type = api.ProvisioningType.THIN_PROVISIONING_ERASE
                elif index == 0 and unit_idx == self.TestEM1Lun:
                    desc.units[unit_idx].b0_lu_enable = api.LUNEnable.ENABLE
                    desc.units[unit_idx].b1_boot_lun_id = api.BootLUNID.NOT_BOOTABLE
                    desc.units[unit_idx].b2_lu_write_protect = api.LUNWriteProtect.NOT_WRITE_PROTECTED
                    desc.units[unit_idx].b3_memory_type = api.MemoryType.ENHANCED_1
                    desc.units[unit_idx].l4_num_alloc_units = int(self.Total_AU_Count /4)
                    desc.units[unit_idx].b8_data_reliability = api.DataReliability.LUN_NOT_PROTECTED
                    desc.units[unit_idx].b9_logical_block_size = api.LogicalBlockSize.SIZE_4KB
                    desc.units[unit_idx].b10_provisioning_type = api.ProvisioningType.THIN_PROVISIONING_ERASE
                else:
                    desc.units[unit_idx].b0_lu_enable = api.LUNEnable.DISABLE
                    desc.units[unit_idx].l4_num_alloc_units = 0
                    desc.units[unit_idx].b9_logical_block_size = 0

            cmd.set_desc(desc)
            ExecuteCMD.enqueue(cmd)
            ExecuteCMD.send() 
           
        for lun in range(0, _param.gMaxNumberLU):
            unit_descriptor = ExecuteCMD.ReadDescriptor()
            unit_descriptor.assign(DescriptorIDN.UNIT, lun)
            self.unit_desc_idxes.append(ExecuteCMD.enqueue(unit_descriptor))

        ExecuteCMD.send(clear_on_success=False)
        for index in self.unit_desc_idxes:
            update_descriptor(DescriptorIDN.UNIT, index, cast(QueryResponse, ExecuteCMD.read_response(index)))
        ExecuteCMD.clear()
        #test unit ready all enable lun
        for lun in range(_param.gMaxNumberLU):
            if  _param.gUnit[lun].b3_lu_enable:
                test_unit_ready = ExecuteCMD.CmdSeqTestUnitReady()
                test_unit_ready.set_option(lun)
                ExecuteCMD.enqueue(test_unit_ready)
        ExecuteCMD.send(clear_on_success=False)
        ExecuteCMD.clear()
        api.write_attribute(idn=api.AttributeIDN.BOOT_LUN_EN, val=api.BootLUNID.BOOT_LUN_A)
    def print_open_vb_information_phison(self, open_vb_info: OpenVBInfo) -> None:
    
        logger.info('================= open_vb_information =================')
        # 取得所有屬於 OpenVBInfoUnit 的子單元
        sub_units = {
            name: obj
            for name, obj in open_vb_info.__dict__.items()
            if hasattr(obj, "__dict__")               # 必須是物件
            and any(hasattr(v, "start_offset") for v in obj.__dict__.values())  # 內含欄位
        }

        for unit_name, unit_obj in sub_units.items():
            # 收集該單元內所有具有 start_offset / end_offset / value 的欄位
            fields = [
                (fname, fobj)
                for fname, fobj in unit_obj.__dict__.items()
                if hasattr(fobj, "start_offset")
                and hasattr(fobj, "end_offset")
                and hasattr(fobj, "value")
            ]

            # 依起始位元組排序
            fields.sort(key=lambda kv: kv[1].start_offset)

            # 輸出單元標頭
            logger.info(f'--- {unit_name} ---')
            # 輸出欄位資訊
            for fname, fobj in fields:
                logger.info(
                    f'Byte[{fobj.start_offset}:{fobj.end_offset}]: '
                    f'{unit_name}.{fname} = {fobj.value}'
                )
    def print_open_vb_information_ai(self, open_vb_information: project_api.OpenVBInformation) -> None:
    
        logger.info('================= open_vb_information =================')
        fields = [
            (name, field) for name, field in open_vb_information.__dict__.items()
            if hasattr(field, "start_offset") and hasattr(field, "end_offset") and hasattr(field, "value")
        ]
        fields.sort(key=lambda kv: kv[1].start_offset)
        # 以 __dict__ 走訪，僅挑選具備 start_offset、end_offset、value 的欄位物件
        for name, field in fields:
            logger.info(
                f'Byte[{field.start_offset}:{field.end_offset}]: {name} = {field.value}'
            )
    def print_open_vb_information(self, open_vb_information:project_api.OpenVBInformation) -> None:
        logger.info('================= open_vb_information =================')
        logger.info(f'Byte[{open_vb_information.L2_Open_logical_VB_Host_TLC_number.start_offset}:{open_vb_information.L2_Open_logical_VB_Host_TLC_number.end_offset}]: L2_Open_logical_VB_Host_TLC_number = {open_vb_information.L2_Open_logical_VB_Host_TLC_number.value}')
        logger.info(f'Byte[{open_vb_information.first_free_physical_page_of_L2_Open_logical_VB_Host_TLC.start_offset}:{open_vb_information.first_free_physical_page_of_L2_Open_logical_VB_Host_TLC.end_offset}]: first_free_physical_page_of_L2_Open_logical_VB_Host_TLC = {open_vb_information.first_free_physical_page_of_L2_Open_logical_VB_Host_TLC.value}')
        logger.info(f'Byte[{open_vb_information.open_logical_VB_number_for_Normal_Defrag_GC_Open_VB_TLC.start_offset}:{open_vb_information.open_logical_VB_number_for_Normal_Defrag_GC_Open_VB_TLC.end_offset}]: open_logical_VB_number_for_Normal_Defrag_GC_Open_VB_TLC = {open_vb_information.open_logical_VB_number_for_Normal_Defrag_GC_Open_VB_TLC.value}')
        logger.info(f'Byte[{open_vb_information.first_free_physical_page_for_Normal_Defrag_VB_GC_Open_VB_TLC.start_offset}:{open_vb_information.first_free_physical_page_for_Normal_Defrag_VB_GC_Open_VB_TLC.end_offset}]: first_free_physical_page_for_Normal_Defrag_VB_GC_Open_VB_TLC = {open_vb_information.first_free_physical_page_for_Normal_Defrag_VB_GC_Open_VB_TLC.value}')

        logger.info(f'Byte[{open_vb_information.open_logical_VB_number_for_EM1_L2_Host.start_offset}:{open_vb_information.open_logical_VB_number_for_EM1_L2_Host.end_offset}]: open_logical_VB_number_for_EM1_L2_Host = {open_vb_information.open_logical_VB_number_for_EM1_L2_Host.value}')
        logger.info(f'Byte[{open_vb_information.first_free_physical_page_of_EM1_L2_Host_VB.start_offset}:{open_vb_information.first_free_physical_page_of_EM1_L2_Host_VB.end_offset}]: first_free_physical_page_of_EM1_L2_Host_VB_ = {open_vb_information.first_free_physical_page_of_EM1_L2_Host_VB.value}')
        logger.info(f'Byte[{open_vb_information.open_logical_VB_number_for_EM1_GC.start_offset}:{open_vb_information.open_logical_VB_number_for_EM1_GC.end_offset}]: open_logical_VB_number_for_EM1_GC = {open_vb_information.open_logical_VB_number_for_EM1_GC.value}')
        logger.info(f'Byte[{open_vb_information.first_free_physical_page_of_EM1_GC_VB.start_offset}:{open_vb_information.first_free_physical_page_of_EM1_GC_VB.end_offset}]: first_free_physical_page_of_EM1_GC_VB = {open_vb_information.first_free_physical_page_of_EM1_GC_VB.value}')
        
        
        logger.info(f'Byte[{open_vb_information.open_logical_VB_number_for_Write_Booster_WB_L2.start_offset}:{open_vb_information.open_logical_VB_number_for_Write_Booster_WB_L2.end_offset}]: open_logical_VB_number_for_Write_Booster_WB_L2 = {open_vb_information.open_logical_VB_number_for_Write_Booster_WB_L2.value}')
        logger.info(f'Byte[{open_vb_information.first_free_physical_page_of_Write_Booster_WB_L2.start_offset}:{open_vb_information.first_free_physical_page_of_Write_Booster_WB_L2.end_offset}]: first_free_physical_page_of_Write_Booster_WB_L2 = {open_vb_information.first_free_physical_page_of_Write_Booster_WB_L2.value}')
        logger.info(f'Byte[{open_vb_information.open_Remap_VB_number_for_Write_Booster_WB_L2.start_offset}:{open_vb_information.open_Remap_VB_number_for_Write_Booster_WB_L2.end_offset}]: open_Remap_VB_number_for_Write_Booster_WB_L2 = {open_vb_information.open_Remap_VB_number_for_Write_Booster_WB_L2.value}')
        logger.info(f'Byte[{open_vb_information.open_logical_VB_number_for_RPMB_VB.start_offset}:{open_vb_information.open_logical_VB_number_for_RPMB_VB.end_offset}]: open_logical_VB_number_for_RPMB_VB = {open_vb_information.open_logical_VB_number_for_RPMB_VB.value}')
        logger.info(f'Byte[{open_vb_information.first_free_physical_page_of_RPMB_VB.start_offset}:{open_vb_information.first_free_physical_page_of_RPMB_VB.end_offset}]: first_free_physical_page_of_RPMB_VB = {open_vb_information.first_free_physical_page_of_RPMB_VB.value}')
        logger.info(f'Byte[{open_vb_information.open_Remap_VB_number_for_RPMB_VB.start_offset}:{open_vb_information.open_Remap_VB_number_for_RPMB_VB.end_offset}]: open_Remap_VB_number_for_RPMB_VB = {open_vb_information.open_Remap_VB_number_for_RPMB_VB.value}')
        
        logger.info(f'Byte[{open_vb_information.PTE_Block_VB_number_logical.start_offset}:{open_vb_information.PTE_Block_VB_number_logical.end_offset}]: PTE_Block_VB_number_logical = {open_vb_information.PTE_Block_VB_number_logical.value}')
        logger.info(f'Byte[{open_vb_information.PTE_block_First_free_physical_page.start_offset}:{open_vb_information.PTE_block_First_free_physical_page.end_offset}]: PTE_block_First_free_physical_page = {open_vb_information.PTE_block_First_free_physical_page.value}')
        logger.info(f'Byte[{open_vb_information.LOG_block_VB_number_logical.start_offset}:{open_vb_information.PTE_Block_VB_number_logical.end_offset}]: PTE_Block_VB_number_logical = {open_vb_information.PTE_Block_VB_number_logical.value}')
        logger.info(f'Byte[{open_vb_information.PTE_block_First_free_physical_page.start_offset}:{open_vb_information.PTE_block_First_free_physical_page.end_offset}]: PTE_block_First_free_physical_page = {open_vb_information.PTE_block_First_free_physical_page.value}')
        logger.info(f'Byte[{open_vb_information.PTE_Block_VB_number_logical.start_offset}:{open_vb_information.PTE_Block_VB_number_logical.end_offset}]: PTE_Block_VB_number_logical = {open_vb_information.PTE_Block_VB_number_logical.value}')
        logger.info(f'Byte[{open_vb_information.PTE_block_First_free_physical_page.start_offset}:{open_vb_information.PTE_block_First_free_physical_page.end_offset}]: PTE_block_First_free_physical_page = {open_vb_information.PTE_block_First_free_physical_page.value}')
        logger.info(f'Byte[{open_vb_information.PTE_Block_VB_number_logical.start_offset}:{open_vb_information.PTE_Block_VB_number_logical.end_offset}]: PTE_Block_VB_number_logical = {open_vb_information.PTE_Block_VB_number_logical.value}')
        logger.info(f'Byte[{open_vb_information.PTE_block_First_free_physical_page.start_offset}:{open_vb_information.PTE_block_First_free_physical_page.end_offset}]: PTE_block_First_free_physical_page = {open_vb_information.PTE_block_First_free_physical_page.value}')
       
        return 
    def check_all_zero(self, obj: Any) -> None:
        if isinstance(obj, (bytearray, bytes)):
             payload = obj 
        else:
            payload = obj.payload
        for idx, byte_val in enumerate(payload):
            if byte_val != 0:
                logger.error(f"expect data all zero, but result fail")
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
    def get_and_print_open_vb_information(self) -> project_api.OpenVBInformation:
        rsp, open_vb_information = project_api.issue_40C1_to_get_open_vb_information()
        self.print_open_vb_information_ai(open_vb_information)
        return open_vb_information    
run = Pattern().run
if __name__ == "__main__":
    run()