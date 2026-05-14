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

### 切分维度

- **流量切分**：按 `user_id hash mod 100` 分桶
- **灰度桶范围**：W2=[0,10), W3=[0,50), W4=[0,100)
- **内部白名单**：W1 团队账户不受 hash 影响，始终走新链路

### 阶段表

| 周次 | 流量比例 | 切分维度 | 监控重点 | 回退触发条件 | 回退动作 |
|------|---------|---------|---------|------------|---------|
| W1 | 内部 dogfood | 团队白名单 | 全部 6 指标 | 任一 P0 错误 | 立即回 v3.1 |
| W2 | 10% | user_id hash | latency_p99 + misclassification_rate | P99 > 300ms 或误分类 > 8% | 24h 内回退 |
| W3 | 50% | user_id hash | spec_acceptance_rate | < 70% 持续 2h | 灰度暂停 |
| W4 | 100% | 全量 | 全部 6 指标 | 任一指标连续 2h 超阈值 | 切回 W3 状态 |
| W5-7 | 100% + 旧链路保留 | — | 持续观察 | — | — |
| W8 | 移除 v3.1 旧链路 | — | — | — | — |

### 等价性验证

灰度期间（W2-W4），对灰度流量同时调用 v3.1 与 v4.0（影子模式），对比关键字段：

| 对比字段 | 允许差异 | 超限处置 |
|---------|---------|---------|
| 章节数 | ≤ 1 | >1 触发审计 |
| ⚠️ 数量 | ≤ 2 | >2 触发审计 |
| 置信度等级 | 完全相同 | 不同触发审计 |

差异 > 5% 的用例 → 自动采样 20 条 → 人工复盘。

### 回退操作手册

1. **触发条件命中** → 值班人员收到告警（PagerDuty / 企微群通知）
2. **执行回退**：
   ```bash
   # 方案 A：配置热更新（推荐，<30s 生效）
   hermes config set skills.formalize.default_version "3.1"
   
   # 方案 B：紧急回滚（如配置更新不可用）
   git revert <grayscale-commit> && git push
   ```
3. **验证**：30 秒内确认 100% 流量回到 v3.1 链路
4. **复盘**：72 小时内提交事故复盘，包含根因 + 修复计划 + 重新灰度时间表
5. **状态恢复**：确认修复后，从 W1（dogfood）重新开始灰度流程

---

## 八、指标采集方案

### 采集可行性分级

| 指标 | P1/P2 阶段 | P3 阶段 | 采集方式 |
|------|-----------|--------|---------|
| `classifier.latency_p99_ms` | ❌ 不可采集 | ✅ orchestrator 钩子 | pre/post API call 时间戳差值 |
| `classifier.confidence_avg` | ✅ 直接聚合 | ✅ 直接聚合 | classifier JSON 输出 `confidence` 字段 |
| `classifier.misclassification_rate` | ⚠️ 定性观察 | ✅ 周度抽样 | 每周从日志中随机采样 100 条，人工标注 |
| `formalize.spec_acceptance_rate` | ⚠️ 定性观察 | ✅ 用户行为代理 | 用户"进入下一步实现"事件作为代理指标 |
| `handoff.schema_validation_failures` | ❌ 不可采集 | ✅ 调度层校验 | jsonschema.validate() 异常计数 |
| `orchestrator.fallback_count` | ❌ 不可采集 | ✅ 调度层计数器 | fallback 分支命中次数 |

### P1/P2 阶段降级方案

P1/P2 阶段无 orchestrator 钩子，仅记录 classifier 输出 JSON 中的 `confidence` 与 `primary_intent` 分布。指标 1/5/6 暂不采集，待 P3 代码层钩子上线后补齐。

> ⚠️ **重要**：灰度发布策略（第七章）依赖 P3 阶段的 orchestrator 钩子才能完整执行。P1/P2 期间回退只能通过 git revert，无法秒级切换。


