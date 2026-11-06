from dictmerge.dictmerge import merge, parse_key

# 1) 先确认解析
p = parse_key("+<+.google.cn>")
print("parse:", p)
assert p.key == "+.google.cn", f"key 错误: {p.key!r}"
assert p.left is True and p.right is False, f"left/right 错误: {p.left}, {p.right}"
assert p.strict is False
assert p.escaped is True

# 2) 再测合并
base2 = {"dns": {"nameserver-policy": {"+.google.cn": ["1.1.1.1"]}}}
r = merge(base2, {"dns": {"nameserver-policy": {"+<+.google.cn>": ["8.8.8.8"]}}})

print("result:", r["dns"]["nameserver-policy"])

# 如果结果里有 '<+.google.cn>' 这个 key，说明 ①/③ 的转义判断有问题
print("keys   :", list(r["dns"]["nameserver-policy"].keys()))

assert r["dns"]["nameserver-policy"]["+.google.cn"] == ["8.8.8.8", "1.1.1.1"]
