---
name: solution-architecture-designer
description: Create a lightweight software solution design based on a user-specified local code repository and codebase-analysis.json, choosing the minimum-change implementation route that reuses existing software capabilities. Use after requirement decomposition and codebase analysis, before code implementation.
---

# Solution Architecture Designer

## 工作目标

基于用户指定的本地代码目录和 `codebase-analysis-reporter` 产出的代码事实，生成一份**轻量软件方案设计**。本阶段只做编码前的实现路线决策，不写权威详细设计。

本 skill 必须遵守：

- 现有代码优先。
- 最小改动优先。
- 复用现有软件功能优先。
- 没有代码依据时，不得把设计判断写成确定方案。

权威详细设计仍应在代码实现并测试通过后，基于真实代码回填。

## 输入要求

优先读取：

- 用户指定的本地代码目录路径。
- `outputs/04_现有代码分析报告.md`
- `state/structured/codebase-analysis.json`
- `outputs/03_需求拆解清单.md`
- `state/structured/requirement-breakdown.json`
- `knowledge/架构原则.md`、`knowledge/设计规范.md`（若存在）

如果用户只给了代码目录但没有代码分析产物，应先调用 `codebase-analysis-reporter` 分析该目录，再进入方案设计。

缺少代码目录且没有 `state/structured/codebase-analysis.json` 时，记录阻塞项，不生成正式方案。

## 工作流程

1. 读取 `requirement-breakdown.json`，确定本次实现范围和关联 `SWR-*`。
2. 读取 `codebase-analysis.json`，确认代码仓库路径、可复用模块、现有接口、数据结构、调用关系和测试缺口。
3. 映射需求到现有能力：可复用、需小改、需新增、需隔离。
4. 设计最小改动方案：说明推荐路线、影响模块、接口与数据影响、实现约束。
5. 给出备选方案与放弃原因，避免单一路线臆断。
6. 标识风险与验证策略，尤其是边界条件、兼容性、回归影响和测试方式。
7. 输出 `outputs/05_软件方案设计.md` 和 `state/structured/solution-design.json`。
8. 运行 `scripts/校验方案设计.py state/structured/solution-design.json`，校验通过后才可进入代码实现。

## 产出规则

- 用户可见产物：`outputs/05_软件方案设计.md`
- 结构化产物：`state/structured/solution-design.json`
- 不直接修改目标代码目录。
- 不把 `solution-design.json` 放入 `outputs/`。

## 质量标准

- 推荐方案必须说明为什么是最小合理改动。
- 必须列出现有能力复用项；若无法复用，必须说明代码事实依据。
- 影响模块必须有代码依据。
- 方案不得脱离 `codebase-analysis.json` 自行设计全新架构。
- 不写函数级、类级、字段级详细设计；除非该内容是已有代码事实并带代码依据。
- 所有待确认参数、接口、边界和业务取舍都进入待确认项。

## 支持模式

- 阶段直达：支持，但必须有代码目录或代码分析产物。
- 需求驱动：支持。读取 `requirement-breakdown.json` + `codebase-analysis.json`。
- 代码驱动：支持。仅基于现有代码输出当前方案说明与最小改造建议，但不得臆造需求。
- 代码实现前置：支持。作为 `implementation-executor` 的轻量路线输入。
- 参考文档驱动：可读取 `state/reference-document-profile.json` 调整文档结构。

## 资源

- `templates/软件方案设计模板.md`：Markdown 评审产物模板。
- `templates/方案设计数据模板.json`：`solution-design.json` 结构契约。
- `references/代码先行方案设计规则.md`：最小改动、复用优先和代码依据规则。
- `scripts/校验方案设计.py`：校验方案是否基于现有代码、是否可追踪、是否避免详设化。
