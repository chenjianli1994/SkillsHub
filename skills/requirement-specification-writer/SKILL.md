---
name: requirement-specification-writer
description: Write an optimized Chinese requirements specification from a confirmed requirements analysis report, user clarification notes, draft PRD, or approved requirement baseline. Use after the user confirms analysis results and wants a formatted, complete, testable requirements specification with numbered functional requirements, acceptance criteria, scope boundaries, assumptions, dependencies, and traceability. Default output is Markdown; if the user explicitly requests Word/DOCX, generate structured requirements data for the dedicated Word template instead of converting Markdown to Word; if the user requests PDF, use the requirement-document-exporter skill.
---

# Requirement Specification Writer

## 工作目标

基于已经确认的需求分析结果，生成一份结构完整、术语统一、编号清晰、可评审、可开发、可测试的 Markdown 需求规格书。

## 输入要求

优先使用以下输入：

- 需求分析报告。
- 用户对待确认问题的确认结果。
- 原始需求文件或补充说明。

如果缺少确认结果，不要停止；继续生成规格书，但必须把未确认内容写入“待后续确认事项”，并在相关需求条目中标注假设。

## 工作流程

1. 读取已确认的需求分析报告和用户补充说明。
2. 合并同义术语，建立术语表，避免同一对象多种叫法。
3. 明确范围内、范围外、本期、后续，避免把运营动作或实现方案误写成需求。
4. 将功能需求拆成可编号条目，每条需求包含触发条件、前置条件、处理规则、输入输出、异常场景和验收标准。
5. 对数据、权限、流程、非功能、外部依赖分别成章，避免散落在功能描述中。
6. 可运行 `scripts/生成需求编号.py` 辅助扫描候选功能需求并生成编号建议。
7. 读取 `templates/优化后的需求规格书模板.md`，按模板输出中文 Markdown 规格书。
8. 如果用户明确要求 Word/DOCX，不要把 Markdown 转成 Word；同时生成 `需求规格书Word数据.json`，其结构参考 `requirement-document-exporter/templates/需求规格书Word数据模板.json`，再调用 `requirement-document-exporter` 按 Word 模板生成 DOCX。
9. 如果用户明确要求 PDF，调用 `requirement-document-exporter` 将指定文件或当前最新规格书导出为 PDF。

## 编写规则

- 功能需求编号使用 `FR-001`、`FR-002`。
- 非功能需求编号使用 `NFR-001`、`NFR-002`。
- 数据需求编号使用 `DR-001`、`DR-002`。
- 权限需求编号使用 `PR-001`、`PR-002`。
- 每条需求都要能被测试或验收，避免“友好”“高效”“完善”“尽快”等不可验证表述。
- 未经确认的推断必须标注为“假设”，不能写成确定事实。
- 用户明确指定的实现约束可以保留；否则不要把技术实现提前固化为业务需求。
- 默认只生成 `.md` 文件；用户明确要求 Word/DOCX 时才生成结构化 JSON 和 `.docx`，明确要求 PDF 时才生成 `.pdf`。

## 质量门禁

规格书交付前检查：

- 结构是否完整，章节是否按模板齐全。
- 每个核心功能是否有编号、触发、规则、输出、异常和验收标准。
- 范围内外是否明确。
- 角色、权限、数据口径是否一致。
- 待确认事项是否没有被静默吞掉。
- 是否保留需求来源或确认依据。

## 资源

- `templates/优化后的需求规格书模板.md`：规格书模板，必须读取并按其结构输出。
- `templates/优化后的需求规格书Word导出说明.md`：Word 模板直出说明；实际导出由 `requirement-document-exporter` 完成。
- `scripts/生成需求编号.py`：扫描文本中的候选功能需求并生成编号建议。
