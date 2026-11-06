# dictmerge

深度合并字典

## 用法

```python
from dictmerge import merge
merged = merge(old, new1, new2)
```

## 规则

1. `key!`: 严格替换
2. `+key`: 向左添加（仅列表）
3. `key+`: 向右添加（仅列表）
4. `key`: 合并

列表合并规则：剔除覆写列表中与原始列表重复的元素后执行 `key+`