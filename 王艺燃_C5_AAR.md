# 王艺燃_C5_AAR — shipcheck 项目复盘

> 学号 2025105400102 ｜ 挑战 C5「GitHub Repository」
> 仓库：https://github.com/415wang417-hao/shipcheck

---

## 1. 目标与预期（Anticipated）

**开始时的预期**：用 AI 把一个"检查 GitHub 仓库是否符合 C5 要求"的小工具做出来，推到 GitHub 就完成 C5。

**修正后的真实目标**（第 2 天调整）：不是"做出能跑的代码"，而是"别人 clone 下来 5 分钟内能跑、能看懂、愿意用"。验收标准从"程序不报错"升级为四条可观测指标：

| 指标 | 目标值 |
|------|--------|
| 测试通过 | 全部用例通过，0 失败 |
| 可复现 | README 命令逐条复制可执行 |
| 文档自洽 | 文档里的模块名/规则条数与代码一致 |
| 仓库合规 | 用 shipcheck 检查自己的仓库得满分 |

---

## 2. 实际结果（Actual）

**做成了什么**

- `shipcheck` 是一个零依赖 Python CLI：输入本地仓库路径，输出结构化"发货检查"报告（31 条规则、5 个评分维度、0.03 秒跑完）。
- 第 6 阶段自检：`python -m shipcheck .` 对自身仓库返回 **100/100**。
- 测试：`python -m unittest discover` → **Ran 63 tests / OK**。
- 仓库上线：public，36 个文件，含 README / LICENSE / CONTRIBUTING / CODE_OF_CONDUCT / SECURITY / CHANGELOG / Issue 模板 / PR 模板 / AI_LOG / ATTRIBUTION / examples。
- 交付物 4 件齐全，文件名统一为 `王艺燃_C5_*`。

---

## 3. 差异与不足（Difference）— 真正踩到的坑

### 坑 1：文档写得比代码漂亮，但写错了

README 与 AI_LOG 里出现了 **代码里根本不存在** 的模块名（`checker.py` / `reporter.py` / `test_checker.py`），规则条数写成"33 条"，而代码实际是 **31 条**、模块是 `engine/facts/rules/fixer/report/md/scoring`。

**根因**：文档是在 v0.1.0 骨架阶段由 AI 生成的，v1.0.0 重构后没有回写文档。AI 生成文档时会"顺着上一版想象"，不会主动核对当前代码。

**代价**：如果没发现，评审只要打开文件列表就能看出文档在编造——这是"文档质量"最致命的失败模式。

### 坑 2：测试一直是红的，我却以为"能跑就是好了"

第一次真跑 `unittest`：**7 个失败 + 1 个错误，共 63 个用例**。之前只在几个手工例子上验证过，就以为项目"已完成"。

**根因**：把"我手动试过没报错"当成"测试通过"。手工验证只覆盖我想得到的分支，测试才暴露断言层面的真实差异。

### 坑 3：本机 git 是坏的，我却先怀疑代码

`git` 在 PATH 里但 `git.exe` 不存在，也没有 GitHub 凭据——推不上去。中途浪费了一轮排查在"是不是仓库配置写错了"。

**修复**：装用户级 Git 2.56.0.4 + GitHub CLI 2.103.3，走设备码授权推上去。

### 坑 4：CI 工作流先被拒收，补齐 scope 后才上线

第一次推 `.github/workflows/ci.yml` 被 GitHub 拒收，原话是 "refusing to allow an OAuth App to create or update workflow ... without `workflow` scope"——当时的 token 只有 `gist / read:org / repo`。我先退一步：把 README 徽章换成**真实存在的静态测试徽章**（`Tests-63 passed`），不留"CI 在跑"这种没发生的表述。

**修复**：`gh auth refresh -s workflow` 重新授权拿到 `workflow` scope 后重推，工作流上线，徽章同时换成指向真实 Actions 运行的动态徽章。

**这条坑后来还挖出一个更值钱的问题**：CI 第一次跑就红了——`facts.py` 的长度规则按字节计长，Windows 检出是 CRLF、Linux 是 LF，同一个文件两端算出不同长度，ubuntu 绿、windows 红。这说明"本地全绿"从来不等于"能交付"，异构环境才会暴露这类差异。

### 坑 5：交付物缺 AAR

平台 `required_deliverables` 只列了 README / repo 链接 / AI 日志 / 拿来说明 4 件，我按平台清单交，漏掉了 rubric 里 `reflectionQuality`（20 分）明确要求的 AAR 复盘——平台因此返回 `needs_revision`。

**根因**：把"平台必交清单"当成"评分清单"。平台的 required 是**门槛**，rubric 的 dimensions 才是**打分项**，两者不一致时必须按更严的那份准备。

---

## 4. 改进与下一步（Improvement）

| 问题 | 改进动作 | 状态 |
|------|----------|------|
| 文档与代码脱节 | 用脚本断言替换次数，改完全局搜索旧模块名/旧条数，规范化字符数逐项比对 | 已做 |
| 测试形同虚设 | 交付前必跑 `unittest discover`，失败即修，不接受"手工试过" | 已做 |
| 环境不可用 | 交付前置检查：`git --version`、`gh auth status`、远端可达 | 已做 |
| 声称与实际不符 | 所有徽章/数字改为可复现的真实输出，未验证不写 | 已做 |
| 只按平台清单交 | 建立"平台 required ∪ rubric dimensions"合并清单，逐项打勾 | 已做（补 AAR） |

**下一次的可迁移规则**：交付前跑三件事——① 真跑测试；② 文档里的每个专有名词都能在代码里搜到；③ 用平台的 required 和 rubric 两份清单取并集自查。

---

## 5. 复盘落地证据

- 测试：本地 `Ran 63 tests / OK`（EXIT=0）；CI 在 `ubuntu-latest` 与 `windows-latest` 上各跑一遍，均 OK
- 自检：`python -m shipcheck .` → 100/100
- CI：GitHub Actions `CI` 工作流 run 44891338869（提交 35064b7）双平台全绿；首轮失败 run 44890246729 的过程见坑 4
- 文档规范化：README / CHANGELOG 本地与远端逐字一致
- 旧模块名/旧规则条数残留：0 处
- 仓库：`main = 35064b7`，本地 HEAD 与 `ls-remote` 一致，无 `__pycache__` 入库

---

## 6. 失败经验沉淀（给下一个项目的自己）

1. **AI 会顺着旧文档编新事实**：任何"数字/文件名/命令"类断言，必须由脚本从真实产出里取，不能由模型回忆。
2. **"能跑"和"测过"是两件事**：没有失败过的测试跑，说明你没写测试。
3. **工具链也是交付面**：git/凭据/权限不通，代码再好也发不出去，开局就该验证一次。
4. **清单取并集**：平台要求是及格线，rubric 是得分线，别用及格线交卷。


---

> **入库说明（2026-11-21）**：本文件与 `王艺燃_C5_AI日志.md`、`王艺燃_C5_拿来说明.md`、`王艺燃_C5_AAR.md` 一并提交进本仓库，以便按挑战交付物清单核验。文中引用的 `main = 35064b7` 与 CI run `44891338869` 是功能代码定版时的记录；随后新增的这几个 Markdown 文档不改变任何代码与测试结果（仍为 63/63 全绿）。
