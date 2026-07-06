# -*- coding: utf-8 -*-
import argparse


def has_any(text: str, keywords: list[str]) -> bool:
    return any(keyword.lower() in text for keyword in keywords)


def has_all(text: str, keywords: list[str]) -> bool:
    return all(keyword.lower() in text for keyword in keywords)


def detect_entry_type(text: str) -> str:
    normalized = text.lower()

    # 1. full-flow 强信号
    if has_any(normalized, ["完整流程", "完整跑", "全流程", "从需求开始"]):
        return "full-flow"

    # 2. 参考文档驱动类（"参考"是强信号，前置判断避免被 export-only 截胡）
    if "参考" in normalized:
        # 参考 + 代码 + 设计 → design-from-code-with-reference
        if has_any(normalized, ["代码", "现有代码", "当前代码"]) and has_any(normalized, ["设计", "详细设计", "方案"]):
            return "design-from-code-with-reference"
        # 参考 + 策略 → strategy-from-reference
        if "策略" in normalized:
            return "strategy-from-reference"
        # 参考 + 需求 → requirement-from-reference
        if "需求" in normalized:
            return "requirement-from-reference"
        # 参考 + 格式/样式/版式 + 导出动作 → export-with-reference-style
        if has_any(normalized, ["格式", "样式", "版式"]) and has_any(normalized, ["导出", "生成", "出", "转", "给我"]):
            return "export-with-reference-style"
        # 参考 + 设计/方案（无代码）→ reference-doc-driven，避免"生成"过宽截胡
        if has_any(normalized, ["设计", "详细设计", "方案"]):
            return "reference-doc-driven"
        # 参考 + 明确的 Word/DOCX/PDF 导出动作 → export-with-reference-style
        if has_any(normalized, ["word", "docx", "pdf"]) and has_any(normalized, ["导出", "生成", "出", "转", "给我"]):
            return "export-with-reference-style"
        # 参考文档驱动（兜底）
        return "reference-doc-driven"

    # 3. 代码驱动类（无参考文档，基于代码）
    # 3.1 codebase-only：宽松匹配"分析/看看/了解" + "代码/仓库/架构/实现"
    if has_any(normalized, ["分析", "看看", "了解"]) and has_any(normalized, ["代码", "仓库", "架构", "实现"]):
        return "codebase-only"
    # codebase-only 整词关键词（保留原有关键词作为补充）
    if has_any(normalized, ["代码分析", "分析当前代码", "只分析代码", "分析仓库", "代码结构"]):
        return "codebase-only"
    # 3.2 strategy-from-code：代码 + 策略
    if has_all(normalized, ["代码", "策略"]):
        return "strategy-from-code"
    if has_any(normalized, ["基于当前代码", "按照当前代码", "现有代码", "代码中"]) and "策略" in normalized:
        return "strategy-from-code"
    # 3.3 design-from-code：代码 + 设计
    if has_any(normalized, ["基于当前代码", "按照当前代码", "现有代码", "代码中"]) and has_any(normalized, ["设计", "详细设计", "方案"]):
        return "design-from-code"

    # 4. export-only（严格：必须有导出动作 + 格式词，避免"word"单独触发）
    export_actions = ["导出", "转", "给我", "输出", "生成", "出"]
    export_formats = ["word", "docx", "pdf"]
    if has_any(normalized, export_actions) and has_any(normalized, export_formats):
        return "export-only"

    # 5. quality-only
    if has_any(normalized, ["质量", "检查", "评审"]) and not has_any(normalized, ["生成", "设计", "需求"]):
        return "quality-only"

    # 6. task-plan-from-design
    if has_any(normalized, ["根据设计拆任务", "开发任务计划", "任务计划", "拆任务", "拆开发任务"]):
        return "task-plan-from-design"

    # 7. requirement-only
    if has_any(normalized, ["需求分析", "需求规格书", "需求确认", "需求文档"]):
        return "requirement-only"

    return "full-flow"


def main() -> int:
    parser = argparse.ArgumentParser(description="根据用户请求初步识别软件交付工作流入口类型。")
    parser.add_argument("text", nargs="+", help="用户请求文本")
    args = parser.parse_args()
    print(detect_entry_type(" ".join(args.text)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
