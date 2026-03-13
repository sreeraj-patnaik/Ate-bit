from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User

from .models import UserProfile


class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={"class": "w-full rounded-lg border border-slate-300 px-3 py-2"}))

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for key in ("username", "password1", "password2"):
            self.fields[key].widget.attrs["class"] = "w-full rounded-lg border border-slate-300 px-3 py-2"


class SignInForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={"class": "w-full rounded-lg border border-slate-300 px-3 py-2"}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={"class": "w-full rounded-lg border border-slate-300 px-3 py-2"}))


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ["full_name", "college", "degree", "graduation_year", "skills", "bio"]
        widgets = {
            "full_name": forms.TextInput(attrs={"class": "w-full rounded-lg border border-slate-300 px-3 py-2"}),
            "college": forms.TextInput(attrs={"class": "w-full rounded-lg border border-slate-300 px-3 py-2"}),
            "degree": forms.TextInput(attrs={"class": "w-full rounded-lg border border-slate-300 px-3 py-2"}),
            "graduation_year": forms.NumberInput(attrs={"class": "w-full rounded-lg border border-slate-300 px-3 py-2"}),
            "skills": forms.Textarea(attrs={"rows": 3, "class": "w-full rounded-lg border border-slate-300 px-3 py-2"}),
            "bio": forms.Textarea(attrs={"rows": 4, "class": "w-full rounded-lg border border-slate-300 px-3 py-2"}),
        }
