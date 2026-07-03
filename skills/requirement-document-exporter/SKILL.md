---
name: requirement-document-exporter
description: Export generated Chinese requirements documents to DOCX Word files or PDF files on request. Use when the user explicitly asks for a Word/DOCX version generated directly from a dedicated Word template and structured requirements data, asks to convert a Markdown/Word/HTML/TXT requirements document to PDF, or requests multiple output formats. Default workflow output remains Markdown; Word and PDF are generated only when explicitly requested.
---

# Requirement Document Exporter

## 工作目标

在需求分析和需求规格书工作流中提供格式导出能力。默认只输出 Markdown；只有用户明确要求 Word、DOCX 或 PDF 时，才生成对应格式。

## 导出规则

1. 默认交付需求规格书为 `.md`。
2. 用户要求“Word”“docx”“可编辑 Word 版”时，不要把 Markdown 转成 Word；先生成 `templates/需求规格书Word数据模板.json` 形状的结构化数据，再使用 `scripts/按Word模板生成规格书.py` 和 `templates/需求规格书Word模板_美化版.docx` 直接生成 `.docx`。
3. 用户要求“PDF”“转 PDF”“给我 pdf 文件”时，使用 `scripts/文件转pdf.py` 将指定文件导出为 `.pdf`。
4. 如果用户没有指定源文件，优先选择当前工作流最新的需求规格书 Markdown。
5. 如果用户同时要求 Word 和 PDF，Word 按 Word 模板直接生成；PDF 按用户指定源文件生成，未指定时默认从最新规格书 Markdown 生成。
6. 如果转换依赖不可用，输出清晰原因和可继续执行的替代方案，不要伪造已生成文件。

## 支持格式

| 操作 | 输入 | 输出 | 说明 |
| --- | --- | --- | --- |
| Word 模板直出 | 结构化 `.json` | `.docx` | 使用独立 Word 模板直接生成需求规格书 |
| Markdown 转 Word | `.md`、`.txt` | `.docx` | 仅作为辅助工具或旧文档转换，不作为需求规格书 Word 输出路径 |
| Markdown/HTML/TXT 转 PDF | `.md`、`.html`、`.txt` | `.pdf` | 优先使用 Edge/Chrome 无头打印 |
| Word 转 PDF | `.docx` | `.pdf` | 优先使用 LibreOffice；其次尝试 Microsoft Word COM |
| PDF 复制 | `.pdf` | `.pdf` | 源文件已是 PDF 时复制到目标路径 |

## Word 输出要求

- 必须使用 `templates/需求规格书Word模板_美化版.docx` 作为模板。
- 必须让 Agent 先生成 `templates/需求规格书Word数据模板.json` 同形状的数据文件。
- 使用 `scripts/按Word模板生成规格书.py` 将结构化数据填充进 Word 模板。
- 输出必须包含封面、目录、页眉、页脚页码、清晰标题层级、合理段前段后距、列表缩进和可读表格。
- 宽表不要直接横向堆满页面；数据需求、权限需求、非功能需求、依赖、验收、追踪和待确认项优先使用“条目标题 + 两列表格”的可读结构。
- 中文正文默认使用微软雅黑；英文数字使用 Aptos；标题使用加粗蓝色层级样式。
- 目录使用 Word TOC 域，打开 Word/WPS 后更新域即可生成带页码目录。
- 不从 Markdown 转换生成 Word；Word 内容应与需求分析、确认记录和规格书数据同源生成。

## PDF 输出要求

- Markdown/TXT 输入先渲染为临时 HTML，再由浏览器打印为 PDF。
- PDF 页面使用 A4、中文字体、适合评审阅读的字号和表格样式。
- DOCX 输入转 PDF 时，优先调用 LibreOffice；如果不可用，尝试 Windows Microsoft Word COM；两者都不可用时返回失败原因。

## 资源

- `templates/需求规格书Word模板_美化版.docx`：默认 Word 输出样式模板，包含封面、目录、页眉页脚、页码、标题、列表和表格样式。
- `templates/需求规格书Word数据模板.json`：Word 直出时的结构化数据模板。
- `templates/需求规格书Word模板.md`：Word 模板的人类可读结构说明。
- `scripts/按Word模板生成规格书.py`：按 Word 模板和结构化数据生成 DOCX。
- `scripts/markdown转word.py`：辅助转换脚本，不用于需求规格书 Word 直出。
- `scripts/文件转pdf.py`：将 Markdown/TXT/HTML/DOCX/PDF 转为 PDF。
