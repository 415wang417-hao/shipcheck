# Contributing to shipcheck

感谢你有兴趣为 shipcheck 做贡献！ 🎉

这份指南面向所有人——无论你是第一次参与开源项目，还是经验丰富的开发者。

---

## 如何贡献

### 方式 1：提 Issue（最简单）

发现 bug、有功能想法、或文档不清楚？
直接 [开一个 Issue](https://github.com/415wang417-hao/shipcheck/issues/new/choose)。

**好的 Issue 包含：**
- 你在做什么
- 期望发生什么
- 实际发生了什么
- 你的操作系统和 Python 版本

---

### 方式 2：贡献新检查规则

shipcheck 的核心价值在于规则集。如果你发现某个 C5 要求没有被检测到，可以贡献一条新规则：

1. Fork 本项目
2. 在 `shipcheck/rules.py` 中按照现有格式添加新规则函数
3. 在 `tests/test_rules.py` 中添加对应测试
4. 更新 `README.md` 中的"检查规则"表格
5. 提交 PR

**规则函数格式：**

```python
def has_your_rule(repo_path: Path) -> tuple[bool, str]:
    """检查 <你的规则描述>."""
    # ... 检查逻辑
    if condition:
        return True, "通过原因"
    return False, "失败原因及建议"
```

---

### 方式 3：改进文档

README 有歧义？示例不够清楚？直接提 PR 修改 Markdown 文件。

---

## 开发环境设置

```bash
git clone https://github.com/415wang417-hao/shipcheck.git
cd shipcheck
pip install -e ".[dev]"
```

**运行测试：**

```bash
pytest tests/ -v
```

**测试单个文件：**

```bash
pytest tests/test_rules.py -v
```

---

## 代码风格

- 遵循 PEP 8
- 函数和类必须有 docstring
- 新规则必须附带测试
- Commit message 格式：`type: 简短描述`（如 `feat: add has_wiki rule`）

---

## 行为准则

- 保持友善和包容
- 欢迎任何技术水平的贡献者
- 对建议持开放态度

---

**有问题？** 在 Issue 里问，或者直接在 PR 中留言。我们很乐意帮助！
