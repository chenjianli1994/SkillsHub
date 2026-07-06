---
name: strategy-document-writer
description: Generate a Chinese control strategy document from a requirement document plus implementation code, headers, diffs, calibration notes, or related PDFs/DOCX files. Use this whenever the user asks for 策略文档, 控制策略文档, 软件策略说明, or wants to derive a strategy document from 需求文档 and code. The default deliverable is Markdown; when the user explicitly asks for Word or DOCX, generate structured JSON that matches this skill's Word data template and use the bundled generator script to produce the final DOCX directly from the dedicated template.
---

# Strategy Document Writer

## 工作目标

基于需求文档、代码实现、头文件、diff、标定信息和补充说明，生成一份可评审、可追溯、结构稳定的中文策略文档。  
文档重点不是复述需求，而是把“需求约束 + 代码行为 + 状态/条件/时序/动作”整理成工程团队可直接评审的策略说明。

## 触发场景

遇到以下需求时应优先使用本 skill：

- 用户明确说“生成策略文档”“写控制策略文档”“根据需求文档和代码出一份策略文档”
- 输入材料里同时出现需求说明和 `.c` / `.h` / `.diff` / 标定表 / 功能定义 PDF
- 用户已有类似策略文档样例，希望沿用同类章节结构输出新的策略文档
- 用户要求 Word/DOCX 版策略文档，而不是普通 Markdown 说明

## 输入要求

优先收集以下材料：

- 需求文档、功能定义文档、需求规格书、功能说明 PDF/DOCX
- 实现代码：`.c`、`.h`
- 代码差异：`.diff`
- 标定/枚举/信号表
- 已有类似策略文档样例

如果材料不齐，不要停下。继续输出文档，但必须：

- 把未确认事实写成“当前假设”或 `TBD（需确认）`
- 在附录或尾部列出待确认项
- 不得把代码中看不到、需求里也没有的结论伪装成事实

## 产出规则

默认输出：

- 一份中文 Markdown 策略文档

用户明确要求 Word/DOCX 时：

1. 先生成符合 `templates/策略文档Word数据模板.json` 结构的 JSON
2. 再运行 `scripts/按Word模板生成策略文档.py`
3. 使用 `templates/策略文档Word模板_美化版.docx` 直接生成 DOCX

不要把 Markdown 机械转换成 Word。

## 文档编写流程

1. 读取输入材料，区分“需求约束”“实现事实”“推断/假设”。
2. 从代码和头文件中提取：
   - 输入信号
   - 输出信号
   - 状态枚举
   - 关键条件
   - 计时器/阈值
   - 动作结果
   - 退出/异常场景
3. 对照需求文档，补齐代码里没有但需求明确要求的业务背景、目标和边界。
4. 参考 `references/样本文档结构总结.md` 决定章节骨架和常见表格类型。
5. 按 `templates/策略文档模板.md` 先生成 Markdown 草稿。
6. 如果用户要 Word，生成结构化 JSON，再调用 Word 生成脚本。

## 编写准则

- 以“条件 -> 判断 -> 动作 -> 状态反馈 -> 退出”组织策略逻辑。
- 每个关键逻辑块优先写清：
  - 进入条件
  - 执行动作
  - 状态保持
  - 退出条件
  - 特殊场景或异常处理
- 信号表只写文档真正依赖的信号，不要把无关变量堆进去。
- 代码中的常量、宏、状态枚举，优先转写成工程可读的中文解释。
- 代码无法证明的时序、阈值、持续时间，不要擅自补齐；写 `TBD（需确认）`。
- 需求与代码冲突时，明确指出冲突来源，不做静默覆盖。
- 样本文档里的章节是“模式”，不是必须逐字照搬。若某功能没有对应内容，可删去该小节；若有特有逻辑，可新增二级或三级节。

## 推荐章节骨架

样本文档收敛出的稳定骨架通常是：

1. 概述
2. 信号描述
3. 逻辑设计
4. 附录

常见可选小节：

- `1.3 功能概述`
- `2.3 档位映射 / 参数映射 / 状态定义`
- `3.2 开启条件 / 进入条件`
- `3.3 执行动作 / 时序逻辑 / 状态机`
- `3.4 退出条件`
- `3.5 特殊场景处理 / 状态反馈 / 共用约束`

## Word 直出要求

如果生成 DOCX，必须包含：

- 首页标题、副标题、审批信息
- 修订记录
- 目录
- 正文分级标题
- 清晰表格
- 页眉页脚与页码

首页审批信息、修订记录、目录的版式参考现有需求规格书模板；正文章节结构参考策略文档样本。

## 最终自检

交付前检查：

- 是否同时利用了需求文档和代码事实，而不是只改写其中一边
- 输入/输出信号、状态、条件、动作是否有来源可追溯
- 每个核心逻辑块是否说明了进入、执行、退出
- 不确定项是否被显式标出
- Word 输出是否由模板直出，而不是文本另存为

## 资源

- `references/样本文档结构总结.md`：已完成策略文档的共性总结
- `templates/策略文档模板.md`：Markdown 策略文档骨架
- `templates/策略文档Word模板.md`：Word 结构说明
- `templates/策略文档Word数据模板.json`：Word 直出的结构化数据模板
- `templates/策略文档Word模板_美化版.docx`：Word 样式模板
- `scripts/按Word模板生成策略文档.py`：按模板和 JSON 生成 DOCX
