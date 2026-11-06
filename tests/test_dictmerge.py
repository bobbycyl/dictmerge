import pytest

from dictmerge import merge

base: dict = {
    "mixed-port": 7890,
    "dns": {
        "enable": True,
        "ipv6": True,
        "enhanced-mode": "fake-ip",
        "fake-ip-range": "28.0.0.1/8",
        "nameserver": ["https://dns.alidns.com/dns-query"],
    },
    "proxies": [
        {
            "name": "ss",
            "type": "ss",
            "server": "127.0.0.1",
            "port": 443,
            "password": "mihomo",
            "cipher": "none",
        },
    ],
    "proxy-groups": [
        {"name": "国内", "type": "select", "proxies": ["DIRECT"]},
    ],
    "rules": ["GEOIP,CN,DIRECT", "MATCH,home"],
}

base2: dict = {"dns": {"nameserver-policy": {"+.google.cn": ["1.1.1.1"]}}}


def test_merge():
    # 字典合并
    r = merge(base, {"dns": {"enable": False}})
    assert r["dns"]["enable"] is False
    assert r["dns"]["ipv6"] is True  # 未被覆盖
    assert r["dns"]["nameserver"] == base["dns"]["nameserver"]

    # 字典替换
    r = merge(base, {"dns!": {"enable": False}})
    assert r["dns"] == {"enable": False}

    # 列表合并
    r = merge(base, {"rules": ["MATCH,home", "DOMAIN,baidu.com,DIRECT", "MATCH,home"]})
    assert r["rules"] == ["GEOIP,CN,DIRECT", "MATCH,home", "DOMAIN,baidu.com,DIRECT"]

    # 列表替换
    r = merge(base, {"rules!": ["DOMAIN,baidu.com,DIRECT"]})
    assert r["rules"] == ["DOMAIN,baidu.com,DIRECT"]

    # 列表前插
    r = merge(base, {"+rules": ["DOMAIN,baidu.com,DIRECT"]})
    assert r["rules"] == ["DOMAIN,baidu.com,DIRECT", "GEOIP,CN,DIRECT", "MATCH,home"]

    # 列表后加
    r = merge(base, {"rules+": ["DOMAIN,baidu.com,DIRECT"]})
    assert r["rules"] == ["GEOIP,CN,DIRECT", "MATCH,home", "DOMAIN,baidu.com,DIRECT"]

    # '+' 遇到缺失 key：直接赋值，不产生空 list
    r = merge(base, {"+new-list": [1, 2]})
    assert r["new-list"] == [1, 2]

    # '+' 遇到 dict：报错
    with pytest.raises(TypeError):
        merge(base, {"+dns": {"x": 1}})

    # 深层 '!'：只替换 a.x
    r = merge({"a": {"x": 1, "y": 2}}, {"a": {"x!": 9}})
    assert r["a"] == {"x": 9, "y": 2}
    r = merge({"a": {"x": 1, "y": 2}}, {"a": {"x!": [1, 9]}})
    assert r["a"] == {"x": [1, 9], "y": 2}

    # 转义：+.google.cn 前插
    r = merge(base2, {"dns": {"nameserver-policy": {"+<+.google.cn>": ["8.8.8.8"]}}})
    assert r["dns"]["nameserver-policy"]["+.google.cn"] == ["8.8.8.8", "1.1.1.1"]

    # 转义：<+.google.cn> 合并
    r = merge(base2, {"dns": {"nameserver-policy": {"<+.google.cn>": ["8.8.8.8", "1.1.1.1", "8.8.8.8", "1.1.1.1"]}}})
    assert r["dns"]["nameserver-policy"]["+.google.cn"] == ["1.1.1.1", "8.8.8.8", "8.8.8.8"]

    # '<+.google.cn>+' 后加
    r = merge(base2, {"dns": {"nameserver-policy": {"<+.google.cn>+": ["8.8.8.8"]}}})
    assert r["dns"]["nameserver-policy"]["+.google.cn"] == ["1.1.1.1", "8.8.8.8"]

    # 列表双端插
    r = merge({"a": [1]}, {"+a+": [2, 1]})
    assert r["a"] == [2, 1, 1, 2, 1]

    # 同名键可重复覆写
    r = merge({"a": [1]}, {"+a": [2], "a!": [2]})
    assert r["a"] == [2]
    r = merge({"a": [1]}, {"a!": [2], "+a": [2]})
    assert r["a"] == [2, 2]

    # '!' 与 '+' 同时出现，+ 视为普通字符
    r = merge({"a": [1]}, {"+a!": [2]})
    assert r == {"a": [1], "+a": [2]}
