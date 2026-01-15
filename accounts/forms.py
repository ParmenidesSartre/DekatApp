from allauth.account.forms import SignupForm
from django import forms

from .models import UserProfile


class DekatSignupForm(SignupForm):
    role = forms.ChoiceField(
        choices=UserProfile.Role.choices,
        initial=UserProfile.Role.CUSTOMER,
        widget=forms.Select,
        required=True,
        label="I am a",
    )

    def __init__(self, *args, **kwargs):
        self.request = kwargs.get('request')
        super().__init__(*args, **kwargs)
        if self.request:
            role = self.request.GET.get('role')
            if role in dict(UserProfile.Role.choices):
                self.fields['role'].initial = role

    def save(self, request):
        user = super().save(request)
        profile, _ = UserProfile.objects.get_or_create(user=user)
        role = self.cleaned_data.get('role') or UserProfile.Role.CUSTOMER
        profile.role = role
        profile.save(update_fields=['role'])
        return user
