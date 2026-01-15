from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Min, Q
from django.http import HttpResponseForbidden
from django.shortcuts import render, get_object_or_404

from venues.models import Venue
from accounts.models import UserProfile
from .models import MerchantMembership, Product, ProductCategory, ProductVariant
from .utils import bounding_box, haversine_km


def venue_item_search(request, slug):
    venue = get_object_or_404(Venue, slug=slug)
    query = request.GET.get('q', '').strip()
    category_slug = request.GET.get('category')
    near = request.GET.get('near') == '1'
    radius_km = float(request.GET.get('radius', '15') or 15)

    user_lat = user_lon = None
    if near and request.user.is_authenticated:
        profile = getattr(request.user, 'userprofile', None)
        if profile and profile.latitude is not None and profile.longitude is not None:
            user_lat, user_lon = profile.latitude, profile.longitude

    products = (
        Product.objects.filter(merchant__floor__venue=venue, is_active=True)
        .select_related('merchant', 'merchant__floor')
        .prefetch_related('images', 'variants', 'categories')
    )

    if category_slug:
        products = products.filter(categories__slug=category_slug)

    if query:
        products = products.filter(
            Q(name__icontains=query)
            | Q(description__icontains=query)
            | Q(merchant__name__icontains=query)
            | Q(variants__name__icontains=query)
            | Q(variants__sku__icontains=query)
        ).distinct()

    products = products.annotate(min_price=Min('variants__price_rm'))

    categories = ProductCategory.objects.filter(products__merchant__floor__venue=venue, is_active=True).distinct().order_by('name')

    distance_map = {}
    if near and user_lat is not None and user_lon is not None:
        min_lat, max_lat, min_lon, max_lon = bounding_box(user_lat, user_lon, radius_km)
        products = products.filter(
            merchant__latitude__isnull=False,
            merchant__longitude__isnull=False,
            merchant__latitude__gte=min_lat,
            merchant__latitude__lte=max_lat,
            merchant__longitude__gte=min_lon,
            merchant__longitude__lte=max_lon,
        )

        product_list = list(products)
        filtered = []
        for p in product_list:
            if p.merchant.latitude is None or p.merchant.longitude is None:
                continue
            d = haversine_km(user_lat, user_lon, p.merchant.latitude, p.merchant.longitude)
            if d <= radius_km:
                distance_map[p.id] = d
                filtered.append(p)
        filtered.sort(key=lambda p: distance_map.get(p.id, 10**9))
        paginator = Paginator(filtered, 24)
    else:
        paginator = Paginator(products, 24)

    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'venue': venue,
        'products': page_obj,
        'search_query': query,
        'categories': categories,
        'current_category': category_slug,
        'near': near,
        'radius_km': int(radius_km),
        'has_location': user_lat is not None and user_lon is not None,
        'distance_map': distance_map,
    }

    if request.headers.get('HX-Request'):
        return render(request, 'merchants/partials/product_list.html', context)

    return render(request, 'merchants/venue_item_search.html', context)


def product_detail(request, slug, product_id):
    venue = get_object_or_404(Venue, slug=slug)
    product = get_object_or_404(
        Product.objects.select_related('merchant', 'merchant__floor', 'merchant__floor__venue')
        .prefetch_related('images', 'variants', 'categories'),
        pk=product_id,
        merchant__floor__venue=venue,
        is_active=True,
    )
    min_price = product.variants.filter(is_active=True).aggregate(min_price=Min('price_rm'))['min_price']
    return render(request, 'merchants/product_detail.html', {'venue': venue, 'product': product, 'min_price': min_price})


@login_required
def merchant_portal(request):
    role = getattr(getattr(request.user, 'userprofile', None), 'role', None)
    if role != UserProfile.Role.MERCHANT:
        return HttpResponseForbidden("Merchant portal is for merchant accounts.")

    memberships = MerchantMembership.objects.filter(user=request.user).select_related('merchant', 'merchant__floor', 'merchant__floor__venue')
    merchant_id = request.GET.get('merchant')
    selected_merchant = None
    if merchant_id:
        selected_merchant = get_object_or_404(memberships, merchant_id=merchant_id).merchant
    elif memberships:
        selected_merchant = memberships[0].merchant

    products = Product.objects.filter(merchant=selected_merchant).prefetch_related('variants', 'images') if selected_merchant else Product.objects.none()
    return render(request, 'merchants/portal/index.html', {'memberships': memberships, 'merchant': selected_merchant, 'products': products})


@login_required
def merchant_product_create(request):
    role = getattr(getattr(request.user, 'userprofile', None), 'role', None)
    if role != UserProfile.Role.MERCHANT:
        return HttpResponseForbidden("Merchant portal is for merchant accounts.")

    memberships = MerchantMembership.objects.filter(user=request.user).select_related('merchant')
    if not memberships:
        return HttpResponseForbidden("No merchant linked to your account.")

    merchant = get_object_or_404(memberships, merchant_id=request.GET.get('merchant') or memberships[0].merchant_id).merchant

    if request.method == "POST":
        name = (request.POST.get('name') or '').strip()
        description = (request.POST.get('description') or '').strip()
        price_rm = request.POST.get('price_rm')
        stock_qty = request.POST.get('stock_qty')
        if name and price_rm:
            product = Product.objects.create(merchant=merchant, name=name, description=description, is_active=True)
            ProductVariant.objects.create(
                product=product,
                name=(request.POST.get('variant_name') or '').strip(),
                price_rm=price_rm,
                stock_qty=int(stock_qty or 0),
                is_active=True,
            )
            return render(request, 'merchants/portal/product_created.html', {'product': product, 'merchant': merchant})

    return render(request, 'merchants/portal/product_create.html', {'merchant': merchant, 'memberships': memberships})
