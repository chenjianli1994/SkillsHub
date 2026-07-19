# 第二节课作业：汽车软件需求助手

## 1. 作业定位

本提交包基于脱敏的“动力电池冷却控制需求”构建“汽车软件需求助手”，覆盖 Persona、Knowledge、Workflow、Skill 和运行评测。默认中文 Markdown 输出，所有不确定的温度、时间、信号、故障等级、降级和安全参数均保留为待确认项，不写成确定事实。

## 2. 验收项与实现内容

| 评分项 | 实现内容 | 证据 |
| --- | --- | --- |
| Persona 设计 | 服务汽车软件产品、系统、开发和测试工程师；固定区分确定事实、合理推断、待确认假设 | `Agent设计/场景说明.md`、`Agent设计/Persona配置.md`、`Agent设计/01_Agent基础配置.png`、`Agent设计/02_Persona配置.png`、`Agent设计/03_Agent对话测试.png` |
| Knowledge | 创建“汽车软件需求工程知识集”，上传三份脱敏 Markdown 并完成索引 | `Knowledge/知识文件说明.md`、`Knowledge/04_Knowledge创建.png`、`Knowledge/05_文件索引完成.png` |
| 知识问答 | 完成事实/推断/待确认、P0/P1、编号、功能字段、传感器异常五类问题 | `Knowledge/知识问答测试记录.md`、`Knowledge/06_知识问答.png` |
| Workflow | 用户输入 → 知识检索 → 需求分析 → 需求规格化 → 质量检查 → 结果输出；支持 analysis/full 两阶段 | `Workflow/流程设计说明.md`、`Workflow/节点配置.md`、`Workflow/07_Workflow完整画布.png`、`Workflow/08_节点配置.png`、`Workflow/09_Workflow运行结果.png` |
| Skill | 按题目要求封装现有两个 Skill，目录仅含 SKILL.md、assets、references、examples | `Skill/my-skill/`、`Skill/10_Skill目录结构.png`、`Skill/11_SKILL.md内容.png`、`Skill/12_Skill运行验证.png` |
| 运行评测 | DEAP 创建并索引五类案例评测集，最终任务 V4 评估成功，覆盖模糊阈值、完整确认、需求冲突、传感器异常、材料不完整 | `评测/评测集说明.md`、`评测/汽车软件需求助手五类案例评测集_精简验证.xlsx`、`评测/智能体评测结果.md`、`评测/13_智能体评测结果.png`、`评测/14_五类案例数据明细.png` |

## 3. 本地交付目录

```text
第二节课作业/
├── README.md
├── 需求分析报告.md
├── 需求规格书.md
├── 需求质量检查报告.md
├── Agent设计/
├── Knowledge/
├── Workflow/
├── 评测/
└── Skill/my-skill/
    ├── SKILL.md
    ├── assets/
    ├── references/
    └── examples/
```

DEAP 资源记录：Agent“汽车软件需求助手”（ID：`9cae2ca3-6bdc-4e07-8277-afe791c718dd`）；Knowledge“汽车软件需求工程知识集”（ID：`9332e3d2-06f4-4c6d-968a-01ab303b3785`）；Workflow“需求分析与规格书生成流程”；最终评测任务“汽车软件需求助手_评测任务_V4”。

## 4. 使用顺序

1. 将 `Knowledge/` 下三份 Markdown 上传到 DEAP Knowledge，并等待索引状态完成。
2. 创建或打开 Agent“汽车软件需求助手”，绑定知识集和 Skill。
3. 创建 Workflow“需求分析与规格书生成流程”，先以 `run_mode=analysis` 运行，再以 `run_mode=full` 运行。
4. 使用 `评测/评测集说明.md` 中的五个案例执行评测；最终平台结果为 5 条、评估成功、综合 84 分（安全性 99、准确性 81、可解释性 73）。
5. 使用 `需求质量检查报告.md` 和 `state/structured/第二节课作业/` 下结构化记录复核本地交付。

## 5. 数据与安全边界

- 所有业务材料均为脱敏示例，不含真实企业资料、账号、密钥或个人信息。
- 作业只要求在 DEAP 平台保存本人可见或平台允许的最小可见范围，不公开发布 Agent。
- 未确认的 P0/P1 领域参数只输出待确认草稿；P2/P3 仅在 `allow_low_risk_assumptions=true` 时显式标记假设推进。

## 6. 验证记录

- 知识问答：5/5 通过。
- Workflow：`analysis` 和 `full` 均成功。
- Skill：运行验证 19/19 通过。
- 本地机械检查：需求分析、需求规格书均无缺失章节、无模糊词命中；需求编号、验收表述和来源追踪已核对。
- 截图证据：Agent 4 张、Knowledge 3 张、Workflow 3 张、Skill 3 张、评测 2 张，共 15 张；截图仅保留作业页面和 DEAP 结果，不含密钥或历史企业资料。

## 7. 非阻塞限制

DEAP 自动评分综合得分为 84 分，其中个别案例的可解释性分数偏低；但五类业务门禁已在数据明细中逐条核对通过。初始同名完整评测集曾出现平台导入乱码，已保留为历史资源，最终采用 UTF-8 精简验证集 V4，避免乱码影响验收。
