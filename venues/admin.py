from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from .models import Venue, Floor, Plan, VenueSubscription, VenueLead


class FloorInline(admin.TabularInline):
    model = Floor
    extra = 1


@admin.register(Venue)
class VenueAdmin(admin.ModelAdmin):
    list_display = ('name', 'venue_type', 'owner', 'subscription_summary', 'view_live_button')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [FloorInline]

    def view_on_site(self, obj):
        return reverse('venue_directory', args=[obj.slug])

    def view_live_button(self, obj):
        url = reverse('venue_directory', args=[obj.slug])
        return format_html(
            '<a class="button" href="{}" target="_blank" style="background-color: #2563eb; color: white; padding: 4px 10px; border-radius: 4px; font-weight: bold;">Open Directory</a>',
            url,
        )
    view_live_button.short_description = "Preview"

    def subscription_summary(self, obj):
        subscription = getattr(obj, 'subscription', None)
        if not subscription:
            return "No subscription"
        return f"{subscription.plan.code} • {subscription.status}"
    subscription_summary.short_description = "Billing"


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'monthly_fee_rm', 'featured_merchant_fee_rm', 'max_merchants', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('code', 'name')


@admin.register(VenueSubscription)
class VenueSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('venue', 'plan', 'status', 'current_period_end', 'cancel_at_period_end', 'updated_at')
    list_filter = ('status', 'plan', 'cancel_at_period_end')
    search_fields = ('venue__name', 'venue__slug')


@admin.register(VenueLead)
class VenueLeadAdmin(admin.ModelAdmin):
    list_display = ('company', 'name', 'email', 'phone_number', 'venue_type', 'created_at')
    search_fields = ('company', 'name', 'email', 'phone_number')
    list_filter = ('venue_type', 'created_at')

