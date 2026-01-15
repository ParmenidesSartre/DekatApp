from django import forms
from django.utils.text import slugify

from .models import Venue, VenueLead


class VenueCreateForm(forms.ModelForm):
    class Meta:
        model = Venue
        fields = ['name', 'venue_type', 'cover_image']

    def save(self, owner, commit=True):
        venue = super().save(commit=False)
        venue.owner = owner

        base_slug = slugify(venue.name)[:50] or "venue"
        slug = base_slug
        i = 2
        while Venue.objects.filter(slug=slug).exists():
            suffix = f"-{i}"
            slug = f"{base_slug[: max(1, 50 - len(suffix))]}{suffix}"
            i += 1
        venue.slug = slug

        if commit:
            venue.save()
            self.save_m2m()
        return venue


class VenueLeadForm(forms.ModelForm):
    class Meta:
        model = VenueLead
        fields = ['name', 'company', 'venue_type', 'email', 'phone_number', 'message']
        widgets = {
            'message': forms.Textarea(attrs={'rows': 5}),
        }
