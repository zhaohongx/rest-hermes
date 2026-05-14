# Templates Index

> **状态**：本文件作为兼容性入口保留。实际模板已拆分至 `templates/` 子目录，请直接引用子文件。
> **计划移除**：v4.1

## 模板索引

| 复杂度 | 文件 | 适用场景 |
|--------|------|---------|
| L1 微型 | [templates/L1.md](templates/L1.md) | 单对象、单输入输出、无规则分支 |
| L2 标准 | [templates/L2.md](templates/L2.md) | 2-5 对象，含规则，无系统级 |
| L3 扩展 | [templates/L3.md](templates/L3.md) | >5 对象 / 系统级 / 多模块 |
| STEM | [templates/stem.md](templates/stem.md) | 数学/物理/算法建模（通用） |
| STEM-Eng | [stem-eng-sub-template.md](stem-eng-sub-template.md) | 工艺/制造/化工（继承 stem.md） |

## 公共片段

跨模板共享的结构元素见 [templates/_shared.md](templates/_shared.md)。
