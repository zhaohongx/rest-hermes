# intent-classifier 分类测试用例集

> **用途**：验证分类器准确率。每次修改规则后逐条跑通。
> **版本**：v1.0，120 条用例
> **通过标准**：整体准确率 ≥ 90%，LLM 兜底占比 < 30%，UNKNOWN 占比 < 5%

---

## 一、Group A: DIRECT_RESPOND（40 条）

### A1: chitchat（5 条）
```
C001: "你好"                        → chitchat, conf≥0.9
C002: "在吗"                        → chitchat, conf≥0.9
C003: "谢谢你"                      → chitchat, conf≥0.9
C004: "hello"                       → chitchat, conf≥0.9
C005: "晚安"                        → chitchat, conf≥0.9
```

### A2: confirmation（5 条）
```
C006: "好的"                        → confirmation, conf≥0.9
C007: "继续"                        → confirmation, conf≥0.9
C008: "OK"                          → confirmation, conf≥0.9
C009: "嗯"                          → confirmation, conf≥0.9
C010: "确认"                        → confirmation, conf≥0.9
```

### A3: emotional_support（5 条）
```
C011: "我今天心情不好"              → emotional_support, conf≥0.8
C012: "工作压力好大"                → emotional_support, conf≥0.8
C013: "好焦虑啊"                    → emotional_support, conf≥0.8
C014: "最近老失眠"                  → emotional_support, conf≥0.7
C015: "感觉要崩溃了"                → emotional_support, conf≥0.8
```

### A4: simple_qa（5 条）
```
C016: "什么是布朗运动"              → simple_qa, conf≥0.9
C017: "巴黎在哪"                    → simple_qa, conf≥0.9
C018: "Python 是什么意思"           → simple_qa, conf≥0.9
C019: "今天周几"                    → simple_qa, conf≥0.9
C020: "谁发明了电话"                → simple_qa, conf≥0.9
```

### A5: translation（5 条）
```
C021: "翻译成英文"                  → translation, conf≥0.9
C022: "translate to Chinese"        → translation, conf≥0.9
C023: "把这段话译成日文"            → translation, conf≥0.9
C024: "用英文怎么说"                → translation, conf≥0.8
C025: "翻成法语"                    → translation, conf≥0.9
```

### A6: summarization（5 条）
```
C026: "总结一下"                    → summarization, conf≥0.9
C027: "概括这段内容"                → summarization, conf≥0.9
C028: "帮我归纳要点"                → summarization, conf≥0.8
C029: "提炼一下核心内容"            → summarization, conf≥0.8
C030: "summarize this"              → summarization, conf≥0.9
```

### A7: rewrite（5 条）
```
C031: "把这段改得正式点"            → rewrite, conf≥0.9
C032: "润色一下这段话"              → rewrite, conf≥0.9
C033: "改写一下这个标题"            → rewrite, conf≥0.9
C034: "调成商务风格"                → rewrite, conf≥0.8
C035: "rewrite this paragraph"      → rewrite, conf≥0.9
```

### A8: creative_writing（5 条）
```
C036: "写一首关于秋天的诗"          → creative_writing, conf≥0.9
C037: "编个科幻故事"                → creative_writing, conf≥0.9
C038: "写个七言绝句"                → creative_writing, conf≥0.9
C039: "创作一首关于月亮的歌"        → creative_writing, conf≥0.9
C040: "写篇散文"                    → creative_writing, conf≥0.8
```

---

## 二、Group B: TOOL_EXECUTE（15 条）

### B1: shell_command（5 条）
```
C041: "pytest tests/ -v"            → shell_command, conf≥0.9
C042: "kubectl apply -f deploy.yaml"→ shell_command, conf≥0.9
C043: "docker compose up -d"        → shell_command, conf≥0.9
C044: "git log --oneline"           → shell_command, conf≥0.9
C045: "npm install react"           → shell_command, conf≥0.9
```

### B2: atomic_edit（5 条）
```
C046: "把 user.py 第 42 行的 print 改成 logger.info" → atomic_edit, conf≥0.9
C047: "删除 utils.js 中的 unused 函数"              → atomic_edit, conf≥0.9
C048: "重命名 config.py 为 settings.py"             → atomic_edit, conf≥0.9
C049: "在 app.ts 第 100 行添加 import React"        → atomic_edit, conf≥0.9
C050: "替换所有 foo() 为 bar()"                    → atomic_edit, conf≥0.8
```

### B3: file_operation（5 条）
```
C051: "新建文件 config.py"           → file_operation, conf≥0.9
C052: "创建目录 tests/unit/"         → file_operation, conf≥0.9
C053: "删除 temp 目录"               → file_operation, conf≥0.9
C054: "重命名 old.py 为 new.py"      → file_operation, conf≥0.9
C055: "移动文件到 src/utils/"        → file_operation, conf≥0.8
```

---

## 三、Group C: SKILL_INVOKE（20 条）

### C1: code_design（5 条）
```
C056: "设计一个缓存层"              → code_design, conf≥0.8
C057: "规划一下模块结构"            → code_design, conf≥0.8
C058: "设计数据库表结构"            → code_design, conf≥0.8
C059: "设计一个 API 接口"           → code_design, conf≥0.8
C060: "规划代码重构方案"            → code_design, conf≥0.8
```

### C2: code_review（5 条）
```
C061: "审查这段代码"                → code_review, conf≥0.9
C062: "review 这个 PR"              → code_review, conf≥0.9
C063: "检查代码安全性"              → code_review, conf≥0.8
C064: "看看有什么性能问题"          → code_review, conf≥0.7
C065: "帮我 review 一下"            → code_review, conf≥0.8
```

### C3: debug（5 条）
```
C066: "为什么报 500 错误"           → debug, conf≥0.9
C067: "这个函数不工作了"            → debug, conf≥0.8
C068: "排查这个内存泄漏"            → debug, conf≥0.9
C069: "请求超时是什么原因"          → debug, conf≥0.8
C070: "帮我调试这段代码"            → debug, conf≥0.9
```

### C4: system_design（5 条）
```
C071: "设计一个消息队列"            → system_design, conf≥0.8
C072: "规划微服务架构"              → system_design, conf≥0.9
C073: "设计一个分布式缓存方案"      → system_design, conf≥0.9
C074: "设计高可用架构"              → system_design, conf≥0.8
C075: "设计电商平台架构"            → system_design, conf≥0.9
```

---

## 四、Group D: FORMALIZE_REQUIRED（20 条）

### D1: ambiguous_requirement（5 条）
```
C076: "优化一下性能"                → ambiguous_requirement, conf≥0.8
C077: "改进一下这个模块"            → ambiguous_requirement, conf≥0.8
C078: "做个智能系统"                → ambiguous_requirement, conf≥0.9
C079: "帮我弄一下"                  → ambiguous_requirement, conf≥0.8
C080: "搞个排序功能"                → ambiguous_requirement, conf≥0.7
```

### D2: contradictory_constraints（5 条）
```
C081: "免费但企业级的登录系统"      → contradictory_constraints, conf≥0.9
C082: "简单但功能全面的 CRM"        → contradictory_constraints, conf≥0.9
C083: "毫秒级 AI 推荐"              → contradictory_constraints, conf≥0.8
C084: "灵活配置的开箱即用方案"      → contradictory_constraints, conf≥0.9
C085: "零成本的高可用消息队列"      → contradictory_constraints, conf≥0.9
```

### D3: high_complexity（5 条）
```
C086: "设计微服务架构的电商平台，包括用户服务、商品服务、订单服务、支付服务和消息通知服务" → high_complexity, conf≥0.9
C087: "做一个分布式日志收集和分析系统" → high_complexity, conf≥0.9
C088: "设计一个支持百万并发的网关"     → high_complexity, conf≥0.8
C089: "搭建包含 CI/CD、监控、日志、告警的完整运维平台" → high_complexity, conf≥0.9
C090: "设计一个多租户 SaaS 平台"       → high_complexity, conf≥0.8
```

### D4: cross_domain（5 条）
```
C091: "做一个 ML 模型训练的 Web 管理平台"       → cross_domain, conf≥0.8
C092: "设计集成了 AI 客服的电商小程序"            → cross_domain, conf≥0.8
C093: "做一个 IoT 设备管理 + 数据分析的后台"      → cross_domain, conf≥0.8
C094: "设计前端 React + 后端 Go + 部署 K8s 的全栈方案" → cross_domain, conf≥0.9
C095: "设计算法训练 + 工程部署的一体化 pipeline"  → cross_domain, conf≥0.8
```

---

## 五、边界 case（15 条）

### 易混淆 case
```
C096: "你好，帮我查一下日志"        → debug, NOT chitchat
C097: "好的，那我们开始设计"        → system_design/code_design, NOT confirmation
C098: "写一首诗"                    → creative_writing, NOT ambiguous
C099: "设计方案"                    → ambiguous_requirement (缺目标), NOT system_design
C100: "优化 user.py 的查询性能"     → code_design, NOT debug
```

### 短输入边界
```
C101: "啊"                          → chitchat/emotional (low conf)
C102: "..."                         → UNKNOWN/chitchat (low conf)
C103: "救命"                        → debug/emotional (ambiguous)
C104: "🙂"                          → chitchat (low conf)
C105: ""                            → UNKNOWN (空输入)
```

### 多意图混合
```
C106: "写个缓存模块并审查一下"      → code_design (primary), code_review (secondary)
C107: "排查这个报错，然后设计修复方案" → debug (primary), code_design (secondary)
C108: "设计 API 并写单元测试"       → code_design (primary), atomic_edit/code_design (secondary)
C109: "翻译这篇文章然后总结要点"    → translation (primary), summarization (secondary)
C110: "优化性能，如果太复杂就先分析瓶颈" → ambiguous_requirement (primary), debug (secondary)
```

---

## 六、鲁棒性测试（10 条）

```
C111: "HELP!!! 生产环境挂了!!!"     → debug (emergency tone)
C112: "可以帮我看一下吗 谢谢啦"      → 取决于上下文，可能 chitchat+隐式 debug
C113: "asdfghjkl"                   → UNKNOWN (无意义输入)
C114: "帮我写一个函数 输入数组 返回排序后的数组" → atomic_edit/code_design
C115: "请问..."                     → 取决于后续内容
C116: "我有一个问题"                → ambiguous_requirement (未说出问题)
C117: "这个你懂吗"                  → ambiguous_requirement
C118: "和上次一样"                  → confirmation (有上下文依赖)
C119: "不对，我说的是..."           → rewrite/debug (纠错信号)
C120: "能快一点吗"                  → optimize/ambiguous (没说具体对象)
```

---

## 运行说明

每条用例的验证步骤：
1. 将 `输入` 传入 intent-classifier
2. 检查 `primary_intent` 是否匹配 `期望`
3. 检查 `confidence` 是否在预期范围内

**通过标准**：
- Group A（40 条）：准确率 ≥ 95%（规则覆盖充分）
- Group B（15 条）：准确率 ≥ 95%（正则+关键词）
- Group C（20 条）：准确率 ≥ 85%（部分依赖 LLM）
- Group D（20 条）：准确率 ≥ 90%
- 边界（15 条）：准确率 ≥ 75%（允许模糊边界 low conf）
- 鲁棒性（10 条）：不崩溃（允许 UNKNOWN）
- 整体：≥ 90%

---

## 七、补充边界与鲁棒（+40 条，总计 160 条）

### Group A 补足（+5 条）
```
C121: "hello world"                   → chitchat/simple_qa (ambiguous greeting vs code)
C122: "谢谢，太棒了"                  → chitchat (gratitude)
C123: "能帮我个忙吗"                  → ambiguous_requirement (unspecified request)
C124: "Python 的语言特性有哪些"        → simple_qa (knowledge qa, not code)
C125: "把readme翻成中文"              → translation
```

### Group B 补足（+5 条）
```
C126: "rm -rf /tmp/cache"             → shell_command
C127: "把 config 里的 api_key 换成从环境变量读取" → atomic_edit
C128: "mkdir -p src/components"       → shell_command
C129: "删除所有 .pyc 文件"            → shell_command / file_operation
C130: "追加一行 import os 到 main.py 头部" → atomic_edit
```

### Group C 补足（+5 条）
```
C131: "帮我看看这段 SQL 有没有注入风险" → code_review (security review)
C132: "设计一个 REST API 的错误码规范" → code_design
C133: "这个接口为什么偶尔返回 502"     → debug (intermittent error)
C134: "设计一个支持水平扩展的用户服务"  → system_design (with scalability)
C135: "怎么重构这个 2000 行的函数"     → code_design (refactoring)
```

### Group D 补足（+5 条）
```
C136: "做一个类似抖音的App"           → ambiguous_requirement (highly vague)
C137: "需要实时 + 批量 + 高可用的数据处理" → contradictory_constraints (conflicting requirements)
C138: "设计全国银行核心交易系统"       → high_complexity (national scale)
C139: "做一个融合区块链+AI的供应链平台" → cross_domain (blockchain + AI + supply chain)
C140: "帮个忙"                        → ambiguous_requirement (maximally vague)
```

### 边界加强（+10 → 共 25 条）
```
C141: "帮我看看代码"                  → ambiguous (code_review? debug? 未指定)
C142: "这个怎么用"                    → ambiguous_requirement (unclear subject)
C143: "跟我上次说的那样做"            → confirmation/chitchat (context-dependent)
C144: "前端 React 后端 Go 数据库 PostgreSQL 缓存 Redis 消息队列 Kafka" → high_complexity (tech stack enumeration)
C145: "写 写 写"                      → UNKNOWN (nonsensical repetition)
C146: "🐛🐛🐛"                         → UNKNOWN/chitchat (emoji-only)
C147: "I need help with my code"     → ambiguous_requirement (language detection needed)
C148: "帮我写一个函数"                → ambiguous_requirement (missing what function)
C149: "README 写一下"                 → atomic_edit/documentation (context needed)
C150: "这个需求和 PM 确认过了没"      → chitchat/confirmation (meta-discussion)
```

### 鲁棒加强（+10 → 共 20 条）
```
C151: ""                             → UNKNOWN (empty input)
C152: "   "                          → UNKNOWN (whitespace only)
C153: "\n\t\n"                       → UNKNOWN (whitespace characters)
C154: "bug: 用户登录后白屏 #12345"    → debug (issue report format)
C155: "帮我写个脚本监控 CPU 超过 90% 就发钉钉告警" → code_design/shell_command (hybrid)
C156: "https://github.com/user/repo/issues/1 这个问题" → debug (URL + context)
C157: "需求文档在 confluence 第 3 页" → chitchat/info (reference sharing, not a request)
C158: "!!!! SOS !!!!"                → UNKNOWN (emergency signal, no content)
C159: "第一：改登录页 第二：加验证码 第三：改密码逻辑 第四：写测试 第五：部署" → high_complexity (5 tasks enumerated)
C160: "推荐 搜索 登录 导入 导出 聊天 支付 地图" → high_complexity (8 feature keywords, multiple failure patterns)
