---
name: shipcheck
description: 开源仓库发布体检。输入一个本地项目目录，输出 100 分制的「能不能发布到 GitHub」体检报告：五个维度逐条检查，给出缺口与修复命令。当用户说「检查我的 repo」「看看我的项目能不能开源发布」「C5 提交前自查」时使用。
---

# shipcheck：仓库发布体检技能

你（AI 助手）可以用本技能帮用户在把项目发布到 GitHub 之前做一次全面体检。

## 何时触发

- 用户说「帮我检查一下这个仓库/项目能不能发出去」
- 用户在提交 C5（GitHub Repository）挑战前需要自查
- 用户想知道自己的开源项目缺哪些要素（README/LICENSE/AI_LOG/贡献指南…）
- CI 里需要一道「仓库质量门槛」

## 怎么做

### 第 1 步：运行体检

在**用户项目根目录**执行（零依赖，Python ≥ 3.9）：

```bash
python -m shipcheck <项目路径>
```

> 前提：用户项目里没有 shipcheck 包时，先在 shipcheck 仓库根目录运行，
> 或用 `python <shipcheck仓库>/scripts/run_check.py <项目路径>`。

输出：总分（100 分制）、五个维度得分、必需项缺口、修复建议。

### 第 2 步：解读报告

五个维度对应 C5 评分标准：

| 维度 | 满分 | 看什么 |
| --- | ---: | --- |
| 仓库质量 | 25 | README 完整度、LICENSE、.gitignore |
| 社区要素 | 20 | CONTRIBUTING、issue/PR 模板、CI、CHANGELOG |
| 产物完整性 | 15 | 真实代码、测试、示例、可运行入口 |
| AI 使用质量 | 20 | AI_LOG.md 的阶段/prompt/迭代记录 |
| 复盘质量 | 20 | AAR 四要素、失败经验、改进方案、落地证据 |

### 第 3 步：给出修复建议

- 缺社区文件 → 建议 `python -m shipcheck . --fix --apply` 生成骨架，然后**人工填充**（骨架含 TODO，体检会识别未填充状态）；
- README 缺章节 → 按报告里每条规则的 `↳ 提示` 逐条补；
- AI_LOG 太薄 → 引导用户补：阶段表格、prompt 原文、失败记录、AAR 四要素。

### 第 4 步：复检

修复后重新运行体检，确认：

- 总分 ≥ 80（CI 默认门槛）
- 必需项全部通过（否则退出码为 1）

## 输出格式

| 命令 | 用途 |
| --- | --- |
| `python -m shipcheck .` | 终端报告 |
| `python -m shipcheck . -f markdown -o REPORT.md` | Markdown 报告 |
| `python -m shipcheck . -f json` | JSON（CI 集成） |
| `python -m shipcheck . --list-rules` | 全部规则与权重 |
| `python -m shipcheck . --fix` | 可补齐文件清单（干跑） |

## 注意

- 工具**只读**：不改用户项目，除非显式 `--fix --apply`（只新建、不覆盖）。
- 判断要基于报告输出，不要凭空猜测用户仓库缺什么。
- 若用户项目就是 shipcheck 本身（自检），预期结果应为满分。
