# ATTRIBUTION.md — 借鉴来源说明

> 遵循 Elite20 拿来主义原则：公开借鉴来源，给予应有归属。

---

## 借鉴内容清单

### 1. 检查规则设计

**来源：** Elite20 C5 CHALLENGE.md 中的"十一、检查清单"
**借鉴内容：** 8 条必须项 + 4 条加分项的分类框架
**使用方式：** 直接作为 `rules.py` 中规则集的设计基础
**链接：** 课程内部资料

---

### 2. Python 项目结构规范

**来源：** [Python Packaging User Guide](https://packaging.python.org/)
**借鉴内容：** `pyproject.toml` 配置格式、`src` layout vs flat layout 的选择依据
**使用方式：** 参考选择了 flat layout，简化安装

---

### 3. CLI 工具设计模式

**来源：** Python 标准库 [argparse 文档](https://docs.python.org/3/library/argparse.html)
**借鉴内容：** 子命令、格式化帮助文本的写法
**使用方式：** `__main__.py` 的 ArgumentParser 配置

---

### 4. README 模板结构

**来源：** Elite20 C5 CHALLENGE.md 第 3.2 节"README.md 标准模板"
**借鉴内容：** 一句话说明、解决什么问题、快速开始、示例、项目结构等章节顺序
**使用方式：** 直接按此结构撰写本项目 README

---

### 5. GitHub Actions CI 配置

**来源：** GitHub 官方文档 [Using workflows](https://docs.github.com/en/actions/using-workflows)
**借鉴内容：** `push` + `pull_request` 触发器写法、`actions/checkout@v4` + `actions/setup-python@v5` 组合
**使用方式：** `.github/workflows/ci.yml` 的基础框架

---

### 6. Issue 模板格式

**来源：** GitHub 官方文档 [Configuring issue templates](https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests)
**借鉴内容：** Bug report 和 Feature request 的 YAML front matter 格式
**使用方式：** `.github/ISSUE_TEMPLATE/` 下两个模板文件

---

### 7. 终端颜色输出方案

**来源：** [Rich library 文档](https://rich.readthedocs.io/) 的设计理念（未直接使用该库）
**借鉴内容：** 分层展示（必须项 / 加分项）、emoji 状态指示的 UX 设计
**使用方式：** `report.py` 的输出格式设计（用标准库实现，未引入 rich 依赖）

---

## 未借鉴声明

以下内容为原创开发，未参考外部来源：
- `facts.py` 中 README 章节检测的正则逻辑
- `rules.py` 中 `has_examples` 的"非空目录"检测逻辑
- Windows/Linux 跨平台路径兼容处理
