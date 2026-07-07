# 项目级软件开发全流程 Skills 包

## 基本约束

- 本项目只使用项目内 skills，路径为 `skills/`，不要安装到全局 skills 目录。
- 本项目用于沉淀覆盖软件开发主要流程的项目级 Skills 包，包括需求分析、需求整理、需求拆解、代码分析、软件方案设计、详细设计、策略描述、代码实现、质量检查和文档导出。
- 工作流必须支持全流程模式、阶段直达模式、代码驱动模式和参考文档驱动模式。
- 文档内容和文件名尽量使用中文。
- 默认输出 Markdown；结构化中间产物使用 JSON，并统一放到 `state/`。
- 用户可见的实际业务交付物统一放到 `outputs/`，不要把工作流状态、画像、阶段 JSON 等中间产物放入 `outputs/`。
- Skills 包自身的建设方案、设计说明、产物契约、迭代计划统一放到 `docs/`，不要放到 `outputs/`。

## 目录职责

| 目录 | 职责 |
| --- | --- |
| `docs/` | 存放 Skills 包自身的设计方案、建设计划、产物契约、维护说明 |
| `skills/` | 存放项目级可用 skills，每个 skill 保留自己的 `SKILL.md`、`templates/`、`scripts/`、`references/` |
| `knowledge/` | 存放本地业务知识、术语、需求规范、设计规范、架构原则、编码规范、测试规范 |
| `mcp/` | 存放 MCP 示例配置，后续接入企业文档库、数据库、搜索服务、需求管理系统等 |
| `scripts/` | 存放项目级辅助脚本，例如知识库初始化、检索、Agent 包校验 |
| `state/` | 存放 Agent 内部工作流状态、结构化 JSON、参考文档画像等中间产物 |
| `outputs/` | 只存放通过 skills 生成的实际项目交付物 |

## 工作流入口

### 软件开发全流程

- 软件开发全流程建设方案见 `docs/软件开发全流程Skills包建设方案.md`。
- 完整软件开发流程采用“一个总工作流 skill + 多个阶段 skill + 横切质量门禁”的结构。
- 后续完整软件交付工作流默认入口为 `skills/software-delivery-orchestrator/SKILL.md`。
- 当 `software-delivery-orchestrator` 尚未建立时，按 `docs/软件开发全流程Skills包建设方案.md` 中的阶段设计执行和扩展。
- 不强制所有任务都从需求分析开始；用户可以直接进入代码分析、软件设计、策略文档、质量检查或导出阶段。
- 用户可以不使用项目内固定模板，而是提供一份参考文档；此时应先解析参考文档画像，再进入目标阶段。

软件开发全流程阶段：

1. 工作流初始化
2. 需求分析
3. 需求整理
4. 需求拆解
5. 现有代码分析
6. 软件方案设计
7. 软件详细设计
8. 策略描述文档
9. 开发任务计划
10. 代码实现
11. 质量门禁与导出

### 阶段直达与代码驱动

- 当用户明确要求直接执行某个阶段时，按阶段直达模式处理。
- 当用户没有需求输入，但要求基于当前代码输出软件设计文档、详细设计文档或策略描述文档时，按代码驱动模式处理。
- 代码驱动模式优先使用 `codebase-analysis-reporter` 分析当前代码，再调用 `solution-architecture-designer`、`detailed-design-writer` 或 `strategy-document-writer` 生成目标文档。
- 代码驱动模式下必须区分“确定事实”“合理推断”“待确认项”，不得把代码推断直接写成确定业务规则。

支持的入口类型：

| 入口类型 | 用途 |
| --- | --- |
| `full-flow` | 从需求开始执行完整流程 |
| `full-flow-with-code` | 从需求开始执行完整流程并生成测试通过的代码，再回填详设/策略 |
| `requirement-only` | 只做需求分析、需求整理、需求规格书或需求拆解 |
| `codebase-only` | 只分析当前代码结构和实现现状 |
| `design-from-code` | 基于当前代码生成软件方案或详细设计 |
| `strategy-from-code` | 基于当前代码生成策略描述文档 |
| `reference-doc-driven` | 基于用户提供的参考文档结构、风格或格式生成内容 |
| `design-from-code-with-reference` | 基于当前代码生成设计文档，同时参考用户提供的文档 |
| `strategy-from-reference` | 参考用户提供的策略文档生成新策略文档 |
| `requirement-from-reference` | 参考用户提供的需求文档生成新需求文档 |
| `export-with-reference-style` | 导出 Word/DOCX 时参考用户提供的文档格式或样式 |
| `task-plan-from-design` | 基于已有设计生成开发任务计划 |
| `implement-from-plan` | 基于任务计划或详细设计生成代码并测试通过 |
| `quality-only` | 只检查已有阶段产物质量 |
| `export-only` | 只导出 Word/DOCX 或 PDF |

### 参考文档驱动

- 当用户提供参考文档作为样例、模板、格式参考或内容参考时，按参考文档驱动模式处理。
- 参考文档驱动模式应优先使用 `skills/reference-document-profiler/SKILL.md`。如果该 skill 尚未建立，应按 `docs/软件开发全流程Skills包建设方案.md` 中的参考文档画像规则执行。
- 参考文档不能直接等同于项目模板；必须先判断参考用途：结构参考、内容参考、格式参考或综合参考。
- 参考文档画像应输出到 `state/参考文档结构画像.md` 和 `state/reference-document-profile.json`。
- 后续阶段 skill 应读取 `state/reference-document-profile.json`，按参考文档画像生成目标内容。
- 只要求参考结构时，不得复用参考文档原文内容。
- 只要求参考格式时，不得把参考文档旧项目内容带入新文档。
- 允许内容参考时，必须标记来源，并进入质量门禁检查。
- 参考文档中的项目名称、人员姓名、客户信息、日期、历史数据默认属于禁止复用项，除非用户明确要求保留。

### 需求规格书工作流

- 当前完整需求规格书工作流默认从 `skills/requirement-workflow-orchestrator/SKILL.md` 开始。
- 需求分析任务使用 `skills/requirement-analysis-report/SKILL.md`。
- 需求规格书撰写任务使用 `skills/requirement-specification-writer/SKILL.md`。
- 需求规格书默认输出 `outputs/02_需求规格书.md`，并同步输出 `state/structured/requirement-specification.json` 供需求拆解和后续设计消费。
- 需求质量检查任务使用 `skills/requirement-quality-gate/SKILL.md`。
- Word/DOCX 或 PDF 导出任务使用 `skills/requirement-document-exporter/SKILL.md`，但只能在用户明确要求导出时使用。

### 策略文档工作流

- 策略描述、控制策略、业务策略、规则逻辑、算法逻辑相关任务优先使用 `skills/strategy-document-writer/SKILL.md`。
- 策略文档可以作为软件开发全流程的独立阶段产物，也可以单独执行。

### 代码实现工作流

- 代码生成、按任务计划或详细设计落地实现、端到端从需求做到代码，优先使用 `skills/implementation-executor/SKILL.md`。
- 代码实现的产物是代码本身，写入代码仓库或工作区，不写入 `outputs/`；实现记录写入 `state/structured/implementation-record.json`，执行报告写入 `outputs/09_开发执行报告.md`。
- 只有实现记录中 `可进入代码驱动出文档 = true`（全部任务测试通过、无阻塞）时，才进入代码驱动模式，用真实代码反出权威版详细设计和策略文档；此时详设/策略以「测试通过的代码」为事实来源，编码前的前向设计只作为实现输入。

## 阶段产物规则

- 每个阶段优先输出 Markdown 文档，用于人类评审。
- 需要被后续阶段稳定消费的内容，应同时输出结构化 JSON。
- 后续阶段不得只依赖对话上下文，应优先读取上一阶段的 Markdown 和 JSON 产物。
- 阶段直达模式可以只生成目标阶段必要产物，但必须记录入口类型、跳过阶段和缺失前置材料。
- 代码驱动模式的产物必须保留代码依据、推断依据和待确认项。
- 参考文档驱动模式的产物必须保留参考文档路径、参考用途、允许复用范围和禁止复用项。
- 用户需要评审或交付的阶段 Markdown 产物默认放入 `outputs/`。
- 工作流状态、结构化 JSON、参考文档画像等中间产物放入 `state/` 或 `state/structured/`。
- 导出的 Word/DOCX 或 PDF 建议放入 `outputs/exported/`。

建议产物命名：

```text
outputs/
├── 01_需求分析报告.md
├── 02_需求规格书.md
├── 03_需求拆解清单.md
├── 04_现有代码分析报告.md
├── 05_软件方案设计.md
├── 06_软件详细设计说明书.md
├── 07_策略描述文档.md
├── 08_开发任务计划.md
├── 09_开发执行报告.md
├── 10_质量检查报告.md
└── exported/

state/
├── 工作流状态.json
├── 参考文档结构画像.md
├── reference-document-profile.json
└── structured/
```

## 导出规则

- 默认交付 Markdown，不主动生成 Word/DOCX 或 PDF。
- 只有用户明确要求 Word/DOCX 时，才使用对应 document exporter。
- 需求规格书 Word/DOCX 必须通过结构化 JSON 和 `skills/requirement-document-exporter/templates/需求规格书Word模板_美化版.docx` 直出。
- 不允许使用 Markdown 转 Word 作为需求规格书 Word 交付路径。
- 用户要求参考某份 Word/DOCX 格式导出时，应先生成参考文档画像，再决定是否提取或复用样式；不得直接把参考文档正文内容污染到新文档。
- 只有用户明确要求 PDF 时，才调用 PDF 导出脚本。

## 本地知识库

- 本地知识库放在 `knowledge/`。
- Agent 在分析需求、设计方案或分析代码前，应优先读取相关知识。
- `knowledge/索引.json` 维护知识文件、用途和关键词，便于检索。
- 新增业务规则、术语、需求规范、设计规范、架构原则、编码规范、测试规范或模板说明时，应同步更新 `knowledge/索引.json`。

建议知识库文件：

```text
knowledge/
├── 业务规则.md
├── 术语表.md
├── 需求规范.md
├── 设计规范.md
├── 架构原则.md
├── 编码规范.md
├── 测试规范.md
├── 文档模板说明.md
└── 索引.json
```

## MCP 接入

- MCP 配置和示例放在 `mcp/`。
- 当前仅提供示例配置，不包含真实凭据。
- 后续可接入企业文档库、数据库、搜索服务、需求管理系统、缺陷管理系统、代码仓库检索服务等。
- 接入 MCP 后，仍应先使用项目内 `knowledge/`、`state/`、`outputs/` 和 `skills/`，再按需查询外部系统。
- MCP 返回内容必须标记来源，不得无来源地覆盖项目内明确规则。

## 项目级辅助脚本

- `scripts/初始化项目知识库.py`：检查知识库必备文件是否存在。
- `scripts/查询知识库.py`：按关键词搜索 `knowledge/` 下的 Markdown 文档。
- `scripts/校验Agent包.py`：检查项目级 Agent 包结构和 skill 必备文件。

## Skills 包开发约定

- 新增或修改 skills 包自身设计文档时，放入 `docs/`。
- 新增业务产物、需求文档、设计文档、策略文档、导出文档时，放入 `outputs/`。
- 新增工作流状态、阶段 JSON、参考文档画像等内部衔接产物时，放入 `state/`。
- 新增阶段 skill 时，应包含 `SKILL.md`，并按需要包含 `templates/`、`scripts/`、`references/`。
- 每个 skill 应只做一个清晰环节，不要把全流程能力塞入单一 skill。
- 每个阶段 skill 应声明是否支持阶段直达、是否支持代码驱动模式、缺少前置材料时如何处理。
- 每个可能生成文档的阶段 skill 应声明是否支持参考文档驱动模式，以及如何消费 `state/reference-document-profile.json`。
- 总工作流 skill 负责编排、检查前置产物、更新状态、调用阶段 skill，不直接替代所有阶段 skill。
- 质量检查应作为横切环节，不要只依赖各阶段自检。

## 协作约定

- 可启用多 Agent 协同处理调研、代码分析、方案设计、质量检查等独立子任务。
- 子任务完成后应及时回收不再需要的子 Agent 或临时资源。
- 修改本包时保持一次交付自洽、可评审、可继续开发。
