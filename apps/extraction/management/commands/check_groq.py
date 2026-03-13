import json
import os

from django.core.management.base import BaseCommand

from services.llm_interface import Groq, OpportunityExtractor
from services.opportunity_parser import OpportunityParser


class Command(BaseCommand):
    help = "Validate Groq integration by running OpportunityExtractor on sample text."

    def add_arguments(self, parser):
        parser.add_argument(
            "--message",
            type=str,
            default=(
                "Google STEP Internship\n"
                "Eligibility: 2nd year\n"
                "Deadline: May 10\n"
                "Apply: https://example.com/apply"
            ),
            help="Sample opportunity message to test extraction.",
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Checking Groq integration..."))

        api_key = os.getenv("GROQ_API_KEY", "")
        model = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

        if not api_key:
            self.stdout.write(
                self.style.WARNING("GROQ_API_KEY is not set. Falling back to mock extraction.")
            )
        else:
            masked = f"{api_key[:4]}...{api_key[-4:]}" if len(api_key) > 8 else "***"
            self.stdout.write(self.style.SUCCESS(f"GROQ_API_KEY found: {masked}"))

        if Groq is None:
            self.stdout.write(
                self.style.WARNING("groq package is not installed. Using mock extraction.")
            )
        else:
            self.stdout.write(self.style.SUCCESS(f"groq package available. Model: {model}"))

        message = options["message"]
        extractor = OpportunityExtractor()
        result = extractor.extract(message)
        parser = OpportunityParser(extractor=extractor)
        normalized = parser.parse_message(message)

        self.stdout.write(f"\nExtraction source: {extractor.last_source}")

        self.stdout.write("\nExtraction result:")
        self.stdout.write(json.dumps(result, indent=2))
        self.stdout.write("\nNormalized parser result:")
        self.stdout.write(json.dumps({**normalized, "deadline": str(normalized.get("deadline"))}, indent=2))

        used_mock = extractor.last_source != "groq"
        if used_mock:
            if extractor.last_error:
                self.stdout.write(self.style.WARNING(f"\nReason: {extractor.last_error}"))
            self.stdout.write(
                self.style.WARNING(
                    "\ncheck_groq completed with mock extraction."
                )
            )
            return

        if any(value for value in result.values()):
            self.stdout.write(self.style.SUCCESS("\ncheck_groq succeeded with live Groq extraction."))
        else:
            self.stdout.write(
                self.style.WARNING(
                    "\nGroq call may have failed or returned empty values. Check API key/model and retry."
                )
            )
