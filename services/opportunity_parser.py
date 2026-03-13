import re
from datetime import datetime, timedelta

from django.db import transaction
from django.utils import timezone

from apps.opportunities.models import Opportunity
from utils.security import sanitize_message_text, validate_safe_url

from .llm_interface import OpportunityExtractor


class OpportunityParser:
    def __init__(self, extractor=None):
        self.extractor = extractor or OpportunityExtractor()

    def parse_message(self, message_text):
        cleaned_message = sanitize_message_text(message_text)
        extracted = self.extractor.extract(cleaned_message)
        extracted["deadline"] = self._normalize_deadline(extracted.get("deadline", ""))
        if extracted["deadline"] is None:
            extracted["deadline"] = self._normalize_deadline(cleaned_message)
        extracted["category"] = self._normalize_category(extracted.get("category", "other"))
        extracted["application_link"] = validate_safe_url(extracted.get("application_link", ""))
        extracted["summary"] = self.extractor.summarize(cleaned_message)
        return extracted

    @transaction.atomic
    def create_opportunity_from_message(self, message_text, user=None):
        cleaned_message = sanitize_message_text(message_text)
        structured = self.parse_message(cleaned_message)

        company = structured.get("company") or "Unknown"
        role = structured.get("role") or "General Opportunity"
        deadline = structured.get("deadline")

        existing = self._find_duplicate(company, role, deadline, user=user)
        if existing:
            self._merge_duplicate(existing, structured, cleaned_message)
            return existing

        return Opportunity.objects.create(
            owner=user,
            company=company,
            role=role,
            eligibility=structured.get("eligibility", ""),
            deadline=deadline,
            application_link=structured.get("application_link", ""),
            category=structured.get("category", Opportunity.Category.OTHER),
            summary=structured.get("summary", ""),
            description=cleaned_message,
            is_saved=False,
            status=Opportunity.Status.SAVED,
        )

    def _find_duplicate(self, company, role, deadline, user=None):
        if not deadline:
            return None
        return (
            Opportunity.objects.filter(
                owner=user,
                company__iexact=company.strip(),
                role__iexact=role.strip(),
                deadline=deadline,
            )
            .order_by("-created_at")
            .first()
        )

    def _merge_duplicate(self, existing, structured, cleaned_message):
        updated = False

        if not existing.eligibility and structured.get("eligibility"):
            existing.eligibility = structured["eligibility"]
            updated = True

        if not existing.application_link and structured.get("application_link"):
            existing.application_link = structured["application_link"]
            updated = True

        if not existing.summary and structured.get("summary"):
            existing.summary = structured["summary"]
            updated = True

        if cleaned_message and cleaned_message not in (existing.description or ""):
            joined = f"{existing.description}\n\n--- Duplicate Entry ---\n{cleaned_message}" if existing.description else cleaned_message
            existing.description = joined[:10000]
            updated = True

        existing.duplicate_count += 1
        updated = True

        if updated:
            existing.save()

    def _normalize_category(self, category_value):
        valid_categories = {choice[0] for choice in Opportunity.Category.choices}
        category_value = (category_value or "other").lower().strip()
        return category_value if category_value in valid_categories else Opportunity.Category.OTHER

    def _normalize_deadline(self, raw_deadline):
        raw_deadline = (raw_deadline or "").strip()
        if not raw_deadline:
            return None

        now = timezone.localdate()
        lowered = raw_deadline.lower().strip()

        direct_relative = {
            "today": 0,
            "tomorrow": 1,
            "next week": 7,
        }
        if lowered in direct_relative:
            return now + timedelta(days=direct_relative[lowered])
        if lowered == "next month":
            return now + timedelta(days=30)

        relative_match = re.search(
            r"\b(?:in|by|within|for|extended by)?\s*"
            r"(?P<num>\d+|one|two|three|four|five|six|seven|eight|nine|ten)\s*[- ]\s*"
            r"(?P<unit>day|days|hour|hours|week|weeks)\b",
            lowered,
        )
        if relative_match:
            quantity = self._word_to_int(relative_match.group("num"))
            unit = relative_match.group("unit")
            if quantity is not None:
                if unit.startswith("week"):
                    return now + timedelta(days=quantity * 7)
                if unit.startswith("hour"):
                    extra = 1 if quantity > 0 else 0
                    return now + timedelta(days=extra)
                return now + timedelta(days=quantity)

        raw_deadline = re.sub(r"(?<=\d)(st|nd|rd|th)\b", "", raw_deadline, flags=re.IGNORECASE)
        raw_deadline = raw_deadline.replace("'", " ")
        raw_deadline = raw_deadline.replace(",", " ")
        raw_deadline = re.sub(r"\s+", " ", raw_deadline).strip()
        raw_deadline = self._strip_deadline_labels(raw_deadline)
        raw_deadline = self._strip_time_portion(raw_deadline)
        raw_deadline = self._extract_date_candidate(raw_deadline)

        for fmt in ("%Y-%m-%d", "%B %d %Y", "%b %d %Y", "%d %B %Y", "%d %b %Y", "%d %B %y", "%d %b %y", "%b %d %y", "%B %d %y"):
            try:
                return datetime.strptime(raw_deadline, fmt).date()
            except ValueError:
                continue

        for fmt in ("%B %d", "%b %d", "%d %B", "%d %b"):
            try:
                parsed = datetime.strptime(raw_deadline, fmt).date().replace(year=now.year)
                if parsed < now:
                    return parsed.replace(year=parsed.year + 1)
                return parsed
            except ValueError:
                continue

        return None

    def _strip_deadline_labels(self, value):
        value = re.sub(
            r"^(?:deadline|due date|apply by|last date|closing date|registration closes?)\s*[:\-]?\s*",
            "",
            value,
            flags=re.IGNORECASE,
        )
        return value.strip()

    def _word_to_int(self, value):
        value = (value or "").lower()
        mapping = {
            "one": 1,
            "two": 2,
            "three": 3,
            "four": 4,
            "five": 5,
            "six": 6,
            "seven": 7,
            "eight": 8,
            "nine": 9,
            "ten": 10,
        }
        if value.isdigit():
            return int(value)
        return mapping.get(value)

    def _strip_time_portion(self, value):
        value = re.sub(
            r"\b(?:at|time)\b\s*[:\-]?\s*\d{1,2}[:.]\d{2}\s*(?:am|pm)?",
            "",
            value,
            flags=re.IGNORECASE,
        )
        value = re.sub(
            r"\b\d{1,2}[:.]\d{2}\s*(?:am|pm)\b",
            "",
            value,
            flags=re.IGNORECASE,
        )
        return re.sub(r"\s+", " ", value).strip()

    def _extract_date_candidate(self, value):
        patterns = [
            r"\b\d{4}-\d{2}-\d{2}\b",
            r"\b\d{1,2}\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\s+\d{2,4}\b",
            r"\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\s+\d{1,2}\s+\d{2,4}\b",
            r"\b\d{1,2}\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\b",
            r"\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\s+\d{1,2}\b",
        ]
        for pattern in patterns:
            match = re.search(pattern, value, flags=re.IGNORECASE)
            if match:
                return match.group(0).strip()
        return value
