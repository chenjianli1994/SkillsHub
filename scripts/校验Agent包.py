# -*- coding: utf-8 -*-
import json
from pathlib import Path


REQUIRED_DIRS = [
    "docs",
    "skills",
    "knowledge",
    "mcp",
    "scripts",
    "state",
    "outputs",
]

REQUIRED_SKILLS = {
    "software-delivery-orchestrator": ["templates", "scripts", "references"],
    "reference-document-profiler": ["templates", "scripts", "references"],
    "requirement-workflow-orchestrator": ["templates", "scripts"],
    "requirement-analysis-report": ["templates", "scripts"],
    "requirement-specification-writer": ["templates", "scripts"],
    "requirement-document-exporter": ["templates", "scripts"],
    "requirement-quality-gate": ["templates"],
    "strategy-document-writer": ["templates", "scripts", "references"],
}

REQUIRED_FILES = [
    "docs/软件开发全流程Skills包建设方案.md",
    "state/README.md",
    "state/.gitignore",
    "state/structured/README.md",
    "skills/software-delivery-orchestrator/templates/工作流状态模板.json",
    "skills/software-delivery-orchestrator/templates/入口类型判定表.md",
    "skills/software-delivery-orchestrator/references/阶段调度规则.md",
    "skills/software-delivery-orchestrator/scripts/识别入口类型.py",
    "skills/software-delivery-orchestrator/scripts/更新工作流状态.py",
    "skills/reference-document-profiler/templates/参考文档画像模板.json",
    "skills/reference-document-profiler/templates/参考文档结构画像模板.md",
    "skills/reference-document-profiler/references/参考用途判定规则.md",
    "skills/reference-document-profiler/scripts/生成参考文档画像.py",
]

JSON_TEMPLATES = [
    "skills/software-delivery-orchestrator/templates/工作流状态模板.json",
    "skills/reference-document-profiler/templates/参考文档画像模板.json",
]

FORBIDDEN_OUTPUT_NAMES = {
    "工作流状态.json",
    "00_工作流状态.json",
    "reference-document-profile.json",
    "参考文档结构画像.md",
}


def main() -> int:
    project_root = Path(__file__).resolve().parents[1]
    errors: list[str] = []

    if not (project_root / "AGENTS.md").is_file():
        errors.append("缺少 AGENTS.md")

    for dirname in REQUIRED_DIRS:
        if not (project_root / dirname).is_dir():
            errors.append(f"缺少目录：{dirname}/")

    for filename in REQUIRED_FILES:
        if not (project_root / filename).is_file():
            errors.append(f"缺少必备文件：{filename}")

    for filename in JSON_TEMPLATES:
        path = project_root / filename
        if path.is_file():
            try:
                json.loads(path.read_text(encoding="utf-8-sig"))
            except json.JSONDecodeError as exc:
                errors.append(f"JSON 模板不可解析：{filename}（{exc}）")

    skills_dir = project_root / "skills"
    state_dir = project_root / "state"
    if state_dir.is_dir():
        if not (state_dir / "README.md").is_file():
            errors.append("缺少内部状态目录说明：state/README.md")
        if not (state_dir / ".gitignore").is_file():
            errors.append("缺少内部状态忽略规则：state/.gitignore")
        if not (state_dir / "structured").is_dir():
            errors.append("缺少结构化中间产物目录：state/structured/")

    outputs_dir = project_root / "outputs"
    if outputs_dir.is_dir():
        if (outputs_dir / "structured").exists():
            errors.append("outputs/ 中不得包含内部结构化目录：outputs/structured/")
        for path in outputs_dir.rglob("*"):
            if path.is_file() and (path.name in FORBIDDEN_OUTPUT_NAMES or path.suffix.lower() == ".json"):
                relative_path = path.relative_to(project_root).as_posix()
                errors.append(f"outputs/ 中不得存放内部状态或 JSON 中间产物：{relative_path}")

    for skill_name, required_subdirs in REQUIRED_SKILLS.items():
        skill_dir = skills_dir / skill_name
        if not skill_dir.is_dir():
            errors.append(f"缺少 skill 目录：skills/{skill_name}/")
            continue
        if not (skill_dir / "SKILL.md").is_file():
            errors.append(f"缺少 skill 入口：skills/{skill_name}/SKILL.md")
        for subdir in required_subdirs:
            if not (skill_dir / subdir).is_dir():
                errors.append(f"缺少 skill 资源目录：skills/{skill_name}/{subdir}/")

    if errors:
        print("Agent 包校验未通过：")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Agent 包校验通过。")
    print("已检查 AGENTS.md、docs/、skills/、knowledge/、mcp/、scripts/、state/、outputs/。")
    print("已检查项目内必备 skills 的 SKILL.md 以及 templates/scripts/references 等资源目录。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
