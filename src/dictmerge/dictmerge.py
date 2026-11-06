import json
from collections.abc import Hashable
from copy import deepcopy
from functools import lru_cache, reduce
from typing import Any, NamedTuple

_MISSING = object()


class ParsedKey(NamedTuple):
    key: str
    left: bool = False  # +key
    right: bool = False  # key+
    strict: bool = False  # key!
    escaped: bool = False  # 避免 <key> 与 key 同名


@lru_cache(maxsize=1024)
def parse_key(k: str) -> ParsedKey:
    """解析键

    :param k: 键
    :return: 解析后的键对象
    """
    if not k:
        raise ValueError("empty key not allowed")

    strict = k[-1] == "!"
    if strict:
        k = k[:-1]
        if not k:
            raise ValueError("empty key with '!' not allowed")
        left = right = False
    else:
        # strick 与 left/right 不能同时为 True
        left = k[0] == "+"
        right = k[-1] == "+"
        if left:
            k = k[1:]
        if right:
            k = k[:-1]
        if not k:
            raise ValueError("empty key with '+' not allowed")

    # 处理转义
    if k[0] == "<" and k[-1] == ">":
        k = k[1:-1]
        if not k:
            raise ValueError("empty key with '<>' not allowed")
        return ParsedKey(k, left, right, strict, True)

    return ParsedKey(k, left, right, strict, False)


def _make_hashable_key(v: Any) -> Hashable:
    try:
        return hash(v)
    except TypeError:
        return json.dumps(v, sort_keys=True, default=str)


def _as_list[_T](x: _T | list[_T]) -> list[_T]:
    return x if isinstance(x, list) else [x]


def _merge_value(old: Any, new: Any, p: ParsedKey) -> Any:
    if p.strict:
        return deepcopy(new)

    if isinstance(old, list):
        new = _as_list(new)

        if not (p.left or p.right):
            old_h = {_make_hashable_key(v) for v in old}
            dedup_new = [v for v in new if _make_hashable_key(v) not in old_h]
            return _merge_value(old, dedup_new, p._replace(left=False, right=True, strict=False))

        res = []
        if p.left:
            res.extend(new)
        res.extend(old)
        if p.right:
            res.extend(new)
        return res

    if isinstance(old, dict):
        if not isinstance(new, dict):
            raise TypeError(f"cannot merge dict with {type(new).__name__}: {p.key}")
        if p.left or p.right:
            raise TypeError(f"'+' not allowed with dict: {p.key}")
        return merge_one(old, new)

    # 其他情况（如 old 为 None），直接返回 new
    return deepcopy(new)


def merge_one(base: dict, override: dict) -> dict:
    """深度合并两个字典

    :param base: 原始字典
    :param override: 覆写字典
    :return: 合并后的字典
    """
    parsed_override: dict[ParsedKey, Any] = {parse_key(k): v for k, v in override.items()}
    result = deepcopy(base)
    for p, new_v in parsed_override.items():
        result[p.key] = _merge_value(result.get(p.key, _MISSING), new_v, p)

    return result


def merge(base: dict, *override: dict) -> dict:
    """递归深度合并

    规则:
        1. key!: 严格替换
        2. +key: 向左添加（仅列表）
        3. key+: 向右添加（仅列表）
        4. key: 合并

    列表合并规则：剔除覆写列表中与原始列表重复的元素后执行 key+

    :param base: 原始字典
    :param override: 覆写字典
    :return: 合并后的字典
    """
    return reduce(merge_one, override, base)
