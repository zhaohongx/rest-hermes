# Changelog

本项目遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，版本号遵循 [Semantic Versioning](https://semver.org/lang/zh-CN/)。

---

## [Unreleased]

### 计划中
- intent-classifier v1.0 转正（取决于 D14 评估结果）
- formalize v4.0 toolkit-mode 转正
- preview 文件升 active（tool-contracts.md, pipeline-recipes.md）

---

## [P3-Beta] - 2026-05-16

> ⚠️ Beta 阶段：默认关闭，仅在 dogfood 触发时启用。评估日 2026-05-30，硬截止 2026-06-15。

### 新增（Added）
- **intent-classifier v1.0.0**（beta）：意图分类技能，4 组分类法（A/B/C/D），160 条测试用例
  - `references/intent-taxonomy.md` — 意图分类法定义
  - `references/decision-rules.md` — O(1) 规则匹配层
  - `tests/classification-cases.md` — 160 条分类场景
  - `tests/classifier-edge-cases.md` — 6 条历史误判档案
- **formalize v4.0.0**（beta, toolkit-mode）：拆分为 8 个独立工具的工具包模式
  - `references/tool-contracts.md`（beta）— 8 工具契约
  - `references/pipeline-recipes.md`（beta）— 8 跨技能管道配方
- **orchestration/** 编排层（beta）
  - `hermes-agent-skill-authoring/references/orchestration-protocol.md` — handoff schema + error codes + metrics
- **docs/beta-program/** dogfood 文档
  - `dogfood-guide.md`
  - `feedback-template.md`
  - `promotion-checklist.md`
  - `mid-term-check-sop.md`
- **skill-authoring** 增加编排协议章节
- **glossary.md** — 19 个标准术语拼写

### 配置
- 所有 P3 文件 `enabled_by_default: false`
- 触发方式：输入前缀 `#beta` / `[experimental]`，或 dogfood 团队白名单
- Fallback：任何 P3 错误 → 降级到 formalize v3.1

### 不影响
- formalize v3.1（active）调用方零感知
- v3.0 调用方零感知（v3.1 完全向后兼容）

### 风险与回退
- P0 事件触发：`git revert <commit-2-hash>`，P1+P2 不受影响
- 转正决策：见 `docs/beta-program/promotion-checklist.md`

---

## [3.1.0] - 2026-05-14

### 变更（Changed）
- **formalize**：v3.0 → v3.1（active，向后兼容）
  - S0 跳过判定扩充 5 类（创意/情感/知识/翻译/总结）
  - S2.3 语义张力检测 + contradiction-heuristics.md
  - S7.1 反例触发机制（⚠️=0 且 L2+ → 强制重审）
  - 收敛 skeleton-card.md 职责，抽离独立的 confidence-rubric.md
  - templates.md 拆分为 templates/ 子目录（L1/L2/L3/stem/_shared）
  - stem-eng-sub-template.md 引入 `@extends` 关系链
- **references/** 重构为 14 个单一职责文件

### 弃用（Deprecated）
- `references/templates.md`（保留为兼容索引，计划 v4.1 移除）

### 新增（Added）
- **intent-classifier** skill 基础设施（P-1 always-on 路由层，P3 beta 启用）
- `references/confidence-rubric.md`
- `references/templates/L1.md` `L2.md` `L3.md` `stem.md` `_shared.md`
- `references/v3-to-v4-migration.md`（含灰度策略 + 指标采集方案）
- `tests/regression-cases.md`（25 条回归用例）
- CI 校验脚本：`ci/check-frontmatter.py` `check-status-references.py` `check-glossary.py`
- `ci/frontmatter-schema.json`
- `glossary.md`（19 个标准术语）

### 修复（Fixed）
- skeleton-card.md 历史过载问题（5+ 关注点 → 单一职责拆分）
- templates.md 难以独立演进各 level 的问题
- formalize 误触发创意/情感/翻译等非结构化场景

### 测试
- 回归测试：25/25 通过
- Frontmatter：14/14 通过 schema 校验
- Cross-reference：0 死链
- 文件大小：max 13.5KB（远低于 50KB 上限）

### 兼容性
- v3.0 调用方：零修改
- v3.1 新特性：通过显式 `@reference` 路径 opt-in
- v4.0 preview 文件已标记 `@status: beta`（不自启）
