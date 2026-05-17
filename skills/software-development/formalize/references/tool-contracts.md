# formalize v4.0 — 工具契约（Tool Contracts）

> **@status: active**
> **定位**：本文档定义 formalize toolkit 所有原子工具的输入/输出 schema，作为 inter-skill 调用的**唯一契约锚点**。

---

## 工具索引

| # | 工具 | 用途 | 成本 | 延迟预算 |
|---|------|------|------|---------|
| T1 | `detect_contradiction` | 矛盾约束识别 | low | 100ms |
| T2 | `classify_complexity` | L0/L1/L2/L3 分级 | low | 50ms |
| T3 | `match_failure_pattern` | 失败模式库匹配 | medium | 150ms |
| T4 | `extract_assumptions` | 隐含假设抽取 | low | 100ms |
| T5 | `scan_dimensions` | 10 维度扫描 | medium | 200ms |
| T6 | `generate_spec` | 生成规格书 | **high** | 2000ms |
| T7 | `validate_spec` | 规格书自检 | medium | 300ms |
| T8 | `compute_confidence` | 置信度评估 | low | 50ms |

---

## T1: detect_contradiction

```yaml
purpose: >
  识别用户需求中的矛盾约束。基于关键词词对 + 语义启发式双层检测。
  命中高严重度矛盾时，要求"强追问，不可继续形式化"。

input:
  text:
    type: string
    required: true
    description: "用户原始输入全文"
  language:
    type: enum[zh, en, auto]
    required: false
    default: auto
    description: "文本语言，影响矛盾词对匹配"

output:
  has_contradiction:
    type: bool
    description: "是否存在矛盾约束"
  pairs:
    type: array
    description: "检测到的矛盾对列表"
    items:
      dimension:
        type: enum[成本vs质量, 简洁vs完备, 速度vs复杂, 灵活vs易用, 通用vs深度, 语义张力]
        description: "矛盾所属维度"
      term_a:
        type: string
        description: "原文片段 A"
      term_b:
        type: string
        description: "原文片段 B"
      severity:
        type: enum[high, medium, low]
        description: >
          high: 必须追问，不可继续形式化
          medium: 标 ⚠️ 后可继续
          low: 仅记录，不阻塞流程
      detection_method:
        type: enum[keyword_pair, semantic_heuristic]
        description: "命中方式"
  recommendation:
    type: enum[强追问不可继续, 标⚠️后可继续, 仅记录]
    description: "对调用方的操作建议"

side_effects: none
idempotent: true
stateless: true

calling_example: |
  # 伪代码
  result = detect_contradiction({text: "帮我设计一个免费但企业级的登录系统"})
  # → has_contradiction: true
  # → pairs[0]: { dimension: "成本vs质量", severity: "high" }
  # → recommendation: "强追问不可继续"
```

---

## T2: classify_complexity

```yaml
purpose: >
  对任务进行 L0/L1/L2/L3 复杂度分级，决定后续模板选择和处理深度。

input:
  text:
    type: string
    required: true
    description: "用户输入或需求描述"

output:
  level:
    type: enum[L0, L1, L2, L3]
    description: "复杂度级别"
  signals:
    type: object
    description: "分级依据"
    fields:
      entity_count:
        type: int
        description: "识别到的实体（名词短语）数量"
      rule_branches:
        type: int
        description: "IF/WHEN/CASE 分支数"
      has_system_keywords:
        type: bool
        description: "是否含系统级关键词（服务/集群/分布式/多端）"
      has_stem_formula:
        type: bool
        description: "是否含数学/物理/算法公式"
  template_recommendation:
    type: enum[skip, mini, standard, extended]
    description: "推荐的模板级别"
  rationale:
    type: string
    description: "分级理由（一句话）"

side_effects: none
idempotent: true
stateless: true

calling_example: |
  result = classify_complexity({text: "优化一下数据库查询性能"})
  # → level: L2
  # → signals: { entity_count: 2, rule_branches: 1, ... }
  # → template_recommendation: "standard"
```

---

## T3: match_failure_pattern

```yaml
purpose: >
  将用户需求与 8 类已知失败模式匹配，返回命中的模式及对应的强制要求清单。
  模式库定义在 `references/failure-patterns.md`。

input:
  text:
    type: string
    required: true
    description: "用户需求描述"
  domain_hint:
    type: string
    required: false
    description: "领域提示词，辅助匹配（如 'web', 'mining', 'ml'）"

output:
  matched_patterns:
    type: array
    description: "命中的失败模式列表（可能为空）"
    items:
      id:
        type: string
        description: "模式编号（P1-P8）"
      name:
        type: string
        description: "模式名称（如'推荐系统类'）"
      confidence:
        type: float
        description: "匹配置信度（0-1）"
      keywords_hit:
        type: array[string]
        description: "触发的关键词"
      mandatory_requirements:
        type: array[string]
        description: "该模式的强制要求清单（逐条可校验）"
      mandatory_count:
        type: int
        description: "强制要求数量"

side_effects: >
  读取 references/failure-patterns.md（按需加载，仅当关键词命中时）
idempotent: true
stateless: false  # 可能加载外部文件

calling_example: |
  result = match_failure_pattern({text: "做一个推荐系统"})
  # → matched_patterns[0]: {
  #     id: "P1", name: "推荐系统类",
  #     mandatory_requirements: ["必含冷启动策略", "必含评估指标(>=2)", "必给复杂度"],
  #     mandatory_count: 3
  #   }
```

---

## T4: extract_assumptions

```yaml
purpose: >
  从需求中抽取显式声明、隐含假设、以及用户未提及但关键的信息。

input:
  text:
    type: string
    required: true
    description: "用户需求描述"
  domain_hint:
    type: string
    required: false
    description: "领域提示，辅助识别领域特有的隐含假设"

output:
  explicit:
    type: array[object]
    description: "用户明确声明的假设"
    items:
      text: string
      confidence: enum[high]
  implicit:
    type: array[object]
    description: "未经验证的隐含假设"
    items:
      text: string
      should_warn: bool
      reason: string
  unstated_but_critical:
    type: array[string]
    description: "用户未提及但关键的信息（建议补充）"
  total_assumptions:
    type: int
    description: "三类假设总数"

side_effects: none
idempotent: true
stateless: true

calling_example: |
  result = extract_assumptions({text: "用户需要把数据从 MySQL 迁移到 PostgreSQL"})
  # → explicit: [{ text: "源库是 MySQL", confidence: "high" }]
  # → implicit: [{ text: "假设目标库已安装", should_warn: true }]
  # → unstated_but_critical: ["数据量级", "停机窗口要求"]
```

---

## T5: scan_dimensions

```yaml
purpose: >
  对需求进行 10 维度扫描，每维标注 ✓/⚠️/✗。扫描深度根据复杂度级别自适应。

input:
  text:
    type: string
    required: true
    description: "用户需求描述"
  level:
    type: enum[L1, L2, L3]
    required: true
    description: "复杂度级别，决定扫描深度"
  domain_hint:
    type: string
    required: false

output:
  dimensions:
    type: object
    description: "10 维度扫描结果"
    fields:
      object:    { status: enum[✓, ⚠️, ✗], note: string }
      structure: { status: enum[✓, ⚠️, ✗], note: string }
      relation:  { status: enum[✓, ⚠️, ✗], note: string }
      change:    { status: enum[✓, ⚠️, ✗], note: string }
      symmetry:  { status: enum[✓, ⚠️, ✗], note: string }
      invariant: { status: enum[✓, ⚠️, ✗], note: string }
      constraint:{ status: enum[✓, ⚠️, ✗], note: string }
      possibility:{ status: enum[✓, ⚠️, ✗], note: string }
      mapping:   { status: enum[✓, ⚠️, ✗], note: string }
      scale:     { status: enum[✓, ⚠️, ✗], note: string }
  weak_dimensions:
    type: array[string]
    description: "标记为 ⚠️ 或 ✗ 的维度名称列表"
  scan_depth:
    type: enum[L1_basic, L2_full, L3_full_with_risk]
    description: "实际使用的扫描深度"

side_effects: none
idempotent: true
stateless: true

calling_example: |
  result = scan_dimensions({text: "...", level: "L2"})
  # → weak_dimensions: ["可能性", "尺度"]
  # → dimensions.object: { status: "✓", note: "实体识别完整" }
```

---

## T6: generate_spec

```yaml
purpose: >
  生成完整形式化规格书。这是 toolkit 中最重的工具，调用前应先用 T2 确认确有必要。
  支持三级模板 + STEM/STEM-Eng 子模板。

input:
  text:
    type: string
    required: true
    description: "用户需求全文"
  level:
    type: enum[L1, L2, L3]
    required: true
    description: "决定模板选择"
  template:
    type: enum[mini, standard, extended, stem, stem-eng]
    required: false
    description: "显式指定模板（覆盖 level 推荐）"
  include_sections:
    type: array[string]
    required: false
    description: "裁剪章节列表（如 [B1, B2, B4]），不指定则全量"
  output_mode:
    type: enum[visible, hidden, hybrid]
    required: true
    description: >
      visible: 完整展示给用户
      hidden: 包装在 [FORMALIZE-HIDDEN] 标记中，仅下游 skill 消费
      hybrid: ⚠️ 列表展示给用户，完整 spec 给下游
  failure_patterns:
    type: array[PatternMatch]
    required: false
    description: "来自 T3 的命中模式，用于注入强制要求"
  assumptions:
    type: AssumptionList
    required: false
    description: "来自 T4 的假设列表"
  dimensions:
    type: DimensionReport
    required: false
    description: "来自 T5 的维度扫描"

output:
  spec_document:
    type: SpecDocument
    description: "完整规格书（结构由 template 决定）"
  metadata:
    type: object
    fields:
      word_count: int
      sections: array[string]
      warnings_count: int
      template_used: string

cost_warning: >
  调用前必须先用 T2 确认 level ≥ L1。
  对 L0 任务调用本工具是禁止的（应在 S0 阶段跳过）。

side_effects: >
  可能加载 references/templates/{L1,L2,L3,stem}.md + references/stem-eng-sub-template.md + references/failure-patterns.md
stateless: false

calling_example: |
  result = generate_spec({
    text: "...",
    level: "L2",
    output_mode: "hybrid",
    failure_patterns: [来自 T3 的匹配结果],
    assumptions: 来自 T4 的假设列表,
    dimensions: 来自 T5 的维度报告
  })
  # → spec_document: <完整规格书>
  # → metadata: { word_count: 1200, sections: ["B1","B2","B3","B4","B5","B6","B7"], ... }
```

---

## T7: validate_spec

```yaml
purpose: >
  校验已生成的规格书是否合规。对标 formalize 的自检清单（skeleton-card.md）。

input:
  spec:
    type: SpecDocument | string
    required: true
    description: "待校验的规格书全文或对象"
  strictness:
    type: enum[standard, relaxed, anti_case_only]
    required: false
    default: standard
    description: >
      standard: 全量检查
      relaxed: 仅检查高危项（禁用词/置信度格式/章节齐全）
      anti_case_only: 仅检查反例触发（⚠️=0 且 L2+）

output:
  passed:
    type: bool
    description: "是否通过所有检查"
  issues:
    type: array
    items:
      rule:
        type: string
        description: "违反的规则名称"
      severity:
        type: enum[high, medium, low]
      details:
        type: string
        description: "具体违规内容"
      suggested_fix:
        type: string
  anti_case_triggered:
    type: bool
    description: "反例触发是否激活（⚠️=0 且 L2+ 时）"
  rewrite_recommended:
    type: bool
    description: "是否建议重写"
  checklist_summary:
    type: string
    description: "自检报告行（如 '✓ 章节齐全 ✓ 置信度合规 ✓ 无禁用词'）"

side_effects: >
  读取 references/skeleton-card.md（校验规则来源）
stateless: false

calling_example: |
  result = validate_spec({spec: spec_doc})
  if not result.passed:
      if result.rewrite_recommended:
          spec_doc = generate_spec(...)  # 最多重写 1 次
```

---

## T8: compute_confidence

```yaml
purpose: >
  评估规格书的整体置信度，给出降低不确定性的下一步建议。

input:
  spec:
    type: SpecDocument
    required: true
  dimensions:
    type: DimensionReport
    required: true
    description: "来自 T5 的维度扫描结果"

output:
  level:
    type: enum[高, 中, 低]
    description: >
      高: ≥8 ✓ 且 无关键 ⚠️
      中: ≥6 ✓ 且 1-3 关键 ⚠️
      低: <6 ✓ 或 ≥4 关键 ⚠️
  rationale:
    type: string
    description: "判定依据"
  warning_count:
    type: int
    description: "⚠️ 总数"
  critical_warning_count:
    type: int
    description: "关键 ⚠️ 数"
  next_action_to_reduce_uncertainty:
    type: string
    description: "低置信度时必填，给出最值得追问的 1 个点"

side_effects: none
idempotent: true
stateless: true

calling_example: |
  result = compute_confidence({spec: spec_doc, dimensions: dim_report})
  # → level: "中"
  # → rationale: "7/10 ✓，2 个关键 ⚠️：数据规模未声明、第三方 API 版本未指定"
  # → next_action_to_reduce_uncertainty: "确认目标数据量级（日活用户数）"
```

---

## 管道组合规则

### Pipeline A: full_formalize（v3 兼容）

```
T1 → T2 → T3 → T4 → T5 → T6 → T7 → T8
```

- 串行执行，每步输出是下一步输入
- T1 若返回 severity=high → 中断管道，返回追问建议
- T7 若 rewrite_recommended → 回到 T6 重写 1 次
- 输出 = v3 完整规格书

### Pipeline B: quick_check（轻量预检）

```
T1 (detect_contradiction) ─┐
                            ├→ 汇总 → 路由建议
T2 (classify_complexity) ──┘
```

- T1 + T2 **可并行**（相互无依赖）
- 成本 = full_formalize 的 ~15%
- 供 orchestrator / intent-classifier 快速判定

### Pipeline C: assumption_audit（假设审计）

```
T4 (extract_assumptions) → T7 (validate_spec, strictness=relaxed)
```

- 供 code_design 等 skill 在生成代码前快速检查
- 不产生完整规格书，仅输出假设列表 + 高危校验

---

## 调用方兼容性承诺

| 版本 | 工具签名兼容 | 输出格式兼容 |
|------|------------|------------|
| v4.0.0 (stable) | 基线 | 基线 |
| v4.0.x (patch) | 向后兼容 | 向后兼容 |
| v4.x.0 (minor) | 新增可选字段 | 向后兼容 |
| v5.0.0 (major) | 不保证 | 不保证 |

**Deprecation 规则**：输出字段移除前至少跨 1 个 minor 版本标记 `deprecated`。
