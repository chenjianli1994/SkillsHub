# -*- coding: utf-8 -*-
from pathlib import Path


REQUIRED_FILES = [
    "业务规则.md",
    "术语表.md",
    "需求规范.md",
    "文档模板说明.md",
    "索引.json",
]


def main() -> int:
    project_root = Path(__file__).resolve().parents[1]
    knowledge_dir = project_root / "knowledge"

    if not knowledge_dir.exists():
        print(f"缺少知识库目录：{knowledge_dir}")
        return 1

    missing = [name for name in REQUIRED_FILES if not (knowledge_dir / name).is_file()]
    if missing:
        print("知识库缺少必备文件：")
        for name in missing:
            print(f"- knowledge/{name}")
        return 1

    print("知识库必备文件检查通过。")
    for name in REQUIRED_FILES:
        print(f"- knowledge/{name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
