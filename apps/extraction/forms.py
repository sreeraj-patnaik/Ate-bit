from django import forms


class MessageSubmissionForm(forms.Form):
    message_text = forms.CharField(
        label="Opportunity Message",
        required=False,
        widget=forms.Textarea(
            attrs={
                "rows": 12,
                "class": "w-full rounded-lg border border-slate-300 px-3 py-2",
                "placeholder": "Paste internship, job, or hackathon message here...",
            }
        ),
    )
    image_file = forms.ImageField(
        label="Screenshot/Image (OCR)",
        required=False,
        widget=forms.ClearableFileInput(
            attrs={
                "class": "w-full rounded-lg border border-slate-300 px-3 py-2",
                "accept": "image/png,image/jpeg,image/jpg,image/webp",
            }
        ),
    )

    def clean(self):
        cleaned_data = super().clean()
        text = (cleaned_data.get("message_text") or "").strip()
        image = cleaned_data.get("image_file")
        if not text and not image:
            raise forms.ValidationError("Provide message text or upload an image for OCR.")
        return cleaned_data
