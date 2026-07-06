---
name: reference-document-profiler
description: Analyze a user-provided reference document and produce a reusable document profile for downstream project-local skills. Use when the user provides a DOCX, Markdown, TXT, or already-extracted text sample document as a structure, content, format, or style reference for generating requirements documents, software design documents, strategy documents, or exports.
---

# Reference Document Profiler

## 工作目标

把用户提供的参考文档解析为“文档画像”，供后续需求、设计、策略、导出等阶段 skill 使用。

本 skill 不直接生成目标业务文档；它只产出参考文档结构、风格、格式和复用边界。

## 目录规则

- 参考文档画像 Markdown 写入 `state/参考文档结构画像.md`。
- 参考文档画像 JSON 写入 `state/reference-document-profile.json`。
- 不要把内部画像 JSON、内部画像 Markdown 或状态文件复制到 `outputs/`。
- 如果用户明确要求把画像作为交付物查看，应另行生成面向评审的 Markdown 文档到 `outputs/`，不要搬运 `state/` 下的内部文件。

## 参考用途

必须先判断参考文档用途：

| 参考用途 | 含义 | 默认复用边界 |
| --- | --- | --- |
| 结构参考 | 只参考章节、表格、编号、栏目组织 | 不复用正文内容 |
| 内容参考 | 允许提炼术语、业务规则、策略逻辑 | 必须标记来源 |
| 格式参考 | 参考 Word 样式、标题层级、表格样式、页眉页脚 | 不复用旧项目正文 |
| 综合参考 | 同时参考结构、内容和格式 | 必须列出禁止复用项 |

如果用户未说明参考用途，默认按“结构参考 + 格式参考”处理，不复用正文业务内容。

## 文档画像内容

文档画像应包含：

- 参考文档路径
- 文档类型
- 参考用途
- 允许复用内容
- 允许复用格式
- 允许复用术语
- 章节结构
- 表格结构
- 编号规则
- 写作风格
- 固定栏目
- 禁止复用项
- 待确认项

默认禁止复用项：

- 项目名称
- 人员姓名
- 客户信息
- 日期
- 历史数据
- 旧项目结论

## 执行流程

1. 读取用户提供的参考文档；脚本支持 Markdown/TXT/DOCX，PDF 需先由外部工具或后续 MCP 提取为文本。
2. 判断文档类型：需求规格书、详细设计、策略文档、测试方案、汇报材料或其他。
3. 提取标题层级和章节顺序。
4. 提取表格表头、字段名称和表格用途。
5. 提取编号规则和固定栏目。
6. 提取写作风格和常用表达。
7. 判断参考用途与复用边界。
8. 生成 Markdown 画像和 JSON 画像到 `state/`。
9. 在画像中列出后续 skill 应遵守的生成约束。

## 下游使用规则

后续阶段 skill 使用本 skill 的输出时：

- 必须读取 `state/reference-document-profile.json`。
- 必须遵守参考用途和禁止复用项。
- 只参考结构时，不得复用原文内容。
- 只参考格式时，不得把旧项目内容带入新文档。
- 内容参考时，必须保留来源说明。

## 自检清单

交付前检查：

- 是否明确参考用途。
- 是否区分结构、内容、格式。
- 是否列出禁止复用项。
- 是否生成 JSON 和 Markdown 两种画像。
- 是否没有把内部画像或 JSON 写入 `outputs/`。

## 资源

- `templates/参考文档画像模板.json`：结构化画像模板。
- `templates/参考文档结构画像模板.md`：Markdown 画像模板。
- `scripts/生成参考文档画像.py`：从 Markdown/TXT/DOCX 初步生成画像。
- `references/参考用途判定规则.md`：参考用途、复用边界和污染防护规则。
