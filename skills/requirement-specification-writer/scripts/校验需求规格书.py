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
    "上游依据",
    "文档信息",
    "修订记录",
    "背景与目标",
    "术语与定义",
    "范围",
    "用户角色与权限",
    "业务流程",
    "功能需求",
    "数据需求",
    "权限需求",
    "非功能需求",
    "外部依赖与约束",
    "验收标准汇总",
    "需求追踪矩阵",
    "待后续确认事项",
]

VALID_REQUIREMENT_TYPES = {"功能", "接口", "数据", "非功能", "约束"}
VALID_VERIFICATION_METHODS = {"评审", "测试", "台架", "HIL", "实车", "待确认"}
VALID_TRACE_STATES = {"已确认", "假设", "待确认"}
VALID_DECOMPOSITION_FLAGS = {"是", "否", "待确认"}
PLACEHOLDER_VALUES = {"todo", "tbd", "待填写", "待补充", "待定", "xxx", "示例", "占位"}
PLACEHOLDER_FRAGMENTS = ("todo", "tbd", "待填写", "待补充", "待定", "xxx", "示例", "占位")
VAGUE_TERMS = ("友好", "高效", "完善", "尽快", "稳定可靠", "易用", "优化")
REQ_ID_RE = re.compile(r"^(FR|NFR|DR|PR)-\d{3,}$")
FR_ID_RE = re.compile(r"^FR-\d{3,}$")
UPSTREAM_ID_RE = re.compile(r"^(SYS|FR|NFR|DR|PR|UR|CR)-\d{3,}$")


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


def contains_vague_term(value: object) -> bool:
    return isinstance(value, str) and any(term in value for term in VAGUE_TERMS)


def check_string_list(value: object, field: str) -> list[str]:
    if not isinstance(value, list):
        return [f"{field} 必须是数组"]
    errors = []
    for idx, item in enumerate(value, 1):
        if not is_real_string(item):
            errors.append(f"{field}[{idx}] 不能为空或占位")
    return errors


def check_specification(data: dict) -> list[str]:
    errors: list[str] = []

    for field in TOP_FIELDS:
        if field not in data:
            errors.append(f"缺少顶层字段：{field}")

    for field in ["项目名称", "入口类型", "生成时间"]:
        if field in data and not is_real_string(data.get(field)):
            errors.append(f"顶层字段不能为空或占位：{field}")

    errors.extend(check_no_placeholders(data, "root"))

    for field in ["修订记录", "术语与定义", "用户角色与权限", "功能需求", "数据需求", "权限需求", "非功能需求", "外部依赖与约束", "验收标准汇总", "需求追踪矩阵", "待后续确认事项"]:
        if field in data and not isinstance(data.get(field), list):
            errors.append(f"顶层字段必须是数组：{field}")

    document_info = data.get("文档信息", {})
    if not isinstance(document_info, dict):
        errors.append("文档信息 必须是对象")
    else:
        for field in ["需求名称", "版本", "来源材料", "确认依据", "编写日期", "状态"]:
            if not is_real_string(document_info.get(field)):
                errors.append(f"文档信息缺少字段或字段占位：{field}")

    background = data.get("背景与目标", {})
    if not isinstance(background, dict):
        errors.append("背景与目标 必须是对象")
    else:
        for field in ["背景", "业务目标", "成功标准"]:
            errors.extend(check_string_list(background.get(field), f"背景与目标.{field}"))

    scope = data.get("范围", {})
    if not isinstance(scope, dict):
        errors.append("范围 必须是对象")
    else:
        for field in ["本期范围", "不在本期范围", "后续可能扩展"]:
            errors.extend(check_string_list(scope.get(field), f"范围.{field}"))

    flows = data.get("业务流程", {})
    if not isinstance(flows, dict):
        errors.append("业务流程 必须是对象")
    else:
        for field in ["主流程", "异常流程"]:
            errors.extend(check_string_list(flows.get(field), f"业务流程.{field}"))
        if not isinstance(flows.get("状态流转"), list):
            errors.append("业务流程.状态流转 必须是数组")

    functional_requirements = data.get("功能需求", [])
    fr_ids: set[str] = set()
    if isinstance(functional_requirements, list):
        if not functional_requirements:
            errors.append("功能需求不能为空")
        for idx, item in enumerate(functional_requirements, 1):
            prefix = f"功能需求[{idx}]"
            if not isinstance(item, dict):
                errors.append(f"{prefix} 必须是对象")
                continue
            req_id = item.get("编号")
            if not (is_real_string(req_id) and FR_ID_RE.match(req_id)):
                errors.append(f"{prefix} 编号格式非法：{req_id!r}")
            else:
                fr_ids.add(req_id)
            if not is_real_string(item.get("名称")):
                errors.append(f"{prefix} 缺少名称")
            upstream_ids = item.get("上游来源编号")
            if not is_real_string_list(upstream_ids):
                errors.append(f"{prefix} 上游来源编号不能为空")
            else:
                invalid = [upstream_id for upstream_id in upstream_ids if not UPSTREAM_ID_RE.match(upstream_id)]
                if invalid:
                    errors.append(f"{prefix} 上游来源编号格式非法：{invalid}")
            if item.get("需求类型") not in VALID_REQUIREMENT_TYPES:
                errors.append(f"{prefix} 需求类型非法：{item.get('需求类型')!r}")
            for field in ["目标", "触发条件", "前置条件", "参与角色", "处理规则", "输入", "输出", "异常场景", "验收标准", "来源/确认依据"]:
                if not is_real_string(item.get(field)):
                    errors.append(f"{prefix} 缺少字段或字段占位：{field}")
            methods = item.get("建议验证方式")
            if not is_real_string_list(methods):
                errors.append(f"{prefix} 建议验证方式不能为空")
            else:
                invalid = [method for method in methods if method not in VALID_VERIFICATION_METHODS]
                if invalid:
                    errors.append(f"{prefix} 建议验证方式非法：{invalid}")
            if item.get("追踪状态") not in VALID_TRACE_STATES:
                errors.append(f"{prefix} 追踪状态非法：{item.get('追踪状态')!r}")
            if item.get("是否进入软件需求拆解") not in VALID_DECOMPOSITION_FLAGS:
                errors.append(f"{prefix} 是否进入软件需求拆解 非法：{item.get('是否进入软件需求拆解')!r}")
            for field in ["目标", "处理规则", "验收标准"]:
                if contains_vague_term(item.get(field)):
                    errors.append(f"{prefix} {field} 包含模糊词，需改成可验证表述")

    for list_field, id_prefix in [("数据需求", "DR"), ("权限需求", "PR"), ("非功能需求", "NFR")]:
        items = data.get(list_field, [])
        if isinstance(items, list):
            for idx, item in enumerate(items, 1):
                prefix = f"{list_field}[{idx}]"
                if not isinstance(item, dict):
                    errors.append(f"{prefix} 必须是对象")
                    continue
                req_id = item.get("编号")
                if not (is_real_string(req_id) and re.match(rf"^{id_prefix}-\d{{3,}}$", req_id)):
                    errors.append(f"{prefix} 编号格式非法：{req_id!r}")

    acceptance_items = data.get("验收标准汇总", [])
    if isinstance(acceptance_items, list):
        if not acceptance_items:
            errors.append("验收标准汇总不能为空")
        for idx, item in enumerate(acceptance_items, 1):
            prefix = f"验收标准汇总[{idx}]"
            if not isinstance(item, dict):
                errors.append(f"{prefix} 必须是对象")
                continue
            for field in ["编号", "验收项", "验收方法", "通过标准"]:
                if not is_real_string(item.get(field)):
                    errors.append(f"{prefix} 缺少字段或字段占位：{field}")
            if contains_vague_term(item.get("通过标准")):
                errors.append(f"{prefix} 通过标准包含模糊词，需改成可验证表述")

    traceability_items = data.get("需求追踪矩阵", [])
    traced_spec_ids: set[str] = set()
    if isinstance(traceability_items, list):
        if not traceability_items:
            errors.append("需求追踪矩阵不能为空")
        for idx, item in enumerate(traceability_items, 1):
            prefix = f"需求追踪矩阵[{idx}]"
            if not isinstance(item, dict):
                errors.append(f"{prefix} 必须是对象")
                continue
            spec_id = item.get("规格书编号")
            if not (is_real_string(spec_id) and REQ_ID_RE.match(spec_id)):
                errors.append(f"{prefix} 规格书编号格式非法：{spec_id!r}")
            else:
                traced_spec_ids.add(spec_id)
            upstream_ids = item.get("上游来源编号")
            if not is_real_string_list(upstream_ids):
                errors.append(f"{prefix} 上游来源编号不能为空")
            else:
                invalid = [upstream_id for upstream_id in upstream_ids if not UPSTREAM_ID_RE.match(upstream_id)]
                if invalid:
                    errors.append(f"{prefix} 上游来源编号格式非法：{invalid}")
            if item.get("需求类型") not in VALID_REQUIREMENT_TYPES:
                errors.append(f"{prefix} 需求类型非法：{item.get('需求类型')!r}")
            methods = item.get("建议验证方式")
            if not is_real_string_list(methods):
                errors.append(f"{prefix} 建议验证方式不能为空")
            else:
                invalid = [method for method in methods if method not in VALID_VERIFICATION_METHODS]
                if invalid:
                    errors.append(f"{prefix} 建议验证方式非法：{invalid}")
            if item.get("是否进入软件需求拆解") not in VALID_DECOMPOSITION_FLAGS:
                errors.append(f"{prefix} 是否进入软件需求拆解 非法：{item.get('是否进入软件需求拆解')!r}")
            if item.get("状态") not in VALID_TRACE_STATES:
                errors.append(f"{prefix} 状态非法：{item.get('状态')!r}")
            for field in ["来源编号/原文依据", "确认记录"]:
                if not is_real_string(item.get(field)):
                    errors.append(f"{prefix} 缺少字段或字段占位：{field}")

    missing_trace = sorted(fr_ids - traced_spec_ids)
    if missing_trace:
        errors.append(f"功能需求缺少追踪矩阵记录：{missing_trace}")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="校验 requirement-specification.json 的字段完整性、编号、验收和追踪关系。")
    parser.add_argument("specification", help="requirement-specification.json 路径")
    args = parser.parse_args()

    path = Path(args.specification)
    if not path.is_file():
        print(f"文件不存在：{path}")
        return 1
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        print(f"JSON 不可解析：{exc}")
        return 1
    if not isinstance(data, dict):
        print("需求规格书数据必须是 JSON 对象")
        return 1

    errors = check_specification(data)
    if errors:
        print("需求规格书数据校验未通过：")
        for error in errors:
            print(f"- {error}")
        return 1

    print("需求规格书数据校验通过。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
