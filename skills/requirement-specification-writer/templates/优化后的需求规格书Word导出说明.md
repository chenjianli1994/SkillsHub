# 优化后的需求规格书 Word 导出说明

默认规格书输出为 Markdown。用户明确要求 Word/DOCX 时，不要将 Markdown 转换为 Word，而是按 Word 模板直出：

1. 读取需求分析报告、确认记录和补充说明。
2. 生成 `state/structured/需求规格书Word数据.json`，结构参考 `requirement-document-exporter/templates/需求规格书Word数据模板.json`。
3. 调用 `requirement-document-exporter/scripts/按Word模板生成规格书.py`。
4. 使用 `requirement-document-exporter/templates/需求规格书Word模板_美化版.docx` 作为默认模板。
5. Word 文件应保留模板的封面、目录、页眉页脚、页码、标题层级、列表缩进、表格样式、需求编号和验收标准。
6. Markdown 与 Word 可以同源生成，但 Word 不能由 Markdown 转换得到。

建议命名：

```text
优化后的需求规格书.docx
```
