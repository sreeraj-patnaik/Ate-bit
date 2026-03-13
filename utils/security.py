import re

from django.core.validators import URLValidator
from django.core.exceptions import ValidationError
from django.utils.html import strip_tags


SUSPICIOUS_DOMAINS = {"bit.ly", "tinyurl.com"}


def sanitize_message_text(value):
    cleaned = strip_tags(value or "").replace("\r\n", "\n").replace("\r", "\n")
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in cleaned.split("\n")]
    return "\n".join(line for line in lines if line).strip()


def validate_safe_url(value):
    if not value:
        return ""

    candidate = value.strip()
    validator = URLValidator()
    try:
        validator(candidate)
    except ValidationError:
        return ""

    lowered = candidate.lower()
    if any(domain in lowered for domain in SUSPICIOUS_DOMAINS):
        return ""
    return candidate
