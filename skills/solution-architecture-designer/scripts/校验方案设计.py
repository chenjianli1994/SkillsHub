# -*- coding: utf-8 -*-
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except (AttributeError, OSError):
    pass

import argparse
import json
import re
from pathlib import Path


TOP_FIELDS = [
    "项目名称",
    "入口类型",
    "生成时间",
    "代码仓库路径",
    "上游依据",
    "方案定位",
    "实现范围",
    "现有能力复用",
    "最小改动方案",
    "推荐方案",
    "备选方案与放弃原因",
    "影响模块",
    "接口与数据影响",
    "风险与验证策略",
    "实现约束",
    "代码依据",
    "推断项",
    "待确认项",
    "阻塞项",
]

VALID_SCOPE_FLAGS = {"是", "否", "待确认"}
VALID_REUSE_TYPES = {"模块", "接口", "数据结构", "配置", "测试"}
VALID_REUSE_MODES = {"直接复用", "小改复用", "参考复用"}
VALID_IMPACT_TYPES = {"复用", "小改", "新增", "隔离", "不改"}
VALID_INTERFACE_TYPES = {"接口", "数据", "配置", "通信", "诊断", "标定"}
VALID_VERIFICATION_METHODS = {
    "评审",
    "静态分析",
    "单元测试",
    "集成测试",
    "台架测试",
    "HIL测试",
    "实车测试",
    "待确认",
}
PLACEHOLDER_VALUES = {"todo", "tbd", "待填写", "待补充", "待定", "xxx", "示例", "占位"}
NEGATION_WORDS = ("不", "非", "无", "无需", "不引入", "不采用")
DETAIL_DESIGN_FRAGMENTS = ("新增类", "新增函数", "新增方法", "新增字段", "函数签名", "class ", "function ")
REQ_ID_RE = re.compile(r"^(SWR|FR|NFR|DR|PR|SYS|UR)-\d{3,}$")


def is_non_empty_string(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def is_placeholder_string(value: object) -> bool:
    if not isinstance(value, str):
        return False
    normalized = value.strip().lower()
    return normalized in PLACEHOLDER_VALUES


def is_real_string(value: object) -> bool:
    return is_non_empty_string(value) and not is_placeholder_string(value)


def is_real_string_list(value: object) -> bool:
    return isinstance(value, list) and len(value) > 0 and all(is_real_string(item) for item in value)


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


def contains_detail_design(value: object) -> bool:
    return isinstance(value, str) and any(fragment in value for fragment in DETAIL_DESIGN_FRAGMENTS)


def contains_unnegated_new_architecture(value: object) -> bool:
    if not isinstance(value, str):
        return False
    target = "全新架构"
    start = 0
    while True:
        index = value.find(target, start)
        if index == -1:
            return False
        prefix = value[max(0, index - 4):index]
        if not any(word in prefix for word in NEGATION_WORDS):
            return True
        start = index + len(target)


def check_code_evidence(value: object, field: str) -> list[str]:
    if not is_real_string_list(value):
        return [f"{field} 代码依据不能为空"]
    return []


def check_solution(data: dict) -> list[str]:
    errors: list[str] = []

    for field in TOP_FIELDS:
        if field not in data:
            errors.append(f"缺少顶层字段：{field}")

    for field in ["项目名称", "入口类型", "生成时间", "代码仓库路径", "方案定位"]:
        if field in data and not is_real_string(data.get(field)):
            errors.append(f"顶层字段不能为空或占位：{field}")

    for field in [
        "实现范围",
        "现有能力复用",
        "最小改动方案",
        "备选方案与放弃原因",
        "影响模块",
        "接口与数据影响",
        "风险与验证策略",
        "实现约束",
        "代码依据",
        "推断项",
        "待确认项",
        "阻塞项",
    ]:
        if field in data and not isinstance(data.get(field), list):
            errors.append(f"顶层字段必须是数组：{field}")

    upstream = data.get("上游依据", {})
    if not isinstance(upstream, dict):
        errors.append("上游依据 必须是对象")
    else:
        if not is_real_string(upstream.get("代码分析结构化数据")):
            errors.append("上游依据.代码分析结构化数据 不能为空")

    scope_items = data.get("实现范围", [])
    if isinstance(scope_items, list):
        if not scope_items:
            errors.append("实现范围不能为空")
        for idx, item in enumerate(scope_items, 1):
            prefix = f"实现范围[{idx}]"
            if not isinstance(item, dict):
                errors.append(f"{prefix} 必须是对象")
                continue
            req_id = item.get("需求ID")
            if not (is_real_string(req_id) and REQ_ID_RE.match(req_id)):
                errors.append(f"{prefix} 需求ID 格式非法：{req_id!r}")
            if not is_real_string(item.get("范围说明")):
                errors.append(f"{prefix} 范围说明不能为空")
            if item.get("是否本次实现") not in VALID_SCOPE_FLAGS:
                errors.append(f"{prefix} 是否本次实现 非法：{item.get('是否本次实现')!r}")

    reuse_items = data.get("现有能力复用", [])
    if isinstance(reuse_items, list):
        if not reuse_items:
            errors.append("现有能力复用不能为空：方案必须优先说明复用现有能力")
        for idx, item in enumerate(reuse_items, 1):
            prefix = f"现有能力复用[{idx}]"
            if not isinstance(item, dict):
                errors.append(f"{prefix} 必须是对象")
                continue
            for field in ["复用对象", "代码位置"]:
                if not is_real_string(item.get(field)):
                    errors.append(f"{prefix} {field} 不能为空")
            if item.get("类型") not in VALID_REUSE_TYPES:
                errors.append(f"{prefix} 类型非法：{item.get('类型')!r}")
            if item.get("复用方式") not in VALID_REUSE_MODES:
                errors.append(f"{prefix} 复用方式非法：{item.get('复用方式')!r}")
            errors.extend(check_code_evidence(item.get("代码依据"), f"{prefix}.代码依据"))

    change_items = data.get("最小改动方案", [])
    if isinstance(change_items, list):
        if not change_items:
            errors.append("最小改动方案不能为空")
        for idx, item in enumerate(change_items, 1):
            prefix = f"最小改动方案[{idx}]"
            if not isinstance(item, dict):
                errors.append(f"{prefix} 必须是对象")
                continue
            for field in ["改动项", "当前代码现状", "最小改动方向", "不改动内容"]:
                if not is_real_string(item.get(field)):
                    errors.append(f"{prefix} {field} 不能为空")
            errors.extend(check_code_evidence(item.get("代码依据"), f"{prefix}.代码依据"))
            if contains_detail_design(item.get("最小改动方向")) and not item.get("代码依据"):
                errors.append(f"{prefix} 像详细设计但缺少现有代码依据")

    recommended = data.get("推荐方案", {})
    if not isinstance(recommended, dict):
        errors.append("推荐方案 必须是对象")
    else:
        for field in ["方案名称", "方案描述", "最小合理改动理由", "复用说明", "兼容性说明"]:
            if not is_real_string(recommended.get(field)):
                errors.append(f"推荐方案缺少字段或字段占位：{field}")
        errors.extend(check_code_evidence(recommended.get("代码依据"), "推荐方案.代码依据"))
        if contains_unnegated_new_architecture(recommended.get("方案描述")) and not data.get("阻塞项"):
            errors.append("推荐方案包含全新架构倾向，必须用阻塞项或代码事实说明现有代码无法承接")
        if contains_detail_design(recommended.get("方案描述")) and not recommended.get("代码依据"):
            errors.append("推荐方案像详细设计但缺少现有代码依据")

    alternatives = data.get("备选方案与放弃原因", [])
    if isinstance(alternatives, list):
        if not alternatives:
            errors.append("备选方案与放弃原因不能为空")
        for idx, item in enumerate(alternatives, 1):
            prefix = f"备选方案与放弃原因[{idx}]"
            if not isinstance(item, dict):
                errors.append(f"{prefix} 必须是对象")
                continue
            for field in ["备选方案", "放弃原因", "风险或代价"]:
                if not is_real_string(item.get(field)):
                    errors.append(f"{prefix} {field} 不能为空")

    module_items = data.get("影响模块", [])
    if isinstance(module_items, list):
        if not module_items:
            errors.append("影响模块不能为空")
        for idx, item in enumerate(module_items, 1):
            prefix = f"影响模块[{idx}]"
            if not isinstance(item, dict):
                errors.append(f"{prefix} 必须是对象")
                continue
            for field in ["模块", "路径", "影响说明"]:
                if not is_real_string(item.get(field)):
                    errors.append(f"{prefix} {field} 不能为空")
            if item.get("影响类型") not in VALID_IMPACT_TYPES:
                errors.append(f"{prefix} 影响类型非法：{item.get('影响类型')!r}")
            errors.extend(check_code_evidence(item.get("代码依据"), f"{prefix}.代码依据"))

    interface_items = data.get("接口与数据影响", [])
    if isinstance(interface_items, list):
        for idx, item in enumerate(interface_items, 1):
            prefix = f"接口与数据影响[{idx}]"
            if not isinstance(item, dict):
                errors.append(f"{prefix} 必须是对象")
                continue
            for field in ["对象", "影响说明", "兼容策略"]:
                if not is_real_string(item.get(field)):
                    errors.append(f"{prefix} {field} 不能为空")
            if item.get("类型") not in VALID_INTERFACE_TYPES:
                errors.append(f"{prefix} 类型非法：{item.get('类型')!r}")
            errors.extend(check_code_evidence(item.get("代码依据"), f"{prefix}.代码依据"))

    risks = data.get("风险与验证策略", [])
    if isinstance(risks, list):
        if not risks:
            errors.append("风险与验证策略不能为空")
        for idx, item in enumerate(risks, 1):
            prefix = f"风险与验证策略[{idx}]"
            if not isinstance(item, dict):
                errors.append(f"{prefix} 必须是对象")
                continue
            for field in ["风险", "影响"]:
                if not is_real_string(item.get(field)):
                    errors.append(f"{prefix} {field} 不能为空")
            methods = item.get("验证方式")
            if not is_real_string_list(methods):
                errors.append(f"{prefix} 验证方式不能为空")
            else:
                invalid = [method for method in methods if method not in VALID_VERIFICATION_METHODS]
                if invalid:
                    errors.append(f"{prefix} 验证方式非法：{invalid}")
            if not is_real_string_list(item.get("覆盖对象")):
                errors.append(f"{prefix} 覆盖对象不能为空")

    if not is_real_string_list(data.get("实现约束")):
        errors.append("实现约束不能为空")
    if not is_real_string_list(data.get("代码依据")):
        errors.append("代码依据不能为空：方案必须引用代码分析中的依据")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="校验 solution-design.json 是否基于现有代码、复用优先、最小改动且避免详设化。")
    parser.add_argument("solution", help="solution-design.json 路径")
    args = parser.parse_args()

    path = Path(args.solution)
    if not path.is_file():
        print(f"文件不存在：{path}")
        return 1
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        print(f"JSON 不可解析：{exc}")
        return 1
    if not isinstance(data, dict):
        print("方案设计数据必须是 JSON 对象")
        return 1

    errors = check_solution(data)
    if errors:
        print("方案设计数据校验未通过：")
        for error in errors:
            print(f"- {error}")
        return 1

    print("方案设计数据校验通过。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
