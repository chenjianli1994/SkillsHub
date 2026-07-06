# -*- coding: utf-8 -*-
import argparse


def has_any(text: str, keywords: list[str]) -> bool:
    return any(keyword.lower() in text for keyword in keywords)


def has_all(text: str, keywords: list[str]) -> bool:
    return all(keyword.lower() in text for keyword in keywords)


def detect_entry_type(text: str) -> str:
    normalized = text.lower()

    if has_any(normalized, ["完整流程", "完整跑", "全流程", "从需求开始"]):
        return "full-flow"
    if has_any(normalized, ["导出", "生成word", "生成 docx", "生成pdf"]) and has_any(normalized, ["参考", "样式", "格式"]):
        return "export-with-reference-style"
    if has_any(normalized, ["导出", "word", "docx", "pdf"]):
        return "export-only"
    if has_any(normalized, ["质量", "检查", "评审"]) and not has_any(normalized, ["生成", "设计", "需求"]):
        return "quality-only"
    if has_all(normalized, ["参考", "代码"]) and has_any(normalized, ["设计", "详细设计", "方案"]):
        return "design-from-code-with-reference"
    if has_all(normalized, ["参考", "策略"]):
        return "strategy-from-reference"
    if has_all(normalized, ["参考", "需求"]):
        return "requirement-from-reference"
    if has_any(normalized, ["代码分析", "分析当前代码", "只分析代码", "仓库架构", "分析仓库"]):
        return "codebase-only"
    if has_all(normalized, ["代码", "策略"]):
        return "strategy-from-code"
    if has_any(normalized, ["基于当前代码", "按照当前代码", "现有代码"]) and has_any(normalized, ["设计", "详细设计", "方案"]):
        return "design-from-code"
    if "参考" in normalized:
        return "reference-doc-driven"
    if has_any(normalized, ["需求分析", "需求规格书", "需求确认", "需求文档"]):
        return "requirement-only"
    if has_any(normalized, ["根据设计拆任务", "开发任务计划", "任务计划"]):
        return "task-plan-from-design"
    return "full-flow"


def main() -> int:
    parser = argparse.ArgumentParser(description="根据用户请求初步识别软件交付工作流入口类型。")
    parser.add_argument("text", nargs="+", help="用户请求文本")
    args = parser.parse_args()
    print(detect_entry_type(" ".join(args.text)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
