---
name: requirement-quality-gate
description: Review Chinese requirements analysis reports and requirements specifications for completeness, consistency, ambiguity, traceability, and testability. Use when the user asks to inspect a generated requirements report, validate whether a specification is ready for review/development/testing, find requirement problems, or run a quality gate before delivery.
---

# Requirement Quality Gate

## 工作目标

对需求分析报告或需求规格书做质量门禁检查，输出问题清单、阻塞结论和可执行修订建议。

## 适用输入

- 需求分析报告。
- 优化后的需求规格书。
- PRD 草稿、业务需求文档、接口需求说明。
- 用户要求“检查需求质量”“看看能不能评审/开发/测试”的文档。

## 工作流程

1. 识别文档类型：分析报告、规格书或混合文档。
2. 可运行 `scripts/检查需求文档.py` 做机械检查：必备章节、模糊词、编号、验收标准线索。
3. 人工审阅语义质量：完整性、一致性、可验证性、可实现性、范围边界、角色权限、数据口径、异常流程、依赖约束。
4. 按问题严重度分类：
   - `阻塞`：不修复会导致规格书方向错误、无法开发或无法验收。
   - `重要`：影响核心流程质量，但可通过明确假设继续推进。
   - `一般`：影响表达、可读性或边界完备度。
5. 读取 `templates/需求质量检查报告模板.md`，按模板输出中文 Markdown 检查报告。

## 检查标准

- 完整性：背景、目标、角色、范围、功能、数据、权限、非功能、验收、依赖是否齐全。
- 一致性：术语、流程、状态、权限、数据口径是否自相矛盾。
- 可验证性：每条需求是否有清晰输入、输出、规则和验收标准。
- 可追踪性：需求是否能追溯到原文、分析报告或用户确认记录。
- 可实现性：是否存在过度宽泛、不可落地、跨系统依赖未说明的问题。
- 边界：是否明确不在本期范围和未确认事项。

## 输出规则

- 先给门禁结论：`通过`、`有条件通过`、`不通过`。
- 问题清单必须包含位置、问题、影响、建议修复。
- 对模糊词不要只指出词本身，要给出可验证改写方向。
- 对不确定内容标注为“需确认”，不要替用户做业务决策。

## 资源

- `templates/需求质量检查报告模板.md`：质量检查报告模板，必须读取并按其结构输出。
- `scripts/检查需求文档.py`：机械质量扫描脚本，用作审阅辅助。
