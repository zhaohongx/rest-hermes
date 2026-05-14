# P3 Beta 转正决策检查表

> **评估人**：≥ 2 人（含 1 名非 P3 owner）
> **评估日期**：2026-05-30（D14）

## A. 量化指标（必达）

| 指标 | 目标值 | 实测值 | 达标？ |
|------|-------|-------|------|
| misclassification_rate | < 8% | __% | ☐ |
| dogfood_satisfaction | ≥ 4.0/5 | __ | ☐ |
| P0 incidents | == 0 | __ | ☐ |
| EC-001 累计 (classifier timeout) | ≤ 5 | __ | ☐ |
| EC-002 累计 (classifier low confidence) | ≤ 5 | __ | ☐ |
| classifier confidence 平均 | ≥ 0.75 | __ | ☐ |
| dogfood 调用总数 | ≥ 50 | __ | ☐ |

## B. 定性评估

| 维度 | 评估 |
|------|------|
| 等价性偏差（v3.1 vs v4.0 关键字段差异） | < 10% / 10-20% / > 20% |
| 团队反馈情绪倾向 | 积极 / 中性 / 消极 |
| 文档与实际行为一致性 | 一致 / 局部偏离 / 显著偏离 |
| 是否有未预料的 corner case | 无 / 有但已修复 / 有未解决 |

## C. 决策矩阵

| 综合表现 | 决策 | 后续动作 |
|---------|------|---------|
| A 全达标 + B 全积极 | 🟢 转正 | 移除 beta 字段，enabled_by_default: true，preview → active |
| A 1-2 项不达标 | 🟡 延长 2 周 | 定向修复，D28 再评估，不超过 hard_deadline |
| A 3+ 项不达标 / B 显著消极 | 🔴 回退 | 标 deprecated，git revert Commit 2，复盘重新规划 |
| 出现 P0 | 🔴 立即回退 | 不等评估日，直接 revert |

## D. 转正动作清单（若 🟢）

- [ ] intent-classifier/SKILL.md: status: beta → active, 移除 beta 字段
- [ ] formalize/SKILL.md: status: beta → active, mode: toolkit
- [ ] tool-contracts.md: @status: beta → active
- [ ] pipeline-recipes.md: @status: beta → active
- [ ] orchestration-protocol.md: status: beta → active
- [ ] enabled_by_default: false → true
- [ ] CHANGELOG.md 记录转正
- [ ] 团队通告 + 更新 README

## E. 回退动作清单（若 🔴）

- [ ] git revert <Commit 2 hash>
- [ ] 验证 P1+P2 不受影响（25 条回归用例）
- [ ] 团队通告回退原因
- [ ] 撰写 incident postmortem（72h 内）
- [ ] 重新规划：是否需要重设计 classifier？是否拆分更小的 P3.1/P3.2？

## 签字

- **评估人 1**（P3 owner）：______________
- **评估人 2**（独立 reviewer）：______________
- **决策日期**：2026-05-30
- **决策结果**：🟢 / 🟡 / 🔴
