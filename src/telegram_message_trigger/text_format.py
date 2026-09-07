import html
import re

_TAG_RE = re.compile(r"<[^>]+>")


def strip_html_preview(text: str) -> str:
    return html.unescape(_TAG_RE.sub("", text))
