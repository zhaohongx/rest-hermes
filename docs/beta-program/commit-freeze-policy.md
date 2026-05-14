# Beta 期 Commit Freeze Policy

> **适用范围**：D2 (2026-05-16) → D14 (2026-05-30)
> **目的**：稳定 beta 期变量，避免 D7/D14 决策时无法定位回归根因
> **负责人**：P3 owner

---

## 一、为什么需要 freeze

当前 main 分支已积累 15 个 P3 相关 commit。Beta 期的核心任务是**收集真实使用反馈**，而非继续开发新功能。继续插入 commit 会带来：

1. **回归根因定位困难**：D7 发现问题时，无法用 `git bisect` 快速定位
2. **指标污染**：D2-D14 的 7 指标基线必须建立在稳定代码之上
3. **决策依据失效**：D14 评审时若代码已大幅变化，evaluation 结论无法外推

---

## 二、Commit 分类与处置

### 🟢 允许（Allowed）— 自合

| 类型 | 前缀 | 示例 |
|------|------|------|
| 文档更新 | `docs:` | 更新 CHANGELOG / 增加 daily report |
| 配置调整 | `chore:` | 调整 health-check 阈值 |
| CI 修复 | `chore(ci):` | 修复 CI 脚本 bug |
| Daily 数据 | `data:` | 落盘 daily metrics |

### 🟡 受限（Restricted）— 需 P3 owner + 1 reviewer

| 类型 | 前缀 | 示例 |
|------|------|------|
| P2 bug fix | `fix:` | 修复 v3.1 active 路径的非阻塞 bug |
| Beta 文档 | `docs(beta):` | 修订 dogfood-guide |
| 测试增补 | `test:` | 增补 edge case |

### 🔴 禁止（Forbidden）— 无例外

| 类型 | 示例 | 例外条件 |
|------|------|---------|
| 新功能 | 新 skill / 新 reference | **无例外**，等 D14 后 |
| 重构 | references 再次拆分 | **无例外** |
| classifier 规则调整 | 修改 decision-rules.md | 仅 P0/P1 hotfix |
| toolkit-mode 工具修改 | 修改 v4.0 tool-contracts | 仅 P0/P1 hotfix |

### ⚡ Hotfix 通道

P0 事件触发时：

```bash
git checkout -b hotfix/p0-<description>
git commit -m "hotfix(<scope>): <description>

P0: triggered on dogfood D<day>
Owner: <name>
Refs: issue #<number>"
```

**Hotfix 要求**：24h 内 review + merge，≤ 30 行改动，必须附 regression test，daily standup 通报。

---

## 三、Branch Protection

```bash
# GitHub repo settings → Branches → main:
# - Require PR review (1 approver)
# - Require status checks: check-frontmatter / check-status-references / check-glossary
# - Require linear history
# - Restrict pushes (PR only)
```

---

## 四、解冻条件

Freeze 自动解除（任一）：

1. **D14 评审通过**：P3 转正 active，进入正常开发
2. **D14 评审失败**：执行回退后恢复开发
3. **P3 owner 显式解冻**：仅 dogfood 提前完成且无异常时

---

## 五、签字确认

团队成员确认已阅读本 policy：

- [ ] @member1
- [ ] @member2
- [ ] @member3

**签字截止**：D3 (2026-05-17) EOD
