# Hermes 跨技能编排协议 v1.0

> **定位**：定义 hermes-agent 技能之间如何发现、调用、传递上下文。本文档是契约层，不是实现层——技能通过遵守此协议实现互操作，不依赖中心化调度器。

---

## 一、架构总览

```
用户输入
  │
  ↓
┌──────────────────────────────────────┐
│ [L0] intent-classifier (P-1, always-on) │  ← 轻量前置路由
│      输出 RouteDecision JSON           │
└──────────────┬───────────────────────┘
               ↓
┌──────────────────────────────────────┐
│ [L1] 技能调用（按 RouteDecision）      │
│  ├─ 直接响应（A 组意图）               │
│  ├─ 工具执行（B 组意图）               │
│  ├─ 技能调用（C 组意图）               │
│  └─ 技能调用 + 形式化（D 组意图）       │
└──────────────┬───────────────────────┘
               ↓
┌──────────────────────────────────────┐
│ [L2] quality_gate（可选，关键决策点）   │
│      用 formalize 的 validate_spec     │
│      反查输出是否覆盖强制要求           │
└──────────────┬───────────────────────┘
               ↓
           最终输出
```

---

## 二、Handoff JSON Schema（技能间传递契约）

当技能 A 需要将上下文传递给技能 B 时，使用此标准格式：

```json
{
  "$schema": "https://hermes-agent.local/schemas/handoff-v1.json",
  "schema_version": "1.0",
  "trace_id": "uuid",
  "from_skill": "intent-classifier",
  "to_skill": "formalize",
  "context": {
    "raw_query": "<用户原始输入>",
    "classifier_signals": {
      "primary_intent": "high_complexity",
      "confidence": 0.85,
      "ambiguity_score": 0.3,
      "contradiction_detected": false,
      "entity_count": 7,
      "complexity_estimate": "L3"
    },
    "previous_outputs": [
      {
        "skill": "intent-classifier",
        "output_type": "RouteDecision",
        "summary": "<一句话摘要>"
      }
    ]
  },
  "directives": {
    "expected_output_mode": "hybrid",
    "max_tokens": 3000,
    "must_include_sections": ["B1", "B2", "B3"],
    "pipeline_hint": "quick_check"
  }
}
```

### 字段语义

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `schema_version` | semver | ✓ | 协议版本，用于兼容性检查 |
| `trace_id` | uuid | ✓ | 跨技能追踪 ID |
| `from_skill` | string | ✓ | 调用方技能名（snake_case） |
| `to_skill` | string | ✓ | 目标技能名（snake_case） |
| `context.raw_query` | string | ✓ | 用户原始输入，不经任何加工 |
| `context.classifier_signals` | object | 条件 | 仅当 from=intent-classifier 时必填 |
| `context.previous_outputs` | array | ✓ | 调用链上的上游输出摘要 |
| `directives.expected_output_mode` | enum | 否 | visible / hidden / hybrid |
| `directives.pipeline_hint` | string | 否 | 建议目标技能使用的管道 |

### 兼容性规则

- **向后兼容**：接收方忽略未知字段（不报错）
- **向前兼容**：发送方不应假设接收方理解所有 directives
- **版本协商**：接收方若 `schema_version` 比自己高，降级到自己的最高支持版本处理

---

## 三、`[INTENT-CLASSIFIED]` 标记约定

intent-classifier 在输出中注入此标记，供下游技能消费：

```
[INTENT-CLASSIFIED: primary=high_complexity, confidence=0.85, complexity=L3]
```

### 结构

```
[INTENT-CLASSIFIED: <k1>=<v1>, <k2>=<v2>, ...]
```

**标准字段**：
| key | 必填 | 说明 |
|-----|------|------|
| `primary` | ✓ | 主意图（17 类之一） |
| `confidence` | ✓ | 置信度 0-1 |
| `complexity` | 条件 | L1/L2/L3，D 组意图必填 |
| `needs_formalize` | 否 | true/false |
| `formalize_mode` | 否 | full_formalize / quick_check |

### 生命周期

1. **注入点**：classifier 在原始 query 后追加此标记
2. **消费点**：所有技能在 S0 阶段首先检查是否存在此标记
3. **清除点**：经过一次 formalize 处理后，标记可被移除
4. **多重标记**：若存在多个标记（跨轮次），以最新的为准

---

## 四、exposed_tools 调用语法

### 声明（在技能 A 的 frontmatter 中）

```yaml
exposed_tools:
  - name: detect_contradiction
    description: "识别需求中的矛盾约束"
    input: "text: string, language: enum[zh, en, auto]"
    output: "ContradictionReport"
    latency_target_ms: 100
    contract: "references/tool-contracts.md"
```

### 调用（在技能 B 的正文中）

方式 1——加载完整技能后按指令块执行：
```
1. 调用 skill_view(name='formalize') 加载工具集
2. 在 formalize SKILL.md 中找到 detect_contradiction 指令块
3. 按照指令块的 input/output schema 执行
```

方式 2——预加载管道：
```
1. 调用 skill_view(name='formalize') 
2. 按照 pipeline: quick_check 的步骤组合执行 T1+T2
```

### 调用方职责

- 调用前检查 `contract` 指向的文件（如 `references/tool-contracts.md`）确认输入格式
- 必须提供 `input` 中的所有必填字段
- 必须遵守 `latency_target_ms` 预算
- 收到 `severity=high` 的 contradiction 时必须中断当前流程

### 被调用方职责

- 工具输出必须符合声明的 output schema
- 工具实现保持无状态（除非显式声明 `stateless: false`）
- 工具的 side_effects（如加载外部文件）必须在契约中声明

---

## 五、输出模式决策树

```
用户请求到达
  │
  ├─ 用户显式要求"展示完整分析" → visible
  │
  ├─ 调用方为 intent-classifier → hidden
  │    （classifier 只路由，不向用户展示中间产物）
  │
  ├─ 调用方为另一个 skill → hybrid（推荐）或 hidden
  │    hybrid: ⚠️ 风险和关键假设展示给用户
  │            完整规格书注入下游 skill 的上下文
  │    hidden: 全部不展示，仅下游消费
  │
  ├─ 调用方为用户直接调用 → visible 或 hybrid
  │    L1 简单任务 → visible（简短，用户可直接确认）
  │    L2 中等任务 → hybrid（展示关键点 + ⚠️）
  │    L3 复杂任务 → hybrid（避免信息轰炸）
  │
  └─ 默认 → hybrid（安全默认值）
```

### 三种模式定义

| 模式 | 用户看到 | 下游技能看到 | 适用场景 |
|------|---------|-------------|---------|
| `visible` | 完整规格书 | 完整规格书 | 用户显式要求 / L1 简单任务 |
| `hidden` | 无 | `[FORMALIZE-HIDDEN]...[/FORMALIZE-HIDDEN]` | classifier 调用 / 被其他 skill 静默调用 |
| `hybrid` | ⚠️ 列表 + 置信度 + 下一步建议 | 完整规格书 | 推荐默认值 / L2+ 复杂任务 |

### hidden 模式输出格式

```
[FORMALIZE-HIDDEN]
<完整的 formalize 输出>
[/FORMALIZE-HIDDEN]
```

下游技能通过搜索 `[FORMALIZE-HIDDEN]` 标记提取完整规格书。用户端仅展示模式切换时的过渡说明（可选）。

---

## 六、技能 frontmatter 编排字段

为支持跨技能协作，推荐在 SKILL.md frontmatter 新增以下字段：

```yaml
# ──── 编排 ────
mode: always_on | on_demand | toolkit   # 技能运行模式
priority: P-1 | P0 | P1 | P2           # 调度优先级
exposed_tools:                          # toolkit 模式必填
  - name: tool_name
    contract: "references/tool-contracts.md"
pipelines:                              # 预构建管道
  pipeline_name:
    steps: [T1, T2, ...]
    parallel: [T1, T2]                 # 可并行的步骤

# ──── 触发 ────
trigger:                                # 正向触发条件
  - condition: string
not_when:                               # 否定条件（v3.1+）
  - condition: string
invoke_when:                            # 强触发条件（v4.0+）
  - condition: string
force_skip_categories:                  # 强制跳过类别
  - creative_writing

# ──── 输出 ────
output_mode: visible | hidden | hybrid  # 默认输出模式
output_visibility: visible | hidden     # 输出是否对用户可见（legacy）

# ──── 性能 ────
latency_budget_ms: int                  # 延迟预算
token_budget: int                       # Token 预算
cost_tier: low | medium | high          # 成本级别

# ──── 演进 ────
deprecation:
  status: active | deprecated | removed
  replaced_by: skill_name               # 替代技能
  supported_until: ISO8601              # 支持截止日期
  migration_guide: "references/..."     # 迁移指南路径
```

---

## 七、版本兼容矩阵

| 场景 | 处理方式 |
|------|---------|
| 调用方 schema_version > 被调用方 | 被调用方降级到自己的最高支持版本 |
| 调用方 schema_version < 被调用方 | 被调用方向后兼容处理 |
| 调用方传入未知 directives | 被调用方忽略未知字段 |
| 调用方引用不存在的工具 | 被调用方返回 error（code: TOOL_NOT_FOUND） |
| 调用方引用已 deprecated 的工具 | 被调用方正常执行 + 在输出中追加 deprecation warning |

### Deprecation 流程

```
v3.1 标记 deprecated → 至少 1 个 minor 版本后 → v5.0.0 移除
                           ↑
                    并存期 ≥ 1 个月
```

1. 标记 `deprecation.status: deprecated` + `replaced_by` + `migration_guide`
2. 调用时输出 warning（不阻塞）
3. 并存期满后可移除

---

## 八、错误处理协议

### 错误结构

```json
{
  "error": {
    "code": "FORMALIZE_VALIDATION_FAILED",
    "message": "规格书自检未通过且超过重写次数",
    "severity": "recoverable | partial_failure | fatal",
    "skill": "formalize",
    "trace_id": "...",
    "fallback_action": "返回未校验版本 + 标记 ⚠️"
  }
}
```

### 标准错误码

| 错误码 | severity | 说明 |
|--------|----------|------|
| `TOOL_NOT_FOUND` | fatal | 调用的工具在目标技能中不存在 |
| `TOOL_TIMEOUT` | recoverable | 工具执行超时 |
| `TOOL_CONTRACT_VIOLATION` | fatal | 输入不符合工具契约 |
| `SCHEMA_VERSION_MISMATCH` | recoverable | handoff 协议版本不兼容（降级处理） |
| `FORMALIZE_VALIDATION_FAILED` | partial_failure | 规格书自检未通过 |
| `FORMALIZE_CONTRADICTION_HIGH` | recoverable | 检测到高严重度矛盾（转为追问） |
| `CLASSIFIER_LOW_CONFIDENCE` | recoverable | 分类置信度过低（降级为 UNKNOWN） |
| `REFERENCE_LOAD_FAILED` | recoverable | 外部 references 文件加载失败 |

### 错误分级

| 级别 | 处理 | 示例 |
|------|------|------|
| `recoverable` | 降级后继续（如 classifier 超时 → UNKNOWN） | 工具超时、文件加载失败 |
| `partial_failure` | 输出现有结果 + 标注缺失部分 | 自检未通过、部分维度无法扫描 |
| `fatal` | 中止，告知用户具体原因 + 建议下一步 | 关键矛盾不可调和、输入完全无法解析 |

### 降级链

```
classifier 超时 → UNKNOWN + confidence=0 → orchestrator 用默认策略
classifier 低置信度 → pass_through_with_signal → 让下游自行判断
formalize 自检失败 → 最多重写 1 次 → 标记 ⚠️ 输出
formalize 置信度低 → 必填 next_action_to_reduce_uncertainty
```

---

## 九、可观测性

### 建议采集指标

| 指标 | 类型 | 维度 |
|------|------|------|
| `skill.invocation_count` | counter | skill, version |
| `skill.latency_ms` | histogram | skill, percentile |
| `skill.success_rate` | gauge | skill |
| `handoff.count` | counter | from_skill, to_skill |
| `classifier.misclassification_feedback` | gauge | feedback_source |
| `formalize.spec_acceptance_rate` | gauge | — |
| `pipeline.step_latency_ms` | histogram | pipeline, step |
| `error.recovery_rate` | gauge | error_code |
