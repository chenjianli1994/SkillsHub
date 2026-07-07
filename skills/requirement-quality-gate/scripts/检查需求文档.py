#!/usr/bin/env python3
"""Run mechanical checks for Chinese requirement documents."""

from __future__ import annotations

import sys
# Windows PowerShell 中文输出修复
try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except (AttributeError, OSError):
    pass

import argparse
import re
from pathlib import Path


REQUIRED_SECTIONS = {
    "analysis": ["执行摘要", "输入理解", "背景与目标", "功能需求", "待确认问题"],
    "spec": ["背景与目标", "术语", "范围", "用户角色", "业务流程", "功能需求", "验收标准", "待后续确认"],
}

VAGUE_WORDS = ["友好", "高效", "尽快", "完善", "优化", "灵活", "简单", "快速", "稳定", "易用"]


def read_text(path: Path) -> str:
    for encoding in ("utf-8-sig", "utf-8", "gb18030"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    raise RuntimeError(f"无法识别文本编码: {path}")


def infer_doc_type(text: str) -> str:
    if "需求分析报告" in text or "待确认问题" in text:
        return "analysis"
    if "需求规格书" in text or "FR-001" in text:
        return "spec"
    return "spec"


def find_missing_sections(text: str, doc_type: str) -> list[str]:
    return [section for section in REQUIRED_SECTIONS[doc_type] if section not in text]


def find_vague_lines(text: str) -> list[tuple[int, str, str]]:
    hits: list[tuple[int, str, str]] = []
    for line_no, line in enumerate(text.splitlines(), start=1):
        for word in VAGUE_WORDS:
            if word in line:
                hits.append((line_no, word, line.strip()))
                break
    return hits


def render_report(text: str, doc_type: str) -> str:
    missing = find_missing_sections(text, doc_type)
    vague = find_vague_lines(text)
    requirement_ids = re.findall(r"\b(?:FR|NFR|DR|PR)-\d{3}\b", text)
    acceptance_count = text.count("验收")

    lines = [
        "# 需求文档机械检查结果",
        "",
        f"- 文档类型: {doc_type}",
        f"- 缺失章节: {', '.join(missing) if missing else '无'}",
        f"- 需求编号数量: {len(set(requirement_ids))}",
        f"- 验收相关表述数量: {acceptance_count}",
        f"- 模糊表述命中数量: {len(vague)}",
        "",
        "## 模糊表述命中",
        "",
        "| 行号 | 命中词 | 原文 |",
        "| --- | --- | --- |",
    ]
    if vague:
        for line_no, word, line in vague[:50]:
            safe_line = line.replace("|", "\\|")
            lines.append(f"| {line_no} | {word} | {safe_line} |")
    else:
        lines.append("| - | - | 未发现内置模糊词 |")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="检查需求文档必备章节、编号和模糊表述")
    parser.add_argument("input", help="输入 Markdown 或文本文件")
    parser.add_argument("--type", choices=["analysis", "spec", "auto"], default="auto", help="文档类型")
    parser.add_argument("-o", "--output", help="输出 Markdown 文件；省略时写到 stdout")
    args = parser.parse_args()

    text = read_text(Path(args.input))
    doc_type = infer_doc_type(text) if args.type == "auto" else args.type
    report = render_report(text, doc_type)
    if args.output:
        Path(args.output).write_text(report, encoding="utf-8")
    else:
        print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
