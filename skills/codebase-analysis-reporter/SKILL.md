---
name: codebase-analysis-reporter
description: Analyze an existing code repository and produce a fact-based codebase analysis report plus a structured JSON, strictly separating confirmed facts (with code references), reasonable inferences, and open questions. Use for 分析代码 / 分析仓库 / 看看这个项目的架构 / codebase analysis, and as the fact-source entry point of code-driven mode (design-from-code / strategy-from-code) and of the implementation-executor loop (analyzing test-passing code before back-filling detailed design and strategy documents).
---

# Codebase Analysis Reporter

## 工作目标

基于真实代码仓库建立**事实基础**：识别技术栈、目录结构、模块职责、接口、数据模型和关键调用关系，并把结论严格区分为「确定事实 / 合理推断 / 待确认项」。

本 skill 是**代码驱动模式的事实来源起点**。方案设计、详细设计、策略文档在代码驱动模式下都不直接读代码，而是读本 skill 产出的 `codebase-analysis.json`——所以本 skill 的准确性和事实/推断分离，决定了整条代码驱动链路是否可信。

产物：

- `outputs/04_现有代码分析报告.md`（人类评审）
- `state/structured/codebase-analysis.json`（机器可读契约，供下游 skill 消费）

## 在工作流中的位置

本 skill 是两条链路的起点：

```text
【代码驱动模式】
当前代码 → 本 skill → solution-architecture-designer / detailed-design-writer / strategy-document-writer → 质量门禁

【代码生成闭环（implementation-executor 下游）】
测试通过的代码 + implementation-record.json → 本 skill → detailed-design-writer / strategy-document-writer（回填权威版详设/策略）
```

在闭环里，本 skill 读 `implementation-executor` 产出的「测试通过的代码 + 实现记录」，把它转成结构化事实，让详设/策略以真实实现为准。

## 两种运行语境

| 语境 | 事实来源 | 分析重点 |
| --- | --- | --- |
| 需求驱动 | 代码 + 需求拆解 | 现有代码如何承接新需求：可复用 / 需新增 / 需修改 |
| 代码驱动 | 仅代码（无需求输入） | 当前系统真实做了什么：能力、流程、边界、策略 |

两种语境都必须遵守三态区分；代码驱动语境尤其不得把推断写成事实。

## 触发场景

- 用户说「分析这个仓库」「看看这个项目的架构」「分析当前代码结构」「codebase 分析」
- 入口类型 `codebase-only` / `design-from-code` / `strategy-from-code` 的第一步
- `implementation-executor` 完成、测试通过后，回填详设/策略前的第一步

## 输入要求

- 当前代码仓库路径（必需）
- `03_需求拆解清单.md` + `requirement-breakdown.json`（需求驱动语境）
- `state/structured/implementation-record.json` + 测试通过的代码（闭环回填语境）
- README、配置文件、路由、接口定义、数据库迁移、测试、构建脚本
- `knowledge/架构原则.md`、`knowledge/设计规范.md`（若存在）

缺输入的处理：

- 无需求输入时，按代码驱动语境执行，不臆造需求。
- 代码仓库无法访问某些部分时，把「未读区域」记入待确认项，不对未读代码下结论。

## 工作步骤

1. **扫描技术底座**：可先运行 `scripts/扫描代码结构.py` 得到技术栈标志文件、目录结构、入口和文件类型分布，作为分析起点（辅助线索，不是结论）。
2. **识别模块与职责**：读关键目录和入口，梳理模块边界与职责，每项标注代码依据（文件/符号路径）。
3. **提取接口、数据模型、调用关系**：API/路由、数据结构/迁移、关键调用链，均给代码依据。
4. **映射需求（需求驱动）**：把需求拆解项映射到代码，判断可复用 / 需新增 / 需修改。
5. **反向提取能力（代码驱动）**：从条件、规则、状态机反推当前系统能力和边界。
6. **三态归类**：把每条结论归入确定事实、合理推断或待确认项。
7. **识别技术债、风险、测试缺口**。
8. **输出报告和 JSON**：`04_现有代码分析报告.md` + `codebase-analysis.json`。

## 三态强制（核心约束）

对齐全流程一贯要求，任何结论必须落入三态之一：

| 类型 | 定义 | 写法要求 |
| --- | --- | --- |
| 确定事实 | 代码中明确存在的文件、接口、字段、流程、条件判断 | **必须给出代码路径、模块或符号依据** |
| 合理推断 | 从命名、调用关系、条件组合推断出的业务含义 | **必须标记为「推断」**，不能写成事实 |
| 待确认项 | 代码无法证明、需要业务或研发确认的内容 | **必须进入待确认清单** |

不得在未读代码时直接下设计结论；不得把推断包装成确定业务规则。

## 与代码生成闭环的衔接

- 在 `implementation-executor` 之后运行时，优先以 `implementation-record.json` 标记的「已实现且测试通过」任务对应的代码为事实来源。
- 实现记录里的 `需求编号` 让代码分析能继续挂需求追溯链，最终详设/策略可一路回溯到需求规格书。
- 只有实现记录 `可进入代码驱动出文档 = true` 时，才据此产出权威版文档；否则在报告中标注「代码未全部验证，分析仅供参考」。

## 产出规则

- `outputs/04_现有代码分析报告.md` 是人类评审产物。
- `state/structured/codebase-analysis.json` 是机器契约，供下游 skill 读取，不进 `outputs/`。
- 报告中每个确定事实都应能点到具体文件/符号；无依据的判断归入推断或待确认。

## 质量标准 / 最终自检

- 是否基于真实文件和代码引用，而非泛泛而谈。
- 确定事实是否都有代码依据。
- 推断是否显式标记，没有伪装成事实。
- 未读代码、无法确认处是否进了待确认清单。
- 需求驱动语境下，是否说明现有代码如何支撑或阻碍需求。
- 代码驱动语境下，是否避免把当前实现直接当成最优设计。

## 支持的模式

- **阶段直达**：支持。入口 `codebase-only` 只做代码分析。
- **代码驱动**：本 skill 是代码驱动模式的事实来源起点。
- **闭环回填**：读 `implementation-record.json` + 测试通过的代码，供下游回填详设/策略。
- **参考文档驱动**：若用户对报告格式有要求，可读取 `state/reference-document-profile.json`。
- **缺前置材料**：无需求时走代码驱动语境；无法访问的代码进待确认项，不臆造。

## 资源

- `templates/现有代码分析报告模板.md`：报告骨架。
- `templates/代码分析数据模板.json`：`codebase-analysis.json` 的结构契约；其中 `确定事实` 必须使用 `{内容, 代码依据}` 对象，保证每条事实可机器校验到代码依据。
- `references/代码分析规则.md`：扫描顺序、事实与推断判据、三态定义、代码依据要求、两种语境差异。
- `scripts/扫描代码结构.py`：纯标准库扫描技术栈、目录结构、入口和文件类型分布。
- `scripts/校验代码分析.py`：校验 `codebase-analysis.json` 的字段完整性、运行语境、代码依据与三态结构。
