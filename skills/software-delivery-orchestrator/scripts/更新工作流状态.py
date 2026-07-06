# -*- coding: utf-8 -*-
import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any


DEFAULT_STATE: dict[str, Any] = {
    "项目名称": "",
    "入口类型": "",
    "当前阶段": "",
    "阶段状态": [],
    "输入材料": [],
    "用户可见输出": [],
    "内部状态产物": [],
    "阻塞项": [],
    "待确认项": [],
    "更新时间": "",
}

LIST_FIELDS = ["阶段状态", "输入材料", "用户可见输出", "内部状态产物", "阻塞项", "待确认项"]


def load_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        return DEFAULT_STATE.copy()
    state = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(state, dict):
        raise ValueError(f"状态文件不是 JSON 对象：{path}")
    merged = DEFAULT_STATE.copy()
    merged.update(state)
    for field in LIST_FIELDS:
        if not isinstance(merged.get(field), list):
            merged[field] = []
    return merged


def append_unique(values: list[Any], value: str | None) -> list[Any]:
    if value and value not in values:
        values.append(value)
    return values


def main() -> int:
    parser = argparse.ArgumentParser(description="创建或更新 state/工作流状态.json。")
    parser.add_argument("--entry-type", default="", help="入口类型")
    parser.add_argument("--stage", default="", help="当前阶段")
    parser.add_argument("--input", default="", help="追加输入材料")
    parser.add_argument("--output", default="", help="追加用户可见输出")
    parser.add_argument("--state-artifact", default="", help="追加内部状态产物")
    parser.add_argument("--blocker", default="", help="追加阻塞项")
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parents[3]
    state_dir = project_root / "state"
    state_dir.mkdir(parents=True, exist_ok=True)
    state_path = state_dir / "工作流状态.json"

    state = load_state(state_path)
    if args.entry_type:
        state["入口类型"] = args.entry_type
    if args.stage:
        state["当前阶段"] = args.stage
    state["输入材料"] = append_unique(state.get("输入材料", []), args.input)
    state["用户可见输出"] = append_unique(state.get("用户可见输出", []), args.output)
    state["内部状态产物"] = append_unique(state.get("内部状态产物", []), args.state_artifact)
    state["阻塞项"] = append_unique(state.get("阻塞项", []), args.blocker)
    state["更新时间"] = datetime.now().isoformat(timespec="seconds")

    tmp_path = state_path.with_suffix(".json.tmp")
    tmp_path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp_path.replace(state_path)
    print(state_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
