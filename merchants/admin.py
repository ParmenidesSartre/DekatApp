from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from .models import (
    Merchant,
    MerchantCategory,
    MerchantUpdate,
    MerchantFollow,
    MerchantMembership,
    ProductCategory,
    Product,
    ProductImage,
    ProductVariant,
)


@admin.register(MerchantCategory)
class MerchantCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Merchant)
class MerchantAdmin(admin.ModelAdmin):
    list_display = ('name', 'lot_number', 'floor_display', 'category', 'is_featured', 'view_in_app')
    list_filter = ('floor__venue', 'category', 'is_featured', 'is_halal')
    search_fields = ('name', 'lot_number', 'keywords')

    fieldsets = (
        ('Identity', {
            'fields': ('name', 'category', 'logo', 'storefront_image', 'description', 'keywords')
        }),
        ('Location', {
            'fields': ('floor', 'lot_number', 'nearest_entrance')
        }),
        ('Operating Info', {
            'fields': ('operating_hours', 'is_halal', 'accepts_ewallet')
        }),
        ('Digital Presence', {
            'fields': ('phone_number', 'website', 'instagram', 'facebook')
        }),
        ('Monetization', {
            'fields': ('is_featured',)
        }),
    )

    def floor_display(self, obj):
        return f"{obj.floor.venue.name} - {obj.floor.name}"
    floor_display.short_description = "Location"

    def view_in_app(self, obj):
        base_url = reverse('venue_directory', args=[obj.floor.venue.slug])
        return format_html('<a href="{}?q={}" target="_blank">Locate</a>', base_url, obj.name)
    view_in_app.short_description = "View"


@admin.register(MerchantUpdate)
class MerchantUpdateAdmin(admin.ModelAdmin):
    list_display = ('merchant', 'title', 'is_published', 'published_at')
    list_filter = ('is_published', 'published_at', 'merchant__floor__venue')
    search_fields = ('merchant__name', 'title', 'body')


@admin.register(MerchantFollow)
class MerchantFollowAdmin(admin.ModelAdmin):
    list_display = ('user', 'merchant', 'notify_updates', 'notify_restock', 'created_at')
    search_fields = ('user__username', 'user__email', 'merchant__name')
    list_filter = ('created_at', 'merchant__floor__venue')


@admin.register(MerchantMembership)
class MerchantMembershipAdmin(admin.ModelAdmin):
    list_display = ('user', 'merchant', 'role', 'created_at')
    list_filter = ('role', 'created_at', 'merchant__floor__venue')
    search_fields = ('user__username', 'user__email', 'merchant__name')


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1


@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'is_active')
    list_filter = ('is_active',)
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'merchant', 'is_active', 'updated_at')
    list_filter = ('is_active', 'merchant__floor__venue', 'categories')
    search_fields = ('name', 'description', 'merchant__name')
    inlines = [ProductVariantInline, ProductImageInline]
    filter_horizontal = ('categories',)
