# formalize v3.x → v4.0 迁移指南

> **v3.1 支持截止**：2026-08-01
> **迁移窗口**：2026-05 至 2026-08（3 个月并存期）

---

## 一、变更总览

| 维度 | v3.1 | v4.0 |
|------|------|------|
| 架构 | 单体流程（S0-S8 串行） | 工具库 + 管道 |
| 调用方式 | 只能全量执行 | 可按需调用单个工具 |
| 默认输出 | `visible`（全部给用户看） | `hybrid`（⚠️给用户，完整 spec 给下游） |
| 跨技能协作 | 不支持 | 通过 `exposed_tools` + `pipelines` 协作 |
| frontmatter | 简版 | 含 exposed_tools/pipelines/deprecation |

---

## 二、调用方迁移

### 场景 1：用户直接调用 formalize

**v3.1（旧）**：
```
用户: "设计一个推荐系统"
→ formalize 全量执行 S0-S8
→ 输出完整规格书给用户
```

**v4.0（新）**：
```
用户: "设计一个推荐系统"
→ intent-classifier 先分类 → D 组
→ formalize 走 full_formalize 管道
→ hybrid 模式：⚠️给用户，完整 spec 给下游
```

**迁移操作**：无需改动。`full_formalize` 管道等价于 v3.1 行为。

### 场景 2：其他技能调用 formalize 的某个工具

**v3.1（旧）**：不支持。要么全用，要么不用。

**v4.0（新）**：
```
code_design skill:
  1. skill_view(name='formalize')
  2. 调用 classify_complexity 判断是否需形式化
  3. 若 L2+：调用 assumption_audit 管道检查假设
  4. 将结果作为隐形上下文进入设计
```

**迁移操作**：新增调用。详见 `references/pipeline-recipes.md`。

### 场景 3：intent-classifier 快速判定

**v3.1（旧）**：classifier 无法调用 formalize 的工具。

**v4.0（新）**：
```
intent-classifier:
  1. skill_view(name='formalize')
  2. 调用 quick_check 管道 (T1+T2 并行)
  3. 根据结果决定 route.needs_formalize
```

**迁移操作**：新增调用。

---

## 三、输出模式变更

| 旧模式 | 新模式 | 说明 |
|--------|--------|------|
| v3.1 默认全部输出给用户 | `output_mode: hybrid` | 用户只看到 ⚠️ + 置信度，完整 spec 作为下行上下文 |
| — | `output_mode: hidden` | 新增：完全隐藏，仅下游消费 |
| v3.1 行为 | `output_mode: visible` | 保留，用于用户显式要求场景 |

使用 `generate_spec(output_mode='visible')` 可恢复 v3.1 行为。

---

## 四、frontmatter 增量

v4.0 新增字段（均不影响 v3.1 功能）：

```yaml
mode: toolkit
exposed_tools: [...]        # 8 个工具声明
pipelines:                  # 3 个预构建管道
  full_formalize: {...}
  quick_check: {...}
  assumption_audit: {...}
deprecation_notice:         # 兼容期声明
  v3.1_supported_until: "2026-08-01"
  migration_guide: "references/v3-to-v4-migration.md"
```

---

## 五、回滚方法

如 v4.0 出现兼容问题：

1. **技能级回滚**：替换 `formalize/SKILL.md` 为 v3.1 备份（`.v3.1.bak`）
2. **会话级降级**：在当前会话中 `skill_view(name='formalize')` 后手动走 v3.1 流程
3. **路由级降级**：intent-classifier 将 `route.formalize_mode` 设为 `full_formalize` 即可获得 v3.1 等价行为

---

## 六、常见问题

**Q: v4.0 还能直接给用户输出规格书吗？**
A: 可以。`generate_spec(output_mode='visible')` 或走 `full_formalize` 管道（默认 hybrid 不影响规格书完整性）。

**Q: 我的技能还没适配 v4.0，会断吗？**
A: 不会。`full_formalize` 管道输出与 v3.1 完全一致。未适配的技能无需任何改动。

**Q: 怎么判断该用哪个工具？**
A: 先查 `references/tool-contracts.md` 了解每个工具的能力，或直接使用预构建管道（quick_check / assumption_audit / full_formalize）。

---

## 七、灰度发布策略

### 发布节奏

```
Week 1: 内部 dogfood，仅团队成员触发 classifier + v4.0 链路
Week 2: 10% 流量走新链路，监控 misclassification_rate + latency_p99
Week 3: 50% 流量，观察 P99 延迟 + formalize spec_acceptance_rate
Week 4: 100% 流量，但保留 1 周回退开关
Week 5+: 移除 v3.1 旧链路（前提：所有指标达标 ≥ 连续 7 天）
```

### 回退条件

任一触发即暂停灰度扩容并切回 v3.1：

| 条件 | 阈值 | 处置 |
|------|------|------|
| classifier P99 延迟 | > 300ms 持续 10min | 降级到默认路由 |
| classifier 置信度均值 | < 0.65 持续 30min | 切回 v3.1 全量 |
| misclassification_rate | > 8% | 暂停扩容，排查规则 |
| formalize spec_acceptance_rate | < 70% | 触发回归审计 |
| handoff schema_validation_failures | > 0 | 立即告警 + 回退 |

### 回滚方法

1. 将 classifier `mode` 从 `always_on` 改为 `on_demand`（关闭自动路由）
2. 将 formalize `mode` 从 `toolkit` 改回默认（等价 v3.1 full_formalize）
3. 单 commit revert 即可恢复

