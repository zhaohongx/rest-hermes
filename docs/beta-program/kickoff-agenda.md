# P3 Beta Dogfood Kickoff

## 时长：30 分钟 | 日期：2026-05-16

## 参与人
dogfood 团队全员 + P3 owner + 独立 reviewer

---

## 议程

### 1. 背景与目标（5min）
- **为什么做**：当前 formalize 是"全有或全无"的强制流程，90% 的简单请求不需要完整形式化
- **目标**：classifier 前置路由 → 仅复杂需求走 formalize，简单需求直接响应
- **成功标准**：D14 评估时 misclassification < 8%，满意度 ≥ 4.0/5，零 P0

### 2. 触发方式 Demo（5min）
- **方式 1**：`#beta 帮我设计一个推荐系统`
- **方式 2**：`[experimental] 把这段需求 formalize 一下`
- **方式 3**：白名单（LLM 识别 dogfood 团队成员）
- **演示**：Live 跑 2 个示例（简单需求 + 复杂需求）

### 3. 反馈模板介绍（5min）
- 文件位置：`docs/beta-program/feedback-template.md`
- 填写时长：30 秒
- 关键字段：分类准确性 1-5 / 整体满意度 1-5 / 问题标记
- 反馈渠道：GitHub issue with label `beta-feedback`

### 4. 最低基线（5min）
- **每人每天 ≥ 1 次** beta 调用
- **每次调用后 1 条反馈**
- D7 mid-term check 需 ≥ 20 条累计反馈
- 连续 3 天零调用 → 团队群 @ 提醒

### 5. 关键日期（5min）
| 日期 | 事件 |
|------|------|
| 2026-05-16 (D2) | Kickoff，dogfood 正式开始 |
| 2026-05-22 (D7) | Mid-term check（30min SOP） |
| 2026-05-30 (D14) | 转正/延期/回退 决策评审 |
| 2026-06-15 (D30) | 硬截止——必须有最终决策 |

### 6. Q&A + Demo（5min）
- 每人当场跑 1 次 demo
- 确认反馈 issue tracker 链接
- 确认紧急 P0 联系人

---

## 离会确认清单

- [ ] 知道如何触发 beta 路径（#beta / [experimental] / whitelist）
- [ ] 知道反馈 issue tracker 链接
- [ ] 知道反馈模板字段（30 秒填完）
- [ ] 知道紧急 P0 联系人
- [ ] 已在本地跑通 1 次 demo

---

## Issue Labels 配置

```bash
gh label create "beta-feedback" --color "1d76db" --description "P3 beta dogfood feedback entry"
gh label create "misclassified" --color "d93f0b" --description "Classifier returned wrong primary_intent"
gh label create "p0" --color "b60205" --description "Beta P0 incident - immediate rollback required"
gh label create "error-code" --color "fbca04" --description "Error code triggered (EC-XXX)"
gh label create "dogfood-satisfaction" --color "0e8a16" --description "User satisfaction rating"
```
