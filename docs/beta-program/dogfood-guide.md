# Intent-Classifier + Formalize v4.0 Dogfood 指南

## Beta 期信息

- **起始**：2026-05-16（D2 after Commit 2 merge）
- **评估**：2026-05-30（D14）
- **硬截止**：2026-06-15（D30，不允许无限期 beta）

## 如何触发 beta 路径

**方式 1：输入前缀**
```
#beta 帮我写一个登录流程的规格说明
```

**方式 2：显式标记**
```
[experimental] 把这段需求 formalize 一下
```

**方式 3：团队白名单**
LLM 识别到 dogfood 团队成员上下文时自动走 beta 链路。

## 每日最低基线

- 每人每天 ≥ 1 次 beta 调用
- 每次调用后填写一条[反馈](feedback-template.md)（30 秒）

## 反馈渠道

- **Issue tracker**：<待创建>
- **Daily standup**：5 分钟同步异常案例
- **紧急 P0**：直接 @skill-maintainer

## 注意事项

- beta 链路失败不会影响用户体验——自动降级到 v3.1
- 遇到误分类不要手动纠正，如实记录即可
- D7 做 mid-term check，提前发现趋势性问题
