---
name: requirement-decomposition-planner
description: Decompose upstream/customer/system requirements into ASPICE SWE.1 style software requirements, CM traceability matrix, coverage statistics, consistency issues, and design input set. Use for 需求拆解 / 软件需求分析 / CM符合性矩阵 / ASPICE风格需求分解, after a requirements specification or upstream requirement baseline exists.
---

# Requirement Decomposition Planner

## 工作目标

按汽车电子软件开发中的 ASPICE SWE.1 软件需求分析风格，把普通需求规格书、客户需求或系统需求拆解为可进入软件方案设计、详细设计和验证策划的软件需求基线。

本 skill 的核心不是生成开发任务，而是建立：

- 上游需求基线
- 软件需求清单（`SWR-*`）
- CM 符合性矩阵
- 覆盖性统计
- 一致性/不完整性问题
- 设计输入集

首版不强制功能安全字段，不引入 ASIL、FSR、TSR、SSR。

## 输入要求

优先读取：

- `outputs/02_需求规格书.md`
- `state/structured/requirement-specification.json`
- 用户补充的客户需求、系统需求、版本约束、优先级或确认记录
- `knowledge/汽车电子软件需求拆解规范.md`
- `knowledge/需求规范.md`

缺少结构化规格书时，可以从 Markdown 规格书提取上游需求编号和描述。缺少 `02_需求规格书.md` 且没有等价上游需求材料时，记录阻塞项，不伪造拆解产物。

## 工作流程

1. 建立上游需求基线：保留已有 `SYS-*`、`FR-*`、`NFR-*`、`DR-*`、`PR-*` 等编号；无编号时生成 `UR-*` 代理编号并标记来源。
2. 分析上游需求是否清晰、可验证、一致；缺参数、缺边界、冲突和不可验证描述进入一致性问题或待确认项。
3. 将上游需求拆解为软件需求 `SWR-*`，每条软件需求必须可追踪、可验证、可进入设计。
4. 为每条 `SWR-*` 标识需求类型、验证方式、优先级、复杂度、依赖、风险和设计输入提示。
5. 建立 CM 符合性矩阵，表达上游需求到软件需求的直接承接、拆分、合并、派生或约束继承关系。
6. 统计覆盖状态：已覆盖、部分覆盖、未覆盖、待确认、不适用。
7. 生成 `outputs/03_需求拆解清单.md` 和 `state/structured/requirement-breakdown.json`。
8. 运行 `scripts/校验需求拆解.py` 校验结构化 JSON；校验不通过时不得声明产物可进入后续设计。

## 输出规则

- 人类评审产物：`outputs/03_需求拆解清单.md`
- 机器可读产物：`state/structured/requirement-breakdown.json`
- 不要把 JSON 中间产物放入 `outputs/`。
- 文档可按参考文档画像调整版式，但不得牺牲 `SWR-*`、CM 矩阵、覆盖统计和待确认项。

## 编号规则

- 软件需求使用 `SWR-001`、`SWR-002`。
- 上游已有编号必须保留。
- 上游无编号时使用 `UR-001`、`UR-002` 作为代理编号，并在来源说明中标记“代理编号”。
- 每条 `SWR-*` 必须追溯到至少一个上游需求。
- 每条上游功能类需求必须在 CM 矩阵中有覆盖状态。

## 质量标准

- 不把开发任务当成需求拆解主项，例如“前端开发”“后端开发”“数据库开发”“接口开发”。
- 不提前固化代码实现、AUTOSAR 组件、具体接口名或存储结构，除非上游材料明确要求。
- 每条软件需求都要有验证方式。
- 覆盖状态必须自洽；部分覆盖、未覆盖和待确认必须说明原因。
- 上游需求不清晰时，不补脑成确定需求，必须进入一致性问题或待确认项。

## 支持模式

- 阶段直达：支持。需要需求规格书或等价上游需求材料。
- 参考文档驱动：支持。可读取 `state/reference-document-profile.json` 调整表格/章节形态。
- 代码驱动：不支持。没有上游需求时应走 `codebase-analysis-reporter`，不做 SWE.1 需求拆解。

## 资源

- `templates/需求拆解清单模板.md`：Markdown 评审产物模板。
- `templates/需求拆解数据模板.json`：`requirement-breakdown.json` 结构契约。
- `references/ASPICE风格需求拆解规则.md`：拆解规则、字段枚举、CM 表规则。
- `scripts/校验需求拆解.py`：结构化数据质量门。
