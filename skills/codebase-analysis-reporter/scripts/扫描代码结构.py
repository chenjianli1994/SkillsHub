# -*- coding: utf-8 -*-
import sys
# Windows PowerShell 中文输出修复
try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except (AttributeError, OSError):
    pass
import argparse
import json
from collections import Counter
from pathlib import Path


# 技术栈标志文件 → 技术栈线索
STACK_MARKERS = {
    "package.json": "Node.js / JavaScript",
    "tsconfig.json": "TypeScript",
    "requirements.txt": "Python",
    "pyproject.toml": "Python",
    "setup.py": "Python",
    "go.mod": "Go",
    "pom.xml": "Java / Maven",
    "build.gradle": "Java / Gradle",
    "Cargo.toml": "Rust",
    "Gemfile": "Ruby",
    "composer.json": "PHP",
    "CMakeLists.txt": "C/C++ / CMake",
    "Dockerfile": "Docker",
}

# 常见入口文件名（stem，无扩展名部分）
ENTRY_STEMS = {"main", "index", "app", "server", "program", "__main__"}

# 扫描时忽略的目录
IGNORE_DIRS = {
    ".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build",
    ".idea", ".vscode", "target", "bin", "obj", ".codegraph", ".omo",
}


def scan(root: Path) -> dict:
    stack_hints: list[dict] = []
    entries: list[str] = []
    top_dirs: list[str] = []
    ext_counter: Counter = Counter()

    for path in root.rglob("*"):
        parts = path.relative_to(root).parts
        if any(part in IGNORE_DIRS for part in parts):
            continue
        if path.is_dir():
            if len(parts) == 1:
                top_dirs.append(parts[0])
            continue
        if path.name in STACK_MARKERS:
            stack_hints.append(
                {"文件": path.relative_to(root).as_posix(), "线索": STACK_MARKERS[path.name]}
            )
        if path.stem.lower() in ENTRY_STEMS:
            entries.append(path.relative_to(root).as_posix())
        if path.suffix:
            ext_counter[path.suffix.lower()] += 1

    return {
        "代码仓库路径": str(root),
        "技术栈线索": stack_hints,
        "顶层目录": sorted(top_dirs),
        "候选入口": sorted(entries)[:50],
        "文件类型分布": dict(ext_counter.most_common(20)),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="扫描代码仓库，输出技术栈线索、目录结构、候选入口和文件类型分布（辅助线索，非结论）。"
    )
    parser.add_argument("root", nargs="?", default=".", help="代码仓库根路径，默认当前目录")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    if not root.is_dir():
        print(f"目录不存在：{root}")
        return 1

    result = scan(root)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
