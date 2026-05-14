# intent-classifier 决策规则（O(1) 规则匹配层）

> **定位**：定义分类器的规则匹配逻辑。规则按优先级排列，命中即停止。
> **原则**：能用规则不用 LLM。规则覆盖率目标 ≥ 70%。

---

## 规则优先级分层

```
Layer 1: 长度 + 词典（P0，100% 确定性）
Layer 2: 前缀/正则（P0，100% 确定性）
Layer 3: 关键词字典（P1，高置信度）
Layer 4: 矛盾检测（P0，高置信度但需要确认上下文）
Layer 5: 复杂度估算（P1，中等置信度）
Layer 6: LLM 1-shot 兜底（仅对 1-5 全部未命中的输入）
```

---

## Layer 1: 长度 + 词典

```
if len(input) <= 10:
    if input in CONFIRMATION_DICT:
        → A2: confirmation (confidence: 1.0)

CONFIRMATION_DICT: [
    "好的", "好", "OK", "ok", "继续", "嗯", "对",
    "确认", "行", "可以", "是的", "没错", "明白了"
]
```

**边界**：`len("你好，帮我查一下天气")` = 10 字但不属于确认类 —— Layer 3 会纠正。

---

## Layer 2: 前缀/正则

### Shell 命令检测

```
SHELL_REGEX = r'^(git|npm|pip|docker|kubectl|pytest|python|node|curl|wget|ssh|scp) '
if matches(SHELL_REGEX, input):
    → B1: shell_command (confidence: 1.0)
```

### 原子代码修改检测

```
ATOMIC_EDIT_PATTERN = (
    (改|修改|替换|删除|加|重命名) AND
    (filename_ext OR line_number OR function_name) AND
    (target_value)
)
if matches(ATOMIC_EDIT_PATTERN, input):
    → B2: atomic_edit (confidence: 0.95)
```

文件名扩展名列表：`.py .js .ts .go .rs .java .cpp .c .h .rb .php .html .css .yaml .json .toml .md`

---

## Layer 3: 关键词字典扫描

每个标签一个关键词列表。命中 ≥2 个关键词 → 加入候选集。候选集按优先级排序（Group D > Group C > Group B > Group A）。

### Keyword Dictionaries

```
A1_chitchat:      [你好, hi, hello, 在吗, 谢谢, 再见, 晚安, 早安]
A3_emotional:     [心情, 难受, 焦虑, 郁闷, 压力大, 开心, 崩溃了, 想哭]
A4_simple_qa:     [什么是, 定义, 解释一下, 是哪, 在哪里, 谁发明]
A5_translation:   [翻译, translate, 译成, 翻成, 用.*说]
A6_summarization: [总结, 摘要, 概括, 归纳, 提炼, summarize]
A7_rewrite:       [改写, 润色, 改得, 调成, 换成.*风格, rewrite]
A8_creative:      [写诗, 编故事, 创作, 写首, 写篇, 写个.*故事, 写个.*诗]

B3_file_op:       [新建文件, 创建目录, 删除文件, 移动文件, 重命名文件]

C1_code_design:   [设计.*缓存, 设计.*模块, 设计.*接口, 设计.*组件, 规划.*结构]
C2_code_review:   [审查, review, 检查这段代码, 看看.*问题, code review]
C3_debug:         [报错, 异常, 崩溃, 不工作, 为什么.*error, 排查, 调试, debug]
C4_system_design: [设计.*系统, 设计.*架构, 设计.*平台, 设计.*方案, 规划.*架构]

D1_ambiguous:     [优化一下, 改进一下, 弄一下, 做一下, 搞一下] (无具体目标)
D4_cross_domain:  [ML.*Web, AI.*平台, 算法.*工程, 前端.*后端] (双领域)
```

---

## Layer 4: 矛盾检测

见 formalize §2.2 矛盾词对 + formalize `references/contradiction-heuristics.md`。

```
CONTRADICTION_PAIRS = [
    (免费|零成本, 企业级|高可用|SLA),
    (简单|极简, 完整|全面|功能强大),
    (毫秒级|极快, AI|复杂逻辑|大数据),
    (灵活|可配置, 开箱即用|零配置),
    (通用|标准, 深度定制|特化),
]

if any_pair_matches(input):
    → D2: contradictory_constraints (confidence: 0.90)
```

---

## Layer 5: 复杂度估算

```
entity_count = count_noun_phrases(input)
system_keywords = [服务, 集群, 分布式, 微服务, 多端, 网关, 消息队列, 负载均衡]

if entity_count > 5 or has_any(system_keywords):
    → D3: high_complexity (confidence: entity_count > 8 ? 0.90 : 0.75)
```

---

## Layer 6: LLM 1-shot 兜底

仅对 Layer 1-5 全部未命中的输入使用。

```
system_prompt: >
  你是一个轻量级意图分类器。将用户输入分入以下 17 类之一：
  [A1-A8, B1-B3, C1-C4, D1-D4]

  回复 JSON：{"primary_intent": "...", "confidence": 0.0-1.0}

  规则：
  - confidence < 0.6 → primary_intent 设为 "unknown"
  - 不确定时宁可 low confidence 不要猜
  - 只输出 JSON，不附加任何文字

约束：
- 模型：轻量级（Haiku/flash 级别）
- max_tokens：50
- 不读取会话历史
```

---

## 兜底比例监控

```
fallback_ratio = llm_fallback_count / total_classifications

if fallback_ratio > 0.30:
    → 告警：规则覆盖率不足，需补强关键词字典
    → 输出中标记 fallback_exceeded: true
```
