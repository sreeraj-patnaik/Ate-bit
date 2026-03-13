from django import forms

from .models import Opportunity, OpportunityNote


class OpportunityForm(forms.ModelForm):
    class Meta:
        model = Opportunity
        fields = [
            "company",
            "role",
            "eligibility",
            "deadline",
            "application_link",
            "category",
            "summary",
            "description",
            "is_saved",
            "status",
        ]
        widgets = {
            "company": forms.TextInput(attrs={"class": "w-full rounded-lg border border-slate-300 px-3 py-2"}),
            "role": forms.TextInput(attrs={"class": "w-full rounded-lg border border-slate-300 px-3 py-2"}),
            "eligibility": forms.TextInput(attrs={"class": "w-full rounded-lg border border-slate-300 px-3 py-2"}),
            "deadline": forms.DateInput(attrs={"type": "date", "class": "w-full rounded-lg border border-slate-300 px-3 py-2"}),
            "application_link": forms.URLInput(attrs={"class": "w-full rounded-lg border border-slate-300 px-3 py-2"}),
            "category": forms.Select(attrs={"class": "w-full rounded-lg border border-slate-300 px-3 py-2"}),
            "summary": forms.Textarea(attrs={"rows": 3, "class": "w-full rounded-lg border border-slate-300 px-3 py-2"}),
            "description": forms.Textarea(attrs={"rows": 5, "class": "w-full rounded-lg border border-slate-300 px-3 py-2"}),
            "is_saved": forms.CheckboxInput(attrs={"class": "rounded border-slate-300"}),
            "status": forms.Select(attrs={"class": "w-full rounded-lg border border-slate-300 px-3 py-2"}),
        }


class OpportunityNoteForm(forms.ModelForm):
    class Meta:
        model = OpportunityNote
        fields = ["content"]
        widgets = {
            "content": forms.TextInput(
                attrs={
                    "class": "w-full rounded-lg border border-slate-300 px-3 py-2",
                    "placeholder": "e.g. prepare resume / ask referral / apply later",
                }
            )
        }
