#!/usr/bin/env python3
"""Convert requirement documents to PDF.

Markdown/TXT/HTML are printed through Edge or Chrome. DOCX conversion uses
LibreOffice when available, then Microsoft Word COM through PowerShell.
"""

from __future__ import annotations

import argparse
import html
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


BROWSER_CANDIDATES = [
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
]


def read_text(path: Path) -> str:
    for encoding in ("utf-8-sig", "utf-8", "gb18030"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    raise RuntimeError(f"无法识别文本编码: {path}")


def clean_inline(text: str) -> str:
    text = html.escape(text.strip())
    text = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1", text)
    return text


def markdown_to_html(markdown: str, title: str) -> str:
    lines = markdown.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    out: list[str] = []
    in_ul = False
    in_code = False
    code_lines: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith("```"):
            if in_code:
                out.append(f"<pre>{html.escape(chr(10).join(code_lines))}</pre>")
                code_lines = []
                in_code = False
            else:
                in_code = True
            i += 1
            continue
        if in_code:
            code_lines.append(lines[i])
            i += 1
            continue
        if not line:
            if in_ul:
                out.append("</ul>")
                in_ul = False
            i += 1
            continue
        if line.startswith("|") and line.endswith("|") and i + 1 < len(lines) and is_separator(lines[i + 1]):
            if in_ul:
                out.append("</ul>")
                in_ul = False
            table_html, i = parse_table(lines, i)
            out.append(table_html)
            continue
        heading = re.match(r"^(#{1,6})\s+(.+)$", line)
        if heading:
            if in_ul:
                out.append("</ul>")
                in_ul = False
            level = min(len(heading.group(1)), 4)
            out.append(f"<h{level}>{clean_inline(heading.group(2))}</h{level}>")
        elif re.match(r"^[-*+]\s+", line):
            if not in_ul:
                out.append("<ul>")
                in_ul = True
            out.append(f"<li>{clean_inline(re.sub(r'^[-*+]\\s+', '', line))}</li>")
        elif line == "---":
            out.append("<hr>")
        else:
            if in_ul:
                out.append("</ul>")
                in_ul = False
            out.append(f"<p>{clean_inline(line)}</p>")
        i += 1
    if in_ul:
        out.append("</ul>")
    css = """
@page { size: A4; margin: 18mm 16mm; }
body { font-family: "Microsoft YaHei", "Noto Sans SC", "SimSun", sans-serif; color: #222; line-height: 1.55; font-size: 11pt; }
h1 { font-size: 22pt; border-bottom: 1px solid #999; padding-bottom: 8px; }
h2 { font-size: 16pt; margin-top: 22px; }
h3 { font-size: 13pt; margin-top: 18px; }
h4 { font-size: 12pt; margin-top: 14px; }
table { width: 100%; border-collapse: collapse; margin: 10px 0 14px; table-layout: fixed; }
th, td { border: 1px solid #999; padding: 5px 7px; vertical-align: top; word-break: break-word; }
th { background: #f0f2f5; font-weight: 700; }
code, pre { font-family: Consolas, "Microsoft YaHei", monospace; background: #f5f5f5; }
pre { padding: 10px; white-space: pre-wrap; }
"""
    return f"<!doctype html><html><head><meta charset=\"utf-8\"><title>{html.escape(title)}</title><style>{css}</style></head><body>{''.join(out)}</body></html>"


def is_separator(line: str) -> bool:
    cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
    return bool(cells) and all(re.fullmatch(r":?-{3,}:?", cell or "") for cell in cells)


def parse_table(lines: list[str], start: int) -> tuple[str, int]:
    rows: list[list[str]] = []
    i = start
    while i < len(lines) and lines[i].strip().startswith("|") and lines[i].strip().endswith("|"):
        if i == start + 1 and is_separator(lines[i]):
            i += 1
            continue
        rows.append([clean_inline(cell) for cell in lines[i].strip().strip("|").split("|")])
        i += 1
    html_rows = []
    for idx, row in enumerate(rows):
        tag = "th" if idx == 0 else "td"
        html_rows.append("<tr>" + "".join(f"<{tag}>{cell}</{tag}>" for cell in row) + "</tr>")
    return "<table>" + "".join(html_rows) + "</table>", i


def find_browser() -> Path | None:
    for candidate in BROWSER_CANDIDATES:
        path = Path(candidate)
        if path.exists():
            return path
    for name in ("msedge", "chrome", "chromium"):
        found = shutil.which(name)
        if found:
            return Path(found)
    return None


def html_to_pdf(html_file: Path, output: Path) -> None:
    browser = find_browser()
    if not browser:
        raise RuntimeError("未找到 Edge/Chrome，无法将 Markdown/HTML 打印为 PDF。")
    output.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        str(browser),
        "--headless=new",
        "--disable-gpu",
        "--no-first-run",
        f"--print-to-pdf={output}",
        html_file.resolve().as_uri(),
    ]
    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=90,
    )
    if result.returncode != 0 or not output.exists():
        raise RuntimeError(f"浏览器打印 PDF 失败: {result.stderr or result.stdout}")


def markdown_or_text_to_pdf(source: Path, output: Path) -> None:
    markdown = read_text(source)
    with tempfile.TemporaryDirectory(prefix="req-pdf-") as tmp:
        html_file = Path(tmp) / f"{source.stem}.html"
        html_file.write_text(markdown_to_html(markdown, source.stem), encoding="utf-8")
        html_to_pdf(html_file, output)


def html_file_to_pdf(source: Path, output: Path) -> None:
    html_to_pdf(source, output)


def convert_docx_with_soffice(source: Path, output: Path) -> bool:
    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    if not soffice:
        for candidate in (r"C:\Program Files\LibreOffice\program\soffice.exe", r"C:\Program Files (x86)\LibreOffice\program\soffice.exe"):
            if Path(candidate).exists():
                soffice = candidate
                break
    if not soffice:
        return False
    output.parent.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        [soffice, "--headless", "--convert-to", "pdf", "--outdir", str(output.parent), str(source)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=120,
    )
    produced = output.parent / f"{source.stem}.pdf"
    if result.returncode == 0 and produced.exists():
        if produced.resolve() != output.resolve():
            if output.exists():
                output.unlink()
            produced.replace(output)
        return True
    return False


def convert_docx_with_word_com(source: Path, output: Path) -> bool:
    output.parent.mkdir(parents=True, exist_ok=True)
    script = f"""
$ErrorActionPreference = 'Stop'
$word = New-Object -ComObject Word.Application
$word.Visible = $false
$doc = $word.Documents.Open('{str(source.resolve()).replace("'", "''")}')
$doc.SaveAs([ref]'{str(output.resolve()).replace("'", "''")}', [ref]17)
$doc.Close()
$word.Quit()
"""
    result = subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", script],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=120,
    )
    return result.returncode == 0 and output.exists()


def docx_to_pdf(source: Path, output: Path) -> None:
    if convert_docx_with_soffice(source, output):
        return
    if convert_docx_with_word_com(source, output):
        return
    raise RuntimeError("DOCX 转 PDF 需要 LibreOffice 或 Microsoft Word；当前环境未能调用成功。")


def convert(source: Path, output: Path) -> None:
    suffix = source.suffix.lower()
    if suffix in {".md", ".markdown", ".txt"}:
        markdown_or_text_to_pdf(source, output)
    elif suffix in {".html", ".htm"}:
        html_file_to_pdf(source, output)
    elif suffix == ".docx":
        docx_to_pdf(source, output)
    elif suffix == ".pdf":
        output.parent.mkdir(parents=True, exist_ok=True)
        if source.resolve() != output.resolve():
            shutil.copy2(source, output)
    else:
        raise RuntimeError(f"暂不支持转 PDF 的文件类型: {suffix}")


def main() -> int:
    parser = argparse.ArgumentParser(description="将需求文档转换为 PDF")
    parser.add_argument("input", help="输入文件路径，支持 md/txt/html/docx/pdf")
    parser.add_argument("-o", "--output", help="输出 PDF 路径；默认与输入同名")
    args = parser.parse_args()

    source = Path(args.input)
    if not source.exists():
        print(f"输入文件不存在: {source}", file=sys.stderr)
        return 1
    output = Path(args.output) if args.output else source.with_suffix(".pdf")
    try:
        convert(source, output)
    except Exception as exc:  # noqa: BLE001
        print(f"转换失败: {exc}", file=sys.stderr)
        return 2
    print(str(output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
