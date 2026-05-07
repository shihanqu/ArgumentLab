import mailbox
import re
from dataclasses import dataclass, field
from datetime import datetime
from email import policy
from email.message import EmailMessage
from email.parser import BytesParser
from email.utils import getaddresses, parsedate_to_datetime
from pathlib import Path

from bs4 import BeautifulSoup
from dateutil import parser as date_parser


LEGAL_TAG_KEYWORDS = {
    "notice": ["notice", "notify", "notification", "object", "objection"],
    "waiver": ["waive", "waiver", "reserved rights", "reservation of rights"],
    "modification": ["modify", "modification", "amend", "change order", "revised terms"],
    "repudiation": ["repudiate", "will not perform", "refuse", "termination"],
    "delay": ["delay", "late", "deadline", "extension"],
    "reliance": ["relied", "reliance", "based on your", "because you"],
    "damages": ["damages", "loss", "cost", "invoice", "mitigate"],
    "admission": ["admit", "acknowledge", "confirmed", "agree"],
}


@dataclass
class ParsedEmail:
    thread_id: str
    message_id: str | None = None
    in_reply_to: str | None = None
    sender: str | None = None
    recipients: list[str] = field(default_factory=list)
    cc: list[str] = field(default_factory=list)
    bcc: list[str] = field(default_factory=list)
    subject: str | None = None
    original_timestamp: str | None = None
    normalized_timestamp: datetime | None = None
    detected_timezone: str | None = None
    raw_body: str | None = None
    normalized_body: str | None = None
    quoted_text: str | None = None
    attachments: list[dict] = field(default_factory=list)
    legal_event_tags: list[str] = field(default_factory=list)
    duplicate_quote_warning: bool = False


def parse_email_file(path: Path, filename: str) -> list[ParsedEmail]:
    suffix = path.suffix.lower()
    if suffix == ".mbox":
        return parse_mbox(path)
    if suffix == ".eml":
        message = BytesParser(policy=policy.default).parsebytes(path.read_bytes())
        return [parse_message(message)]
    text = path.read_text(errors="ignore")
    return parse_copied_thread(text=text, subject=filename)


def parse_mbox(path: Path) -> list[ParsedEmail]:
    parsed: list[ParsedEmail] = []
    box = mailbox.mbox(path)
    for item in box:
        message = EmailMessage(policy=policy.default)
        for key, value in item.items():
            message[key] = value
        payload = item.get_payload()
        if isinstance(payload, list):
            message.set_content("\n".join(str(part.get_payload()) for part in payload))
        else:
            message.set_content(str(payload))
        parsed.append(parse_message(message))
    return parsed


def parse_message(message: EmailMessage) -> ParsedEmail:
    body = extract_body(message)
    normalized_body, quoted_text, duplicate_warning = strip_quoted_text(body)
    timestamp, timezone = normalize_timestamp(message.get("date"))
    subject = message.get("subject")
    message_id = message.get("message-id")
    thread_seed = message.get("in-reply-to") or message_id or subject or "email-thread"
    attachments = []
    for part in message.walk():
        filename = part.get_filename()
        if filename:
            attachments.append({"filename": filename, "content_type": part.get_content_type()})
    return ParsedEmail(
        thread_id=normalize_thread_id(thread_seed),
        message_id=message_id,
        in_reply_to=message.get("in-reply-to"),
        sender=first_address(message.get("from")),
        recipients=parse_addresses(message.get("to")),
        cc=parse_addresses(message.get("cc")),
        bcc=parse_addresses(message.get("bcc")),
        subject=subject,
        original_timestamp=message.get("date"),
        normalized_timestamp=timestamp,
        detected_timezone=timezone,
        raw_body=body,
        normalized_body=normalized_body,
        quoted_text=quoted_text,
        attachments=attachments,
        legal_event_tags=detect_legal_tags(normalized_body),
        duplicate_quote_warning=duplicate_warning,
    )


def extract_body(message: EmailMessage) -> str:
    if message.is_multipart():
        plain = []
        html = []
        for part in message.walk():
            content_type = part.get_content_type()
            disposition = part.get_content_disposition()
            if disposition == "attachment":
                continue
            try:
                content = part.get_content()
            except Exception:
                continue
            if content_type == "text/plain":
                plain.append(str(content))
            elif content_type == "text/html":
                html.append(html_to_text(str(content)))
        return "\n".join(plain or html)
    try:
        content = message.get_content()
    except Exception:
        content = message.get_payload(decode=True) or b""
        if isinstance(content, bytes):
            return content.decode(errors="ignore")
    if message.get_content_type() == "text/html":
        return html_to_text(str(content))
    return str(content)


def html_to_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style"]):
        tag.extract()
    return soup.get_text("\n")


def parse_copied_thread(text: str, subject: str | None = None) -> list[ParsedEmail]:
    chunks = split_copied_thread(text)
    parsed: list[ParsedEmail] = []
    for idx, chunk in enumerate(chunks):
        headers, body = parse_loose_headers(chunk)
        normalized_body, quoted_text, duplicate_warning = strip_quoted_text(body)
        raw_timestamp = headers.get("date") or headers.get("sent")
        timestamp, timezone = normalize_timestamp(raw_timestamp)
        parsed.append(
            ParsedEmail(
                thread_id=normalize_thread_id(headers.get("thread-id") or headers.get("subject") or subject or "copied-thread"),
                message_id=headers.get("message-id") or f"copied-{idx + 1}",
                in_reply_to=headers.get("in-reply-to"),
                sender=headers.get("from"),
                recipients=parse_addresses(headers.get("to")),
                cc=parse_addresses(headers.get("cc")),
                bcc=parse_addresses(headers.get("bcc")),
                subject=headers.get("subject") or subject,
                original_timestamp=raw_timestamp,
                normalized_timestamp=timestamp,
                detected_timezone=timezone,
                raw_body=body,
                normalized_body=normalized_body,
                quoted_text=quoted_text,
                attachments=[],
                legal_event_tags=detect_legal_tags(normalized_body),
                duplicate_quote_warning=duplicate_warning,
            )
        )
    return sorted(parsed, key=lambda item: item.normalized_timestamp or datetime.max)


def split_copied_thread(text: str) -> list[str]:
    separators = [
        r"\n(?=From:\s.+\n(?:Sent|Date):)",
        r"\n(?=On .+ wrote:)",
        r"\n-{5,}\s*Original Message\s*-{5,}\n",
    ]
    chunks = [text]
    for separator in separators:
        next_chunks: list[str] = []
        for chunk in chunks:
            next_chunks.extend([part for part in re.split(separator, chunk, flags=re.IGNORECASE) if part.strip()])
        chunks = next_chunks
    return chunks[:100]


def parse_loose_headers(chunk: str) -> tuple[dict[str, str], str]:
    headers: dict[str, str] = {}
    body_lines: list[str] = []
    in_headers = True
    for line in chunk.splitlines():
        match = re.match(r"^(from|to|cc|bcc|subject|date|sent|message-id|in-reply-to|thread-id):\s*(.*)$", line, re.IGNORECASE)
        if in_headers and match:
            headers[match.group(1).lower()] = match.group(2).strip()
            continue
        if line.strip() == "" and in_headers:
            in_headers = False
            continue
        in_headers = False
        body_lines.append(line)
    return headers, "\n".join(body_lines).strip() or chunk.strip()


def strip_quoted_text(body: str | None) -> tuple[str, str | None, bool]:
    if not body:
        return "", None, False
    lines = body.splitlines()
    normalized: list[str] = []
    quoted: list[str] = []
    quote_mode = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith(">") or re.match(r"^On .+ wrote:$", stripped, re.IGNORECASE) or "Original Message" in stripped:
            quote_mode = True
        if quote_mode:
            quoted.append(line)
        else:
            normalized.append(line)
    normalized_text = "\n".join(normalized).strip()
    quoted_text = "\n".join(quoted).strip() or None
    return normalized_text or body.strip(), quoted_text, bool(quoted_text)


def normalize_timestamp(value: str | None) -> tuple[datetime | None, str | None]:
    if not value:
        return None, None
    try:
        dt = parsedate_to_datetime(value)
    except Exception:
        try:
            dt = date_parser.parse(value, fuzzy=True)
        except Exception:
            return None, None
    timezone = dt.tzname() if dt.tzinfo else None
    return dt.replace(tzinfo=None), timezone


def parse_addresses(value: str | None) -> list[str]:
    if not value:
        return []
    return [email or name for name, email in getaddresses([value]) if email or name]


def first_address(value: str | None) -> str | None:
    parsed = parse_addresses(value)
    return parsed[0] if parsed else value


def normalize_thread_id(value: str) -> str:
    clean = re.sub(r"^(re|fw|fwd):\s*", "", value.strip(), flags=re.IGNORECASE)
    clean = re.sub(r"[^a-zA-Z0-9_.@-]+", "-", clean).strip("-").lower()
    return clean[:180] or "email-thread"


def detect_legal_tags(text: str | None) -> list[str]:
    if not text:
        return []
    lower = text.lower()
    tags = [tag for tag, keywords in LEGAL_TAG_KEYWORDS.items() if any(keyword in lower for keyword in keywords)]
    return tags[:8]

