#!/usr/bin/env python3
"""Generate a polished DOCX requirements specification from structured data.

This is intentionally not a Markdown-to-Word converter. The input is a JSON
document shaped like templates/需求规格书Word数据模板.json. The DOCX template is
used as a package seed, while this script writes the professional Word layout,
styles, table format, TOC field, header, footer, and page settings.
"""

from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import sys
import zipfile
from pathlib import Path
from typing import Any


W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"

PAGE_WIDTH = 11906
PAGE_HEIGHT = 16838
MARGIN_LEFT = 1587
MARGIN_RIGHT = 1361
MARGIN_TOP = 1181
MARGIN_BOTTOM = 1417
HEADER_DISTANCE = 0
FOOTER_DISTANCE = 964
USABLE_WIDTH = PAGE_WIDTH - MARGIN_LEFT - MARGIN_RIGHT

REWRITE_PARTS = {
    "[Content_Types].xml",
    "_rels/.rels",
    "word/document.xml",
    "word/_rels/document.xml.rels",
    "word/styles.xml",
    "word/numbering.xml",
    "word/settings.xml",
    "word/header1.xml",
    "word/footer1.xml",
    "docProps/core.xml",
    "docProps/app.xml",
}

SECTION_TITLES = [
    {"level": 1, "title": "修订记录", "page": "2"},
    {"level": 1, "title": "1. 背景与目标", "page": "4"},
    {"level": 2, "title": "1.1 背景", "page": "4"},
    {"level": 2, "title": "1.2 业务目标", "page": "4"},
    {"level": 2, "title": "1.3 成功标准", "page": "4"},
    {"level": 1, "title": "2. 术语与定义", "page": "5"},
    {"level": 1, "title": "3. 范围", "page": "5"},
    {"level": 2, "title": "3.1 本期范围", "page": "5"},
    {"level": 2, "title": "3.2 不在本期范围", "page": "5"},
    {"level": 2, "title": "3.3 后续可能扩展", "page": "5"},
    {"level": 1, "title": "4. 用户角色与权限", "page": "6"},
    {"level": 1, "title": "5. 业务流程", "page": "6"},
    {"level": 2, "title": "5.1 主流程", "page": "6"},
    {"level": 2, "title": "5.2 异常流程", "page": "6"},
    {"level": 2, "title": "5.3 状态流转", "page": "6"},
    {"level": 1, "title": "6. 功能需求", "page": "7"},
    {"level": 1, "title": "7. 数据需求", "page": "8"},
    {"level": 1, "title": "8. 权限需求", "page": "8"},
    {"level": 1, "title": "9. 非功能需求", "page": "9"},
    {"level": 1, "title": "10. 外部依赖与约束", "page": "9"},
    {"level": 1, "title": "11. 验收标准汇总", "page": "10"},
    {"level": 1, "title": "12. 需求追踪矩阵", "page": "10"},
    {"level": 1, "title": "13. 待后续确认事项", "page": "11"},
]


def text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        return "\n".join(part for part in (text(item).strip() for item in value) if part)
    if isinstance(value, dict):
        return "；".join(f"{key}: {text(val)}" for key, val in value.items())
    return str(value)


def compact(value: Any, fallback: str = "无") -> str:
    value_text = text(value).strip()
    return value_text if value_text else fallback


def chinese_date(value: Any) -> str:
    value_text = compact(value, "")
    if not value_text:
        return ""
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y.%m.%d"):
        try:
            parsed = dt.datetime.strptime(value_text, fmt).date()
            return f"{parsed.year} 年 {parsed.month:02d} 月 {parsed.day:02d} 日"
        except ValueError:
            pass
    return value_text


def esc(value: Any) -> str:
    return html.escape(text(value), quote=False)


def run_text(value: Any, *, bold: bool = False, color: str | None = None, size: int | None = None) -> str:
    rpr = []
    if bold:
        rpr.append("<w:b/>")
    if color:
        rpr.append(f'<w:color w:val="{color}"/>')
    if size:
        rpr.append(f'<w:sz w:val="{size}"/><w:szCs w:val="{size}"/>')
    rpr_xml = f"<w:rPr>{''.join(rpr)}</w:rPr>" if rpr else ""

    pieces: list[str] = []
    lines = esc(value).split("\n")
    for index, line in enumerate(lines):
        if index:
            pieces.append("<w:br/>")
        pieces.append(f'<w:t xml:space="preserve">{line}</w:t>')
    if not pieces:
        pieces.append('<w:t xml:space="preserve"></w:t>')
    return f"<w:r>{rpr_xml}{''.join(pieces)}</w:r>"


def paragraph(
    value: Any = "",
    style: str | None = None,
    *,
    align: str | None = None,
    keep_next: bool = False,
    page_break_before: bool = False,
    num_id: int | None = None,
    ilvl: int = 0,
    indent_left: int | None = None,
    indent_hanging: int | None = None,
    spacing_before: int | None = None,
    spacing_after: int | None = None,
    bold: bool = False,
    color: str | None = None,
    size: int | None = None,
) -> str:
    ppr = []
    if style:
        ppr.append(f'<w:pStyle w:val="{style}"/>')
    if keep_next:
        ppr.append("<w:keepNext/>")
    if page_break_before:
        ppr.append("<w:pageBreakBefore/>")
    if num_id is not None:
        ppr.append(f'<w:numPr><w:ilvl w:val="{ilvl}"/><w:numId w:val="{num_id}"/></w:numPr>')
    if indent_left is not None or indent_hanging is not None:
        attrs = []
        if indent_left is not None:
            attrs.append(f'w:left="{indent_left}"')
        if indent_hanging is not None:
            attrs.append(f'w:hanging="{indent_hanging}"')
        ppr.append(f"<w:ind {' '.join(attrs)}/>")
    if spacing_before is not None or spacing_after is not None:
        attrs = []
        if spacing_before is not None:
            attrs.append(f'w:before="{spacing_before}"')
        if spacing_after is not None:
            attrs.append(f'w:after="{spacing_after}"')
        ppr.append(f"<w:spacing {' '.join(attrs)}/>")
    if align:
        ppr.append(f'<w:jc w:val="{align}"/>')
    ppr_xml = f"<w:pPr>{''.join(ppr)}</w:pPr>" if ppr else ""
    return f"<w:p>{ppr_xml}{run_text(value, bold=bold, color=color, size=size)}</w:p>"


def page_break() -> str:
    return '<w:p><w:r><w:br w:type="page"/></w:r></w:p>'


def bullet(value: Any) -> str:
    return paragraph(compact(value), "ListParagraph", num_id=1, ilvl=0)


def numbered(value: Any) -> str:
    return paragraph(compact(value), "ListParagraph", num_id=2, ilvl=0)


def toc_field() -> str:
    fallback_entries = "".join(
        toc_entry(item["title"], item["page"], int(item["level"]))
        for item in SECTION_TITLES
    )
    return (
        "<w:p>"
        "<w:r><w:fldChar w:fldCharType=\"begin\"/></w:r>"
        '<w:r><w:instrText xml:space="preserve">TOC \\o "1-3" \\h \\z \\u</w:instrText></w:r>'
        "<w:r><w:fldChar w:fldCharType=\"separate\"/></w:r>"
        "</w:p>"
        f"{fallback_entries}"
        "<w:p><w:r><w:fldChar w:fldCharType=\"end\"/></w:r></w:p>"
    )


def toc_entry(title: str, page: str, level: int = 1) -> str:
    style = f"TOC{min(max(level, 1), 3)}"
    return (
        "<w:p>"
        f'<w:pPr><w:pStyle w:val="{style}"/></w:pPr>'
        f"{run_text(title)}"
        "<w:r><w:tab/></w:r>"
        f"{run_text(page)}"
        "</w:p>"
    )


def table_widths(headers: list[str], widths: list[int] | None = None) -> list[int]:
    if widths:
        base = widths
    elif len(headers) == 1:
        base = [USABLE_WIDTH]
    elif len(headers) == 2:
        base = [1900, USABLE_WIDTH - 1900]
    elif len(headers) == 3:
        base = [1900, 5000, USABLE_WIDTH - 6900]
    elif len(headers) == 4:
        base = [1500, 2500, 2800, USABLE_WIDTH - 6800]
    elif len(headers) == 5:
        base = [1500, 1700, 2400, 1800, USABLE_WIDTH - 7400]
    else:
        equal = USABLE_WIDTH // len(headers)
        base = [equal] * len(headers)
        base[-1] = USABLE_WIDTH - sum(base[:-1])

    scale = USABLE_WIDTH / max(sum(base), 1)
    scaled = [max(700, int(round(width * scale))) for width in base]
    scaled[-1] = USABLE_WIDTH - sum(scaled[:-1])
    return scaled


def split_cell_value(value: Any) -> tuple[list[str], bool]:
    if value is None or text(value).strip() == "":
        return ["无"], False
    if isinstance(value, list):
        return [compact(item) for item in value if compact(item, "")], True
    parts = [part.strip() for part in text(value).splitlines() if part.strip()]
    return (parts or ["无"]), False


def table_paragraph(value: str, *, header: bool = False, bullet_item: bool = False) -> str:
    if header:
        return paragraph(value, "TableHeader", align="center")
    if bullet_item:
        return paragraph(
            f"• {value}",
            "TableText",
            indent_left=300,
            indent_hanging=180,
            spacing_after=40,
        )
    return paragraph(value, "TableText")


def table_cell(value: Any, width: int, *, header: bool = False, key_cell: bool = False) -> str:
    fill = "EDEDED" if header else None
    shading = f'<w:shd w:fill="{fill}"/>' if fill else ""
    tc_pr = (
        f'<w:tcPr><w:tcW w:w="{width}" w:type="dxa"/><w:vAlign w:val="top"/>'
        '<w:tcMar><w:top w:w="40" w:type="dxa"/><w:left w:w="108" w:type="dxa"/>'
        '<w:bottom w:w="40" w:type="dxa"/><w:right w:w="108" w:type="dxa"/></w:tcMar>'
        f"{shading}</w:tcPr>"
    )
    values, is_list = split_cell_value(value)
    paras = "".join(table_paragraph(item, header=header, bullet_item=(is_list and not header)) for item in values)
    return f"<w:tc>{tc_pr}{paras}</w:tc>"


def table_row(cells: list[Any], widths: list[int], *, header: bool = False, key_first_cell: bool = False) -> str:
    tr_pr = "<w:trPr><w:tblHeader/><w:cantSplit/></w:trPr>" if header else ""
    cell_xml = []
    for index, cell in enumerate(cells):
        cell_xml.append(table_cell(cell, widths[index], header=header, key_cell=(key_first_cell and index == 0)))
    return f"<w:tr>{tr_pr}{''.join(cell_xml)}</w:tr>"


def table(headers: list[str], rows: list[dict[str, Any]] | list[list[Any]], widths: list[int] | None = None) -> str:
    col_widths = table_widths(headers, widths)
    normalized_rows: list[list[Any]] = []
    for row in rows:
        if isinstance(row, dict):
            normalized_rows.append([row.get(header, "") for header in headers])
        else:
            normalized_rows.append(list(row))
    if not normalized_rows:
        normalized_rows.append(["无"] + [""] * (len(headers) - 1))

    grid = "".join(f'<w:gridCol w:w="{width}"/>' for width in col_widths)
    xml_rows = [table_row(headers, col_widths, header=True)]
    xml_rows.extend(table_row(row, col_widths, key_first_cell=(len(headers) == 2)) for row in normalized_rows)
    return (
        "<w:tbl>"
        '<w:tblPr><w:tblW w:w="5000" w:type="pct"/><w:tblLayout w:type="fixed"/>'
        '<w:tblBorders><w:top w:val="single" w:sz="4" w:space="0" w:color="000000"/>'
        '<w:left w:val="single" w:sz="4" w:space="0" w:color="000000"/>'
        '<w:bottom w:val="single" w:sz="4" w:space="0" w:color="000000"/>'
        '<w:right w:val="single" w:sz="4" w:space="0" w:color="000000"/>'
        '<w:insideH w:val="single" w:sz="4" w:space="0" w:color="000000"/>'
        '<w:insideV w:val="single" w:sz="4" w:space="0" w:color="000000"/></w:tblBorders>'
        '<w:tblCellMar><w:top w:w="40" w:type="dxa"/><w:left w:w="108" w:type="dxa"/>'
        '<w:bottom w:w="40" w:type="dxa"/><w:right w:w="108" w:type="dxa"/></w:tblCellMar>'
        "</w:tblPr>"
        f"<w:tblGrid>{grid}</w:tblGrid>{''.join(xml_rows)}</w:tbl>"
        + paragraph("", spacing_after=80)
    )


def signoff_table(data: dict[str, Any]) -> str:
    info = data.get("document_info", {})
    approval = data.get("approval_info") or data.get("会签评审人员") or {}
    if isinstance(approval, list):
        merged: dict[str, Any] = {}
        for item in approval:
            if isinstance(item, dict):
                label = compact(item.get("角色") or item.get("评审职责"), "")
                name = compact(item.get("姓名") or item.get("签字"), "")
                if label:
                    merged[label] = name
        approval = merged

    rows = [
        ("编制:", approval.get("编制") or approval.get("编制人") or info.get("编制人")),
        ("校核:", approval.get("校核") or approval.get("校核人") or info.get("校核人")),
        ("会签:", approval.get("会签") or approval.get("会签人") or info.get("会签人")),
        ("批准:", approval.get("批准") or approval.get("批准人") or info.get("批准人")),
    ]
    widths = [1350, 2500]
    row_xml = []
    for label, value in rows:
        row_xml.append(
            "<w:tr>"
            f"{signoff_cell(label, widths[0], label_cell=True)}"
            f"{signoff_cell(compact(value, ''), widths[1])}"
            "</w:tr>"
        )
    grid = "".join(f'<w:gridCol w:w="{width}"/>' for width in widths)
    return (
        '<w:tbl><w:tblPr><w:jc w:val="center"/><w:tblW w:w="3850" w:type="dxa"/><w:tblLayout w:type="fixed"/>'
        '<w:tblBorders><w:top w:val="dashed" w:sz="4" w:space="0" w:color="BFBFBF"/>'
        '<w:left w:val="dashed" w:sz="4" w:space="0" w:color="BFBFBF"/>'
        '<w:bottom w:val="dashed" w:sz="4" w:space="0" w:color="BFBFBF"/>'
        '<w:right w:val="dashed" w:sz="4" w:space="0" w:color="BFBFBF"/>'
        '<w:insideH w:val="single" w:sz="4" w:space="0" w:color="000000"/>'
        '<w:insideV w:val="dashed" w:sz="4" w:space="0" w:color="BFBFBF"/></w:tblBorders>'
        '</w:tblPr>'
        f"<w:tblGrid>{grid}</w:tblGrid>{''.join(row_xml)}</w:tbl>"
    )


def signoff_cell(value: Any, width: int, *, label_cell: bool = False) -> str:
    return (
        "<w:tc>"
        f'<w:tcPr><w:tcW w:w="{width}" w:type="dxa"/><w:vAlign w:val="center"/>'
        '<w:tcMar><w:top w:w="140" w:type="dxa"/><w:left w:w="180" w:type="dxa"/>'
        '<w:bottom w:w="140" w:type="dxa"/><w:right w:w="180" w:type="dxa"/></w:tcMar></w:tcPr>'
        f"{paragraph(value, 'SignoffLabel' if label_cell else 'SignoffText', align='center' if not label_cell else None)}"
        "</w:tc>"
    )


def kv_table(data: dict[str, Any]) -> str:
    rows = [{"项目": key, "内容": value} for key, value in data.items()]
    return table(["项目", "内容"], rows, [1800, USABLE_WIDTH - 1800])


def list_section(title: str, values: Any, *, ordered: bool = False) -> str:
    parts = [paragraph(title, "Heading3")]
    value_list = values if isinstance(values, list) else [values] if text(values).strip() else []
    if not value_list:
        parts.append(paragraph("无", "BodyText"))
    else:
        parts.extend((numbered(item) if ordered else bullet(item)) for item in value_list)
    return "".join(parts)


def item_heading(item: dict[str, Any], title_keys: list[str]) -> str:
    parts = [compact(item.get(key), "") for key in title_keys]
    label = " ".join(part for part in parts if part).strip()
    return label or compact(item.get("编号"), "未编号条目")


def detail_collection(
    title: str,
    items: list[dict[str, Any]],
    title_keys: list[str],
    fields: list[str],
    *,
    heading_style: str = "RequirementTitle",
) -> str:
    parts = [paragraph(title, "Heading2")]
    if not items:
        parts.append(paragraph("无", "BodyText"))
        return "".join(parts)
    for item in items:
        parts.append(paragraph(item_heading(item, title_keys), heading_style))
        rows = [{"项目": field, "内容": item.get(field, "")} for field in fields]
        parts.append(table(["项目", "内容"], rows, [1700, USABLE_WIDTH - 1700]))
    return "".join(parts)


def render_cover(data: dict[str, Any]) -> str:
    info = data.get("document_info", {})
    approval = data.get("approval_info") if isinstance(data.get("approval_info"), dict) else {}
    title = compact(info.get("需求名称"), "需求规格书")
    version = compact(info.get("版本"), "v1.0")
    organization = compact(approval.get("单位") or info.get("编写单位"), "")
    date = chinese_date(approval.get("日期") or info.get("编写日期") or dt.date.today().isoformat())
    return "".join(
        [
            paragraph(f"{title} {version}".strip(), "CoverTitle", align="center", spacing_before=180),
            paragraph("需求规格书", "CoverSubtitle", align="center"),
            paragraph("", spacing_after=1500),
            signoff_table(data),
            paragraph("", spacing_after=880),
            paragraph(organization, "CoverOrg", align="center") if organization else "",
            paragraph(date, "CoverDate", align="center") if date else "",
        ]
    )


def render_toc() -> str:
    parts = [paragraph("目录", "TOCHeading")]
    parts.append(toc_field())
    return "".join(parts)


def render_functional_requirements(items: list[dict[str, Any]]) -> str:
    fields = ["目标", "触发条件", "前置条件", "参与角色", "处理规则", "输入", "输出", "异常场景", "验收标准", "来源/确认依据", "备注"]
    return detail_collection("6. 功能需求", items, ["编号", "名称"], fields, heading_style="Heading3")


def render_body(data: dict[str, Any]) -> str:
    parts: list[str] = [render_cover(data), page_break()]

    parts.append(paragraph("修订记录", "Heading1"))
    parts.append(table(["版本", "日期", "修订内容", "修订人"], data.get("revision_history", [])))
    parts.append(page_break())
    parts.append(render_toc())
    parts.append(page_break())

    background = data.get("background", {})
    parts.append(paragraph("1. 背景与目标", "Heading1"))
    parts.append(list_section("1.1 背景", background.get("背景", [])))
    parts.append(list_section("1.2 业务目标", background.get("业务目标", [])))
    parts.append(list_section("1.3 成功标准", background.get("成功标准", [])))

    parts.append(paragraph("2. 术语与定义", "Heading1"))
    parts.append(table(["术语", "定义", "备注"], data.get("terms", [])))

    scope = data.get("scope", {})
    parts.append(paragraph("3. 范围", "Heading1"))
    parts.append(list_section("3.1 本期范围", scope.get("本期范围", [])))
    parts.append(list_section("3.2 不在本期范围", scope.get("不在本期范围", [])))
    parts.append(list_section("3.3 后续可能扩展", scope.get("后续可能扩展", [])))

    parts.append(paragraph("4. 用户角色与权限", "Heading1"))
    parts.append(table(["角色", "角色说明", "可执行操作", "数据可见范围"], data.get("roles", [])))

    flows = data.get("flows", {})
    parts.append(paragraph("5. 业务流程", "Heading1"))
    parts.append(list_section("5.1 主流程", flows.get("主流程", []), ordered=True))
    parts.append(list_section("5.2 异常流程", flows.get("异常流程", [])))
    parts.append(paragraph("5.3 状态流转", "Heading3"))
    parts.append(table(["状态", "进入条件", "可执行动作", "退出条件"], flows.get("状态流转", [])))

    parts.append(render_functional_requirements(data.get("functional_requirements", [])))

    parts.append(
        detail_collection(
            "7. 数据需求",
            data.get("data_requirements", []),
            ["编号", "数据对象"],
            ["字段/口径", "来源", "更新规则", "保留/归档", "验收标准"],
        )
    )
    parts.append(
        detail_collection(
            "8. 权限需求",
            data.get("permission_requirements", []),
            ["编号", "角色", "操作"],
            ["条件", "限制", "审计要求"],
        )
    )
    parts.append(
        detail_collection(
            "9. 非功能需求",
            data.get("non_functional_requirements", []),
            ["编号", "类型"],
            ["要求", "验收方式"],
        )
    )
    parts.append(
        detail_collection(
            "10. 外部依赖与约束",
            data.get("dependencies", []),
            ["依赖/约束", "类型"],
            ["影响", "负责人/系统", "处理方案"],
        )
    )
    parts.append(
        detail_collection(
            "11. 验收标准汇总",
            data.get("acceptance_criteria", []),
            ["编号", "验收项"],
            ["验收方法", "通过标准"],
        )
    )
    parts.append(
        detail_collection(
            "12. 需求追踪矩阵",
            data.get("traceability", []),
            ["规格书编号"],
            ["来源编号/原文依据", "确认记录", "状态"],
        )
    )
    parts.append(
        detail_collection(
            "13. 待后续确认事项",
            data.get("open_questions", []),
            ["编号", "问题"],
            ["当前假设", "影响范围", "需要谁确认"],
        )
    )
    return "".join(parts)


def content_types() -> str:
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
<Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
<Override PartName="/word/numbering.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.numbering+xml"/>
<Override PartName="/word/settings.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.settings+xml"/>
<Override PartName="/word/header1.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.header+xml"/>
<Override PartName="/word/footer1.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.footer+xml"/>
<Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>
<Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>
</Types>"""


def package_rels() -> str:
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>
<Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>
</Relationships>"""


def document_rels() -> str:
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rIdStyles" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
<Relationship Id="rIdNumbering" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/numbering" Target="numbering.xml"/>
<Relationship Id="rIdSettings" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/settings" Target="settings.xml"/>
<Relationship Id="rIdHeader1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/header" Target="header1.xml"/>
<Relationship Id="rIdFooter1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/footer" Target="footer1.xml"/>
</Relationships>"""


def styles() -> str:
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
<w:docDefaults>
<w:rPrDefault><w:rPr><w:rFonts w:ascii="Times New Roman" w:eastAsia="宋体" w:hAnsi="Times New Roman"/><w:sz w:val="21"/><w:szCs w:val="21"/><w:color w:val="000000"/></w:rPr></w:rPrDefault>
<w:pPrDefault><w:pPr><w:spacing w:after="0" w:line="360" w:lineRule="auto"/></w:pPr></w:pPrDefault>
</w:docDefaults>
<w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/><w:qFormat/><w:pPr><w:spacing w:after="0" w:line="360" w:lineRule="auto"/></w:pPr><w:rPr><w:rFonts w:ascii="Times New Roman" w:eastAsia="宋体" w:hAnsi="Times New Roman"/><w:sz w:val="21"/><w:szCs w:val="21"/><w:color w:val="000000"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="BodyText"><w:name w:val="Body Text"/><w:basedOn w:val="Normal"/><w:pPr><w:spacing w:after="0" w:line="360" w:lineRule="auto"/></w:pPr></w:style>
<w:style w:type="paragraph" w:styleId="CoverTitle"><w:name w:val="Cover Title"/><w:basedOn w:val="Normal"/><w:pPr><w:spacing w:before="80" w:after="100"/></w:pPr><w:rPr><w:b/><w:color w:val="000000"/><w:sz w:val="44"/><w:szCs w:val="44"/><w:rFonts w:ascii="Times New Roman" w:eastAsia="宋体" w:hAnsi="Times New Roman"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="CoverSubtitle"><w:name w:val="Cover Subtitle"/><w:basedOn w:val="Normal"/><w:pPr><w:spacing w:after="280"/></w:pPr><w:rPr><w:b/><w:color w:val="000000"/><w:sz w:val="40"/><w:szCs w:val="40"/><w:rFonts w:ascii="Times New Roman" w:eastAsia="宋体" w:hAnsi="Times New Roman"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="CoverOrg"><w:name w:val="Cover Organization"/><w:basedOn w:val="Normal"/><w:pPr><w:spacing w:before="160" w:after="80"/></w:pPr><w:rPr><w:color w:val="000000"/><w:sz w:val="36"/><w:szCs w:val="36"/><w:rFonts w:ascii="Times New Roman" w:eastAsia="宋体" w:hAnsi="Times New Roman"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="CoverDate"><w:name w:val="Cover Date"/><w:basedOn w:val="Normal"/><w:pPr><w:spacing w:after="80"/></w:pPr><w:rPr><w:color w:val="000000"/><w:sz w:val="36"/><w:szCs w:val="36"/><w:rFonts w:ascii="Times New Roman" w:eastAsia="宋体" w:hAnsi="Times New Roman"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="SignoffLabel"><w:name w:val="Signoff Label"/><w:basedOn w:val="Normal"/><w:pPr><w:spacing w:after="0" w:line="360" w:lineRule="auto"/></w:pPr><w:rPr><w:b/><w:color w:val="000000"/><w:sz w:val="28"/><w:szCs w:val="28"/><w:rFonts w:ascii="Times New Roman" w:eastAsia="宋体" w:hAnsi="Times New Roman"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="SignoffText"><w:name w:val="Signoff Text"/><w:basedOn w:val="Normal"/><w:pPr><w:spacing w:after="0" w:line="360" w:lineRule="auto"/></w:pPr><w:rPr><w:color w:val="000000"/><w:sz w:val="28"/><w:szCs w:val="28"/><w:rFonts w:ascii="Times New Roman" w:eastAsia="宋体" w:hAnsi="Times New Roman"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="TOCHeading"><w:name w:val="TOC Heading"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:qFormat/><w:pPr><w:spacing w:before="120" w:after="160"/></w:pPr><w:rPr><w:color w:val="0070C0"/><w:sz w:val="36"/><w:szCs w:val="36"/><w:rFonts w:ascii="Times New Roman" w:eastAsia="宋体" w:hAnsi="Times New Roman"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="TOC1"><w:name w:val="toc 1"/><w:basedOn w:val="Normal"/><w:pPr><w:spacing w:after="0" w:line="300" w:lineRule="auto"/><w:tabs><w:tab w:val="right" w:leader="dot" w:pos="9300"/></w:tabs></w:pPr><w:rPr><w:sz w:val="21"/><w:szCs w:val="21"/><w:rFonts w:ascii="Times New Roman" w:eastAsia="宋体" w:hAnsi="Times New Roman"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="TOC2"><w:name w:val="toc 2"/><w:basedOn w:val="TOC1"/><w:pPr><w:ind w:left="420"/><w:spacing w:after="0" w:line="300" w:lineRule="auto"/><w:tabs><w:tab w:val="right" w:leader="dot" w:pos="9300"/></w:tabs></w:pPr></w:style>
<w:style w:type="paragraph" w:styleId="TOC3"><w:name w:val="toc 3"/><w:basedOn w:val="TOC1"/><w:pPr><w:ind w:left="840"/><w:spacing w:after="0" w:line="300" w:lineRule="auto"/><w:tabs><w:tab w:val="right" w:leader="dot" w:pos="9300"/></w:tabs></w:pPr></w:style>
<w:style w:type="paragraph" w:styleId="Heading1"><w:name w:val="heading 1"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:qFormat/><w:pPr><w:keepNext/><w:spacing w:before="340" w:after="330" w:line="578" w:lineRule="auto"/><w:outlineLvl w:val="0"/></w:pPr><w:rPr><w:b/><w:color w:val="000000"/><w:sz w:val="44"/><w:szCs w:val="44"/><w:rFonts w:ascii="Times New Roman" w:eastAsia="黑体" w:hAnsi="Times New Roman"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="Heading2"><w:name w:val="heading 2"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:qFormat/><w:pPr><w:keepNext/><w:keepLines/><w:spacing w:before="260" w:after="260" w:line="416" w:lineRule="auto"/><w:outlineLvl w:val="1"/></w:pPr><w:rPr><w:b/><w:color w:val="000000"/><w:sz w:val="32"/><w:szCs w:val="32"/><w:rFonts w:ascii="Times New Roman" w:eastAsia="黑体" w:hAnsi="Times New Roman"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="Heading3"><w:name w:val="heading 3"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:qFormat/><w:pPr><w:keepNext/><w:spacing w:before="120" w:after="120" w:line="360" w:lineRule="auto"/><w:outlineLvl w:val="2"/></w:pPr><w:rPr><w:b/><w:color w:val="000000"/><w:sz w:val="24"/><w:szCs w:val="24"/><w:rFonts w:ascii="Times New Roman" w:eastAsia="宋体" w:hAnsi="Times New Roman"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="RequirementTitle"><w:name w:val="Requirement Title"/><w:basedOn w:val="Normal"/><w:pPr><w:keepNext/><w:spacing w:before="120" w:after="80" w:line="360" w:lineRule="auto"/></w:pPr><w:rPr><w:b/><w:color w:val="000000"/><w:sz w:val="24"/><w:szCs w:val="24"/><w:rFonts w:ascii="Times New Roman" w:eastAsia="宋体" w:hAnsi="Times New Roman"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="ListParagraph"><w:name w:val="List Paragraph"/><w:basedOn w:val="Normal"/><w:pPr><w:ind w:left="720" w:hanging="360"/><w:spacing w:after="80" w:line="360" w:lineRule="auto"/></w:pPr></w:style>
<w:style w:type="paragraph" w:styleId="TableText"><w:name w:val="Table Text"/><w:basedOn w:val="Normal"/><w:pPr><w:spacing w:after="0" w:line="300" w:lineRule="auto"/></w:pPr><w:rPr><w:sz w:val="20"/><w:szCs w:val="20"/><w:rFonts w:ascii="Times New Roman" w:eastAsia="宋体" w:hAnsi="Times New Roman"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="TableHeader"><w:name w:val="Table Header"/><w:basedOn w:val="TableText"/><w:rPr><w:b/><w:color w:val="000000"/><w:sz w:val="20"/><w:szCs w:val="20"/><w:rFonts w:ascii="Times New Roman" w:eastAsia="宋体" w:hAnsi="Times New Roman"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="HeaderFooter"><w:name w:val="Header Footer"/><w:basedOn w:val="Normal"/><w:pPr><w:spacing w:after="0"/></w:pPr><w:rPr><w:color w:val="000000"/><w:sz w:val="18"/><w:szCs w:val="18"/><w:rFonts w:ascii="Times New Roman" w:eastAsia="宋体" w:hAnsi="Times New Roman"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="Caption"><w:name w:val="Caption"/><w:basedOn w:val="Normal"/><w:pPr><w:spacing w:before="80" w:after="80"/></w:pPr><w:rPr><w:color w:val="666666"/><w:sz w:val="18"/><w:szCs w:val="18"/><w:rFonts w:ascii="Times New Roman" w:eastAsia="宋体" w:hAnsi="Times New Roman"/></w:rPr></w:style>
</w:styles>"""


def numbering() -> str:
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:numbering xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
<w:abstractNum w:abstractNumId="1"><w:multiLevelType w:val="singleLevel"/><w:lvl w:ilvl="0"><w:start w:val="1"/><w:numFmt w:val="bullet"/><w:lvlText w:val="•"/><w:lvlJc w:val="left"/><w:pPr><w:ind w:left="720" w:hanging="360"/></w:pPr><w:rPr><w:rFonts w:ascii="Symbol" w:hAnsi="Symbol" w:hint="default"/></w:rPr></w:lvl></w:abstractNum>
<w:abstractNum w:abstractNumId="2"><w:multiLevelType w:val="singleLevel"/><w:lvl w:ilvl="0"><w:start w:val="1"/><w:numFmt w:val="decimal"/><w:lvlText w:val="%1."/><w:lvlJc w:val="left"/><w:pPr><w:ind w:left="720" w:hanging="360"/></w:pPr></w:lvl></w:abstractNum>
<w:num w:numId="1"><w:abstractNumId w:val="1"/></w:num>
<w:num w:numId="2"><w:abstractNumId w:val="2"/></w:num>
</w:numbering>"""


def settings() -> str:
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:settings xmlns:w="{W_NS}"><w:updateFields w:val="true"/></w:settings>"""


def header_xml(data: dict[str, Any]) -> str:
    info = data.get("document_info", {})
    title = compact(info.get("需求名称"), "需求规格书")
    version = compact(info.get("版本"), "v1.0")
    status = compact(info.get("状态"), "待评审")
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:hdr xmlns:w="{W_NS}" xmlns:r="{R_NS}">
<w:p>
<w:pPr>
<w:pStyle w:val="HeaderFooter"/>
<w:jc w:val="center"/>
<w:pBdr><w:bottom w:val="single" w:sz="6" w:space="1" w:color="000000"/></w:pBdr>
</w:pPr>
{run_text(f"{title}    {version}    {status}", size=18)}
</w:p>
</w:hdr>"""


def footer_xml() -> str:
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:ftr xmlns:w="{W_NS}" xmlns:r="{R_NS}">
<w:p><w:pPr><w:pStyle w:val="HeaderFooter"/><w:jc w:val="center"/></w:pPr>
<w:r><w:t xml:space="preserve">第 </w:t></w:r>
<w:r><w:fldChar w:fldCharType="begin"/></w:r><w:r><w:instrText xml:space="preserve">PAGE</w:instrText></w:r><w:r><w:fldChar w:fldCharType="end"/></w:r>
<w:r><w:t xml:space="preserve"> / </w:t></w:r>
<w:r><w:fldChar w:fldCharType="begin"/></w:r><w:r><w:instrText xml:space="preserve">NUMPAGES</w:instrText></w:r><w:r><w:fldChar w:fldCharType="end"/></w:r>
<w:r><w:t xml:space="preserve"> 页</w:t></w:r>
</w:p>
</w:ftr>"""


def document_xml(body: str) -> str:
    sect_pr = (
        '<w:sectPr><w:headerReference w:type="default" r:id="rIdHeader1"/>'
        '<w:footerReference w:type="default" r:id="rIdFooter1"/>'
        f'<w:pgSz w:w="{PAGE_WIDTH}" w:h="{PAGE_HEIGHT}"/>'
        f'<w:pgMar w:top="{MARGIN_TOP}" w:right="{MARGIN_RIGHT}" w:bottom="{MARGIN_BOTTOM}" '
        f'w:left="{MARGIN_LEFT}" w:header="{HEADER_DISTANCE}" w:footer="{FOOTER_DISTANCE}" w:gutter="0"/>'
        '<w:cols w:space="720"/></w:sectPr>'
    )
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="{W_NS}" xmlns:r="{R_NS}">
<w:body>{body}{sect_pr}</w:body>
</w:document>"""


def core_props(title: str) -> str:
    now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
<dc:title>{esc(title)}</dc:title><dc:creator>Codex</dc:creator><cp:lastModifiedBy>Codex</cp:lastModifiedBy><dcterms:created xsi:type="dcterms:W3CDTF">{now}</dcterms:created><dcterms:modified xsi:type="dcterms:W3CDTF">{now}</dcterms:modified>
</cp:coreProperties>"""


def app_props() -> str:
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties" xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes"><Application>Codex Requirement DOCX Exporter</Application></Properties>"""


def write_from_template(template: Path, output: Path, data: dict[str, Any]) -> None:
    if not template.exists():
        raise RuntimeError(f"Word 模板不存在: {template}")
    output.parent.mkdir(parents=True, exist_ok=True)
    title = data.get("document_info", {}).get("需求名称", output.stem)
    body = render_body(data)

    with zipfile.ZipFile(template, "r") as src, zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as dst:
        for item in src.infolist():
            if item.filename in REWRITE_PARTS:
                continue
            if item.filename.startswith("word/header") or item.filename.startswith("word/footer"):
                continue
            dst.writestr(item, src.read(item.filename))

        dst.writestr("[Content_Types].xml", content_types())
        dst.writestr("_rels/.rels", package_rels())
        dst.writestr("word/_rels/document.xml.rels", document_rels())
        dst.writestr("word/document.xml", document_xml(body))
        dst.writestr("word/styles.xml", styles())
        dst.writestr("word/numbering.xml", numbering())
        dst.writestr("word/settings.xml", settings())
        dst.writestr("word/header1.xml", header_xml(data))
        dst.writestr("word/footer1.xml", footer_xml())
        dst.writestr("docProps/core.xml", core_props(title))
        dst.writestr("docProps/app.xml", app_props())


def main() -> int:
    parser = argparse.ArgumentParser(description="按 Word 模板生成需求规格书 DOCX")
    parser.add_argument("input", help="需求规格书结构化 JSON 文件")
    parser.add_argument("-t", "--template", required=True, help="Word 模板 DOCX 文件")
    parser.add_argument("-o", "--output", required=True, help="输出 DOCX 文件")
    args = parser.parse_args()

    try:
        data = json.loads(Path(args.input).read_text(encoding="utf-8-sig"))
        write_from_template(Path(args.template), Path(args.output), data)
    except Exception as exc:  # noqa: BLE001
        print(f"生成 Word 失败: {exc}", file=sys.stderr)
        return 2
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
