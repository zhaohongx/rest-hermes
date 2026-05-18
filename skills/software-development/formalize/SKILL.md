---
name: formalize
version: 4.0.0
status: active
enabled_by_default: true
description: 自然语言需求 → 可执行规格书，融合自检循环 + 渐进式模板 + 失败模式库。v4.0 支持 toolkit 模式按需调用。
deprecation:
  status: stable
  next_major: 4.0.0
  next_major_status: beta
  v3_1_compat: "full_formalize pipeline (output-equivalent, no migration needed)"
trigger:
  - 用户表达需求/意图但描述模糊、跳跃、含矛盾或隐含假设
  - 涉及数学/物理/算法建模
  - 需在动手前对齐"做什么"
  - 其他技能通过 exposed_tools 调用
skip_when:
  - 明确的 shell/工具指令
  - 原子代码修改（动作+位置+目标三要素齐全）
  - 复述/确认型短语
not_when:
  - creative_writing（创意写作："写一首诗""编个故事"）
  - emotional_support（情感支持："我今天心情不好"）
  - knowledge_qa（知识问答："什么是布朗运动"）
  - translation（翻译请求："翻译成英文"）
  - summarization（摘要请求："总结一下"）
priority: P0
mode: toolkit
reference_loading_policy:
  on_match_failure_pattern: references/failure-patterns.md
  on_stem_engineering: references/stem-eng-sub-template.md
  on_contradiction_suspected: references/contradiction-heuristics.md
  on_validate_rules: references/skeleton-card.md
  on_validate_rubric: references/confidence-rubric.md
  on_tool_contract: references/tool-contracts.md
  on_template_L1: references/templates/L1.md
  on_template_L2: references/templates/L2.md
  on_template_L3: references/templates/L3.md
  on_template_stem: references/templates/stem.md
  on_complexity_l3plus: references/complexity-depth-reference.md
output_mode: hybrid
exposed_tools:
  - name: detect_contradiction
    description: "识别需求中的矛盾约束（词对+语义双层检测）"
    input: "text: string, language: enum[zh, en, auto]"
    output: "ContradictionReport"
    latency_target_ms: 100
    contract: "references/tool-contracts.md#T1"
  - name: classify_complexity
    description: "对任务进行 L0/L1/L2/L3 复杂度分级"
    input: "text: string"
    output: "ComplexityLevel"
    latency_target_ms: 50
    contract: "references/tool-contracts.md#T2"
  - name: match_failure_pattern
    description: "将需求与 8 类已知失败模式匹配"
    input: "text: string, domain_hint?: string"
    output: "PatternMatch[]"
    latency_target_ms: 150
    contract: "references/tool-contracts.md#T3"
  - name: extract_assumptions
    description: "从需求中抽取显式声明、隐含假设、关键缺失"
    input: "text: string, domain_hint?: string"
    output: "AssumptionList"
    latency_target_ms: 100
    contract: "references/tool-contracts.md#T4"
  - name: scan_dimensions
    description: "对需求进行 10 维度扫描（自适应深度）"
    input: "text: string, level: enum[L1, L2, L3]"
    output: "DimensionReport"
    latency_target_ms: 200
    contract: "references/tool-contracts.md#T5"
  - name: generate_spec
    description: "生成完整形式化规格书（重型工具，慎调）"
    input: "text: string, level: enum[L1-L3], output_mode: enum[visible,hidden,hybrid], ..."
    output: "SpecDocument"
    latency_target_ms: 2000
    contract: "references/tool-contracts.md#T6"
    cost_warning: "调用前先用 classify_complexity 确认 level >= L1"
  - name: validate_spec
    description: "校验规格书是否合规（对标自检清单）"
    input: "spec: SpecDocument, strictness?: enum[standard,relaxed,anti_case_only]"
    output: "ValidationReport"
    latency_target_ms: 300
    contract: "references/tool-contracts.md#T7"
  - name: compute_confidence
    description: "评估规格书整体置信度"
    input: "spec: SpecDocument, dimensions: DimensionReport"
    output: "ConfidenceLevel"
    latency_target_ms: 50
    contract: "references/tool-contracts.md#T8"
pipelines:
  full_formalize:
    description: "v3.1 兼容模式——完整 S0-S8 流程"
    steps: [detect_contradiction, classify_complexity, match_failure_pattern, extract_assumptions, scan_dimensions, generate_spec, validate_spec, compute_confidence]
    equivalent_to: "v3.1 默认行为"
  quick_check:
    description: "轻量预检——仅矛盾检测+复杂度分级"
    steps: [detect_contradiction, classify_complexity]
    parallel: ["detect_contradiction", "classify_complexity"]
    cost: "full_formalize 的 ~15%"
  assumption_audit:
    description: "假设审计——供其他 skill 生成代码前使用"
    steps: [extract_assumptions, validate_spec]
    validate_mode: relaxed
deprecation_notice:
  v3.1_supported_until: "2026-08-01"
  migration_guide: "references/v3-to-v4-migration.md"
---

# formalize SKILL v4.0

> **使命**：把"人话"翻译成"机器能照做、能验证、能追责"的规格书。
> **设计原则**：宁可追问不可猜测；宁可标 ⚠️ 不可装确认；宁可简洁不可冗余。
> **v4 重大变更**：从单体流程升级为 toolkit 模式——保留完整管道（full_formalize）兼容 v3.1，同时开放 8 个原子工具供其他技能按需调用。

---

## 0. 使用模式

v4.0 支持三种调用模式：

### 模式 A：完整管道（用户直接调用）

当用户显式要求形式化或 intent-classifier 路由到 D 组意图时，走 `full_formalize` 管道（等价于 v3.1 完整流程）：
```
S0 → S1 → S2 → S3 → S4 → S5 → S6 → S7 → S8
```

### 模式 B：工具调用（其他技能按需调用）

其他技能可通过 `skill_view(name='formalize')` 加载本技能，然后按 `exposed_tools` 的契约调用单个工具。工具 schema 详见 `references/tool-contracts.md`。

示例——code_design 技能调用假设审计：
```
1. skill_view(name='formalize')            # 加载工具集
2. 执行 assumption_audit 管道: T4 → T7(relaxed)
3. 获得 AssumptionList + ValidationReport
```

### 模式 C：质量门（后置校验）

下游技能生成输出后，调用 `validate_spec`（严格模式）反查是否覆盖 formalize 的强制要求。详见 `references/pipeline-recipes.md`。

---

## 0.1 执行流（严格按顺序）

```
[S0] 跳过判定 ─┬→ 跳过 → [SKIP-FORMALIZE]
              │
              └→ 不跳过
                 ↓
[S1] 形态识别 ─┬→ 极端模糊/矛盾 → 追问模式 (<=3 问)
              │
              └→ 信息基本充足
                 ↓
[S2] 复杂度分级 → L1 微型 / L2 标准 / L3 扩展
                 ↓
[S3] STEM 检测 + 失败模式匹配
                 ↓
[S4] 10 维度扫描（按级别选取深度）
                 ↓
[S5] 按对应模板生成
                 ↓
[S6] 防幻觉加固（⚠️ 标注）
                 ↓
[S7] ★ 自检循环（v3 新增）
       ↓ 不通过
       回到 S5 重写（最多 1 次）
                 ↓
[S8] 置信度评估 + 输出
```

---

## 1. S0：跳过判定

满足任一立即跳过，**禁止**生成规格书。

### 条件 A：Shell/工具指令

特征：命令前缀 + 参数/路径。

```
✓ pytest tests/ -v
✓ kubectl apply -f deployment.yaml
✓ docker compose up -d
✓ git push origin main
```

### 条件 B：原子代码修改（动作 + 位置 + 目标）

| 要素 | 关键词 |
|------|--------|
| 动作 | 改、修改、替换、删除、添加、重命名 |
| 位置 | 文件名（.py/.js/.ts/.go/...）/ 行号 / 函数名 / 变量名 |
| 目标 | 明确的新值或结果 |

```
✓ 把 user.py 第 42 行的 print 改成 logger.info
✓ 删除 utils.js 中的 unused 函数
✗ 优化一下 user.py（目标不明 → 追问）
```

### 条件 C：复述/确认短语

`对` `好` `好的` `继续` `OK` `确认` `重新跑一下` `再来一次` `嗯`

### 条件 D（v3 新增）：L0 简单题

一眼可算（`1+1`、`sin(pi/2)`、`今天周几`）→ **直接答**，不套 STEM 模板。

### 条件 E（v3.1 新增）：非结构化输出类

以下类别**禁止**生成规格书，直接响应即可：

| 类别 | 示例 | 原因 |
|------|------|------|
| 创意写作 | "写一首诗""编个故事" | 结构化扼杀创意 |
| 情感支持 | "我今天心情不好" | 规格书无意义 |
| 知识问答 | "什么是布朗运动" | 直接回答更高效 |
| 翻译 | "翻译成英文" | 原子转换任务 |
| 摘要/改写 | "总结一下""改得正式点" | 直接处理，无需形式化 |

### 跳过输出格式（硬约束）

```
[SKIP-FORMALIZE] 指令已明确，无需形式化。

执行内容：<一句话简述>
```

---

## 2. S1：形态识别

### 进入【追问模式】的信号

任一成立：

1. 核心对象缺失："优化一下"
2. 目标完全不明："做个智能系统"
3. 明显矛盾："简单但功能全"、"免费但企业级"
4. 关键约束缺失："做个排序"（规模？实时性？）

### 追问硬约束

- **最多 3 个问题**（超过说明问题没拆好）
- 不假设、不预设技术栈
- 每个问题必须能改变后续设计
- 问题间不重复

### 追问输出格式（硬约束）

```
为了准确形式化，我需要先确认 N 个关键点：

1. <问题1> —— 影响：<这个答案如何改变设计>
2. <问题2> —— 影响：<...>
3. <问题3> —— 影响：<...>

请按需回答。
```

### 2.1 追问数收敛原则（硬约束）

| 输入复杂度 | 追问数硬上限 |
|-----------|-------------|
| 简单（单实体单需求） | <= 1 个 |
| 中等（2-5 实体） | <= 2 个 |
| 复杂（>5 实体或系统级） | <= 3 个 |

**合并优先级**：若初步识别出 3 个问题，必须检查能否合并——
"数据规模？性能要求？" → "数据量级及性能预期？"
"用户角色？权限？" → "用户角色及对应权限？"
禁止通过拆分单一关注点凑数。

### 2.2 矛盾约束检测（强追问触发器）

出现以下矛盾词对时，**立即追问，不可继续形式化**：

| 维度 | 矛盾对 |
|------|--------|
| 成本 vs 质量 | "免费/零成本" × "企业级/高可用/SLA" |
| 简洁 vs 完备 | "简单/极简" × "完整/全面/功能强大" |
| 速度 vs 复杂 | "毫秒级/极快" × "AI/复杂逻辑/大数据" |
| 灵活 vs 易用 | "灵活/可配置" × "开箱即用/零配置" |
| 通用 vs 深度 | "通用/标准" × "深度定制/特化" |

**矛盾追问模板**（强制）：

```
检测到约束冲突：

> "<原文片段>"

这些约束难以同时满足，需明确优先级：

1. <约束A> vs <约束B> —— 哪个优先？影响：<差异化设计>
2. 是否接受 <trade-off>？影响：<可行路径>

请按优先级排序后再继续。
```

### 2.3 语义张力检测（v3.1 新增）

词对匹配覆盖字面矛盾，但无法检测**语义张力**（如"简单"但列了 20 个功能）。当词对匹配未命中但存在以下信号时，加载 `references/contradiction-heuristics.md` 进行二次检测：

- 功能实体数 ≥ 5 但用户声称"简单/轻量"
- 时间约束 < 1 周但子系统 ≥ 3
- 成本约束（"开源/免费"）与运维期望不匹配
- 通用性宣称与实际领域紧耦合

语义张力 **不阻塞** 形式化流程（severity ≤ medium），仅要求标注 ⚠️ 并确认。

---

## 3. S2：复杂度分级（v3 新增）

| 级别 | 触发条件 | 模板 | 长度 |
|------|---------|------|------|
| **L1 微型** | 单对象、单输入输出、无规则分支 | mini 模板 | 300-600 字 |
| **L2 标准** | 2-5 个对象，含规则，无系统级 | 标准模板 | 800-1800 字 |
| **L3 扩展** | >5 对象 / 系统级 / STEM L2 / 多模块 | 扩展模板 | 1500-3500 字 |
| **L3+** | 第 6-8 层（弯曲/奇点/多场耦合/统一） | 扩展 + complexity-depth-reference.md | 2000-5000 字 |

### 分级判定算法

```
1. 数实体数量（名词短语）
2. 数规则分支（IF/WHEN/CASE）
3. 是否系统级关键词（服务/集群/分布式/多端）
4. 是否含 STEM 公式

L1: 实体 <= 1 且 规则 <= 1 且 无系统级
L3: 实体 > 5 或 系统级 或 STEM L2
其他: L2
```

---

## 4. S3：STEM 检测 + 失败模式匹配

### 4.1 STEM 触发关键词

| 类别 | 关键词 |
|------|--------|
| 数学 | 求、解、计算、积分、微分、方程、概率、矩阵、向量、证明 |
| 物理 | 速度、加速度、力、能量、动量、电场、磁场 |
| 算法 | 算法、复杂度、推荐、排序、分类、聚类、训练、损失 |

### 4.2 STEM 分级

| 等级 | 标准 | 处理 |
|------|------|------|
| **L0** | 一眼可算 | 直接答（走 S0-D） |
| **L1** | 需建模但公式标准 | STEM 模板 |
| **L2** | 需符号计算/求解 | STEM 模板 + **自动查 Wolfram Alpha** + 建议外部验证 |

### 4.2.1 Wolfram Alpha 自动验证（v4.1 新增）

> LLM 数学推理不可靠。STEM L1/L2 问题**必须**通过 Wolfram Alpha MCP
> 工具验证关键数学结果，不可仅凭 LLM 自我推理。

```
L1: 用 Wolfram Alpha 验证核心公式的数学正确性
L2: 用 Wolfram Alpha 做符号计算/方程求解，结果写入 B1-STEM 段
```

**MCP 工具路径**：
- 通用查询：`mcp_wolfram_full_query` 或 `mcp_wolfram_ask_pipeworx`
- 数学专项：优先用通用查询工具（`integrate` 等专项工具可能返回未结构化错误）
- 将 Wolfram 返回的权威结果写入 B1-STEM 段，标注 `[来源: Wolfram Alpha]`

### 4.3 失败模式知识库（v3 新增 / v3.1 外部化）

生成前匹配是否属于以下已知陷阱。**完整版（含变更日志）见 `references/failure-patterns.md`**，命中时按需加载。

以下为快速参考（8 类模式摘要）：

#### 模式 1：推荐系统类

**陷阱**：忽略冷启动 / 缺评估指标 / 复杂度未给

**强制要求**：
- 必含「冷启动策略」段（新用户、新内容两种）
- 必含「评估指标」表格（>=2 指标 + 目标值）
- 必给时间/空间复杂度

#### 模式 2：动力学/抛物类

**强制要求**：
- 必列运动方程
- 必定义坐标系（原点 + 轴向）
- 简化假设必标 ⚠️

#### 模式 3：对话/客服类

**强制要求**：
- 升级规则必含 IF-THEN 形式
- 必定义对话历史长度上限
- 必含 fallback 策略

#### 模式 4：协议实现类（OAuth、JWT...）

**强制要求**：
- 必含安全相关 ⚠️（token 过期、重放攻击）
- 必含错误码定义
- 必含状态机或时序图描述

#### 模式 5：分布式系统类

**强制要求**：
- 必给一致性级别（强/最终/因果）
- 必含故障场景（节点宕机、网络分区）
- 必给 CAP 取舍说明

#### 模式 6：登录/认证类（v3.1 新增）

**触发关键词**：登录、注册、认证、授权、SSO、OAuth、密码、token

**强制要求**：
- **必含登录方式枚举**：至少 3 种（密码 / OAuth / 验证码 / 生物识别）并说明取舍
- **必含失败场景**：密码错误次数限制、账号锁定阈值、解锁机制
- **必含会话管理**：token 有效期、refresh 策略、并发登录处理
- **必含安全 ⚠️**：密码哈希算法（bcrypt/argon2）、传输加密、防暴力破解
- **必含找回流程**：邮箱/手机验证码、安全问题、人工申诉

**反模式**：只设计"账号+密码"单一路径；未提及 token 过期处理；未声明密码存储方案。

#### 模式 7：数据导入/导出/迁移类（v3.1 新增）

**触发关键词**：导入、导出、迁移、同步、ETL、批处理

**强制要求**：
- **必含模式选择**：全量 / 增量 / 断点续传，并说明触发条件
- **必含失败处理**：部分失败策略（继续/中止）、回滚机制、重复数据去重
- **必含数据校验**：导入前预检（格式/编码/字段映射）、导入后校验（行数/校验和）
- **必含 ⚠️**：编码不一致、时区差异、字段类型不匹配、数据量上限
- **必含可观测**：进度展示、错误日志、失败行导出

#### 模式 8：搜索/查询类（v3.1 新增）

**触发关键词**：搜索、检索、过滤、查询

**强制要求**：
- **必含输入规范**：空查询处理、特殊字符、最小/最大长度
- **必含匹配策略**：精确 / 模糊 / 语义，及优先级
- **必含排序与分页**：默认排序、分页大小、深度分页
- **必含 ⚠️**：相关性 vs 时效性 trade-off、空结果处理、超时降级
- **必含性能约束**：响应时间目标、索引刷新延迟

---

## 5. S4：10 维度扫描

| # | 维度 | 关注点 |
|---|------|--------|
| 1 | 对象 | 涉及哪些实体？ |
| 2 | 结构 | 对象内部组成？ |
| 3 | 关系 | 对象间如何关联？ |
| 4 | 变化 | 时间维度演化？ |
| 5 | 对称 | 有无对偶/守恒？ |
| 6 | 不变量 | 永远成立的约束？ |
| 7 | 约束 | 边界/资源？ |
| 8 | 可能性 | 异常分支？ |
| 9 | 映射 | 输入到输出规则？ |
| 10 | 尺度 | 数据/性能量级？ |

**L1 微型**：只需扫描 1/7/9（对象/约束/映射）
**L2 标准**：全部 10 维
**L3 扩展**：全部 10 维 + 风险分析

每维度标 `✓` / `⚠️` / `✗`，状态符号不可替代。

---

## 6. S5：模板（按级别选用）

### 6.1 L1 微型模板

```
# 形式化规格（微型）

**对象**: <一句话>
**输入 → 输出**: <X> → <Y>
**核心规则**: <一条规则>
**验证**:
- 正例: <input → output>
- 反例: <input → 应拒绝>

**置信度**: 高/中/低
**理由**: <一句话>
```

### 6.2 L2 标准模板

```
# 形式化规格书

## 一、维度扫描报告

| 维度 | 状态 | 说明 |
|------|------|------|
| 对象 | ✓/⚠️/✗ | ... |
| 结构 | ✓/⚠️/✗ | ... |
| 关系 | ✓/⚠️/✗ | ... |
| 变化 | ✓/⚠️/✗ | ... |
| 对称 | ✓/⚠️/✗ | ... |
| 不变量 | ✓/⚠️/✗ | ... |
| 约束 | ✓/⚠️/✗ | ... |
| 可能性 | ✓/⚠️/✗ | ... |
| 映射 | ✓/⚠️/✗ | ... |
| 尺度 | ✓/⚠️/✗ | ... |

## 二、形式化规格

### B1. 核心对象
- **<对象1>**: <属性>

[STEM 题在此插入 B1-STEM]

### B2. 输入
- 类型: ...
- 格式: ...
- 示例: ...

### B3. 输出
- 类型: ...
- 格式: ...
- 示例: ...

### B4. 规则
- IF <条件> THEN <动作>

### B5. 步骤
1. ...
2. ...

### B6. 边界条件
- 上限/下限/异常

### B7. 验证标准
- 正例 / 反例 / 边界例

## 三、防幻觉加固

### 3.1 已显式化的隐含假设
- ✓ <假设1>

### 3.2 需要确认的不确定项
- ⚠️ <项1>

### 3.3 用户未提及但建议补充
- <建议1>

## 四、置信度评估

**置信度**: 高 / 中 / 低
**理由**: <一句话>
**降低不确定性的下一步**: <最值得追问的 1 个点>
```

### 6.3 L3 扩展模板

在 L2 基础上额外追加：

```
## 五、架构与边界

### 5.1 模块划分
| 模块 | 职责 | 输入 | 输出 |
|------|------|------|------|

### 5.2 数据流
<文字描述或 ASCII 图>

## 六、风险与降级

| 风险 | 概率 | 影响 | 缓解 |
|------|------|------|------|
| ⚠️ ... | 高/中/低 | ... | ... |

## 七、非功能性需求
- 性能/可用性/安全/可观测
```

### 6.4 B1-STEM 段（所有 STEM 题必含）

```
### B1-STEM. 数学/物理对象建模

**变量定义**:
| 符号 | 含义 | 类型 | 单位 | 取值范围 |
|------|------|------|------|---------|

**方程**:
<核心方程>

**常量**:
| 常量 | 值 | 可配置 |
|------|-----|--------|

**假设与简化** (必标 ⚠️):
- ⚠️ <假设1>

**坐标系**（如适用）:
- 原点/轴向
```

---

## 7. S6：防幻觉加固

### 必标 ⚠️ 的 6 类

1. 未经验证的库/API/版本
2. 物理/数学简化假设
3. 数据规模不明的"经验值"
4. 跨平台/版本兼容性
5. 性能/SLA 承诺
6. 安全相关默认值

### 禁用词（不可出现在规格主体）

`大概` `应该` `可能` `差不多` `或许` `似乎` `一般来说` `通常` `基本上` `现代` `主流` `流行`

**例外**：出现在防幻觉加固的 ⚠️ 描述中允许。

---

## 8. ★ S7：自检循环（v3 核心新增）

生成完规格书后，**逐项核对**以下 checklist：

```
[ ] 跳过判定执行了吗？
[ ] 模式选对了吗（skip/ask/spec）？
[ ] 复杂度判对了吗（L1/L2/L3）？
[ ] 一级章节齐了吗？
[ ] 状态符号用 ✓⚠️✗ 而非其他吗？
[ ] 置信度格式是 **置信度**: 高/中/低 吗？
[ ] 有禁用词吗（且不在 ⚠️ 上下文中）？
[ ] STEM 题含 B1-STEM 段吗？
[ ] 失败模式库的强制要求满足了吗？
[ ] 隐含假设都标 ⚠️ 或 ✓ 了吗？
[ ] **v3.1**: 追问数符合复杂度对应上限吗？
[ ] **v3.1**: 矛盾约束有没有先于形式化被识别？
[ ] **v3.1**: 命中失败模式 6/7/8 时，强制要求都满足了吗？
[ ] **v3.1**: 登录类是否枚举了 >=3 种登录方式？
[ ] **v3.1**: 导入类是否给了失败处理 + 进度可观测？
```

**自检报告**（必须附在输出末尾）：

```
---
[自检] ✓ 章节齐全 ✓ 置信度合规 ✓ 无禁用词 ✓ 模式匹配 OK
```

**若发现不合规**：
1. 在心中重写一次
2. 输出修正版
3. 自检报告标明哪一项被修复

**硬约束**：每次输出**最多重写 1 次**，避免死循环。

### S7.1 反例触发机制（v3.1 新增）

> 防自检套话化。当规格书零 ⚠️ 时可能是遗漏，而非完美。

```
若 ⚠️ 数量 = 0 且 复杂度 ≥ L2：
  → FALSE NEGATIVE 信号——没有真实复杂规格能做到零不确定性

强制重审以下来源：
1. 隐含假设：是否接受了用户未声明的条件？（如"假设数据库已配置"）
2. 外部依赖：是否假定了某库/API/版本的行为？
3. 性能/SLA：是否假定了规模而未经证实？
4. 边界条件：空输入/超大输入/并发/超时真的都覆盖了吗？

重审后必须新增至少 1 个 ⚠️。
仅当输入穷尽了一切细节（含 SLA/规模/版本/边界）时可豁免。
```

---

## 9. S8：置信度评估

| 等级 | 判定 |
|------|------|
| **高** | 10 维度中 >=8 ✓，无关键 ⚠️ |
| **中** | 10 维度中 >=6 ✓，1-3 个关键 ⚠️ |
| **低** | <6 ✓ 或 >=4 关键 ⚠️ |

低置信度时必须给"降低不确定性的下一步"建议。

---

## 10. 输出长度约束

| 类型 | 目标长度 |
|------|---------|
| 跳过 | < 100 字 |
| 追问 | < 400 字 |
| L1 微型 | 300-600 字 |
| L2 标准 | 800-1800 字 |
| L2 + STEM | 1200-2500 字 |
| L3 扩展 | 1500-3500 字 |

**反模式**：简单问题写 5000 字 ❌ / 复杂问题写 500 字 ❌ / 章节缺失 ❌

---

## 11. 失败模式对照表

| 失败模式 | 表现 | 修正 |
|---------|------|------|
| 该跳过没跳 | 给原子修改输出完整规格 | 强化 S0 |
| 该追问没追 | 对"做个智能系统"直接形式化 | 强化 S1 |
| 追问过多 | >3 个问题 | 收敛到 <=3 |
| 简单问题过度 | L1 用 L3 模板 | S2 分级 |
| 模板飘忽 | 章节标题随意改 | S7 自检 |
| STEM 缺公式 | 物理题没列方程 | B1-STEM |
| 假装确认 | 未验证 API 没标 ⚠️ | S6 |
| 模糊词泛滥 | 充斥"大概/应该" | S7 自检 |
| 置信度缺失 | 末尾无置信度 | S7 自检 |
| 推荐缺冷启动 | 推荐系统未提 | 失败模式 1 |

---

## 12. 版本历史

| 版本 | 变更 |
|------|------|
| 4.0 | + toolkit 模式 + 8 原子工具 + 3 预构建管道 + output_mode: hybrid + deprecation 策略 |
| 3.1 | + 非结构化输出跳过(E类) + 语义张力检测(2.3) + 反例触发(S7.1) + references/ 外部化 |
| 3.0 | + 自检循环 + 渐进式模板(L1/L2/L3) + 失败模式库 + L0简单题 |
| 2.0 | + 强制模板 + STEM 子流程 + 跳过强化 + 自检清单 + 失败对照表 |
| 1.0 | 10 维度 + 7 步骤 + 范式锚定 + 成本档位 |
