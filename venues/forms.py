from django import forms
from django.utils.text import slugify

from .models import Venue, VenueLead, Floor
from merchants.models import Merchant, MerchantCategory


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


class FloorForm(forms.ModelForm):
    class Meta:
        model = Floor
        fields = ['name', 'level_order']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'e.g. Ground Floor, Level 1'}),
            'level_order': forms.NumberInput(attrs={'placeholder': '0'}),
        }


class MerchantForm(forms.ModelForm):
    class Meta:
        model = Merchant
        fields = [
            'name', 'floor', 'category', 'lot_number', 'nearest_entrance',
            'logo', 'storefront_image', 'description', 'operating_hours',
            'phone_number', 'website', 'instagram', 'facebook',
            'is_halal', 'accepts_ewallet', 'keywords', 'is_featured',
            'latitude', 'longitude'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Brief description of the merchant...'}),
            'operating_hours': forms.TextInput(attrs={'placeholder': 'e.g. 10:00 AM - 10:00 PM'}),
            'phone_number': forms.TextInput(attrs={'placeholder': '+60123456789'}),
            'lot_number': forms.TextInput(attrs={'placeholder': 'e.g. G-45'}),
            'nearest_entrance': forms.TextInput(attrs={'placeholder': 'e.g. Near North Entrance'}),
            'keywords': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Comma-separated keywords for search'}),
            'latitude': forms.NumberInput(attrs={'step': 'any', 'placeholder': '3.1390'}),
            'longitude': forms.NumberInput(attrs={'step': 'any', 'placeholder': '101.6869'}),
        }

    def __init__(self, *args, venue=None, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter floors to only show floors belonging to the current venue
        if venue:
            self.fields['floor'].queryset = Floor.objects.filter(venue=venue)
