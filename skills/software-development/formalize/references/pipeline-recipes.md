# formalize v4.0 管道配方（Pipeline Recipes）

> **@status: beta**
> **定位**：常见跨技能协作场景的调用菜谱。
> **当前状态**：Recipe 1 (quick_check) + Recipe 3 (full_formalize) 已可用，其余 Recipe 依赖 v4.0 toolkit 的 beta 工具，默认不启用。

---

## Recipe 1: intent-classifier 快速判定

**场景**：classifier 需要在 200ms 预算内决定是否调用 formalize。

**调用**：
```
1. skill_view(name='formalize')
2. 执行 quick_check 管道：
   - detect_contradiction(text=query)       # 100ms
   - classify_complexity(text=query)         # 50ms
   两者可并行（无依赖），总计 ~100ms
3. 汇总：
   if contradiction.severity == "high":
       return route: { action: "ask_user", ... }
   elif complexity.level == "L3":
       return route: { action: "invoke_skill_with_formalize", formalize_mode: "full_formalize" }
   elif complexity.level == "L2":
       return route: { action: "invoke_skill", needs_formalize: false }
   else:
       return route: { action: "direct_respond" }
```

**产出**：`RouteDecision`（路由决策）

---

## Recipe 2: code_design 假设审计

**场景**：code_design 技能在生成代码方案前，需要检查用户需求的隐含假设。

**调用**：
```
1. skill_view(name='formalize')
2. 执行 assumption_audit 管道：
   - extract_assumptions(text=requirement, domain_hint="web_dev")
   - validate_spec(spec=parsed_requirement, strictness="relaxed")
3. 将结果注入方案生成的上下文：
   - 在 system prompt 中追加 "以下假设未经用户确认：{implicit_assumptions}"
   - 对于 should_warn=true 的假设，在方案中显式标注 ⚠️
```

**产出**：`AssumptionList` + 高危校验报告

---

## Recipe 3: system_design 全量形式化

**场景**：用户提出高复杂度系统设计需求，需完整形式化。

**调用**：
```
1. intent-classifier 分类 → D3: high_complexity
2. formalize: full_formalize 管道（hidden 模式）
   - generate_spec(text=query, level="L3", output_mode="hidden")
3. spec 作为隐形上下文注入 system_design 的 system prompt
4. system_design 基于 spec 产出用户友好的方案
5. 质量门：用 validate_spec 反查方案是否覆盖所有强制要求
```

**产出**：`SpecDocument`(hidden) → 用户友好的系统设计方案

---

## Recipe 4: 矛盾需求处理

**场景**：用户输入包含矛盾约束（如"免费但企业级"）。

**调用**：
```
1. intent-classifier → D2: contradictory_constraints
2. formalize: detect_contradiction(text=query)
   → severity: high
   → recommendation: "强追问不可继续"
3. 向用户输出矛盾追问模板（v3 §2.2 格式）
4. 用户回答后重新分类 → 确定路径
```

**产出**：追问 → 消歧后的需求 → 正式形式化

---

## Recipe 5: 轻量需求 L1 快速处理

**场景**：简单、明确的需求，不需要完整规格书。

**调用**：
```
1. classify_complexity(text=query) → level: L1
2. generate_spec(text=query, level="L1", output_mode="visible")
   → 300-600 字微型规格书
3. 用户确认后进入实现
```

**产出**：微型规格书（300-600 字）

---

## Recipe 6: 质量门——输出后校验

**场景**：下游技能产出方案后，用 formalize 的校验能力反查覆盖度。

**调用**：
```
1. 下游技能产出方案
2. formalize: validate_spec(spec=downstream_output, strictness="standard")
3. 检查 issues 列表：
   if issues 中含 severity=high:
       → 标记 ⚠️，建议下游修正
   if anti_case_triggered:
       → 强制重审方案（⚠️=0 不可信）
```

**产出**：`ValidationReport`，用于合入门禁

---

## Recipe 7: 多轮对话状态累积

**场景**：用户分多轮补充需求，需累积并检测漂移。

**调用**：
```
第 1 轮：full_formalize → spec_v1
第 2 轮：用户补充新信息
  1. extract_assumptions(text=new_info) → 新假设
  2. compute_confidence(spec=spec_v1, dimensions=dim_v1) → 检查是否需要重形式化
  3. 若 confidence < previous：重新 generate_spec（合并新旧信息）
  4. 比较 spec_v1 vs spec_v2：若 >30% 约束变化 → 标记 "SCOPE DRIFT"
```

**产出**：累积规格书 + 漂移检测报告

---

## Recipe 8: STEM-Eng 工程场景

**场景**：工艺/制造/化工类需求（如白云石选矿）。

**调用**：
```
1. classify_complexity → L2/L3
2. match_failure_pattern(text=query) → 若命中 P1-P5，注入强制要求
3. 检测到 STEM-Eng 关键词 → 加载 stem-eng-sub-template.md
4. generate_spec(
     text=query,
     level="L3",
     template="stem-eng",
     include_sections=["B1-STEM", "E1", "E2", "E3", "E4", "E5", "E6"]
   )
```

**产出**：含工艺流程图 + 物料衡算 + 失效模式枚举的规格书

---

## 选择指南

| 你的场景 | 推荐 Recipe |
|---------|-----------|
| 我只想判断要不要形式化 | Recipe 1 |
| 我想检查需求假设 | Recipe 2 |
| 我要完整规格书 | Recipe 3 |
| 用户需求自相矛盾 | Recipe 4 |
| 需求很简单，不需大规格 | Recipe 5 |
| 我想校验下游的输出 | Recipe 6 |
| 用户在分多轮补充 | Recipe 7 |
| 这是工业/工艺类需求 | Recipe 8 |
