#!/usr/bin/env python3
"""Scan text and propose requirement IDs for candidate functional needs."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


CANDIDATE_RE = re.compile(
    r"(用户|系统|平台|管理员|运营|接口|页面|服务|后台).{0,80}"
    r"(应|需|需要|必须|可以|支持|允许|展示|记录|校验|通知|同步|生成|导出|审批|查询|修改)"
)


def read_text(path: Path) -> str:
    for encoding in ("utf-8-sig", "utf-8", "gb18030"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    raise RuntimeError(f"无法识别文本编码: {path}")


def collect_candidates(text: str) -> list[str]:
    candidates: list[str] = []
    seen: set[str] = set()
    for raw_line in text.splitlines():
        line = raw_line.strip(" \t-|#")
        if not line or len(line) < 8:
            continue
        if CANDIDATE_RE.search(line) and line not in seen:
            seen.add(line)
            candidates.append(line)
    return candidates


def render(candidates: list[str]) -> str:
    lines = ["| 编号 | 候选功能需求 |", "| --- | --- |"]
    for index, item in enumerate(candidates, start=1):
        escaped = item.replace("|", "\\|")
        lines.append(f"| FR-{index:03d} | {escaped} |")
    if not candidates:
        lines.append("| - | 未扫描到明显候选功能需求，请人工拆解。 |")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="生成候选功能需求编号")
    parser.add_argument("input", help="输入 Markdown 或文本文件")
    parser.add_argument("-o", "--output", help="输出 Markdown 文件；省略时写到 stdout")
    args = parser.parse_args()

    text = read_text(Path(args.input))
    output = render(collect_candidates(text))
    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
    else:
        print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
