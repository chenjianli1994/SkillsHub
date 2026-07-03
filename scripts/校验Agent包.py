# -*- coding: utf-8 -*-
from pathlib import Path


REQUIRED_DIRS = [
    "skills",
    "knowledge",
    "mcp",
    "scripts",
    "outputs",
]

REQUIRED_SKILLS = [
    "requirement-workflow-orchestrator",
    "requirement-analysis-report",
    "requirement-specification-writer",
    "requirement-document-exporter",
    "requirement-quality-gate",
]


def main() -> int:
    project_root = Path(__file__).resolve().parents[1]
    errors: list[str] = []

    if not (project_root / "AGENTS.md").is_file():
        errors.append("缺少 AGENTS.md")

    for dirname in REQUIRED_DIRS:
        if not (project_root / dirname).is_dir():
            errors.append(f"缺少目录：{dirname}/")

    skills_dir = project_root / "skills"
    for skill_name in REQUIRED_SKILLS:
        skill_dir = skills_dir / skill_name
        if not skill_dir.is_dir():
            errors.append(f"缺少 skill 目录：skills/{skill_name}/")
            continue
        if not (skill_dir / "SKILL.md").is_file():
            errors.append(f"缺少 skill 入口：skills/{skill_name}/SKILL.md")
        if not (skill_dir / "templates").is_dir():
            errors.append(f"缺少 skill 模板目录：skills/{skill_name}/templates/")
        if not (skill_dir / "scripts").is_dir():
            errors.append(f"缺少 skill 脚本目录：skills/{skill_name}/scripts/")

    if errors:
        print("Agent 包校验未通过：")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Agent 包校验通过。")
    print("已检查 AGENTS.md、skills/、knowledge/、mcp/、scripts/、outputs/、所有必备 SKILL.md、templates/ 和 scripts/。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
