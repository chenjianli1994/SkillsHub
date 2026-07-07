---
name: software-delivery-orchestrator
description: Orchestrate the project-level Chinese software delivery workflow across requirements, code analysis, design documents, strategy documents, quality checks, and exports. Use when the user asks to run a full software development documentation workflow, jump directly into a stage, generate design or strategy documents from current code, use a reference document as a structure/style source, check workflow status, or decide which project-local skill should handle a request.
---

# Software Delivery Orchestrator

## 工作目标

作为项目级软件开发全流程入口，识别用户请求属于全流程、阶段直达、代码驱动、参考文档驱动、质量检查或导出任务，并调度项目内对应 skill。

本 skill 只负责编排和状态管理，不直接替代阶段 skill 写完整文档。

## 目录规则

- 用户可见产物写入 `outputs/`。
- Agent 内部状态、结构化 JSON、中间画像写入 `state/`。
- Skills 包建设文档写入 `docs/`。
- 不要把中间 JSON 放入 `outputs/`，除非用户明确要求导出 JSON。

## 入口类型

| 入口类型 | 触发场景 | 后续动作 |
| --- | --- | --- |
| `full-flow` | 用户要求从需求开始跑完整流程 | 需求分析 -> 需求整理 -> 需求拆解 -> 代码分析 -> 方案设计 -> 详细设计 -> 策略文档 -> 任务计划 -> 质量门禁 |
| `full-flow-with-code` | 用户要求从需求一路做到测试通过的代码 | 需求分析 -> …… -> 任务计划 -> 代码实现（`implementation-executor`）-> 代码驱动回填详设/策略 -> 质量门禁 |
| `requirement-only` | 用户只要需求分析、需求规格书、需求拆解或需求确认 | 调用需求类 skills；需求拆解调用 `requirement-decomposition-planner` |
| `codebase-only` | 用户只要分析当前代码结构和实现现状 | 调用 `codebase-analysis-reporter`，未建立时输出待建提示 |
| `design-from-code` | 用户没有需求输入，要求基于当前代码生成设计文档 | 先代码分析，再方案/详细设计 |
| `strategy-from-code` | 用户要求基于当前代码生成策略文档 | 先代码分析，再调用 `strategy-document-writer` |
| `reference-doc-driven` | 用户提供参考文档并要求按结构、风格或格式生成内容 | 先调用 `reference-document-profiler` |
| `design-from-code-with-reference` | 当前代码 + 参考文档生成设计文档 | 参考文档画像 -> 代码分析 -> 设计文档 |
| `strategy-from-reference` | 参考策略文档生成新策略文档 | 参考文档画像 -> 策略文档 |
| `requirement-from-reference` | 参考需求文档生成新需求文档 | 参考文档画像 -> 需求类 skills |
| `export-with-reference-style` | 导出 Word/DOCX 时参考用户提供的文档格式或样式 | 参考文档画像 -> 导出 |
| `task-plan-from-design` | 基于已有设计生成开发任务计划 | 调用任务计划 skill，未建立时输出待建提示 |
| `implement-from-plan` | 按任务计划或详细设计生成代码并跑测试 | 调用 `implementation-executor`；上游任务计划/详设缺失时降级基于规格书并记录阻塞 |
| `quality-only` | 只检查已有产物质量 | 调用质量门禁 |
| `export-only` | 只导出 Word/DOCX/PDF | 调用导出 skill |

## 执行流程

1. 读取 `AGENTS.md` 和 `docs/软件开发全流程Skills包建设方案.md`。
2. 检查 `state/` 和 `outputs/` 是否存在；缺失时提示创建，不要把中间产物写入 `outputs/`。
3. 根据用户请求识别入口类型。
4. 读取 `state/工作流状态.json`，如不存在则按 `templates/工作流状态模板.json` 建立状态结构。
5. 检查目标阶段的最小输入是否满足。
6. 如果用户提供参考文档，先调用 `reference-document-profiler` 生成 `state/reference-document-profile.json`。
7. 调用目标阶段 skill，或在对应 skill 尚未建立时输出明确的待建阶段和阻塞项。
8. 更新 `state/工作流状态.json`。
9. 用户明确要求导出时，调用对应 document exporter。

## 状态文件规则

状态文件位置：

```text
state/工作流状态.json
```

状态文件必须记录：

- 入口类型
- 当前阶段
- 阶段状态
- 输入材料
- 用户可见输出
- 内部状态产物
- 阻塞项
- 待确认项
- 更新时间

状态文件是内部中间产物，不属于用户交付物。

## 阶段调度规则

- 需求类任务优先使用 `requirement-workflow-orchestrator`、`requirement-analysis-report`、`requirement-specification-writer`。
- 需求拆解任务优先使用 `requirement-decomposition-planner`，按 ASPICE SWE.1 风格输出软件需求清单、CM 矩阵和 `requirement-breakdown.json`。
- 策略文档任务优先使用 `strategy-document-writer`。
- 参考文档驱动任务优先使用 `reference-document-profiler`。
- 代码分析、方案设计、详细设计、任务计划等 skill 尚未建立时，不要假装已完成；在状态文件中记录阻塞项。
- 质量检查应作为横切环节，不能仅依赖阶段自检。

## 参考文档驱动规则

当用户提供参考文档时：

1. 先判断参考用途：结构参考、内容参考、格式参考或综合参考。
2. 调用 `reference-document-profiler` 生成参考文档画像。
3. 后续阶段读取 `state/reference-document-profile.json`。
4. 禁止把参考文档中的项目名、人员、客户、日期、历史数据直接污染到新文档。

## 自检清单

交付前检查：

- `outputs/` 是否只包含用户需要的产出物。
- `state/` 是否承载中间 JSON 和工作流状态。
- 入口类型是否记录清楚。
- 缺少的阶段 skill 是否以阻塞项呈现，而不是伪造产物。
- 用户明确要求导出前，是否没有主动生成 Word/PDF。

## 资源

- `templates/工作流状态模板.json`：内部状态文件结构。
- `templates/入口类型判定表.md`：入口类型和触发语义。
- `scripts/识别入口类型.py`：按关键词初步识别入口类型。
- `scripts/更新工作流状态.py`：创建或更新 `state/工作流状态.json`。
- `references/阶段调度规则.md`：阶段调度、缺失 skill 和阻塞处理规则。
