import re
import zipfile
from html import unescape
from pathlib import Path
from xml.etree import ElementTree

from bs4 import BeautifulSoup
from pypdf import PdfReader

from app.schemas import DocumentType


DOC_TYPE_KEYWORDS: list[tuple[DocumentType, list[str]]] = [
    ("opposition", ["opposition", "oppose", "memorandum in opposition"]),
    ("reply", ["reply brief", "reply memorandum", "reply in support"]),
    ("motion", ["notice of motion", "motion to", "memorandum of law", "brief in support"]),
    ("pleading", ["complaint", "answer", "counterclaim", "crossclaim", "petition"]),
    ("contract", ["agreement", "contract", "statement of work", "sow", "msa", "lease"]),
    ("transcript", ["transcript", "deposition", "proceedings"]),
    ("authority", ["v.", "u.s.", "f.3d", "f. supp", "n.y.", "cal.", "statute", "code §"]),
    ("email", ["from:", "sent:", "to:", "subject:", "message-id"]),
    ("correspondence", ["dear ", "sincerely", "letter", "demand"]),
    ("exhibit", ["exhibit", "ex. "]),
]


def extract_text(path: Path, mime_type: str | None, filename: str) -> str:
    suffix = path.suffix.lower()
    try:
        if suffix == ".pdf":
            return extract_pdf(path)
        if suffix == ".docx":
            return extract_docx(path)
        if suffix in {".html", ".htm"}:
            return html_to_text(path.read_text(errors="ignore"))
        if suffix in {".txt", ".md", ".csv", ".eml", ".mbox", ".log"}:
            return path.read_text(errors="ignore")
        return path.read_text(errors="ignore")
    except UnicodeDecodeError:
        return ""
    except Exception as exc:
        return f"[text extraction failed for {filename}: {exc.__class__.__name__}]"


def extract_pdf(path: Path) -> str:
    reader = PdfReader(str(path))
    pages: list[str] = []
    for index, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        if text.strip():
            pages.append(f"[page {index}]\n{text}")
    return "\n\n".join(pages)


def extract_docx(path: Path) -> str:
    with zipfile.ZipFile(path) as archive:
        xml = archive.read("word/document.xml")
    root = ElementTree.fromstring(xml)
    namespace = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    paragraphs: list[str] = []
    for paragraph in root.findall(".//w:p", namespace):
        parts = [node.text or "" for node in paragraph.findall(".//w:t", namespace)]
        if parts:
            paragraphs.append("".join(parts))
    return "\n".join(paragraphs)


def html_to_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style"]):
        tag.extract()
    return unescape(soup.get_text("\n"))


def classify_document(filename: str, text: str) -> tuple[DocumentType, str]:
    haystack = f"{filename}\n{text[:5000]}".lower()
    for doc_type, keywords in DOC_TYPE_KEYWORDS:
        if any(keyword in haystack for keyword in keywords):
            return doc_type, f"Matched {doc_type} indicators: {', '.join([kw for kw in keywords if kw in haystack][:4])}."
    return "other", "No strong local classification signal found."


def create_source_refs(text: str) -> list[dict]:
    refs: list[dict] = []
    page_matches = list(re.finditer(r"\[page\s+(\d+)\]", text, re.IGNORECASE))
    if page_matches:
        for idx, match in enumerate(page_matches):
            next_start = page_matches[idx + 1].start() if idx + 1 < len(page_matches) else len(text)
            snippet = text[match.end() : min(match.end() + 700, next_start)].strip()
            refs.append({"page": int(match.group(1)), "quote": snippet[:500]})
    elif text.strip():
        refs.append({"page": None, "quote": text.strip()[:500]})
    return refs[:25]


def find_citations(text: str) -> list[str]:
    patterns = [
        r"\b\d+\s+U\.S\.\s+\d+\b",
        r"\b\d+\s+F\.\s?(?:2d|3d|4th|Supp\.?\s?\d*d?)\s+\d+\b",
        r"\b\d+\s+N\.Y\.?\s?3d\s+\d+\b",
        r"\b[A-Z][A-Za-z0-9&'. -]+\s+v\.\s+[A-Z][A-Za-z0-9&'. -]+,\s+\d+[^.;\n]+",
        r"\b[A-Z][A-Za-z0-9&'. -]+\s+§\s*[\w.-]+",
    ]
    citations: list[str] = []
    for pattern in patterns:
        citations.extend(re.findall(pattern, text))
    seen: set[str] = set()
    unique = []
    for citation in citations:
        clean = citation.strip()
        if clean not in seen:
            seen.add(clean)
            unique.append(clean)
    return unique[:50]

