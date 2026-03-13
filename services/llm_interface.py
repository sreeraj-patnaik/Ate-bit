import json
import os
import re

try:
    from groq import Groq
except ImportError:  # pragma: no cover - fallback when dependency is not installed
    Groq = None


class OpportunityExtractor:
    """LLM interface boundary.

    Replace/extend only this class to change external AI provider behavior.
    """

    def __init__(self, api_key=None, model=None):
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        self.model = model or os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
        self.last_source = "mock"
        self.last_error = ""

    def extract(self, message_text):
        if self.api_key and Groq:
            groq_extracted = self._extract_with_groq(message_text)
            if groq_extracted:
                self.last_source = "groq"
                return groq_extracted
        self.last_source = "mock"
        return self._extract_with_mock_logic(message_text)

    def summarize(self, message_text):
        if self.api_key and Groq:
            summary = self._summarize_with_groq(message_text)
            if summary:
                self.last_source = "groq"
                return summary
        self.last_source = "mock"
        return self._summarize_with_mock_logic(message_text)

    def _extract_with_groq(self, message_text):
        try:
            client = Groq(api_key=self.api_key)
            completion = client.chat.completions.create(
                model=self.model,
                temperature=0,
                response_format={"type": "json_object"},
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Extract opportunity fields from text and return JSON with keys: "
                            "company, role, deadline, eligibility, application_link, category. "
                            "Use empty string for unknown values. "
                            "Deadline can be an absolute date (e.g., 2026-05-10, May 10, 10 May) "
                            "or relative phrase (e.g., in 3 days, two days, tomorrow, next week). "
                            "Category must be one of internship, job, hackathon, scholarship, workshop, other."
                        ),
                    },
                    {"role": "user", "content": message_text},
                ],
            )
            raw = completion.choices[0].message.content or "{}"
            parsed = json.loads(raw)
            return {
                "company": (parsed.get("company") or "").strip(),
                "role": (parsed.get("role") or "").strip(),
                "deadline": (parsed.get("deadline") or "").strip(),
                "eligibility": (parsed.get("eligibility") or "").strip(),
                "application_link": (parsed.get("application_link") or "").strip(),
                "category": (parsed.get("category") or "").strip().lower(),
            }
        except Exception as exc:
            self.last_error = f"Groq extraction failed; fallback used. Error: {exc}"
            return None

    def _summarize_with_groq(self, message_text):
        try:
            client = Groq(api_key=self.api_key)
            completion = client.chat.completions.create(
                model=self.model,
                temperature=0.2,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Summarize the opportunity message in 2-3 short lines: "
                            "title/context, eligibility if present, and deadline if present."
                        ),
                    },
                    {"role": "user", "content": message_text},
                ],
            )
            text = completion.choices[0].message.content or ""
            return text.strip()
        except Exception as exc:
            self.last_error = f"Groq summarization failed; fallback used. Error: {exc}"
            return None

    def _extract_with_mock_logic(self, message_text):
        text = message_text or ""
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        headline = lines[0] if lines else ""

        extracted = {
            "company": self._extract_company(text, headline),
            "role": self._extract_role(text, headline),
            "deadline": self._extract_deadline_text(text),
            "eligibility": self._extract_field(text, r"eligibility\s*[:\-]\s*(.+)"),
            "application_link": self._extract_application_link(text),
            "category": self._extract_category(text),
        }

        return extracted

    def _summarize_with_mock_logic(self, message_text):
        lines = [line.strip() for line in (message_text or "").splitlines() if line.strip()]
        return "\n".join(lines[:3])[:400]

    def _extract_deadline_text(self, text):
        patterns = [
            r"(?:deadline|due date|apply by|last date|closing date|registration closes?)\s*[:\-]\s*(.+)",
            r"(?:deadline|due date|apply by|last date|closing date|registration closes?)\s+(.+)",
            r"(?:extended|extension).{0,40}\bby\s+((?:\d+|one|two|three|four|five|six|seven|eight|nine|ten)\s*[- ]\s*(?:day|days|hour|hours|week|weeks))\b",
            r"\b((?:\d+|one|two|three|four|five|six|seven|eight|nine|ten)\s*-\s*(?:day|days|hour|hours|week|weeks))\b",
            r"\bin\s+((?:\d+|one|two|three|four|five|six|seven|eight|nine|ten)\s+(?:day|days|hour|hours|week|weeks))\b",
            r"\b(tomorrow|today|next week|next month)\b",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, flags=re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return ""

    def _extract_application_link(self, text):
        labeled = self._extract_field(text, r"(?:apply|application|register)\s*[:\-]\s*(https?://\S+|\S+)")
        if labeled:
            return labeled

        generic_url = re.search(r"https?://[^\s)]+", text, flags=re.IGNORECASE)
        return generic_url.group(0).strip() if generic_url else ""

    def _extract_field(self, text, pattern):
        match = re.search(pattern, text, flags=re.IGNORECASE)
        return match.group(1).strip() if match else ""

    def _extract_company(self, text, headline):
        at_match = re.search(r"(?:at|@)\s+([A-Z][\w&\-. ]+)", text)
        if at_match:
            return at_match.group(1).strip()

        by_match = re.search(r"company\s*[:\-]\s*(.+)", text, flags=re.IGNORECASE)
        if by_match:
            return by_match.group(1).strip()

        if headline:
            return headline.split()[0]
        return "Unknown"

    def _extract_role(self, text, headline):
        role_match = re.search(r"role\s*[:\-]\s*(.+)", text, flags=re.IGNORECASE)
        if role_match:
            return role_match.group(1).strip()
        return headline or "General Opportunity"

    def _extract_category(self, text):
        lowered = text.lower()
        if "hackathon" in lowered:
            return "hackathon"
        if "intern" in lowered:
            return "internship"
        if "scholarship" in lowered:
            return "scholarship"
        if "workshop" in lowered or "bootcamp" in lowered or "webinar" in lowered:
            return "workshop"
        if "job" in lowered or "full-time" in lowered or "full time" in lowered or "hiring" in lowered:
            return "job"
        return "other"
