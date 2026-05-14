# D7 Mid-term Check 标准作业流程

> **目的**：在 beta 期中点提前预警不达标项，避免 D14 评估时才发现问题已无法挽回。
> **时长**：≤ 30 分钟（数据采集 20min + 会议 5min + 决策 5min）
> **参与人**：P3 owner（必）+ 1 名独立 reviewer（必）+ dogfood 核心成员（可选）

---

## 阶段 1：数据采集（会前 24 小时，约 20 分钟）

### 1.1 从 issue tracker 导出反馈数据

```bash
# 假设用 GitHub issues 作为反馈渠道
gh issue list \
  --label "beta-feedback" \
  --state all \
  --json number,title,body,createdAt,labels \
  --limit 200 > /tmp/feedback-d7.json
```

### 1.2 计算 7 项关键指标

| 指标 | 计算方法 | 数据源 |
|------|---------|--------|
| dogfood 调用总数 | feedback 条目数 | issue tracker |
| 误分类率 | "误分类"标签数 / 总数 | issue tracker |
| 平均满意度 | satisfaction 字段算术平均 | feedback template |
| 平均 confidence | confidence 字段算术平均 | feedback template |
| P0 事件数 | "p0" 标签数 | issue tracker |
| EC-001/002 累计 | "error-code" 标签 grep | issue tracker |
| 团队参与率 | 提交反馈人数 / dogfood 团队人数 | issue tracker |

---

## 阶段 2：5 分钟同步会议

### 议程

| 时间 | 内容 | 负责人 |
|------|------|--------|
| 0:00-1:00 | 数据快报（7 指标当前值 vs D14 目标） | P3 owner |
| 1:00-2:00 | 异常案例 top 3 简述 | P3 owner |
| 2:00-3:30 | 独立 reviewer 提问 + 风险点 | reviewer |
| 3:30-4:30 | 决策：继续 / 干预 / 提前回退 | 全员 |
| 4:30-5:00 | 行动项分配 | P3 owner |

### 会议禁忌
- ❌ 讨论具体 bug 的修复方案（移到 standup）
- ❌ 重新设计 classifier 规则（不在本会议范围）
- ❌ 超时（严格 5 分钟，超时即视为决策异常需升级）

---

## 阶段 3：决策矩阵

### 3.1 早期预警阈值（D7 用，比 D14 宽松 1.5 倍）

| 指标 | D14 目标 | D7 预警线 | D7 红线 |
|------|---------|----------|---------|
| 调用总数 | ≥ 50 | ≥ 20 | < 10 |
| 误分类率 | < 8% | < 12% | > 15% |
| 满意度 | ≥ 4.0 | ≥ 3.5 | < 3.0 |
| P0 事件 | 0 | 0 | ≥ 1 |
| EC-001/002 | ≤ 5 | ≤ 4 | > 5 |
| 团队参与率 | - | ≥ 60% | < 40% |

### 3.2 决策树

```
所有指标在预警线内？
├─ 是 → 🟢 继续按原计划，D14 评估
└─ 否 → 检查是否触红线
        ├─ 任一红线 → 🔴 提前回退或冻结 beta
        │              （不等 D14，立即触发 promotion-checklist "回退动作"）
        └─ 仅预警 → 🟡 启动定向干预
                    （见下方干预 playbook）
```

### 3.3 定向干预 Playbook

| 触发条件 | 干预动作 | 负责人 | 完成时限 |
|---------|---------|--------|---------|
| 调用总数 < 20 | 团队群内 @ 提醒 + 提供 5 个示例 query | P3 owner | D8 |
| 误分类率 12-15% | 抽样 10 个误分类案例，更新 decision-rules.md | P3 owner | D10 |
| 满意度 3.0-3.5 | 1:1 访谈 3 位低分反馈者，定位根因 | reviewer | D10 |
| EC-001/002 = 4-5 | 检查降级链是否被频繁触发，确认 fallback 是否生效 | P3 owner | D9 |
| 团队参与率 < 60% | 与未参与成员沟通，降低使用门槛 | manager | D8 |

---

## 阶段 4：Mid-term Check 报告模板

```markdown
# D7 Mid-term Check 报告

- 日期：YYYY-MM-DD
- P3 owner：______
- Independent reviewer：______
- Beta 起始：YYYY-MM-DD（已过 7 天）
- 评估日：YYYY-MM-DD（还有 7 天）

## 7 指标快报

| 指标 | D7 实测 | D7 预警线 | D7 红线 | 状态 |
|------|--------|----------|---------|------|
| 调用总数 | __ | ≥ 20 | < 10 | 🟢/🟡/🔴 |
| 误分类率 | __% | < 12% | > 15% | 🟢/🟡/🔴 |
| 满意度 | __ | ≥ 3.5 | < 3.0 | 🟢/🟡/🔴 |
| confidence 均值 | __ | - | - | - |
| P0 事件 | __ | 0 | ≥ 1 | 🟢/🟡/🔴 |
| EC-001 累计 | __ | ≤ 4 | > 5 | 🟢/🟡/🔴 |
| EC-002 累计 | __ | ≤ 4 | > 5 | 🟢/🟡/🔴 |
| 团队参与率 | __% | ≥ 60% | < 40% | 🟢/🟡/🔴 |

## 异常案例 Top 3
1. ___（issue #___）
2. ___（issue #___）
3. ___（issue #___）

## 决策
- [ ] 🟢 继续，按原计划 D14 评估
- [ ] 🟡 启动定向干预（勾选下方）
- [ ] 🔴 提前回退（执行 promotion-checklist "回退动作"）

## 签字
- P3 owner: ______
- Reviewer: ______
- 报告归档路径：docs/beta-program/reports/d7-YYYY-MM-DD.md
```

---

## 阶段 5：归档与传播

1. 报告落盘到 `docs/beta-program/reports/d7-<date>.md`
2. 摘要发到团队群（≤ 5 行）
3. 行动项进入团队 task tracker
4. 若 🔴 决策，立即触发 incident response 流程

---

## 风险提示

- ⚠️ 不要因为"才过 7 天"而忽略红线信号——早期红线意味着系统性问题，越拖越糟
- ⚠️ 不要把 mid-term check 退化为"汇报会"——必须有决策产出
- ⚠️ 不要让 P3 owner 同时担任 reviewer——必须由独立第三方介入
