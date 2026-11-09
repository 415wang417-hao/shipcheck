# 安全策略（Security Policy）

## 支持的版本

| 版本 | 支持状态 |
| --- | --- |
| 1.0.x | ✅ 支持 |

## 报告漏洞

发现安全漏洞请**不要开公开 Issue**，而是：

1. 通过 [GitHub Security Advisories](https://github.com/415wang417-hao/shipcheck/security/advisories/new) 提交；
2. 或邮件联系维护者（在仓库拥有者主页查看邮箱）。

我们会尽快回复（目标 72 小时内），修复后会在 [CHANGELOG.md](./CHANGELOG.md) 中致谢报告者。

## 安全设计说明

shipcheck 是一个**只读**的本地体检工具：

- 只扫描你指定的目录，不联网、不上传任何数据；
- `--fix --apply` 只会**新建**缺失文件，从不覆盖或删除已有文件；
- 生成的骨架文件内容固定（模板 + 项目名 + 年份），不执行任意代码。

如果你发现以上任何一条被违反，请按上面的流程报告。
