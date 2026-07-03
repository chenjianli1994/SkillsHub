# -*- coding: utf-8 -*-
import argparse
from pathlib import Path


def search_markdown(knowledge_dir: Path, keyword: str) -> list[tuple[Path, int, str]]:
    matches: list[tuple[Path, int, str]] = []
    lowered_keyword = keyword.lower()

    for path in sorted(knowledge_dir.rglob("*.md")):
        text = path.read_text(encoding="utf-8")
        for line_number, line in enumerate(text.splitlines(), start=1):
            if lowered_keyword in line.lower():
                matches.append((path, line_number, line.strip()))

    return matches


def main() -> int:
    parser = argparse.ArgumentParser(description="按关键词搜索 knowledge 目录下的 Markdown 文档。")
    parser.add_argument("关键词", help="要搜索的关键词")
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parents[1]
    knowledge_dir = project_root / "knowledge"

    if not knowledge_dir.exists():
        print(f"缺少知识库目录：{knowledge_dir}")
        return 1

    matches = search_markdown(knowledge_dir, args.关键词)
    if not matches:
        print(f"未找到关键词：{args.关键词}")
        return 1

    for path, line_number, line in matches:
        relative_path = path.relative_to(project_root)
        print(f"{relative_path}:{line_number}: {line}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
