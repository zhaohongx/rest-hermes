# Hermes Agent 术语词典

> **定位**：项目内所有文档、代码注释、技能定义中高频术语的**唯一权威拼写**。
> **CI 校验**：术语扫描脚本可在 `scripts/check_glossary.py`（待创建）中读取本词典并检测违规。

---

## 核心术语

| 术语 | 正确拼写 | 常见错误 | 类别 |
|------|---------|---------|------|
| SpecDocument | `SpecDocument` | SpeDocument / Spec Document / specdocument | 类型名 |
| formalize | `formalize` | Formalize / formalise / Formalise | 技能名 |
| intent-classifier | `intent-classifier` | IntentClassifier / intent_classifier / Intent Classifier | 技能名 |
| Hermes | `Hermes` | hermes / HERMES / Hermès | 产品名 |
| Hermes Agent | `Hermes Agent` | hermes-agent / HermesAgent / hermes agent | 产品全称 |
| orchestrator | `orchestrator` | Orchestrator / orchastrator / orchestator | 组件名 |
| SKILL.md | `SKILL.md` | skill.md / SKILL.MD / Skill.md | 文件名 |
| handoff | `handoff` | hand-off / handOff / hand off | 协议名 |
| exposed_tools | `exposed_tools` | exposedTools / ExposedTools / exposed-tools | frontmatter 字段 |
| reference_loading_policy | `reference_loading_policy` | referenceLoadingPolicy / ref-loading-policy | frontmatter 字段 |

## 状态标记

| 标记 | 正确拼写 | 语义 |
|------|---------|------|
| `@status: preview` | `@status: preview` | 文件内容为预览版，不应被生产引用 |
| `@status: beta` | `@status: beta` | 功能已完成但默认不启用，dogfood 期 |
| `@status: active` | `@status: active` | 生产可用 |
| `@extends:` | `@extends: path/to/file.md` | 模板继承关系声明 |

## 符号约定

| 符号 | Unicode | 语义 | 替代禁止 |
|------|--------|------|---------|
| ✓ | U+2713 | 已确认/已满足 | 不可用 ✅ |
| ⚠️ | U+26A0 U+FE0F | 不确定/需确认 | 不可用 ❗ |
| ✗ | U+2717 | 缺失/不满足 | 不可用 ❌ |

## 文件路径约定

| 路径模式 | 用途 |
|---------|------|
| `skills/<category>/<name>/SKILL.md` | 技能定义 |
| `skills/<category>/<name>/references/` | 技能参考文件 |
| `skills/<category>/<name>/tests/` | 技能测试用例 |
| `references/templates/` | 模板子目录 |
| `references/templates/_shared.md` | 跨模板共享片段（下划线前缀 = 非独立调用） |

## 版本号约定

遵循 [SemVer 2.0](https://semver.org/lang/zh-CN/)：`MAJOR.MINOR.PATCH`

| 变更类型 | 版本号 | 示例 |
|---------|--------|------|
| 兼容性破坏变更 | MAJOR | 1.0.0 → 2.0.0 |
| 向后兼容新增 | MINOR | 1.0.0 → 1.1.0 |
| 向后兼容修复 | PATCH | 1.0.0 → 1.0.1 |
