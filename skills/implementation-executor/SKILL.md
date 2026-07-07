---
name: implementation-executor
description: Turn an approved development task plan or detailed design into working, test-passing code, then record what was actually built. Use when the user asks to 生成代码 / 写代码 / 实现代码 / 按任务计划开发 / 把设计落地成代码, or wants an end-to-end run from requirements all the way to tested code. This skill's deliverable is source code plus a machine-readable implementation record (not a document); that record and the test-passing code become the fact source for code-driven detailed-design and strategy documents.
---

# Implementation Executor

## 工作目标

把「开发任务计划 / 详细设计 / 软件方案」转化为**测试通过、可追溯到需求编号的真实代码**，并产出一份结构化的实现记录。

本 skill 是整个软件交付工作流里唯一真正**产出代码**的环节。它填补了原工作流的缺口：此前流程到「开发任务计划」（阶段8）就停在文档层面，不写代码；而涉及代码的 skill（代码分析、方案设计、详细设计、策略文档）全都把代码当作**输入事实来源**，从不产出代码。

本 skill 的产物不是文档，而是：

- 代码（写入代码仓库/工作区，**不写入 `outputs/`**）
- `state/structured/implementation-record.json`（实现记录，机器可读契约）
- `outputs/09_开发执行报告.md`（面向人类评审的执行报告）

## 在工作流中的位置

本 skill 位于「前向设计」与「代码驱动回填文档」之间，是二者的桥：

```text
需求 → 分析 → 规格书 → 拆解 → 方案设计 → 详细设计（前向蓝图）
                                    │
                        【本 skill：代码生成 + 跑测试直到通过】
                                    │
                测试通过的代码 + implementation-record.json = 事实来源
                                    │
        代码驱动模式：codebase-analysis-reporter
                                    │
        detailed-design-writer / strategy-document-writer（以真实代码为准）
                                    │
        详细设计 / 策略文档（忠实于已验证的实现，不漂移）
```

关键设计后果：详细设计和策略文档因此有两次产出时机——编码**前**的前向蓝图（指导怎么写），和编码**后**测试通过的忠实文档（记录真的写成了什么）。**最终交付以编码后版本为权威版**，前向设计只作为本 skill 的输入。这从根本上治了「设计先于代码、代码一改文档就过时」的漂移问题。

## 触发场景

- 用户说「生成代码」「实现代码」「把设计/任务写成代码」「按任务计划开发」「把这个功能开发出来」
- 用户要求「从需求一路跑到代码」「端到端实现」「写完代码测试通过后再出详细设计/策略文档」
- 已有 `08_开发任务计划.md` 或 `06_软件详细设计说明书.md`，要求据此落地实现

## 输入要求

优先收集（按优先级）：

1. `outputs/08_开发任务计划.md` + `state/structured/implementation-plan.json`（首选依据）
2. `outputs/06_软件详细设计说明书.md` + `state/structured/detailed-design.json`
3. `outputs/05_软件方案设计.md` + `state/structured/solution-design.json`
4. `outputs/02_需求规格书.md` + `state/structured/requirement-specification.json`（需求编号来源）
5. 现有代码仓库（判断复用/新增/修改边界）
6. `knowledge/编码规范.md`、`knowledge/测试规范.md`（若存在）

如果上游材料不齐，**不要停下也不要臆造**：

- 上游任务计划/详细设计尚未产出时，记录阻塞项，可降级为基于需求规格书实现，并标注「依据不足、待补前置设计」。
- 阶段直达时，必须在实现记录中写明 `跳过阶段` 与 `缺失前置材料`。
- 每个无法从设计/需求确认的实现决策，写入待确认项，不伪装成既定方案。
- 绝不把「未实现」标记为「已实现」，不把「跳过测试」当作「测试通过」。

## 工作步骤

1. **建立任务→代码→需求映射**：读任务计划/详细设计，为每个开发任务确定要动的文件，并挂上它追溯的需求编号（FR-xxx / 需求条目）。
2. **实现代码**：逐个任务实现，**优先复用现有代码**，遵守项目既有风格与 `knowledge/编码规范.md`。
3. **编写测试**：为每个任务写单元/集成测试，测试应覆盖该任务对应的验收标准。
4. **运行测试直到通过**：跑测试，失败则修复；无法通过的，如实标记「已实现未验证 + 失败原因」，不得跳过或注释掉测试蒙混。
5. **记录实现**：按 `templates/实现记录模板.json` 生成 `state/structured/implementation-record.json`，逐任务记录实现文件、实现状态、测试结果、复用项、推断项、待确认项。
6. **产出执行报告**：按 `templates/开发执行报告模板.md` 生成 `outputs/09_开发执行报告.md` 供人评审。
7. **过质量门**：只有「测试通过且可追溯需求编号」的任务，才把 `可进入代码驱动出文档` 置为 true；下游代码驱动 skill 据此决定是否可以基于这份代码反出详设/策略文档。

## 实现状态枚举

参照全流程「确定事实 / 合理推断 / 待确认项」的一贯约束，每个任务的实现状态必须落在明确枚举里：

| 状态 | 含义 | 是否可进入下游出文档 |
| --- | --- | --- |
| `已实现且测试通过` | 代码写完，测试跑过 | 是 |
| `已实现未验证` | 代码写完，但测试缺失或未运行 | 否，先补验证 |
| `部分实现` | 只完成一部分，余下有阻塞 | 否 |
| `未实现（阻塞）` | 因前置缺失/歧义无法实现 | 否，记录阻塞项 |

## 与代码驱动模式的衔接（核心契约）

本 skill 是代码驱动模式（`design-from-code` / `strategy-from-code`）的**上游供给方**：

- 它产出的「测试通过的代码 + implementation-record.json」正是 `codebase-analysis-reporter` 需要的事实来源。
- 下游 `detailed-design-writer` / `strategy-document-writer` 在代码驱动模式下读取真实代码 + 实现记录，生成忠实于实现的文档。
- 因此 `full-flow-with-code` 全流程的收尾不是「阶段8 任务计划」，而是「编码 → 测试通过 → 回填详设/策略 → 质量门禁」。
- 实现记录里的 `需求编号` 追溯链，让最终详设/策略文档能一路回溯到需求规格书，保证需求—代码—文档三者对齐。

## 产出规则

- **代码写入代码仓库/工作区，绝不写入 `outputs/`**（代码不是文档交付物）。
- `state/structured/implementation-record.json` 写入 `state/`（内部契约，非用户交付物），并记录入口类型、跳过阶段和缺失前置材料。
- `outputs/09_开发执行报告.md` 是面向评审的人类可读产物，可进 `outputs/`。
- 测试代码随源码进仓库，不进 `outputs/`。

## 质量标准 / 最终自检

- 每个任务是否都挂了需求编号，能回溯到规格书。
- 测试是否真的运行且通过，而不是被跳过或删除。
- 实现状态是否如实反映（不把未完成写成完成）。
- 是否优先复用了现有代码，而非重复造轮子。
- 代码是否写进了仓库而非 `outputs/`。
- `可进入代码驱动出文档` 的判定是否与各任务测试状态自洽（有失败或阻塞时不得为 true）。
- 待确认项、推断项是否显式列出。

## 支持的模式

- **阶段直达**：支持。入口类型 `implement-from-plan`，只要有任务计划或详细设计即可直接执行。
- **代码驱动关系**：本 skill 是代码驱动模式的**供给上游**，不是自身被代码驱动。
- **全流程**：入口类型 `full-flow-with-code`，从需求一路到「测试通过的代码 + 回填详设/策略」。
- **参考文档驱动**：一般不适用（本 skill 产代码不产文档）；若用户对执行报告有格式要求，可读取 `state/reference-document-profile.json`。
- **缺前置材料**：降级基于规格书实现 + 标注依据不足，记录阻塞项，绝不伪造。

## 资源

- `templates/实现记录模板.json`：implementation-record.json 的结构契约。
- `templates/开发执行报告模板.md`：面向评审的执行报告骨架。
- `references/代码实现执行规则.md`：实现顺序、复用优先、测试门槛、状态枚举判定、与代码驱动模式的交接规则。
- `scripts/校验实现记录.py`：校验实现记录 JSON 的字段完整性、需求追溯与质量门自洽性。
