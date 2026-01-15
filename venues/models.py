from django.db import models
from django.conf import settings

class Plan(models.Model):
    class PlanCode(models.TextChoices):
        STARTER = 'STARTER', 'Starter'
        PRO = 'PRO', 'Pro'
        ENTERPRISE = 'ENTERPRISE', 'Enterprise'

    code = models.CharField(max_length=20, choices=PlanCode.choices, unique=True)
    name = models.CharField(max_length=100)
    monthly_fee_rm = models.DecimalField(max_digits=8, decimal_places=2, default=200)
    featured_merchant_fee_rm = models.DecimalField(max_digits=8, decimal_places=2, default=50)
    max_merchants = models.PositiveIntegerField(blank=True, null=True, help_text="Null means unlimited.")
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} (RM{self.monthly_fee_rm}/mo)"

class Venue(models.Model):
    class VenueType(models.TextChoices):
        MALL = 'MALL', 'Shopping Mall'
        CAMPUS = 'CAMPUS', 'University Campus'
        EXPO = 'EXPO', 'Exhibition Center'
        OFFICE = 'OFFICE', 'Office Complex'

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    venue_type = models.CharField(max_length=20, choices=VenueType.choices, default=VenueType.MALL)

    # Visuals for the landing page
    cover_image = models.ImageField(upload_to='venues/', blank=True, null=True)

    # Location for distance-based search
    latitude = models.FloatField(blank=True, null=True, help_text="Venue latitude for location-based search")
    longitude = models.FloatField(blank=True, null=True, help_text="Venue longitude for location-based search")
    address = models.TextField(blank=True, help_text="Full address of the venue")

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class VenueSubscription(models.Model):
    class Status(models.TextChoices):
        TRIALING = 'TRIALING', 'Trialing'
        ACTIVE = 'ACTIVE', 'Active'
        PAST_DUE = 'PAST_DUE', 'Past due'
        CANCELED = 'CANCELED', 'Canceled'

    venue = models.OneToOneField(Venue, related_name='subscription', on_delete=models.CASCADE)
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.TRIALING)

    current_period_start = models.DateField(blank=True, null=True)
    current_period_end = models.DateField(blank=True, null=True)
    trial_end = models.DateField(blank=True, null=True)
    cancel_at_period_end = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.venue.name} - {self.plan.name} ({self.status})"

class VenueLead(models.Model):
    name = models.CharField(max_length=120)
    email = models.EmailField(blank=True)
    phone_number = models.CharField(max_length=30, blank=True)
    company = models.CharField(max_length=150, blank=True)
    venue_type = models.CharField(max_length=80, blank=True, help_text="e.g. Mall, Campus, Expo")
    message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        company = self.company.strip() or "Unknown company"
        return f"{company} - {self.name}"

class Floor(models.Model):
    venue = models.ForeignKey(Venue, related_name='floors', on_delete=models.CASCADE)
    name = models.CharField(max_length=50) # "Level 1", "Basement"
    level_order = models.IntegerField(default=0) 

    class Meta:
        ordering = ['level_order']

    def __str__(self):
        return f"{self.venue.name} - {self.name}"

