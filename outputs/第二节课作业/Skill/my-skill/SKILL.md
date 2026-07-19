---
name: my-skill
description: 将项目内 requirement-analysis-report 与 requirement-specification-writer 的规则和模板封装为汽车软件需求工程 Skill，用于动力电池冷却控制等脱敏汽车软件需求的分析、确认和规格化。
---

# 汽车软件需求工程 Skill

## 功能描述

本 Skill 负责把原始汽车软件需求材料整理为需求分析报告或需求规格书草稿。它复用项目现有两个源 Skill 的工作流程、质量规则和模板：`skills/requirement-analysis-report` 与 `skills/requirement-specification-writer`。源目录保持不修改，本包中的 `assets/` 和 `references/` 是作业提交用副本和约束说明。

## 输入定义

```yaml
raw_requirement: 必填文本
confirmation_answers: 可选文本
run_mode: analysis 或 full，默认 full
allow_low_risk_assumptions: 布尔值，默认 true
```

## 输出定义

- `analysis`：中文 Markdown 需求分析报告，必须包含确定事实、合理推断、待确认假设、问题诊断和确认清单。
- `full`：中文 Markdown 需求规格书或待确认规格书草稿，必须包含 FR、DR、PR、NFR、验收标准、来源依据、验证方式、追踪矩阵和待后续确认事项。
- 结构化需求数据：按 `assets/需求规格书模板.md` 的字段生成，可由项目校验脚本验证。

## 调用规则

1. 先读取并遵循 `references/需求分析规则.md`、`references/规格书规则.md`、`references/汽车软件检查表.md` 和 `references/质量门禁.md`。
2. 对 `run_mode=analysis` 先输出确认清单；不要在没有确认答案时把 P0/P1 写成已确认。
3. 对 `run_mode=full` 合并确认答案；P0/P1 未覆盖时保持待确认草稿；P2/P3 只有在允许低风险假设时才能显式标注假设。
4. 优先使用已索引知识并附文件名/章节来源。知识未提供的参数必须写“未提供/待确认”。
5. 每条核心需求使用唯一的 FR、DR、PR、NFR 编号；FR 必须有触发、前置、规则、输入、输出、异常、验收、验证和追踪状态。
6. 传感器异常必须分别检查异常判定、上报影响、降级动作和恢复条件；不得编造温度、时间、信号、故障等级、替代值或安全参数。
7. 发生需求冲突或材料不完整时，保留各来源和影响，生成待确认项，不擅自选择版本。

## 复用边界

- 规则来源：项目内 `skills/requirement-analysis-report/SKILL.md` 和 `skills/requirement-specification-writer/SKILL.md`，作业副本见 `references/源技能_需求分析规则原文.md`、`references/源技能_需求规格书规则原文.md`。
- 模板来源：项目内两个源 Skill 的模板，作业副本见 `assets/需求分析报告模板.md`、`assets/需求规格书模板.md`。
- 本 Skill 不新增脚本目录，不改变源 Skill，不将领域假设伪装为通用规则。

## 质量门禁

交付前必须完成结构、编号、来源、验收、追踪、三类信息区分、P0/P1 状态和参数禁编检查。失败时输出阻塞问题和待确认清单。

