#!/usr/bin/env python3
"""Extract plain text from common requirement source files."""

from __future__ import annotations

import argparse
import sys
# Windows PowerShell 中文输出修复
try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except (AttributeError, OSError):
    pass

import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET


TEXT_EXTENSIONS = {".txt", ".md", ".csv", ".json", ".yaml", ".yml", ".log"}


def read_text_file(path: Path) -> str:
    for encoding in ("utf-8-sig", "utf-8", "gb18030"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    raise RuntimeError(f"无法识别文本编码: {path}")


def extract_docx(path: Path) -> str:
    w_ns = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
    paragraphs: list[str] = []
    with zipfile.ZipFile(path) as docx:
        xml = docx.read("word/document.xml")
    root = ET.fromstring(xml)
    for paragraph in root.iter(f"{w_ns}p"):
        parts: list[str] = []
        for node in paragraph.iter():
            if node.tag == f"{w_ns}t" and node.text:
                parts.append(node.text)
            elif node.tag == f"{w_ns}tab":
                parts.append("\t")
            elif node.tag == f"{w_ns}br":
                parts.append("\n")
        text = "".join(parts).strip()
        if text:
            paragraphs.append(text)
    return "\n\n".join(paragraphs)


def extract_pdf(path: Path) -> str:
    try:
        from pypdf import PdfReader  # type: ignore
    except ImportError as exc:
        raise RuntimeError("提取 PDF 需要安装 pypdf；可改用系统工具或先转成文本。") from exc

    reader = PdfReader(str(path))
    pages = []
    for index, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        pages.append(f"\n\n--- 第 {index} 页 ---\n\n{text.strip()}")
    return "".join(pages).strip()


def extract(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in TEXT_EXTENSIONS:
        return read_text_file(path)
    if suffix == ".docx":
        return extract_docx(path)
    if suffix == ".pdf":
        return extract_pdf(path)
    raise RuntimeError(f"暂不支持的文件类型: {suffix}")


def main() -> int:
    parser = argparse.ArgumentParser(description="从常见需求文档中提取文本")
    parser.add_argument("input", help="输入文件路径")
    parser.add_argument("-o", "--output", help="输出文本文件路径；省略时写到 stdout")
    args = parser.parse_args()

    path = Path(args.input)
    if not path.exists():
        print(f"文件不存在: {path}", file=sys.stderr)
        return 1

    try:
        text = extract(path)
    except Exception as exc:  # noqa: BLE001
        print(str(exc), file=sys.stderr)
        return 2

    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
