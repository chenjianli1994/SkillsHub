# 策略文档 Word 模板

> 本文件描述策略文档 Word 直出的结构。实际 `.docx` 输出必须由 `scripts/按Word模板生成策略文档.py` 读取结构化 JSON 后直接生成，不从 Markdown 转换。

## 版式来源

- 首页审批信息、修订记录、目录：参考需求规格书模板
- 正文章节骨架、表格类型：参考现有策略文档样本

## 首页结构

封面包含：

- 文档类别：`策略文档`
- 文档标题
- 文档副标题（通常为“控制策略”）
- 版本 / 状态
- 审批信息表：`编制 / 校核 / 会签 / 批准`
- 编写单位
- 日期

## 固定前置章节

1. 修订记录
2. 目录

## 正文组织方式

正文由 `sections` 驱动。每个 section 是一级节，内部使用 `blocks` 描述内容。

支持的 block 类型：

- `heading`
- `paragraph`
- `bullet_list`
- `numbered_list`
- `table`
- `image`
- `note`
- `page_break`

## Heading 规则

- 一级节：Word `Heading 1`
- 二级节：Word `Heading 2`
- 三级节：Word `Heading 3`

标题文本建议直接包含编号，例如：

- `1 概述`
- `1.1 需求描述`
- `3.3.2 延时开启阶段`

## Table 规则

表格数据结构：

```json
{
  "type": "table",
  "title": "可选表题",
  "headers": ["列1", "列2"],
  "rows": [
    ["值1", "值2"],
    ["值3", "值4"]
  ],
  "column_widths_cm": [3.0, 12.0]
}
```

字段说明：

- `title` 可省略
- `column_widths_cm` 可省略；省略时按列数自动均分

## Image 规则

图片块结构：

```json
{
  "type": "image",
  "path": "C:/abs/path/to/image.png",
  "width_cm": 14,
  "caption": "图 1 软件流程图"
}
```

若图片路径不存在，脚本会跳过该图片并保留说明性注释。
