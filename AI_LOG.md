# AI_LOG.md — shipcheck 开发 AI 使用日志

> 本项目在 Elite20 C5 挑战框架下开发，遵循 AI-First 原则。
> 所有 AI 交互均记录于此，以保证透明度与可追溯性。

---

## 总览

| 阶段 | 使用工具 | 交互轮次 | 人工介入程度 |
|------|---------|---------|------------|
| 项目规划 | Antigravity (Claude Sonnet) | 3 轮 | 高（决策由人确定） |
| 核心代码 | Antigravity (Claude Sonnet) | 8 轮 | 中（人工审校 + 修正边界情况） |
| 测试编写 | Antigravity (Claude Sonnet) | 6 轮 | 中（人工补充边界测试与夹具修复） |
| 文档撰写 | Antigravity (Claude Sonnet) | 5 轮 | 低（AI 生成，人工审校） |
| 代码审查 | Antigravity (Claude Sonnet) | 2 轮 | 高（人工决定是否采纳建议） |
| 复盘与对齐 | Antigravity (Claude Sonnet) | 3 轮 | 高（人工核对每条说法与真实文件） |

---

## 阶段 1：项目规划（2026-11-05）

### Prompt

```text
我需要做 C5 GitHub Repository 挑战。
挑战要求创建一个真实的项目，别人 clone 后 5 分钟内能跑起来。
我想做一个工具，帮助检查 GitHub repo 是否满足 C5 的所有要求。
请帮我设计项目架构。
```

### AI 输出摘要

AI 建议了以下架构：
- 核心模块：`facts.py`（扫描事实）+ `rules.py`（规则）+ `report.py`（输出）
- CLI 入口：`__main__.py`
- 纯标准库，降低安装门槛

### 人工决策

- 采纳：模块化架构，事实收集与规则判定分离
- 采纳：纯标准库（无第三方运行时依赖）
- 未采纳：AI 建议用 `click` 做 CLI，改为 `argparse`（减少依赖）

---

## 阶段 2：核心代码多轮迭代（v0.1.0 → v1.0.0）

- **第 1 轮（基础架构）**：设计 `facts.py` 的 `Facts` 数据流与 `engine.py` 的 `Audit`/`CheckResult` 评估引擎，把「读仓库」和「判规则」彻底分开，重构修复了章节解析的深层递归问题。
- **第 2 轮（规则实现）**：实现全部 31 条规则，按五个维度分组落入 `rules.py`；针对 Windows 平台 GBK 编码做兼容重构，修复控制台乱码。
- **第 3 轮（CLI 与修复器）**：新增 `--fix` / `--apply` 脚手架生成能力（`fixer.py`），重构 `cli.py` 的退出码逻辑：必须项不通过返回 2，仅得分低于阈值也返回 2。
- **第 4 轮（计分与输出）**：抽出 `scoring.py` 做五维度加权（合计 100 分），`report.py` 支持 text / markdown / json 三种渲染。

---

## 阶段 3：测试编写（2026-11-05）

### Prompt

```text
帮我为 facts.py 和 rules.py 写 unittest 测试，
用 tests/helpers.py 里的内存夹具构造仓库快照，
覆盖：全部规则通过 / 单条规则失败 / 边界情况。
```

### AI 输出摘要

生成了 `tests/test_rules.py`、`tests/test_engine.py`、`tests/test_facts.py`，后续补齐 `test_fixer.py`、`test_md.py`、`test_cli.py`，当前共 63 个用例。

### 人工补充

- 手动添加 Windows 路径分隔符测试
- 手动区分「空目录」与「完全不存在目录」两种输入
- 手动修正夹具：早期夹具假设了实现并不具备的行为（见复盘第 3 条）

---

## 阶段 4：文档撰写（2026-11-05）

### Prompt（README）

```text
根据以下文件结构和代码，帮我写符合 C5 标准的 README.md，
包含：一句话说明、问题背景、快速开始、示例输出、项目结构、技术栈、规则表。
```

### Prompt（CONTRIBUTING.md）

```text
帮我写 CONTRIBUTING.md，
面向非专业开发者，解释如何提 Issue、如何贡献新规则。
```

### Prompt（CHANGELOG.md）

```text
帮我写 CHANGELOG.md 的 1.0.0 条目，
按 Added / Changed / Fixed 分组。
```

---

## 阶段 5：代码审查（2026-11-05）

### Prompt

```text
请作为资深工程师 review 整个项目：
- 安全问题
- 代码风格（PEP 8）
- 文档完整性
- 是否真的能在 5 分钟内让人跑起来
```

### AI 反馈摘要

- `facts.py` 缺少对 `PermissionError` 的捕获 → 已修复
- 命令行帮助信息不够清晰 → 已改善 argparse description
- 代码结构：通过
- PEP 8：通过（AI 目检，未安装 flake8）

---

## 阶段 6：AAR 复盘与文档对齐（2026-11-06）

### 1. 目标与预期

- **预期目标**：做一个零外部依赖的仓库体检 CLI，学生提交 C5 前能自动核查评分项，clone 后 5 分钟内跑起来，单次体检 < 0.1 秒。
- **交付预期**：完整文档、单元测试、CI 工作流、`--fix` 脚手架。

### 2. 实际结果

- **产出**：`shipcheck v1.0.0`，31 条规则、5 维度加权计分（合计 100 分）、3 种输出格式、`--fix --apply` 自动补齐。
- **性能**：纯标准库，单次体检约 0.03 秒。
- **测试**：63 个 unittest 用例全绿。

### 3. 差异与不足

- **认知偏差**：最初以为十几条规则就够，实际按 rubric 五维度展开后需要 31 条才能覆盖完整。
- **技术不足**：早期忽略 Windows 控制台编码，以及 `.github` 目录被 `os.walk` 误判为 `.git` 前缀的边界问题。
- **文档与实现脱节（本轮发现并已修）**：README 早期版本把模块写成 `checker.py` / `reporter.py`，与实际 `facts.py` / `report.py` 不符；规则数曾同时出现 12、33、31 三个数字；示例输出里的版本号仍是 `v0.1.0`；模块文档提到 `tests/fixtures/bare_repo/` 但项目实际用 `tests/helpers.py` 内存夹具。

### 4. 改进与下一步

- [ ] 规则扩展：增加对 CI 配置（多矩阵构建、pre-commit）的覆盖度校验
- [ ] Web UI：在 C6 阶段把 shipcheck 包成轻量 Web App，输入仓库链接在线体检
- [ ] 修复增强：`--fix` 按仓库主语言自动生成对应的 `.gitignore` 与工作流
- [ ] 文档同步：每次改规则数或模块名，必须在 README、AI_LOG、CHANGELOG 三处同时更新

### 5. 复盘落地证据

| 复盘结论 | 落地动作 | 可验证位置 |
|---------|---------|-----------|
| 模块名与文档不符 | README 项目结构按真实 10 个模块重写 | `README.md` 项目结构节 |
| 规则数是 31 条 | README 规则表逐条列出 ID/维度/权重 | `README.md` 检查规则节 |
| 测试夹具假设了实现没有的行为 | 修 `test_rules.py` / `test_cli.py` / `test_engine.py` / `test_fixer.py`，并修 `rules.py` 两条真实缺陷 | `tests/` 63 用例全绿 |
| 自检分数不能当外部证据 | README 明示 100/100 为自检，另附 unittest 记录 | `README.md` 开发与测试节 |

---

## 失败经验记录

1. **第一版 `report.py` 在 Windows Terminal 下 emoji 显示乱码**
   - 原因：Windows 控制台默认编码问题
   - 解决：输出前强制 `sys.stdout.reconfigure(encoding='utf-8')`

2. **最初设计想直接检查 GitHub URL（走 GitHub API）**
   - 原因：依赖网络、需要 token，不满足「5 分钟能跑」
   - 解决：改为检查本地目录，更简单、更可复现

3. **测试先于实现语义写死，导致 7 个失败 + 1 个错误**
   - 原因：夹具按"我以为的规则"写，而不是按代码真实语义写
   - 解决：逐条读 `rules.py` / `fixer.py` / `engine.py` 确认真实行为，属于真实缺陷的改代码（RQ02、RF02），属于夹具过期的改测试

---

## 结论

AI 在本项目中承担了：
- 约 70% 的初始代码生成
- 约 80% 的文档初稿

人工承担了：
- 100% 的架构决策
- 100% 的边界情况识别与修正
- 100% 的最终审校与测试验证
