---
name: intent-classifier
version: 1.0.0
status: active
enabled_by_default: true
description: "Use when user input arrives. Lightweight pre-router: classify intent into 17 categories across 4 groups, decide whether to formalize, route to downstream skill. Rule-first O(1) matching with LLM fallback. Outputs JSON RouteDecision."
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
priority: P-1
mode: always_on
trigger:
  - 所有用户输入（无条件触发）
skip_when:
  - 当前轮次已有有效分类结果（避免重复分类）
not_when: []
latency_budget_ms: 200
fallback_strategy:
  on_timeout: return_unknown
  on_low_confidence: pass_through_with_signal
fallback_skill: formalize
llm_fallback:
  enabled: true
  model_tier: lightweight
  max_fallback_ratio: 0.30
metadata:
  hermes:
    tags: [routing, classification, intent, pre-processing, always-on, beta]
    related_skills: [formalize]
---

# intent-classifier SKILL v1.0

> **使命**：在 200ms 预算内告诉调用方"这条请求归谁管"。
> **不做**：不生成内容、不形式化、不追问、不思考"该怎么做"。
> **只做**：分类 + 信号提取 + 路由建议。

---

## 0. 执行流（严格按顺序）

```
[S0] 跳过判定 ─┬→ 跳过 → [SKIP-CLASSIFICATION]
              │         （确认/复述/空输入/纯工具指令）
              └→ 不跳过
                 ↓
[S1] 规则匹配（O(1) 前缀/正则/关键词）
                 ↓ 命中 → 输出 RouteDecision
                 ↓ 未命中
[S2] 复杂度 + 矛盾快速检测
                 ↓ 命中矛盾 → 输出 RouteDecision (contradiction)
                 ↓ 无矛盾
[S3] LLM 1-shot 兜底分类
                 ↓
[S4] 输出 RouteDecision JSON
```

---

## 1. S0：跳过判定

以下情况**跳过分类**（直接输出 `direct_respond`）：

| 条件 | 示例 |
|------|------|
| 纯确认/复述（≤10 字 + 命中确认词典） | "好的""继续""嗯""OK" |
| 空输入 | 仅含空白字符 |
| 显式 shell 指令（含命令前缀） | `pytest tests/ -v` |

---

## 2. 类别体系（17 类，4 大组）

### Group A: DIRECT_RESPOND（直接响应，不形式化）

| 标签 | 触发特征 | 示例 |
|------|---------|------|
| `chitchat` | 寒暄、问候 | "你好""在吗" |
| `confirmation` | 确认/复述 | "好的""继续""嗯" |
| `emotional_support` | 情绪表达、倾诉 | "我今天心情不好" |
| `simple_qa` | 事实问答 | "巴黎在哪""Python 是什么" |
| `translation` | 显式翻译请求 | "翻译成英文""translate to Chinese" |
| `summarization` | 显式摘要请求 | "总结一下""概括这段" |
| `rewrite` | 改写/润色 | "改得正式点""润色这段" |
| `creative_writing` | 创作类 | "写首诗""编个故事" |

### Group B: TOOL_EXECUTE（直接执行，不形式化）

| 标签 | 触发特征 | 示例 |
|------|---------|------|
| `shell_command` | 命令前缀 + 参数 | `pytest tests/ -v` |
| `atomic_edit` | 动作+位置+目标 三要素 | "把第42行print改成logger" |
| `file_operation` | 创建/删除/移动文件 | "新建文件 a.py" |

### Group C: SKILL_INVOKE（路由到具体技能）

| 标签 | 典型路由 | 示例 |
|------|---------|------|
| `code_design` | code-design / plan skill | "设计一个缓存层" |
| `code_review` | code-review skill | "审查这段代码" |
| `debug` | investigate / debug skill | "为什么报 500 错误" |
| `system_design` | system-design skill | "设计一个消息队列" |

### Group D: FORMALIZE_REQUIRED（必须先形式化）

| 标签 | 触发条件 |
|------|---------|
| `ambiguous_requirement` | 核心对象/目标缺失 |
| `contradictory_constraints` | 命中矛盾词对或语义张力 |
| `high_complexity` | 实体 >5 或系统级关键词 |
| `cross_domain` | 同时涉及 2+ 专业领域 |

---

## 3. S1/S2：规则匹配

详见 `references/decision-rules.md`。决策优先级：

```
1. 长度 ≤10 字 + 确认词典命中 → confirmation (Group A)
2. 正则匹配 shell/工具指令 → shell_command / atomic_edit (Group B)
3. 关键词字典扫描 → 17 类候选集
4. 矛盾约束检测 → contradictory_constraints (Group D)
5. 复杂度估算 → entity_count >5 or system keyword → high_complexity (Group D)
6. LLM 1-shot 兜底（仅对未命中输入）
```

### 3.1 Group D 默认路由：两阶段工作流（v1.1 新增）

Group D 意图（D1-D4）**默认走两阶段模式**——先生成规格书给用户审查，确认后再执行：

```
阶段 1：formalize_only → 生成规格书 → 展示给用户
阶段 2：用户确认（"开始""执行""继续"）→ 下游 skill 执行
```

**例外**：当用户在同一条消息中同时描述了"需求 + 执行指令"（如"设计一个登录系统并帮我写代码"），可走 `invoke_skill_with_formalize`。

**审批门控**（见 formalize `references/skeleton-card.md`）：
- L3 规格书或置信度为"中/低" → **必须**人工审批后才能执行
- L1/L2 且置信度为"高" → 可跳过审批直接流转
- 审批信号：`确认`/`执行`/`继续` = 放行；`修改: <意见>` = 带反馈重做

**理由**：`#beta` 路径下，分类器不应代替用户决定"审查后再执行"还是"直接执行"。保守默认（先审查）避免错误执行。

---

## 4. S4：输出契约（强制 JSON）

```json
{
  "version": "1.0",
  "primary_intent": "high_complexity",
  "secondary_intents": ["system_design"],
  "confidence": 0.85,
  "route": {
    "action": "invoke_skill_with_formalize",
    "target_skill": "system_design",
    "needs_formalize": true,
    "formalize_mode": "full_formalize"
  },
  "signals": {
    "ambiguity_score": 0.3,
    "contradiction_detected": false,
    "entity_count": 7,
    "stem_keywords": false,
    "complexity_estimate": "L3",
    "language": "zh-CN"
  },
  "trace_id": "ic_20260514_abc123"
}
```

### 字段语义

| 字段 | 类型 | 说明 |
|------|------|------|
| `primary_intent` | enum | 17 类之一，置信度最高 |
| `secondary_intents` | enum[] | 次要标签（多分类） |
| `confidence` | float | <0.6 时调用方应启用兜底策略 |
| `route.action` | enum | `direct_respond` / `execute_tool` / `invoke_skill` / `formalize_only` / `invoke_skill_with_formalize` |
| `route.formalize_only` | bool | D 组默认 `true`——先生成规格书给用户审查，确认后再执行 |
| `route.target_skill` | string | 目标技能名（C/D 组必填） |
| `route.needs_formalize` | bool | D 组为 true |
| `route.formalize_mode` | enum | `full_formalize` / `quick_check` / `assumption_audit` |
| `signals.ambiguity_score` | float | 给下游 formalize 的预热信号 |
| `signals.complexity_estimate` | enum | L1/L2/L3，D 组必填 |
| `trace_id` | string | 用于跨技能追踪 |

---

## 5. `[INTENT-CLASSIFIED]` 标记注入

分类完成后，在原始 query 后追加此行，供下游技能消费：

```
[INTENT-CLASSIFIED: primary=<intent>, confidence=<0-1>, complexity=<L1-L3>, needs_formalize=<bool>]
```

---

## 6. 降级策略

| 情况 | 处理 |
|------|------|
| 超时（>200ms） | 输出 `UNKNOWN` + `confidence: 0` |
| 置信度 < 0.6 | 输出分类结果但标记 `confidence`，让调用方决定 |
| LLM 兜底占比 > 30% | 标记 `fallback_exceeded: true`，提示规则需补强 |

---

## 7. 反模式（明确不做）

| 反模式 | 错误做法 | 正确做法 |
|--------|---------|---------|
| 替代 formalize | 自己生成规格 | 只输出 `needs_formalize: true` |
| 替代下游 skill | 调用具体 skill | 只输出 `target_skill` 名 |
| 输出多余文本 | 给用户解释分类理由 | JSON + 标记，无其他输出 |
| 长上下文消化 | 读完整个会话历史 | 仅看本轮用户输入 + 上一轮意图 |

---

## 8. 与 formalize 的边界

| 关注点 | intent-classifier | formalize |
|--------|------------------|-----------|
| 输出 | 路由标签 | 规格书 |
| 是否追问 | 不追问 | 最多 3 问 |
| 上下文 | 单轮（只看本轮输入） | 可跨轮（S9 多轮状态） |
| 粒度 | 标签级 | 章节级 |
| 用户可见 | 隐藏（仅 JSON，不给用户看） | 取决于 output_mode |

---

## 9. 性能与可观测

- **延迟预算**：P50 < 50ms，P99 < 200ms
- **降级**：超时 → `UNKNOWN` + `confidence: 0`
- **监控项**：
  - `intent_classifier.latency_ms`
  - `intent_classifier.fallback_to_llm` (bool)
  - `intent_classifier.confidence_distribution`
  - `intent_classifier.misclassification_feedback`

---

## 10. 版本历史

| 版本 | 变更 |
|------|------|
| 1.0 | 初始版本：17 类 4 组 + O(1) 规则 + LLM 兜底 + JSON 契约 |
