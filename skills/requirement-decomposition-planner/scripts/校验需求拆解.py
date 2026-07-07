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
    "上游需求基线",
    "软件需求清单",
    "CM矩阵",
    "覆盖性统计",
    "一致性问题",
    "设计输入集",
    "阻塞项",
    "待确认项",
]

VALID_DECOMPOSITION_RELATIONS = {"直接承接", "拆分", "合并", "派生", "约束继承", "不适用"}
VALID_REQUIREMENT_TYPES = {"功能", "接口", "诊断", "数据", "标定", "非功能", "约束"}
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
VALID_COVERAGE_STATUS = {"已覆盖", "部分覆盖", "未覆盖", "待确认", "不适用"}
VALID_PRIORITIES = {"高", "中", "低", "待确认"}
VALID_COMPLEXITIES = {"高", "中", "低", "待确认"}
FUNCTIONAL_UPSTREAM_TYPES = {"功能", "功能需求", "系统需求", "客户需求"}
PLACEHOLDER_VALUES = {
    "todo",
    "tbd",
    "待填写",
    "待补充",
    "待定",
    "xxx",
    "示例",
    "占位",
}
PLACEHOLDER_FRAGMENTS = ("todo", "tbd", "待填写", "待补充", "待定", "xxx", "示例", "占位")
TASK_LIKE_FRAGMENTS = (
    "前端开发",
    "后端开发",
    "数据库开发",
    "接口开发",
    "开发页面",
    "开发接口",
    "编写代码",
)
UPSTREAM_ID_RE = re.compile(r"^(SYS|FR|NFR|DR|PR|UR|CR)-\d{3,}$")
SWR_ID_RE = re.compile(r"^SWR-\d{3,}$")
DI_ID_RE = re.compile(r"^DI-\d{3,}$")
CI_ID_RE = re.compile(r"^CI-\d{3,}$")


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


def contains_task_like_description(value: object) -> bool:
    return isinstance(value, str) and any(fragment in value for fragment in TASK_LIKE_FRAGMENTS)


def check_string_list_field(obj: dict, field: str, prefix: str) -> list[str]:
    errors: list[str] = []
    value = obj.get(field)
    if not isinstance(value, list):
        errors.append(f"{prefix} {field} 必须是数组")
    elif any(not is_real_string(item) for item in value):
        errors.append(f"{prefix} {field} 不能包含空值或占位值")
    return errors


def check_breakdown(data: dict) -> list[str]:
    errors: list[str] = []

    for field in TOP_FIELDS:
        if field not in data:
            errors.append(f"缺少顶层字段：{field}")

    for field in ["项目名称", "入口类型", "生成时间"]:
        if field in data and not is_real_string(data.get(field)):
            errors.append(f"顶层字段不能为空或占位：{field}")

    for field in ["阻塞项", "待确认项", "一致性问题", "设计输入集", "上游需求基线", "软件需求清单", "CM矩阵"]:
        if field in data and not isinstance(data.get(field), list):
            errors.append(f"顶层字段必须是数组：{field}")
        elif field in ["上游需求基线", "软件需求清单", "CM矩阵", "设计输入集"] and field in data and not data.get(field):
            errors.append(f"顶层字段不能为空：{field}")

    errors.extend(check_no_placeholders(data, "root"))

    upstream_items = data.get("上游需求基线", [])
    software_items = data.get("软件需求清单", [])
    cm_items = data.get("CM矩阵", [])

    upstream_ids: set[str] = set()
    functional_upstream_ids: set[str] = set()
    if isinstance(upstream_items, list):
        for idx, item in enumerate(upstream_items, 1):
            prefix = f"上游需求基线[{idx}]"
            if not isinstance(item, dict):
                errors.append(f"{prefix} 必须是对象")
                continue
            upstream_id = item.get("上游需求ID")
            upstream_type = item.get("上游需求类型")
            if not (is_real_string(upstream_id) and UPSTREAM_ID_RE.match(upstream_id)):
                errors.append(f"{prefix} 上游需求ID 格式非法：{upstream_id!r}")
            else:
                upstream_ids.add(upstream_id)
                if upstream_id.startswith("FR-") or upstream_type in FUNCTIONAL_UPSTREAM_TYPES:
                    functional_upstream_ids.add(upstream_id)
            for field in ["上游需求类型", "上游需求描述", "来源", "成熟度"]:
                if not is_real_string(item.get(field)):
                    errors.append(f"{prefix} 缺少字段或字段占位：{field}")

    software_ids: set[str] = set()
    swr_upstream_refs: dict[str, set[str]] = {}
    if isinstance(software_items, list):
        for idx, item in enumerate(software_items, 1):
            prefix = f"软件需求清单[{idx}]"
            if not isinstance(item, dict):
                errors.append(f"{prefix} 必须是对象")
                continue
            swr_id = item.get("软件需求ID")
            if not (is_real_string(swr_id) and SWR_ID_RE.match(swr_id)):
                errors.append(f"{prefix} 软件需求ID 格式非法：{swr_id!r}")
            else:
                software_ids.add(swr_id)
            refs = item.get("来源需求ID")
            if not is_real_string_list(refs):
                errors.append(f"{prefix} 来源需求ID 不能为空")
                refs = []
            unknown_refs = [ref for ref in refs if ref not in upstream_ids]
            if unknown_refs:
                errors.append(f"{prefix} 来源需求ID 未出现在上游需求基线：{unknown_refs}")
            if swr_id:
                swr_upstream_refs[str(swr_id)] = set(refs)
            description = item.get("软件需求描述")
            if not is_real_string(description):
                errors.append(f"{prefix} 软件需求描述不能为空或占位")
            elif contains_task_like_description(description):
                errors.append(f"{prefix} 软件需求描述像开发任务，不应作为 SWE.1 需求拆解主项")
            if item.get("需求类型") not in VALID_REQUIREMENT_TYPES:
                errors.append(f"{prefix} 需求类型非法：{item.get('需求类型')!r}")
            if item.get("优先级") not in VALID_PRIORITIES:
                errors.append(f"{prefix} 优先级非法：{item.get('优先级')!r}")
            if item.get("复杂度") not in VALID_COMPLEXITIES:
                errors.append(f"{prefix} 复杂度非法：{item.get('复杂度')!r}")
            methods = item.get("验证方式")
            if not is_real_string_list(methods):
                errors.append(f"{prefix} 验证方式不能为空")
            else:
                invalid = [method for method in methods if method not in VALID_VERIFICATION_METHODS]
                if invalid:
                    errors.append(f"{prefix} 验证方式非法：{invalid}")
            for list_field in ["依赖", "风险", "设计输入提示"]:
                if list_field in item and not isinstance(item.get(list_field), list):
                    errors.append(f"{prefix} {list_field} 必须是数组")

    cm_covered_upstreams: set[str] = set()
    cm_software_ids: set[str] = set()
    status_counts = {status: 0 for status in VALID_COVERAGE_STATUS}
    if isinstance(cm_items, list):
        for idx, item in enumerate(cm_items, 1):
            prefix = f"CM矩阵[{idx}]"
            if not isinstance(item, dict):
                errors.append(f"{prefix} 必须是对象")
                continue
            upstream_id = item.get("上游需求ID")
            swr_id = item.get("软件需求ID")
            if upstream_id not in upstream_ids:
                errors.append(f"{prefix} 上游需求ID 未出现在上游需求基线：{upstream_id!r}")
            else:
                cm_covered_upstreams.add(upstream_id)
            if swr_id not in software_ids and item.get("覆盖状态") != "不适用":
                errors.append(f"{prefix} 软件需求ID 未出现在软件需求清单：{swr_id!r}")
            elif isinstance(swr_id, str):
                cm_software_ids.add(swr_id)
            for field in ["上游需求描述", "上游需求类型", "软件需求描述"]:
                if item.get("覆盖状态") != "不适用" and not is_real_string(item.get(field)):
                    errors.append(f"{prefix} 缺少字段或字段占位：{field}")
            if item.get("分解关系") not in VALID_DECOMPOSITION_RELATIONS:
                errors.append(f"{prefix} 分解关系非法：{item.get('分解关系')!r}")
            if item.get("需求类型") not in VALID_REQUIREMENT_TYPES:
                errors.append(f"{prefix} 需求类型非法：{item.get('需求类型')!r}")
            if item.get("验证方式") not in VALID_VERIFICATION_METHODS:
                errors.append(f"{prefix} 验证方式非法：{item.get('验证方式')!r}")
            coverage_status = item.get("覆盖状态")
            if coverage_status not in VALID_COVERAGE_STATUS:
                errors.append(f"{prefix} 覆盖状态非法：{coverage_status!r}")
            else:
                status_counts[coverage_status] += 1
            if coverage_status in {"部分覆盖", "未覆盖", "待确认"} and not is_real_string(item.get("一致性问题")):
                errors.append(f"{prefix} 覆盖状态为 {coverage_status!r} 时必须填写一致性问题")

    missing_functional_coverage = sorted(functional_upstream_ids - cm_covered_upstreams)
    if missing_functional_coverage:
        errors.append(f"功能类上游需求缺少 CM 覆盖关系：{missing_functional_coverage}")

    missing_swr_in_cm = sorted(software_ids - cm_software_ids)
    if missing_swr_in_cm:
        errors.append(f"软件需求缺少 CM 映射：{missing_swr_in_cm}")

    for swr_id, refs in swr_upstream_refs.items():
        mapped_refs = {item.get("上游需求ID") for item in cm_items if isinstance(item, dict) and item.get("软件需求ID") == swr_id}
        if refs and not refs.issubset(mapped_refs):
            errors.append(f"{swr_id} 的来源需求未全部进入 CM 矩阵：{sorted(refs - mapped_refs)}")

    stats = data.get("覆盖性统计")
    if not isinstance(stats, dict):
        errors.append("覆盖性统计 必须是对象")
    else:
        expected_counts = {
            "上游需求总数": len(upstream_ids),
            "软件需求总数": len(software_ids),
            "已覆盖": status_counts["已覆盖"],
            "部分覆盖": status_counts["部分覆盖"],
            "未覆盖": status_counts["未覆盖"],
            "待确认": status_counts["待确认"],
            "不适用": status_counts["不适用"],
        }
        for field, expected in expected_counts.items():
            if not isinstance(stats.get(field), int):
                errors.append(f"覆盖性统计字段必须是整数：{field}")
            elif stats.get(field) != expected:
                errors.append(f"覆盖性统计不自洽：{field}={stats.get(field)}，实际应为 {expected}")

    issues = data.get("一致性问题", [])
    if isinstance(issues, list):
        for idx, item in enumerate(issues, 1):
            prefix = f"一致性问题[{idx}]"
            if not isinstance(item, dict):
                errors.append(f"{prefix} 必须是对象")
                continue
            if not (is_real_string(item.get("编号")) and CI_ID_RE.match(item.get("编号"))):
                errors.append(f"{prefix} 编号格式非法")
            errors.extend(check_string_list_field(item, "关联上游需求ID", prefix))
            for ref in item.get("关联上游需求ID", []) if isinstance(item.get("关联上游需求ID"), list) else []:
                if ref not in upstream_ids:
                    errors.append(f"{prefix} 关联上游需求ID 未出现在上游需求基线：{ref}")
            for field in ["问题类型", "问题描述", "影响", "处理建议"]:
                if not is_real_string(item.get(field)):
                    errors.append(f"{prefix} 缺少字段或字段占位：{field}")

    design_inputs = data.get("设计输入集", [])
    if isinstance(design_inputs, list):
        for idx, item in enumerate(design_inputs, 1):
            prefix = f"设计输入集[{idx}]"
            if not isinstance(item, dict):
                errors.append(f"{prefix} 必须是对象")
                continue
            if not (is_real_string(item.get("设计输入ID")) and DI_ID_RE.match(item.get("设计输入ID"))):
                errors.append(f"{prefix} 设计输入ID 格式非法")
            errors.extend(check_string_list_field(item, "来源软件需求ID", prefix))
            for ref in item.get("来源软件需求ID", []) if isinstance(item.get("来源软件需求ID"), list) else []:
                if ref not in software_ids:
                    errors.append(f"{prefix} 来源软件需求ID 未出现在软件需求清单：{ref}")
            if not is_real_string(item.get("设计关注点")):
                errors.append(f"{prefix} 设计关注点不能为空")
            for list_field in ["边界条件", "约束", "风险提示"]:
                if not isinstance(item.get(list_field), list):
                    errors.append(f"{prefix} {list_field} 必须是数组")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(
        description="校验 requirement-breakdown.json 的 ASPICE SWE.1 风格需求追踪、CM 覆盖和字段完整性。"
    )
    parser.add_argument("breakdown", help="requirement-breakdown.json 路径")
    args = parser.parse_args()

    path = Path(args.breakdown)
    if not path.is_file():
        print(f"文件不存在：{path}")
        return 1
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        print(f"JSON 不可解析：{exc}")
        return 1
    if not isinstance(data, dict):
        print("需求拆解数据必须是 JSON 对象")
        return 1

    errors = check_breakdown(data)
    if errors:
        print("需求拆解数据校验未通过：")
        for error in errors:
            print(f"- {error}")
        return 1

    print("需求拆解数据校验通过。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
