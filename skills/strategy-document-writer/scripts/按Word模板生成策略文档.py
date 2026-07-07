#!/usr/bin/env python3
"""Generate a strategy document DOCX from structured JSON and a DOCX template.

This is intentionally not a Markdown-to-Word converter. The input is a JSON
document shaped like templates/策略文档Word数据模板.json. The DOCX template is
used as a package seed, while this script writes the professional Word layout,
styles, table format, TOC field, header, footer, page settings, and image
embedding.

Uses only Python's standard library so the skill works without python-docx,
matching the implementation style of requirement-document-exporter.
"""

from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import struct
import sys
# Windows PowerShell 中文输出修复
try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except (AttributeError, OSError):
    pass

import zipfile
from pathlib import Path
from typing import Any


W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
PIC_NS = "http://schemas.openxmlformats.org/drawingml/2006/picture"
WP_NS = "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"

PAGE_WIDTH = 11906
PAGE_HEIGHT = 16838
MARGIN_LEFT = 1587
MARGIN_RIGHT = 1361
MARGIN_TOP = 1181
MARGIN_BOTTOM = 1417
HEADER_DISTANCE = 0
FOOTER_DISTANCE = 964
USABLE_WIDTH = PAGE_WIDTH - MARGIN_LEFT - MARGIN_RIGHT

# 1 cm = 567 dxa (twips); 1 cm = 360000 EMU
DXA_PER_CM = 567
EMU_PER_CM = 360000

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


# === 辅助函数 ===

def text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    if isinstance(value, list):
        return "\n".join(part for part in (text(item).strip() for item in value) if part)
    if isinstance(value, dict):
        return "；".join(f"{key}: {text(val)}" for key, val in value.items())
    result = str(value)
    return result if result.strip() else default


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


# === 表格 ===

def table_widths(headers: list[str], widths_cm: list[float] | None = None) -> list[int]:
    if widths_cm:
        base = [int(w * DXA_PER_CM) for w in widths_cm]
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


def table_cell(value: Any, width: int, *, header: bool = False) -> str:
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


def table_row(cells: list[Any], widths: list[int], *, header: bool = False) -> str:
    tr_pr = "<w:trPr><w:tblHeader/><w:cantSplit/></w:trPr>" if header else ""
    cell_xml = [table_cell(cell, widths[i], header=header) for i, cell in enumerate(cells)]
    return f"<w:tr>{tr_pr}{''.join(cell_xml)}</w:tr>"


def table_block(block: dict[str, Any]) -> str:
    headers = [text(item) for item in block.get("headers", [])]
    rows = block.get("rows", [])
    if not headers:
        return paragraph("")
    widths = table_widths(headers, block.get("column_widths_cm"))
    normalized_rows: list[list[Any]] = []
    for row in rows:
        if isinstance(row, dict):
            normalized_rows.append([row.get(header, "") for header in headers])
        else:
            normalized_rows.append(list(row))
    if not normalized_rows:
        normalized_rows.append(["无"] + [""] * (len(headers) - 1))

    grid = "".join(f'<w:gridCol w:w="{width}"/>' for width in widths)
    xml_rows = [table_row(headers, widths, header=True)]
    xml_rows.extend(table_row(row, widths) for row in normalized_rows)

    title = text(block.get("title"))
    title_xml = paragraph(title, "Caption") if title else ""
    return (
        title_xml
        + "<w:tbl>"
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


# === 封面 ===

def signoff_cell(value: Any, width: int, *, label_cell: bool = False) -> str:
    return (
        "<w:tc>"
        f'<w:tcPr><w:tcW w:w="{width}" w:type="dxa"/><w:vAlign w:val="center"/>'
        '<w:tcMar><w:top w:w="140" w:type="dxa"/><w:left w:w="180" w:type="dxa"/>'
        '<w:bottom w:w="140" w:type="dxa"/><w:right w:w="180" w:type="dxa"/></w:tcMar></w:tcPr>'
        f"{paragraph(value, 'SignoffLabel' if label_cell else 'SignoffText', align='center' if not label_cell else None)}"
        "</w:tc>"
    )


def signoff_table(data: dict[str, Any]) -> str:
    info = data.get("document_info", {})
    approval = data.get("approval_info") or {}
    rows = [
        ("编制:", approval.get("编制") or info.get("编制")),
        ("校核:", approval.get("校核") or info.get("校核")),
        ("会签:", approval.get("会签") or info.get("会签")),
        ("批准:", approval.get("批准") or info.get("批准")),
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


def render_cover(data: dict[str, Any]) -> str:
    info = data.get("document_info", {})
    approval = data.get("approval_info") or {}
    title = compact(info.get("文档标题"), "策略文档")
    subtitle = compact(info.get("文档副标题"), "控制策略")
    version = compact(info.get("版本"), "r01")
    status = compact(info.get("状态"), "待评审")
    organization = compact(approval.get("单位") or info.get("编写单位"), "")
    date = chinese_date(approval.get("日期") or info.get("编写日期") or dt.date.today().isoformat())
    return "".join(
        [
            paragraph("策略文档", "Caption", align="center", spacing_before=180),
            paragraph(title, "CoverTitle", align="center"),
            paragraph(f"{subtitle} / {version} / {status}", "CoverSubtitle", align="center"),
            paragraph("", spacing_after=1500),
            signoff_table(data),
            paragraph("", spacing_after=880),
            paragraph(organization, "CoverOrg", align="center") if organization else "",
            paragraph(date, "CoverDate", align="center") if date else "",
        ]
    )


def render_revision_history(revisions: list[dict[str, Any]]) -> str:
    parts = [paragraph("修订记录", "Heading1")]
    headers = ["NO", "修订内容", "修订人", "版本号", "发布日期"]
    parts.append(table_block({"headers": headers, "rows": revisions or []}))
    return "".join(parts)


# === 目录 ===

def render_toc() -> str:
    parts = [paragraph("目录", "TOCHeading")]
    # TOC 域：Word/WPS 打开后更新域可生成带页码目录
    parts.append(
        "<w:p>"
        "<w:r><w:fldChar w:fldCharType=\"begin\"/></w:r>"
        '<w:r><w:instrText xml:space="preserve">TOC \\o "1-3" \\h \\z \\u</w:instrText></w:r>'
        "<w:r><w:fldChar w:fldCharType=\"separate\"/></w:r>"
        '<w:r><w:t xml:space="preserve">打开 Word/WPS 后更新域，可生成带页码的目录。</w:t></w:r>'
        "<w:r><w:fldChar w:fldCharType=\"end\"/></w:r>"
        "</w:p>"
    )
    return "".join(parts)


# === 图片 ===

def read_image_size(path: Path) -> tuple[int, int]:
    """Return (width_px, height_px) for PNG/JPEG. Fall back to (0, 0)."""
    suffix = path.suffix.lower()
    data = path.read_bytes()
    if suffix == ".png":
        if data[:8] == b"\x89PNG\r\n\x1a\n" and len(data) >= 24:
            width, height = struct.unpack(">II", data[16:24])
            return width, height
    if suffix in (".jpg", ".jpeg"):
        # Scan JPEG markers for SOF0/SOF2 to find dimensions
        i = 2
        while i + 9 <= len(data):
            if data[i] != 0xFF:
                i += 1
                continue
            marker = data[i + 1]
            if marker in (0xC0, 0xC2):
                height, width = struct.unpack(">HH", data[i + 5:i + 9])
                return width, height
            if marker == 0xDA:  # SOS
                break
            if marker in (0xD0, 0xD1, 0xD2, 0xD3, 0xD4, 0xD5, 0xD6, 0xD7, 0xD9):
                i += 2
                continue
            length = struct.unpack(">H", data[i + 2:i + 4])[0]
            i += 2 + length
    return 0, 0


def image_drawing(rel_id: str, width_emu: int, height_emu: int, image_id: int) -> str:
    return (
        '<w:p>'
        '<w:pPr><w:jc w:val="center"/></w:pPr>'
        '<w:r>'
        '<w:drawing>'
        f'<wp:inline distT="0" distB="0" distL="0" distR="0" xmlns:wp="{WP_NS}">'
        f'<wp:extent cx="{width_emu}" cy="{height_emu}"/>'
        f'<wp:docPr id="{image_id}" name="图片 {image_id}"/>'
        f'<a:graphic xmlns:a="{A_NS}">'
        f'<a:graphicData uri="{PIC_NS}">'
        f'<pic:pic xmlns:pic="{PIC_NS}">'
        '<pic:nvPicPr>'
        f'<pic:cNvPr id="{image_id}" name="图片 {image_id}"/>'
        '<pic:cNvPicPr/>'
        '</pic:nvPicPr>'
        '<pic:blipFill>'
        f'<a:blip r:embed="{rel_id}" xmlns:r="{R_NS}"/>'
        '<a:stretch><a:fillRect/></a:stretch>'
        '</pic:blipFill>'
        '<pic:spPr>'
        '<a:xfrm><a:off x="0" y="0"/>'
        f'<a:ext cx="{width_emu}" cy="{height_emu}"/>'
        '</a:xfrm>'
        '<a:prstGeom prst="rect"><a:avLst/></a:prstGeom>'
        '</pic:spPr>'
        '</pic:pic>'
        '</a:graphicData>'
        '</a:graphic>'
        '</wp:inline>'
        '</w:drawing>'
        '</w:r>'
        '</w:p>'
    )


def render_image_block(block: dict[str, Any], media: list[dict[str, Any]]) -> str:
    path_str = text(block.get("path"))
    if not path_str.strip():
        return paragraph("图片路径为空", "Caption")
    path = Path(path_str)
    if not path.exists():
        return paragraph(f"图片未找到：{path}", "Caption")
    width_cm = float(block.get("width_cm", 14))
    width_emu = int(width_cm * EMU_PER_CM)
    px_w, px_h = read_image_size(path)
    if px_w and px_h:
        height_emu = int(width_emu * px_h / px_w)
    else:
        height_emu = int(width_emu * 0.6)  # fallback aspect ratio
    image_id = len(media) + 1
    rel_id = f"rIdImg{image_id}"
    media.append({
        "rel_id": rel_id,
        "path": path,
        "target": f"media/image{image_id}{path.suffix.lower()}",
    })
    caption = text(block.get("caption"))
    caption_xml = paragraph(caption, "Caption", align="center") if caption else ""
    return image_drawing(rel_id, width_emu, height_emu, image_id) + caption_xml


# === Block 渲染 ===

def render_block(block: dict[str, Any], media: list[dict[str, Any]]) -> str:
    block_type = block.get("type")
    if block_type == "heading":
        level = min(max(int(block.get("level", 2)), 1), 3)
        return paragraph(text(block.get("title")), f"Heading{level}")
    if block_type == "paragraph":
        return paragraph(text(block.get("text")), "BodyText")
    if block_type == "note":
        return paragraph(text(block.get("text")), "Caption")
    if block_type == "bullet_list":
        items = block.get("items", [])
        if not items:
            return paragraph("无", "BodyText")
        return "".join(bullet(item) for item in items)
    if block_type == "numbered_list":
        items = block.get("items", [])
        if not items:
            return paragraph("无", "BodyText")
        return "".join(numbered(item) for item in items)
    if block_type == "table":
        return table_block(block)
    if block_type == "image":
        return render_image_block(block, media)
    if block_type == "page_break":
        return page_break()
    return paragraph(text(block), "BodyText")


def render_sections(sections: list[dict[str, Any]], media: list[dict[str, Any]]) -> str:
    parts: list[str] = []
    for index, section in enumerate(sections):
        title = text(section.get("title"), f"第 {index + 1} 节")
        parts.append(paragraph(title, "Heading1"))
        for block in section.get("blocks", []):
            parts.append(render_block(block, media))
    return "".join(parts)


def render_body(data: dict[str, Any], media: list[dict[str, Any]]) -> str:
    parts: list[str] = [render_cover(data), page_break()]
    parts.append(render_revision_history(data.get("revision_history", [])))
    parts.append(page_break())
    parts.append(render_toc())
    parts.append(page_break())
    parts.append(render_sections(data.get("sections", []), media))
    return "".join(parts)


# === OOXML 基础设施 ===

def content_types(image_extensions: set[str]) -> str:
    defaults = [
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>',
        '<Default Extension="xml" ContentType="application/xml"/>',
    ]
    for ext in sorted(image_extensions):
        if ext == "png":
            defaults.append('<Default Extension="png" ContentType="image/png"/>')
        elif ext in ("jpg", "jpeg"):
            defaults.append(f'<Default Extension="{ext}" ContentType="image/jpeg"/>')
        elif ext == "gif":
            defaults.append('<Default Extension="gif" ContentType="image/gif"/>')
        elif ext == "bmp":
            defaults.append('<Default Extension="bmp" ContentType="image/bmp"/>')
        else:
            defaults.append(f'<Default Extension="{ext}" ContentType="application/octet-stream"/>')
    overrides = [
        '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>',
        '<Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>',
        '<Override PartName="/word/numbering.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.numbering+xml"/>',
        '<Override PartName="/word/settings.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.settings+xml"/>',
        '<Override PartName="/word/header1.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.header+xml"/>',
        '<Override PartName="/word/footer1.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.footer+xml"/>',
        '<Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>',
        '<Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>',
    ]
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        + "".join(defaults) + "".join(overrides) +
        '</Types>'
    )


def package_rels() -> str:
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>
<Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>
</Relationships>"""


def document_rels(media: list[dict[str, Any]]) -> str:
    base = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rIdStyles" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
<Relationship Id="rIdNumbering" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/numbering" Target="numbering.xml"/>
<Relationship Id="rIdSettings" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/settings" Target="settings.xml"/>
<Relationship Id="rIdHeader1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/header" Target="header1.xml"/>
<Relationship Id="rIdFooter1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/footer" Target="footer1.xml"/>"""
    image_rels = "".join(
        f'<Relationship Id="{m["rel_id"]}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="{m["target"]}"/>'
        for m in media
    )
    return base + image_rels + "</Relationships>"


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
    title = compact(info.get("文档标题"), "策略文档")
    version = compact(info.get("版本"), "r01")
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
<dc:title>{esc(title)}</dc:title><dc:creator>Strategy DOCX Exporter</dc:creator><cp:lastModifiedBy>Strategy DOCX Exporter</cp:lastModifiedBy><dcterms:created xsi:type="dcterms:W3CDTF">{now}</dcterms:created><dcterms:modified xsi:type="dcterms:W3CDTF">{now}</dcterms:modified>
</cp:coreProperties>"""


def app_props() -> str:
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties" xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes"><Application>Strategy DOCX Exporter</Application></Properties>"""


# === 写入 ===

def write_from_template(template: Path, output: Path, data: dict[str, Any]) -> None:
    if not template.exists():
        raise RuntimeError(f"Word 模板不存在: {template}")
    output.parent.mkdir(parents=True, exist_ok=True)
    title = data.get("document_info", {}).get("文档标题", output.stem)

    media: list[dict[str, Any]] = []
    body = render_body(data, media)
    image_extensions = {m["path"].suffix.lower().lstrip(".") for m in media}

    with zipfile.ZipFile(template, "r") as src, zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as dst:
        for item in src.infolist():
            if item.filename in REWRITE_PARTS:
                continue
            if item.filename.startswith("word/header") or item.filename.startswith("word/footer"):
                continue
            if item.filename.startswith("word/media/"):
                continue
            dst.writestr(item, src.read(item.filename))

        # 写入图片文件
        for m in media:
            dst.writestr(f"word/{m['target']}", m["path"].read_bytes())

        dst.writestr("[Content_Types].xml", content_types(image_extensions))
        dst.writestr("_rels/.rels", package_rels())
        dst.writestr("word/_rels/document.xml.rels", document_rels(media))
        dst.writestr("word/document.xml", document_xml(body))
        dst.writestr("word/styles.xml", styles())
        dst.writestr("word/numbering.xml", numbering())
        dst.writestr("word/settings.xml", settings())
        dst.writestr("word/header1.xml", header_xml(data))
        dst.writestr("word/footer1.xml", footer_xml())
        dst.writestr("docProps/core.xml", core_props(title))
        dst.writestr("docProps/app.xml", app_props())


def main() -> int:
    parser = argparse.ArgumentParser(description="按 Word 模板生成策略文档 DOCX")
    parser.add_argument("input", help="策略文档结构化 JSON 文件")
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
