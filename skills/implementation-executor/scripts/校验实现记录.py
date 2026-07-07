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


VALID_STATES = {
    "已实现且测试通过",
    "已实现未验证",
    "部分实现",
    "未实现（阻塞）",
}

# 不允许进入「代码驱动出文档」的实现状态
BLOCKING_STATES = {"已实现未验证", "部分实现", "未实现（阻塞）"}
VALID_TEST_RESULTS = {"通过", "失败", "未运行", "跳过"}
PASSING_STATE = "已实现且测试通过"
PASSING_TEST_RESULT = "通过"

TOP_FIELDS = [
    "项目名称",
    "入口类型",
    "生成时间",
    "上游依据",
    "跳过阶段",
    "缺失前置材料",
    "代码落地位置",
    "任务实现",
    "整体测试状态",
    "可进入代码驱动出文档",
    "阻塞项",
    "待确认项",
]


def is_non_empty_string(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def is_non_empty_list(value: object) -> bool:
    return isinstance(value, list) and len(value) > 0 and all(is_non_empty_string(item) for item in value)


def check_record(data: dict) -> list[str]:
    errors: list[str] = []

    for field in TOP_FIELDS:
        if field not in data:
            errors.append(f"缺少顶层字段：{field}")

    for field in ["项目名称", "入口类型", "生成时间", "代码落地位置"]:
        if field in data and not is_non_empty_string(data.get(field)):
            errors.append(f"顶层字段不能为空：{field}")

    for field in ["跳过阶段", "缺失前置材料", "阻塞项", "待确认项"]:
        if field in data and not isinstance(data.get(field), list):
            errors.append(f"顶层字段必须是数组：{field}")
        elif field in data and any(not is_non_empty_string(item) for item in data.get(field)):
            errors.append(f"顶层字段数组不能包含空值：{field}")

    has_unpassed = False
    if isinstance(data.get("阻塞项"), list) and data.get("阻塞项"):
        has_unpassed = True
        errors.append("阻塞项非空：存在阻塞时不得通过实现记录质量门")

    tasks = data.get("任务实现", [])
    if not isinstance(tasks, list):
        errors.append("任务实现 必须是数组")
        tasks = []
    if not tasks:
        errors.append("任务实现 为空：至少应记录一个开发任务")

    for idx, task in enumerate(tasks, 1):
        prefix = f"任务实现[{idx}]"
        if not isinstance(task, dict):
            errors.append(f"{prefix} 必须是对象")
            has_unpassed = True
            continue
        if not task.get("任务编号"):
            errors.append(f"{prefix} 缺少任务编号")
        if not is_non_empty_list(task.get("需求编号")):
            errors.append(f"{prefix} 缺少需求编号（无法追溯到需求规格书）")
        if not is_non_empty_string(task.get("任务描述")):
            errors.append(f"{prefix} 缺少任务描述")
        for list_field in ["复用现有代码", "推断项", "待确认项"]:
            if list_field in task:
                if not isinstance(task.get(list_field), list):
                    errors.append(f"{prefix} {list_field} 必须是数组")
                elif any(not is_non_empty_string(item) for item in task.get(list_field)):
                    errors.append(f"{prefix} {list_field} 不能包含空值")
        state = task.get("实现状态")
        if state not in VALID_STATES:
            errors.append(f"{prefix} 实现状态非法：{state!r}，应为 {sorted(VALID_STATES)}")
        if state in BLOCKING_STATES:
            has_unpassed = True
            errors.append(f"{prefix} 实现状态未完成：{state}")

        test = task.get("测试", {})
        if not isinstance(test, dict):
            errors.append(f"{prefix} 测试 必须是对象")
            has_unpassed = True
            continue

        test_result = test.get("测试结果")
        if test_result not in VALID_TEST_RESULTS:
            errors.append(f"{prefix} 测试结果非法：{test_result!r}，应为 {sorted(VALID_TEST_RESULTS)}")
            has_unpassed = True
        elif test_result != PASSING_TEST_RESULT:
            has_unpassed = True
            errors.append(f"{prefix} 测试未通过：测试结果为 {test_result!r}")

        if not is_non_empty_list(test.get("测试文件")):
            errors.append(f"{prefix} 测试文件不能为空")
        if not is_non_empty_string(test.get("测试命令")):
            errors.append(f"{prefix} 测试命令不能为空")
        if not is_non_empty_list(test.get("覆盖的验收标准")):
            errors.append(f"{prefix} 覆盖的验收标准不能为空")

        if state == PASSING_STATE:
            if not is_non_empty_list(task.get("实现文件")):
                errors.append(f"{prefix} 标记为已实现且测试通过时，实现文件不能为空")
            if test_result != PASSING_TEST_RESULT:
                errors.append(f"{prefix} 标记为已实现且测试通过时，测试结果必须为“通过”")
                has_unpassed = True
        elif test_result == PASSING_TEST_RESULT:
            errors.append(f"{prefix} 实现状态为 {state!r} 时，测试结果不得标记为“通过”")

    overall_test = data.get("整体测试状态", {})
    if not isinstance(overall_test, dict):
        errors.append("整体测试状态 必须是对象")
        has_unpassed = True
    else:
        if not is_non_empty_string(overall_test.get("测试命令")):
            errors.append("整体测试状态缺少测试命令")
        if overall_test.get("结果") != PASSING_TEST_RESULT:
            has_unpassed = True
            errors.append(f"整体测试状态未通过：结果为 {overall_test.get('结果')!r}")
        for count_field in ["失败数", "未运行数"]:
            count = overall_test.get(count_field)
            if isinstance(count, int) and count > 0:
                has_unpassed = True
                errors.append(f"整体测试状态未通过：{count_field}={count}")
            elif not isinstance(count, int):
                errors.append(f"整体测试状态字段必须是整数：{count_field}")

    ready_for_docs = data.get("可进入代码驱动出文档")
    if not isinstance(ready_for_docs, bool):
        errors.append("可进入代码驱动出文档 必须是布尔值")
    if ready_for_docs is True and has_unpassed:
        errors.append(
            "质量门不自洽：可进入代码驱动出文档=true，但存在未通过测试、未运行测试或阻塞项"
        )

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(
        description="校验 implementation-record.json 的字段完整性、需求追溯与质量门自洽性。"
    )
    parser.add_argument("record", help="implementation-record.json 路径")
    args = parser.parse_args()

    path = Path(args.record)
    if not path.is_file():
        print(f"文件不存在：{path}")
        return 1
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        print(f"JSON 不可解析：{exc}")
        return 1
    if not isinstance(data, dict):
        print("实现记录必须是 JSON 对象")
        return 1

    errors = check_record(data)
    if errors:
        print("实现记录校验未通过：")
        for error in errors:
            print(f"- {error}")
        return 1

    print("实现记录校验通过。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
