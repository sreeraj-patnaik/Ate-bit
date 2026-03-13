from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.urls import reverse

from services.notification_service import send_immediate_notifications
from services.ocr_service import extract_text_from_image
from services.opportunity_parser import OpportunityParser
from services.task_queue import enqueue_extraction

from .forms import MessageSubmissionForm


@login_required
def submit_opportunity(request):
    extracted_preview = None

    if request.method == "POST":
        form = MessageSubmissionForm(request.POST, request.FILES)
        if form.is_valid():
            message_text = (form.cleaned_data.get("message_text") or "").strip()
            image_file = form.cleaned_data.get("image_file")
            ocr_text = ""

            if image_file:
                ocr_text, ocr_error = extract_text_from_image(image_file)
                if ocr_error:
                    messages.warning(request, ocr_error)
                elif ocr_text:
                    messages.info(request, "OCR text extracted from uploaded image.")

            combined_text = "\n\n".join(part for part in [message_text, ocr_text] if part).strip()
            if not combined_text:
                messages.error(request, "No extractable text found from input.")
                return render(
                    request,
                    "extraction/submit_opportunity.html",
                    {"form": form, "extracted_preview": extracted_preview},
                )

            enqueue_extraction({"message_preview": combined_text[:120]})

            parser = OpportunityParser()
            extracted_preview = parser.parse_message(combined_text)
            opportunity = parser.create_opportunity_from_message(combined_text, user=request.user)
            send_immediate_notifications(opportunity)

            if opportunity.duplicate_count > 0:
                messages.info(request, "Duplicate detected. Existing opportunity record was updated.")
            else:
                messages.success(request, "Opportunity extracted and stored successfully.")
            detail_url = reverse("opportunity_detail", kwargs={"pk": opportunity.pk})
            if opportunity.deadline:
                return redirect(f"{detail_url}?open_calendar=1")
            return redirect(detail_url)
    else:
        form = MessageSubmissionForm()

    return render(
        request,
        "extraction/submit_opportunity.html",
        {"form": form, "extracted_preview": extracted_preview},
    )
