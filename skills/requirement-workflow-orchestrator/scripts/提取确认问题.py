#!/usr/bin/env python3
"""Extract Q-xxx confirmation rows from a requirements analysis report."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


ROW_RE = re.compile(r"^\|\s*(Q-\d{3})\s*\|\s*(P[0-3])\s*\|\s*(.*?)\s*\|\s*(.*?)\s*\|\s*(.*?)\s*\|")


def read_text(path: Path) -> str:
    for encoding in ("utf-8-sig", "utf-8", "gb18030"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    raise RuntimeError(f"无法识别文本编码: {path}")


def split_cells(row: re.Match[str]) -> tuple[str, str, str, str, str]:
    return tuple(cell.replace("\\|", "|").strip() for cell in row.groups())  # type: ignore[return-value]


def extract_rows(text: str) -> list[tuple[str, str, str, str, str]]:
    rows: list[tuple[str, str, str, str, str]] = []
    for line in text.splitlines():
        match = ROW_RE.match(line.strip())
        if match:
            rows.append(split_cells(match))
    return rows


def render(rows: list[tuple[str, str, str, str, str]]) -> str:
    groups = {
        "必须确认": [row for row in rows if row[1] in {"P0", "P1"}],
        "建议确认": [row for row in rows if row[1] == "P2"],
        "可带假设推进": [row for row in rows if row[1] == "P3"],
    }
    lines = [
        "# 需求确认清单",
        "",
        "请在“用户确认结果”列填写：同意建议 / 修改为... / 暂按假设推进 / 不适用。",
        "",
    ]
    for title, items in groups.items():
        lines.append(f"## {title}")
        lines.append("")
        lines.append("| 编号 | 优先级 | 问题 | 不确认的影响 | 建议默认处理 | 用户确认结果 |")
        lines.append("| --- | --- | --- | --- | --- | --- |")
        if items:
            for number, priority, question, impact, suggestion in items:
                lines.append(f"| {number} | {priority} | {question} | {impact} | {suggestion} |  |")
        else:
            lines.append("| - | - | 无 | - | - | - |")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="从需求分析报告提取待确认问题")
    parser.add_argument("input", help="需求分析报告 Markdown 文件")
    parser.add_argument("-o", "--output", help="输出确认清单 Markdown 文件；省略时写到 stdout")
    args = parser.parse_args()

    output = render(extract_rows(read_text(Path(args.input))))
    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
    else:
        print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
