---
name: requirement-workflow-orchestrator
description: "Orchestrate an end-to-end Chinese requirements engineering workflow across multiple turns: analyze an input requirement file, generate a requirements analysis report, actively request user confirmation for open questions, wait for and merge confirmation answers, generate an optimized Markdown requirements specification by default, optionally generate Word/DOCX directly from a dedicated Word template and structured data or export PDF only when requested, run a quality gate, and revise the specification from user feedback. Use when the user wants a complete workflow rather than a single document generation task."
---

# Requirement Workflow Orchestrator

## 工作目标

把“输入需求文件 -> 需求分析 -> 用户确认 -> 优化规格书 -> 质量检查 -> 反馈修订”组织成一个可跨多轮对话执行的完整工作流。

## 工作流状态

每次进入本 skill 时先判断当前阶段，并维护一份状态记录。可复制 `templates/工作流状态记录模板.md` 到输出目录作为状态文件。

| 阶段 | 触发条件 | 当前动作 | 完成条件 |
| --- | --- | --- | --- |
| S1 输入接收 | 用户提供原始需求文件或文本 | 读取输入，调用需求分析报告能力 | 生成需求分析报告 |
| S2 确认门 | 分析报告包含待确认问题 | 主动输出确认清单，等待用户确认 | P0/P1 问题已确认或被明确标记为假设 |
| S3 规格书生成 | 用户确认分析结果或补充确认答案 | 调用需求规格书生成能力 | 生成优化后的需求规格书和结构化规格书 JSON |
| S4 质量门禁 | 规格书已生成 | 调用需求质量门禁能力 | 输出通过/有条件通过/不通过结论 |
| S5 反馈修订 | 用户对规格书提出修改意见 | 分类反馈并修改规格书 | 输出修订版、变更摘要和剩余问题 |
| S6 格式导出 | 用户明确要求 Word/DOCX/PDF | 调用文档导出能力 | 输出指定格式文件 |

## 执行规则

1. 不要在输入阶段询问可自行判断的问题；先完成分析报告。
2. 分析报告生成后，必须主动列出待确认项，并要求用户逐条确认或批量确认。
3. 未确认的 P0/P1 项不能静默写成事实；只能写成“待确认”或“当前假设”。
4. 用户确认结果要沉淀为确认记录，作为规格书的来源依据。
5. 规格书生成后必须做质量门禁；发现阻塞问题时先修订，再输出最终版本。
6. 用户后续反馈修改文档时，先判断反馈类型，再更新规格书，并追加修订记录。
7. 默认输出 Markdown 格式的需求规格书，并同步生成 `state/structured/requirement-specification.json`；只有用户明确要求 Word、DOCX 或 PDF 时才导出其他格式。

## 调用子 skill 的方式

- S1 使用 `requirement-analysis-report`：读取输入文件，输出需求分析报告。
- S2 使用本 skill 的 `templates/确认清单模板.md` 和 `scripts/提取确认问题.py`：从分析报告提取待确认问题。
- S3 使用 `requirement-specification-writer`：基于分析报告和确认结果生成规格书。
- S4 使用 `requirement-quality-gate`：检查分析报告或规格书质量。
- S5 继续使用 `requirement-specification-writer` 和 `requirement-quality-gate`：完成修订和复检。
- S6 使用 `requirement-document-exporter`：按用户明确要求导出 Word/DOCX 或 PDF。

## 确认门规则

生成确认清单时按优先级分组：

- `必须确认`：P0/P1，影响需求正确性、范围、控制优先级、安全、接口、验收。
- `建议确认`：P2，影响边界、体验、可测试性。
- `可带假设推进`：P3，影响较小，可在规格书中标注假设。

如果用户只说“确认”但没有逐项回答，按以下规则处理：

- 对没有争议且风险低的 P2/P3，记录为“按分析报告建议默认处理”。
- 对 P0/P1，继续要求用户补充，不直接生成最终规格书。
- 如果用户明确说“全部按建议默认处理”，可以进入规格书阶段，但必须在规格书“待后续确认事项”中保留所有默认假设。

## 反馈修订规则

用户反馈规格书后，先分类：

| 反馈类型 | 处理方式 |
| --- | --- |
| 事实纠正 | 修改对应章节，并更新追踪矩阵或确认依据 |
| 新增需求 | 新增 FR/NFR/DR/PR 编号，补充验收标准 |
| 删除需求 | 删除或移入范围外，并记录原因 |
| 表述优化 | 改写文字，不改变需求含义 |
| 术语统一 | 更新术语表和全文引用 |
| 质量问题 | 修订后再次运行质量门禁 |

## 输出文件建议

默认在用户可见输出目录生成以下文件：

- `需求分析报告.md`
- `需求确认清单.md`
- `需求确认记录.md`
- `优化后的需求规格书.md`
- `state/structured/requirement-specification.json`
- `需求质量检查报告.md`
- `需求规格书修订记录.md`
- 可选：`优化后的需求规格书.docx`，仅在用户要求 Word/DOCX 时生成。
- 可选：`优化后的需求规格书.pdf`，仅在用户要求 PDF 时生成。

## 资源

- `templates/工作流状态记录模板.md`：跨轮工作流状态记录。
- `templates/确认清单模板.md`：用户确认问题的输出模板。
- `templates/反馈修订记录模板.md`：用户反馈和文档修订记录模板。
- `scripts/提取确认问题.py`：从需求分析报告提取 `Q-xxx` 待确认问题。

## 格式导出规则

- 用户没有指定格式时，最终规格书输出 Markdown，并同步生成内部结构化 JSON。
- 用户说“同时给 Word”“输出 docx”“我要 Word 版”时，生成 `state/structured/需求规格书Word数据.json`，并调用 `requirement-document-exporter` 按 Word 模板直出 `.docx`；不要把 Markdown 转为 Word。
- 用户说“转 PDF”“给我 PDF”“输出 pdf 文件”时，调用 `requirement-document-exporter` 将用户指定文件或当前最新规格书转换为 `.pdf`。
- 用户要求 Word 和 PDF 时，Word 按模板直出；PDF 默认从 Markdown 生成，除非用户明确要求从 Word 文件转 PDF。
