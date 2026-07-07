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
from pathlib import Path


VALID_CONTEXTS = {"需求驱动", "代码驱动"}
VALID_EVIDENCE_TYPES = {"确定事实", "合理推断"}
PLACEHOLDER_VALUES = {
    "todo",
    "tbd",
    "待填写",
    "待补充",
    "待定",
    "xxx",
    "示例",
    "示例模块",
    "占位",
    "占位：模块职责说明",
}
PLACEHOLDER_FRAGMENTS = ("todo", "tbd", "待填写", "待补充", "待定", "xxx", "示例", "占位")

TOP_FIELDS = [
    "项目名称",
    "运行语境",
    "生成时间",
    "代码仓库路径",
    "技术栈",
    "关键模块",
    "确定事实",
    "合理推断",
    "待确认项",
]

LIST_FIELDS = [
    "技术栈",
    "目录结构",
    "关键模块",
    "接口与API",
    "数据模型",
    "调用关系",
    "需求映射",
    "确定事实",
    "合理推断",
    "待确认项",
    "技术债与风险",
    "测试缺口",
]

TEXT_LIST_FIELDS = {
    "目录结构",
    "合理推断",
    "待确认项",
    "技术债与风险",
    "测试缺口",
}


def is_non_empty_string(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def is_placeholder_string(value: object) -> bool:
    if not isinstance(value, str):
        return False
    normalized = value.strip().lower()
    if normalized in PLACEHOLDER_VALUES:
        return True
    return any(fragment in normalized for fragment in PLACEHOLDER_FRAGMENTS)


def is_real_string(value: object) -> bool:
    return is_non_empty_string(value) and not is_placeholder_string(value)


def is_non_empty_list(value: object) -> bool:
    return isinstance(value, list) and len(value) > 0


def is_non_empty_string_list(value: object) -> bool:
    return isinstance(value, list) and len(value) > 0 and all(is_real_string(item) for item in value)


def check_text_items(items: object, field: str) -> list[str]:
    errors: list[str] = []
    if not isinstance(items, list):
        return errors
    for idx, item in enumerate(items, 1):
        prefix = f"{field}[{idx}]"
        if isinstance(item, str):
            if not is_real_string(item):
                errors.append(f"{prefix} 不能为空")
        elif isinstance(item, dict):
            content = item.get("内容")
            if not is_real_string(content):
                errors.append(f"{prefix} 缺少内容")
            errors.extend(check_no_placeholders(item, prefix))
        else:
            errors.append(f"{prefix} 必须是字符串或对象")
    return errors


def check_no_placeholders(value: object, field: str) -> list[str]:
    errors: list[str] = []
    if isinstance(value, str):
        if is_placeholder_string(value):
            errors.append(f"{field} 包含占位值")
    elif isinstance(value, list):
        for idx, item in enumerate(value, 1):
            errors.extend(check_no_placeholders(item, f"{field}[{idx}]"))
    elif isinstance(value, dict):
        for key, item in value.items():
            errors.extend(check_no_placeholders(item, f"{field}.{key}"))
    return errors


def check_analysis(data: dict) -> list[str]:
    errors: list[str] = []

    for field in TOP_FIELDS:
        if field not in data:
            errors.append(f"缺少顶层字段：{field}")

    context = data.get("运行语境")
    if context not in VALID_CONTEXTS:
        errors.append(f"运行语境非法：{context!r}，应为 {sorted(VALID_CONTEXTS)}")

    for field, value in data.items():
        if field not in LIST_FIELDS:
            errors.extend(check_no_placeholders(value, field))

    for field in ["项目名称", "生成时间", "代码仓库路径"]:
        if field in data and not is_real_string(data.get(field)):
            errors.append(f"顶层字段不能为空：{field}")

    for field in LIST_FIELDS:
        if field in data and not isinstance(data.get(field), list):
            errors.append(f"字段必须是数组：{field}")
        elif field in TEXT_LIST_FIELDS:
            errors.extend(check_text_items(data.get(field), field))
        elif field in data:
            errors.extend(check_no_placeholders(data.get(field), field))

    if "技术栈" in data and not is_non_empty_string_list(data.get("技术栈")):
        errors.append("技术栈不能为空，且每一项都必须是非空字符串")

    modules = data.get("关键模块", [])
    if isinstance(modules, list) and not modules:
        errors.append("关键模块不能为空")
    if isinstance(modules, list):
        for idx, module in enumerate(modules, 1):
            prefix = f"关键模块[{idx}]"
            if not isinstance(module, dict):
                errors.append(f"{prefix} 必须是对象")
                continue
            if not is_real_string(module.get("模块")):
                errors.append(f"{prefix} 缺少模块名称")
            if not is_real_string(module.get("路径")):
                errors.append(f"{prefix} 缺少路径")
            if not is_real_string(module.get("职责")):
                errors.append(f"{prefix} 缺少职责")
            evidence_type = module.get("依据类型")
            if evidence_type not in VALID_EVIDENCE_TYPES:
                errors.append(
                    f"{prefix} 依据类型非法：{evidence_type!r}，应为 {sorted(VALID_EVIDENCE_TYPES)}"
                )
            if not is_non_empty_string_list(module.get("代码依据")):
                errors.append(f"{prefix} 代码依据不能为空")

    facts = data.get("确定事实", [])
    if isinstance(facts, list):
        for idx, fact in enumerate(facts, 1):
            prefix = f"确定事实[{idx}]"
            if not isinstance(fact, dict):
                errors.append(f"{prefix} 必须是对象，包含 内容 和 代码依据")
                continue
            if not is_real_string(fact.get("内容")):
                errors.append(f"{prefix} 缺少内容")
            if not is_non_empty_string_list(fact.get("代码依据")):
                errors.append(f"{prefix} 缺少代码依据")

    # 代码驱动语境下，确定事实与待确认项不应同时为空（否则等于什么都没分析出来）
    if context == "代码驱动":
        pending = data.get("待确认项")
        if isinstance(facts, list) and isinstance(pending, list) and not facts and not pending:
            errors.append("代码驱动语境下，确定事实与待确认项不应同时为空")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(
        description="校验 codebase-analysis.json 的字段完整性、运行语境、代码依据与三态结构。"
    )
    parser.add_argument("analysis", help="codebase-analysis.json 路径")
    args = parser.parse_args()

    path = Path(args.analysis)
    if not path.is_file():
        print(f"文件不存在：{path}")
        return 1
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        print(f"JSON 不可解析：{exc}")
        return 1
    if not isinstance(data, dict):
        print("代码分析数据必须是 JSON 对象")
        return 1

    errors = check_analysis(data)
    if errors:
        print("代码分析数据校验未通过：")
        for error in errors:
            print(f"- {error}")
        return 1

    print("代码分析数据校验通过。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
