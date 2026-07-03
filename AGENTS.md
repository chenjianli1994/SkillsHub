# 项目级需求规格书生成 Agent 包

## 基本约束

- 本项目只使用项目内 skills，路径为 `skills/`，不要安装到全局 skills 目录。
- 需求分析、需求确认、需求规格书生成、质量检查、Word/DOCX 导出、PDF 导出任务，优先读取并使用项目内 skills。
- 完整需求规格书工作流默认从 `skills/requirement-workflow-orchestrator/SKILL.md` 开始。
- 默认输出 Markdown 文档，用户输出文件统一放到 `outputs/`。
- 文档内容和文件名尽量使用中文。

## 工作流入口

完整工作流按以下顺序组织：

1. 读取 `knowledge/` 下与本次需求相关的业务规则、术语、规范和模板说明。
2. 读取 `skills/requirement-workflow-orchestrator/SKILL.md`，由编排 skill 判断后续需要调用的项目内 skill。
3. 需求分析任务使用 `skills/requirement-analysis-report/SKILL.md`。
4. 需求规格书撰写任务使用 `skills/requirement-specification-writer/SKILL.md`。
5. 需求质量检查任务使用 `skills/requirement-quality-gate/SKILL.md`。
6. 只有用户明确要求 Word/DOCX 或 PDF 时，才使用 `skills/requirement-document-exporter/SKILL.md`。

## 导出规则

- 默认交付 Markdown，不主动生成 Word/DOCX 或 PDF。
- 只有用户明确要求 Word/DOCX 时，才使用 `requirement-document-exporter`。
- Word/DOCX 必须通过结构化 JSON 和 `skills/requirement-document-exporter/templates/需求规格书Word模板_美化版.docx` 直出。
- 不允许使用 Markdown 转 Word 作为需求规格书 Word 交付路径。
- 只有用户明确要求 PDF 时，才调用 `skills/requirement-document-exporter/scripts/文件转pdf.py`。

## 本地知识库

- 本地知识库放在 `knowledge/`。
- Agent 在分析需求前应优先读取相关知识。
- `knowledge/索引.json` 维护知识文件、用途和关键词，便于检索。
- 新增业务规则、术语、规范、模板说明时，应同步更新 `knowledge/索引.json`。

## MCP 接入

- MCP 配置和示例放在 `mcp/`。
- 当前仅提供示例配置，不包含真实凭据。
- 后续可接入企业文档库、数据库、搜索服务、需求管理系统等。
- 接入 MCP 后，仍应先使用项目内 knowledge 和 skills，再按需查询外部系统。

## 项目级辅助脚本

- `scripts/初始化项目知识库.py`：检查知识库必备文件是否存在。
- `scripts/查询知识库.py`：按关键词搜索 `knowledge/` 下的 Markdown 文档。
- `scripts/校验Agent包.py`：检查项目级 Agent 包结构和 skill 必备文件。

## 协作约定

- 可启用多 Agent 协同处理调研、生成、检查等独立子任务。
- 子任务完成后应及时回收不再需要的子 Agent 或临时资源。
- 修改本包时保持一次交付自洽、可评审、可继续开发。
