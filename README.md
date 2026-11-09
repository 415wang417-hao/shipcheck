# shipcheck

> 一条命令体检你的 GitHub 仓库，按 Elite20 的五个评分维度打出一份可执行的发货检查报告。

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)
![Tests](https://img.shields.io/badge/tests-63%20passed-brightgreen.svg)

---

## 解决什么问题

提交课程仓库之前，你通常要手动核对十几项：有没有 `README.md`？有没有 `LICENSE`？README 里写了安装步骤吗？有没有 AI 使用日志？复盘写了失败经验吗？

**没有 shipcheck：** 靠肉眼逐条对照评分表，漏项自己不知道，提交后才发现扣分。

**有了 shipcheck：** 一条命令扫描本地仓库，0.03 秒生成结构化报告，哪条不达标、怎么补，报告里直接说清楚。

---

## 快速开始

### 方式一：直接运行（无需安装）

```bash
git clone https://github.com/415wang417-hao/shipcheck.git
cd shipcheck
python -m shipcheck /path/to/your/repo
```

### 方式二：安装为命令

```bash
git clone https://github.com/415wang417-hao/shipcheck.git
cd shipcheck
pip install -e .
shipcheck /path/to/your/repo
```

### 常用参数

```bash
# 检查当前目录
shipcheck .

# 输出 JSON（方便接 CI）
shipcheck . --format json

# 只显示未通过的项
shipcheck . --only-failures

# 自动补齐缺失的脚手架文件（先预演，不写盘）
shipcheck . --fix

# 确认后真正写入
shipcheck . --fix --apply
```

---

## 示例

**输入：**

```bash
shipcheck ./my-project
```

**输出（节选）：**

```
shipcheck v1.0.0 — C5 GitHub Repository Checker
════════════════════════════════════════════════

📁 扫描目录: ./my-project

repoQuality（21/25）
  ✅ RQ01 README 存在且非单薄        — 4821 字符
  ✅ RQ02 README 一句话描述          — 已检测到描述段落
  ❌ RQ05 README 项目结构            — 未找到结构章节
  ✅ RQ07 LICENSE 开源协议           — MIT

aiUsage（14/20）
  ✅ AI01 AI_LOG.md 存在
  ✅ AI02 阶段覆盖 ≥3               — 检测到 5 个阶段
  ❌ AI03 prompt 原文留痕            — 未找到可识别的 prompt 块

─────────────────────────────────────────
总分: 87/100  等级: B
```

**完整规则分数与实测结果都以你的仓库为准，不写死。**

---

## 项目结构

```
shipcheck/
├── README.md               ← 本文件
├── LICENSE                 ← MIT
├── AI_LOG.md               ← AI 辅助开发日志
├── ATTRIBUTION.md          ← 借鉴来源说明
├── CHANGELOG.md            ← 版本更新记录
├── CONTRIBUTING.md         ← 贡献指南
├── CODE_OF_CONDUCT.md      ← 行为准则
├── SECURITY.md             ← 安全策略
├── SKILL.md                ← 作为技能被 Agent 调用时的说明
├── .gitignore
├── pyproject.toml          ← 包配置，版本号与此同步
├── shipcheck/              ← 核心包
│   ├── __init__.py         ← __version__ = "1.0.0"
│   ├── __main__.py         ← python -m shipcheck 入口
│   ├── cli.py              ← 参数解析、退出码、输出格式选择
│   ├── engine.py           ← Audit / CheckResult / compute_exit_code
│   ├── facts.py            ← 仓库事实收集（文件、章节、代码统计）
│   ├── rules.py            ← 31 条规则，唯一规则定义处
│   ├── scoring.py          ← 五维度加权计分与等级换算
│   ├── report.py           ← text / markdown / json 三种渲染
│   ├── md.py               ← Markdown 章节与代码块解析
│   └── fixer.py            ← --fix 脚手架生成与写盘保护
├── scripts/
│   └── run_check.py        ← 免安装直接运行脚本
├── docs/
│   └── img/                ← 预留目录，暂未放截图
├── examples/
│   └── sample_project/     ← 示例仓库（含 hello.py）
├── tests/                  ← unittest，63 个用例
│   ├── helpers.py          ← 内存夹具构造器
│   ├── test_rules.py
│   ├── test_engine.py
│   ├── test_facts.py
│   ├── test_fixer.py
│   ├── test_md.py
│   └── test_cli.py
└── .github/
    ├── ISSUE_TEMPLATE/
    └── PULL_REQUEST_TEMPLATE.md
```

---

## 技术栈

- 语言：Python 3.9+
- 依赖：仅标准库（`pathlib`、`json`、`argparse`、`re`、`difflib`），零第三方运行时依赖
- 测试：`unittest`（标准库自带，`python -m unittest discover -s tests -t .`）
- 质量门禁：`scripts/run_check.py` 可直接接入任意 CI（「必须」项不通过时退出码为 2）
- AI 集成：Antigravity（Claude Sonnet）辅助生成初稿、测试、文档，人工负责架构决策与边界修正

---

## 检查规则

31 条规则分五个维度，权重合计正好 100 分，与课程 rubric 一致。

| 维度 | 满分 | 说明 |
|------|------|------|
| `repoQuality` | 25 | README 完整度、LICENSE、.gitignore |
| `community` | 20 | 贡献指南、Issue/PR 模板、CHANGELOG、行为准则、CI、版本标识 |
| `artifactCompleteness` | 15 | 实际代码、测试、示例、入口、依赖声明、拿来说明 |
| `aiUsage` | 20 | AI 日志存在、阶段覆盖、prompt 留痕、迭代记录、与文件对应 |
| `reflectionQuality` | 20 | AAR 四要素、失败记录、改进方案、落地证据 |

<details>
<summary>展开全部 31 条规则</summary>

| 规则 ID | 维度 | 分级 | 权重 | 检查内容 |
|---------|------|------|------|----------|
| RQ01 | repoQuality | 必须 | 5 | README 存在且非单薄 |
| RQ02 | repoQuality | 必须 | 3 | README 一句话描述 |
| RQ03 | repoQuality | 必须 | 3 | README 安装/快速开始 |
| RQ04 | repoQuality | 必须 | 3 | README 使用示例 |
| RQ05 | repoQuality | 建议 | 2 | README 项目结构 |
| RQ06 | repoQuality | 建议 | 2 | README 技术栈 |
| RQ07 | repoQuality | 必须 | 4 | LICENSE 开源协议 |
| RQ08 | repoQuality | 必须 | 3 | .gitignore |
| CM01 | community | 建议 | 4 | 贡献指南 CONTRIBUTING |
| CM02 | community | 建议 | 4 | Issue 模板 |
| CM03 | community | 建议 | 3 | PR 模板 |
| CM04 | community | 建议 | 3 | CHANGELOG |
| CM05 | community | 建议 | 2 | 行为准则 CODE_OF_CONDUCT |
| CM06 | community | 建议 | 3 | CI 自动化 |
| CM07 | community | 建议 | 1 | 版本标识 |
| AC01 | artifactCompleteness | 必须 | 3 | 实际项目内容 |
| AC02 | artifactCompleteness | 建议 | 3 | 自动化测试 |
| AC03 | artifactCompleteness | 建议 | 2 | 示例/Demo |
| AC04 | artifactCompleteness | 建议 | 2 | 可运行入口 |
| AC05 | artifactCompleteness | 建议 | 2 | 依赖声明 |
| AC06 | artifactCompleteness | 必须 | 2 | 拿来说明 ATTRIBUTION |
| AC07 | artifactCompleteness | 建议 | 1 | 核心文件非空 |
| AI01 | aiUsage | 必须 | 6 | AI_LOG.md 存在 |
| AI02 | aiUsage | 建议 | 4 | 阶段覆盖 ≥3 |
| AI03 | aiUsage | 建议 | 4 | prompt 原文留痕 |
| AI04 | aiUsage | 建议 | 3 | 多轮迭代记录 |
| AI05 | aiUsage | 建议 | 3 | 与仓库文件对应 |
| RF01 | reflectionQuality | 建议 | 5 | AAR 四要素 |
| RF02 | reflectionQuality | 建议 | 5 | 失败与踩坑记录 |
| RF03 | reflectionQuality | 建议 | 5 | 可执行改进方案 |
| RF04 | reflectionQuality | 建议 | 5 | 复盘落地证据 |

</details>

「必须」项不通过时退出码为 2，「建议」项只影响得分不改变退出码，方便在 CI 里做硬门禁。

---

## 开发与测试

```bash
# 跑全部测试
python -m unittest discover -s tests -t .

# 用工具检查本仓库自己（自检，不是外部证据）
python -m shipcheck .
```

需要说明的是：用 shipcheck 检查 shipcheck 得分 100/100 属于自检结果，只能说明规则实现自洽；真正的外部证据是上面的 63 个 unittest 全绿记录。

---

## AI 生成说明

本项目使用 AI 辅助开发，完整交互记录与人工决策详见 [AI_LOG.md](./AI_LOG.md)。

## 借鉴来源

本项目参考了以下来源，详见 [ATTRIBUTION.md](./ATTRIBUTION.md)。

## License

[MIT](./LICENSE) © 2026 王艺燃
