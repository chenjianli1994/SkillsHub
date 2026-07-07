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
import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree


FORBIDDEN_ITEMS = ["项目名称", "人员姓名", "日期", "客户信息", "历史数据", "旧项目结论"]


def read_docx(path: Path) -> str:
    with zipfile.ZipFile(path) as docx:
        xml = docx.read("word/document.xml")
    root = ElementTree.fromstring(xml)
    namespace = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    paragraphs: list[str] = []
    for paragraph in root.findall(".//w:p", namespace):
        texts = [node.text or "" for node in paragraph.findall(".//w:t", namespace)]
        line = "".join(texts).strip()
        if line:
            paragraphs.append(line)
    return "\n".join(paragraphs)


def read_text(path: Path) -> str:
    if path.suffix.lower() == ".docx":
        return read_docx(path)
    if path.suffix.lower() == ".pdf":
        raise ValueError("当前脚本不直接解析 PDF。请先将 PDF 转为 TXT/Markdown，或接入 PDF 文本提取工具后再生成画像。")
    return path.read_text(encoding="utf-8-sig")


def detect_document_type(lines: list[str]) -> str:
    joined = "\n".join(lines[:50])
    if "策略" in joined:
        return "策略文档"
    if "详细设计" in joined or "设计说明" in joined:
        return "详细设计文档"
    if "需求" in joined:
        return "需求文档"
    if "测试" in joined:
        return "测试方案"
    return "未知文档"


def extract_headings(lines: list[str]) -> list[dict[str, str]]:
    headings: list[dict[str, str]] = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        markdown_match = re.match(r"^(#{1,6})\s+(.+)$", stripped)
        numbered_match = re.match(r"^(\d+(?:\.\d+)*)[\.、\s]+(.+)$", stripped)
        if markdown_match:
            headings.append({"级别": str(len(markdown_match.group(1))), "标题": markdown_match.group(2).strip()})
        elif numbered_match:
            level = numbered_match.group(1).count(".") + 1
            headings.append({"级别": str(level), "标题": stripped})
    return headings[:80]


def infer_reference_use(text: str) -> str:
    lowered = text.lower()
    if "格式" in text or "版式" in text or "样式" in text or "word" in lowered:
        return "格式参考"
    if "内容" in text or "规则" in text or "术语" in text:
        return "内容参考"
    return "结构参考"


def build_profile(path: Path, reference_use: str | None) -> dict[str, object]:
    content = read_text(path)
    lines = [line.strip() for line in content.splitlines() if line.strip()]
    use = reference_use or infer_reference_use(content[:1000])
    return {
        "参考文档路径": str(path),
        "文档类型": detect_document_type(lines),
        "参考用途": use,
        "允许复用内容": use in {"内容参考", "综合参考"},
        "允许复用格式": use in {"格式参考", "综合参考", "结构参考"},
        "允许复用术语": use in {"内容参考", "综合参考", "结构参考"},
        "章节结构": extract_headings(lines),
        "表格结构": [],
        "编号规则": [],
        "写作风格": [],
        "固定栏目": [],
        "禁止复用项": FORBIDDEN_ITEMS,
        "待确认项": [],
    }


def markdown_profile(profile: dict[str, object]) -> str:
    headings = profile.get("章节结构", [])
    heading_lines = []
    if isinstance(headings, list):
        for item in headings:
            if isinstance(item, dict):
                heading_lines.append(f"- L{item.get('级别', '')} {item.get('标题', '')}")
    if not heading_lines:
        heading_lines.append("- 未识别到明确标题层级")

    forbidden = profile.get("禁止复用项", [])
    forbidden_lines = [f"- {item}" for item in forbidden] if isinstance(forbidden, list) else ["- 待确认"]
    return "\n".join(
        [
            "# 参考文档结构画像",
            "",
            "## 基本信息",
            "",
            f"- 参考文档路径：{profile.get('参考文档路径', '')}",
            f"- 文档类型：{profile.get('文档类型', '')}",
            f"- 参考用途：{profile.get('参考用途', '')}",
            "",
            "## 章节结构",
            "",
            *heading_lines,
            "",
            "## 禁止复用项",
            "",
            *forbidden_lines,
            "",
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="生成参考文档画像到 state/。")
    parser.add_argument("reference_document", help="参考文档路径，支持 Markdown/TXT/DOCX")
    parser.add_argument("--reference-use", choices=["结构参考", "内容参考", "格式参考", "综合参考"], help="参考用途")
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parents[3]
    path = Path(args.reference_document)
    if not path.is_absolute():
        path = project_root / path
    profile = build_profile(path, args.reference_use)

    state_dir = project_root / "state"
    state_dir.mkdir(parents=True, exist_ok=True)

    json_path = state_dir / "reference-document-profile.json"
    md_path = state_dir / "参考文档结构画像.md"

    payload = json.dumps(profile, ensure_ascii=False, indent=2)
    json_path.write_text(payload, encoding="utf-8")
    md_path.write_text(markdown_profile(profile), encoding="utf-8")

    print(json_path)
    print(md_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
