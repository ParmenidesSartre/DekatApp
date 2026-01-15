from django.conf import settings
from django.db import models


class MerchantCategory(models.Model):
    name = models.CharField(max_length=50)
    slug = models.SlugField(unique=True)
    icon_class = models.CharField(max_length=50, blank=True, default='fa-store')

    class Meta:
        verbose_name_plural = "Merchant Categories"
        db_table = "venues_merchantcategory"

    def __str__(self):
        return self.name


class Merchant(models.Model):
    floor = models.ForeignKey('venues.Floor', related_name='merchants', on_delete=models.CASCADE)
    category = models.ForeignKey(MerchantCategory, on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=255)

    lot_number = models.CharField(max_length=50, blank=True, help_text="e.g. G-45")
    nearest_entrance = models.CharField(max_length=100, blank=True, help_text="e.g. Near North Entrance")

    logo = models.ImageField(upload_to='logos/', blank=True, null=True)
    storefront_image = models.ImageField(upload_to='storefronts/', blank=True, null=True)

    description = models.TextField(blank=True)
    operating_hours = models.CharField(max_length=100, blank=True, null=True, help_text="e.g. 10:00 AM - 10:00 PM")

    phone_number = models.CharField(max_length=20, blank=True)
    website = models.URLField(blank=True)
    instagram = models.URLField(blank=True, null=True, help_text="Full URL, e.g. https://instagram.com/shopname")
    facebook = models.URLField(blank=True, null=True)

    is_halal = models.BooleanField(default=False, verbose_name="Halal Certified")
    accepts_ewallet = models.BooleanField(default=True, verbose_name="Accepts E-Wallet")
    keywords = models.TextField(blank=True, null=True, help_text="Comma separated keywords for search (hidden from user)")

    is_featured = models.BooleanField(default=False)
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)

    class Meta:
        db_table = "venues_merchant"

    def __str__(self):
        return f"{self.name} ({self.lot_number})"

class ProductCategory(models.Model):
    name = models.CharField(max_length=80)
    slug = models.SlugField(unique=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Product(models.Model):
    merchant = models.ForeignKey(Merchant, related_name='products', on_delete=models.CASCADE)
    categories = models.ManyToManyField(ProductCategory, blank=True, related_name='products')

    name = models.CharField(max_length=160)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.merchant.name}: {self.name}"


class ProductImage(models.Model):
    product = models.ForeignKey(Product, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='products/')
    alt_text = models.CharField(max_length=140, blank=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['sort_order', 'id']

    def __str__(self):
        return f"Image for {self.product.name}"


class ProductVariant(models.Model):
    product = models.ForeignKey(Product, related_name='variants', on_delete=models.CASCADE)
    name = models.CharField(max_length=120, blank=True, help_text="e.g. Size M / Red")
    sku = models.CharField(max_length=64, blank=True)

    price_rm = models.DecimalField(max_digits=10, decimal_places=2)
    stock_qty = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f"{self.product.name} - {self.name or 'Default'}"


class MerchantUpdate(models.Model):
    merchant = models.ForeignKey(Merchant, related_name='updates', on_delete=models.CASCADE)
    title = models.CharField(max_length=120)
    body = models.TextField(blank=True)
    link = models.URLField(blank=True)
    is_published = models.BooleanField(default=True)
    published_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-published_at']
        db_table = "venues_merchantupdate"

    def __str__(self):
        return f"{self.merchant.name}: {self.title}"


class MerchantFollow(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='merchant_follows', on_delete=models.CASCADE)
    merchant = models.ForeignKey(Merchant, related_name='followers', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    notify_updates = models.BooleanField(default=True)
    notify_restock = models.BooleanField(default=False)
    categories = models.ManyToManyField(ProductCategory, blank=True, related_name='follow_preferences')

    class Meta:
        unique_together = (('user', 'merchant'),)
        db_table = "venues_merchantfollow"

    def __str__(self):
        return f"{self.user} follows {self.merchant}"


class MerchantMembership(models.Model):
    class Role(models.TextChoices):
        OWNER = 'OWNER', 'Owner'
        STAFF = 'STAFF', 'Staff'

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='merchant_memberships')
    merchant = models.ForeignKey(Merchant, on_delete=models.CASCADE, related_name='memberships')
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.OWNER)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = (('user', 'merchant'),)

    def __str__(self):
        return f"{self.user} - {self.merchant} ({self.role})"
