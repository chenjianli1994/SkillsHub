---
name: requirement-analysis-report
description: Generate a structured Chinese requirements analysis report from an input document, draft PRD, meeting notes, business description, ticket, interface note, or rough product idea. Use when the user provides a file or source material and wants the agent to understand the input, identify requirement problems, classify ambiguity/conflicts/missing information, and output a formatted requirements analysis report before writing the final specification.
---

# Requirement Analysis Report

## 工作目标

把用户输入的原始材料转成可评审的需求分析报告。报告必须说明原文事实、合理推断、待确认假设和需求问题，作为下一阶段生成需求规格书的确认基线。

## 工作流程

1. 读取用户提供的文件或文本。遇到 `.txt`、`.md`、`.docx`、`.pdf` 等文件时，可先运行 `scripts/提取文档文本.py` 提取正文。
2. 识别输入类型：会议纪要、PRD 草稿、业务说明、工单、竞品材料、接口说明、聊天记录或混合材料。
3. 抽取需求元素：业务背景、目标、用户角色、场景、功能点、数据对象、流程、权限、非功能线索、外部依赖。
4. 区分三类信息：原文明确事实、基于原文的推断、需要用户确认的假设。不要把推断写成事实。
5. 诊断需求问题：缺失、模糊、冲突、不可验证、范围不清、流程不完整、角色权限不清、数据口径不清、非功能缺失。
6. 读取 `templates/需求分析报告模板.md`，按模板输出中文 Markdown 报告。
7. 如果信息不足以进入规格书阶段，仍然输出分析报告，并在“规格书生成前置条件”中标记阻塞项。

## 输出规则

- 默认输出中文 Markdown。
- 不在本阶段生成完整需求规格书；只形成分析、问题、建议和确认清单。
- 每条待确认问题都说明“不确认的影响”和“建议默认处理方式”。
- 对用户输入中的原句或事实保持可追踪，优先保留来源段落、文件名、章节名或摘录。
- 对需求优先级使用 `P0/P1/P2/P3`：P0 阻塞规格书正确性，P1 影响核心流程，P2 影响边界或体验，P3 可后置优化。

## 质量门禁

分析报告交付前检查：

- 是否能解释为什么要做、给谁用、解决什么问题。
- 是否提取了核心功能点、数据对象、流程和权限线索。
- 是否列出需求中的缺失、冲突和歧义。
- 是否区分原文事实、推断和假设。
- 是否包含足够明确的待确认问题，供用户确认后进入规格书生成。

## 资源

- `templates/需求分析报告模板.md`：最终报告模板，必须读取并按其结构输出。
- `scripts/提取文档文本.py`：从常见文档格式提取文本，适合在分析前使用。
