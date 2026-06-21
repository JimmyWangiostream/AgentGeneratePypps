from importlib import import_module
from typing import TypeAlias, cast

from Script.api import shared, cmd_seq as ExecuteCMD
from Script.api.cmd_seq.response import QueryResponse
from Script.api.ufs_api.upiu.structs import SfReadDescriptor
from Script.api.ufs_api.descriptors.device_desc.structs import (DeviceDescriptor310, DeviceDescriptor400, DeviceDescriptor410,
                                                                UFSFeaturesSupport310, UFSFeaturesSupport400, UFSFeaturesSupport410,
                                                                ExtendedUFSFeaturesSupport310, ExtendedUFSFeaturesSupport400, ExtendedUFSFeaturesSupport410,
                                                                ExtendedWriteBoosterSupport410)
from Script.api.exception import PATTERN_ASSERT_MODULE_NOT_FOUND, PATTERN_ASSERT_ATTR_NOT_FOUND

_log = shared.logger
_structs_path = 'Script.api.ufs_api.descriptors.device_desc.structs'
_ufs_ver = ''

DeviceDescriptorUnion: TypeAlias = DeviceDescriptor310 | DeviceDescriptor400 | DeviceDescriptor410
UFSFeatureSupportUnion: TypeAlias = UFSFeaturesSupport310 | UFSFeaturesSupport400 | UFSFeaturesSupport410
ExtendedUFSFeaturesSupportUnion: TypeAlias = ExtendedUFSFeaturesSupport310 | ExtendedUFSFeaturesSupport400 | ExtendedUFSFeaturesSupport410
ExtendedWriteBoosterSupportUnion: TypeAlias = ExtendedWriteBoosterSupport410

def get_device_descriptor() -> DeviceDescriptorUnion:
    global _ufs_ver

    idn = 0x00
    index = 0x00
    selector = 0x00
    cmd = ExecuteCMD.ReadDescriptor()
    cmd.assign(idn, index, selector)
    i = ExecuteCMD.enqueue(cmd)

    ExecuteCMD.send(clear_on_success=False)
    resp = cast(QueryResponse, ExecuteCMD.read_response(i))
    ExecuteCMD.clear()

    read_desc = SfReadDescriptor()
    read_desc.from_bytes(resp.upiu.u12_specific_fields)
    dev_desc = DeviceDescriptor310()
    dev_desc.from_bytes(resp.data)
    _ufs_ver = f'{dev_desc.w16_spec_version:x}'
    # Re-initialize dev_desc according to UFS version
    try:
        dev_desc = getattr(import_module(_structs_path), f'DeviceDescriptor{_ufs_ver}')()
        dev_desc.from_bytes(resp.data)
    except ModuleNotFoundError:
        _log.error(f"Module not found: {_structs_path}")
        raise
    except AttributeError:
        _log.error(f"Attribute not found: DeviceDescriptor{_ufs_ver}. Please Add DeviceDescriptor{_ufs_ver} to {_structs_path}")
        raise
    return dev_desc  # type: ignore

def get_ufs_features_support() -> UFSFeatureSupportUnion:
    dev_desc = get_device_descriptor()
    try:
        feat_support = getattr(import_module(_structs_path), f'UFSFeaturesSupport{_ufs_ver}')()
        feat_support.from_bytes(dev_desc.b31_ufs_features_support)
    except ModuleNotFoundError:
        _log.error(f"Module not found: {_structs_path}")
        raise PATTERN_ASSERT_MODULE_NOT_FOUND
    except AttributeError:
        _log.error(f"Attribute not found: UFSFeaturesSupport{_ufs_ver}")
        raise PATTERN_ASSERT_ATTR_NOT_FOUND
    return feat_support  # type: ignore

def get_extended_ufs_features_support() -> ExtendedUFSFeaturesSupportUnion:
    dev_desc = get_device_descriptor()
    try:
        feat_support = getattr(import_module(_structs_path), f'ExtendedUFSFeaturesSupport{_ufs_ver}')()
        feat_support.from_bytes(dev_desc.l79_extended_ufs_features_support)
    except ModuleNotFoundError:
        _log.error(f"Module not found: {_structs_path}")
        raise PATTERN_ASSERT_MODULE_NOT_FOUND
    except AttributeError:
        _log.error(f"Attribute not found: UFSFeaturesSupport{_ufs_ver}")
        raise PATTERN_ASSERT_ATTR_NOT_FOUND
    return feat_support  # type: ignore

def get_extended_write_booster_support() -> ExtendedWriteBoosterSupportUnion:
    dev_desc = get_device_descriptor()
    if not hasattr(dev_desc, 'w77_extended_write_booster_support'):
        _log.error(f"Attribute not found: w77_extended_write_booster_support")
        raise PATTERN_ASSERT_ATTR_NOT_FOUND
    try:
        wb_support = getattr(import_module(_structs_path), f'ExtendedWriteBoosterSupport{_ufs_ver}')()
        wb_support.from_bytes(dev_desc.w77_extended_write_booster_support)
    except ModuleNotFoundError:
        _log.error(f"Module not found: {_structs_path}")
        raise PATTERN_ASSERT_MODULE_NOT_FOUND
    except AttributeError:
        _log.error(f"Attribute not found: ExtendedWriteBoosterSupport{_ufs_ver}")
        raise PATTERN_ASSERT_ATTR_NOT_FOUND
    return wb_support  # type: ignore
