# Dogfood 种子 Query 列表

> **用途**：当 D3-D5 调用量不足时，团队成员可以从本列表选取 query 来触发 beta 路径。
> **使用**：在输入前加 `#beta` 前缀。

---

## Group A: DIRECT_RESPOND（预期：不触发 formalize）

```
#beta 你好
#beta 今天天气怎么样
#beta 什么是 Docker
#beta 把这段话翻译成英文：人工智能正在改变世界
#beta 总结一下这篇关于微服务的文章
```

## Group B: TOOL_EXECUTE（预期：直接执行）

```
#beta pytest tests/ -v
#beta 把 config.py 第 10 行的 DEBUG = False 改成 True
#beta 创建目录 src/components
```

## Group C: SKILL_INVOKE（预期：路由到技能）

```
#beta 设计一个 Redis 缓存层
#beta 审查这段代码：def foo(): pass
#beta 排查为什么 API 返回 500
#beta 设计一个支持水平扩展的网关
```

## Group D: FORMALIZE_REQUIRED（预期：先形式化再执行）

```
#beta 帮我设计一个推荐系统
#beta 做一个用户登录功能
#beta 设计一个分布式任务调度平台，支持优先级队列、失败重试、多租户隔离
#beta 优化一下性能
#beta 免费但企业级的消息队列方案
```

## 矛盾检测专项

```
#beta 简单但功能全面的后台管理系统
#beta 零成本的高可用数据库方案
#beta 毫秒级的 AI 图像识别
```

## 语义张力专项

```
#beta 做一个轻量的项目管理工具，需要甘特图、看板、工时统计、周报生成、资源分配、风险预警、文档管理、团队协作
#beta 这周内完成用户管理、权限控制、审计日志三个模块
```

---

## 覆盖矩阵

| Group | Seed 数 | 测试集覆盖 | 目标场景 |
|-------|--------|----------|---------|
| A | 5 | 40 cases | 直接响应路径验证 |
| B | 3 | 15 cases | 工具执行路径验证 |
| C | 4 | 20 cases | 技能路由验证 |
| D | 5 | 20 cases | 形式化触发验证 |
| 矛盾 | 3 | 5 cases | 矛盾检测验证 |
| 语义张力 | 2 | 5 cases | 语义启发式验证 |
| **总计** | **22** | **105 cases** | |
