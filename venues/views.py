from django.core.paginator import Paginator # Import this
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.db.utils import OperationalError
from django.db.models import Q, Count
from django.contrib import messages
from .models import Venue, Floor
from merchants.models import Merchant, MerchantCategory, MerchantFollow, MerchantUpdate
from .forms import VenueLeadForm, VenueCreateForm, MerchantForm, FloorForm
from .utils import is_open_now
from accounts.models import UserProfile

def home(request):
    venues = Venue.objects.filter(is_active=True).order_by('name')
    return render(request, 'venues/home.html', {'venues': venues})

def owners(request):
    return render(request, 'venues/owners/index.html')

@require_http_methods(["GET", "POST"])
def owners_demo(request):
    if request.method == "POST":
        form = VenueLeadForm(request.POST)
        if form.is_valid():
            form.save()
            return render(request, 'venues/owners/thanks.html')
    else:
        form = VenueLeadForm()

    return render(request, 'venues/owners/demo.html', {'form': form})

@login_required
def venue_portal(request):
    role = getattr(getattr(request.user, 'userprofile', None), 'role', None)
    if role != UserProfile.Role.VENUE:
        return render(request, 'venues/owners/portal_forbidden.html', status=403)

    venues = Venue.objects.filter(owner=request.user).order_by('name')
    return render(request, 'venues/owners/portal.html', {'venues': venues})


@login_required
@require_http_methods(["GET", "POST"])
def venue_create(request):
    role = getattr(getattr(request.user, 'userprofile', None), 'role', None)
    if role != UserProfile.Role.VENUE:
        return render(request, 'venues/owners/portal_forbidden.html', status=403)

    if request.method == "POST":
        form = VenueCreateForm(request.POST, request.FILES)
        if form.is_valid():
            form.save(owner=request.user)
            return render(request, 'venues/owners/venue_created.html')
    else:
        form = VenueCreateForm()

    return render(request, 'venues/owners/venue_create.html', {'form': form})

def pricing(request):
    return render(request, 'venues/pricing.html')

def faq(request):
    return render(request, 'venues/faq.html')

def terms(request):
    return render(request, 'venues/terms.html')

def venue_list(request):
    import math

    # Get user's location from query params
    user_lat = request.GET.get('lat')
    user_lon = request.GET.get('lon')
    radius = request.GET.get('radius', '30')  # Default 30km

    venues = Venue.objects.filter(is_active=True)

    # Helper function to calculate distance using Haversine formula
    def calculate_distance(lat1, lon1, lat2, lon2):
        """Calculate distance between two points in kilometers"""
        if not all([lat1, lon1, lat2, lon2]):
            return None

        R = 6371  # Earth's radius in kilometers

        lat1_rad = math.radians(float(lat1))
        lat2_rad = math.radians(float(lat2))
        delta_lat = math.radians(float(lat2) - float(lat1))
        delta_lon = math.radians(float(lon2) - float(lon1))

        a = math.sin(delta_lat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

        return R * c

    # Calculate distances and filter by radius if location provided
    venues_with_distance = []
    for venue in venues:
        if user_lat and user_lon and venue.latitude and venue.longitude:
            distance = calculate_distance(user_lat, user_lon, venue.latitude, venue.longitude)
            venue.distance = round(distance, 1) if distance else None

            # Filter by radius (if not "all")
            if radius != 'all':
                try:
                    radius_km = float(radius)
                    if distance and distance <= radius_km:
                        venues_with_distance.append(venue)
                except ValueError:
                    venues_with_distance.append(venue)
            else:
                venues_with_distance.append(venue)
        else:
            venue.distance = None
            venues_with_distance.append(venue)

    # Sort by distance if available, otherwise by name
    if user_lat and user_lon:
        venues_with_distance.sort(key=lambda v: (v.distance is None, v.distance if v.distance is not None else float('inf')))
    else:
        venues_with_distance.sort(key=lambda v: v.name)

    context = {
        'venues': venues_with_distance,
        'user_lat': user_lat,
        'user_lon': user_lon,
        'radius': radius,
    }
    return render(request, 'venues/venue_list.html', context)

def merchant_detail(request, slug, merchant_id):
    venue = get_object_or_404(Venue, slug=slug)
    merchant = get_object_or_404(Merchant.objects.select_related('floor', 'category', 'floor__venue'), pk=merchant_id, floor__venue=venue)
    is_following = False
    if request.user.is_authenticated:
        try:
            is_following = MerchantFollow.objects.filter(user=request.user, merchant=merchant).exists()
        except OperationalError:
            is_following = False
    return render(
        request,
        'venues/merchant_detail.html',
        {'venue': venue, 'merchant': merchant, 'is_following': is_following, 'is_open_now': is_open_now(merchant.operating_hours)},
    )

def _merchant_ui_context(merchants, user):
    open_ids = {m.id for m in merchants if is_open_now(m.operating_hours) is True}
    followed_ids = set()
    if user.is_authenticated:
        try:
            followed_ids = set(
                MerchantFollow.objects.filter(user=user, merchant__in=merchants).values_list('merchant_id', flat=True)
            )
        except OperationalError:
            followed_ids = set()
    return {'followed_ids': followed_ids, 'open_ids': open_ids}

@login_required
def user_feed(request):
    try:
        updates = (
            MerchantUpdate.objects.filter(is_published=True, merchant__followers__user=request.user)
            .select_related('merchant', 'merchant__floor', 'merchant__floor__venue')
            .order_by('-published_at')
        )
    except OperationalError:
        updates = MerchantUpdate.objects.none()
    paginator = Paginator(updates, 20)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'venues/feed.html', {'updates': page_obj})

def merchant_updates(request, slug, merchant_id):
    venue = get_object_or_404(Venue, slug=slug)
    merchant = get_object_or_404(Merchant.objects.select_related('floor', 'floor__venue'), pk=merchant_id, floor__venue=venue)
    updates = merchant.updates.filter(is_published=True)
    paginator = Paginator(updates, 20)
    page_obj = paginator.get_page(request.GET.get('page'))
    is_following = False
    if request.user.is_authenticated:
        try:
            is_following = MerchantFollow.objects.filter(user=request.user, merchant=merchant).exists()
        except OperationalError:
            is_following = False
    return render(
        request,
        'venues/merchant_updates.html',
        {'venue': venue, 'merchant': merchant, 'updates': page_obj, 'is_following': is_following},
    )

@login_required
@require_http_methods(["POST"])
def toggle_merchant_follow(request, slug, merchant_id):
    venue = get_object_or_404(Venue, slug=slug)
    merchant = get_object_or_404(Merchant.objects.select_related('floor__venue'), pk=merchant_id, floor__venue=venue)

    try:
        existing = MerchantFollow.objects.filter(user=request.user, merchant=merchant)
        if existing.exists():
            existing.delete()
            is_following = False
        else:
            MerchantFollow.objects.create(user=request.user, merchant=merchant)
            is_following = True
    except OperationalError:
        is_following = False

    return render(request, 'venues/partials/follow_button.html', {'venue': venue, 'merchant': merchant, 'is_following': is_following})

def venue_directory(request, slug):
    venue = get_object_or_404(Venue, slug=slug)
    query = request.GET.get('q', '')
    category_slug = request.GET.get('category')
    
    # 1. Base Query
    merchant_list = Merchant.objects.filter(floor__venue=venue)

    if query:
        merchant_list = merchant_list.filter(
            Q(name__icontains=query) | 
            Q(description__icontains=query) |
            Q(lot_number__icontains=query) |
            Q(category__name__icontains=query) | 
            Q(keywords__icontains=query)
        )

    if category_slug:
        merchant_list = merchant_list.filter(category__slug=category_slug)
    
    # Sort: Featured first, then name
    merchant_list = merchant_list.order_by('-is_featured', 'name')
    
    # 2. PAGINATION LOGIC (Show 20 per page)
    paginator = Paginator(merchant_list, 20) 
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    ui_context = _merchant_ui_context(page_obj.object_list, request.user)
    
    # 3. HTMX CHECK
    # If the browser says "I am HTMX asking for more data", we send only the partial list.
    if request.headers.get('HX-Request'):
        return render(
            request,
            'venues/partials/merchant_list.html',
            {'merchants': page_obj, 'search_query': query, 'current_category': category_slug, **ui_context},
        )

    # Otherwise, send the full page (Header + Search + List)
    categories = MerchantCategory.objects.filter(merchant__floor__venue=venue).distinct()
    
    context = {
        'venue': venue,
        'merchants': page_obj, # Pass the Page object, not the full list
        'categories': categories,
        'search_query': query,
        'current_category': category_slug,
        **ui_context,
    }
    return render(request, 'venues/directory.html', context)


# ============================================
# VENUE OWNER MANAGEMENT VIEWS
# ============================================

def _check_venue_owner(user, venue):
    """Helper function to check if user owns the venue"""
    if venue.owner != user:
        return False
    role = getattr(getattr(user, 'userprofile', None), 'role', None)
    return role == UserProfile.Role.VENUE


@login_required
def venue_dashboard(request, venue_id):
    """Venue management dashboard for owners"""
    venue = get_object_or_404(Venue, pk=venue_id)

    if not _check_venue_owner(request.user, venue):
        return render(request, 'venues/owners/portal_forbidden.html', status=403)

    # Get stats
    floors = venue.floors.all().annotate(merchant_count=Count('merchants')).order_by('level_order')
    merchants = Merchant.objects.filter(floor__venue=venue).select_related('floor', 'category')
    total_merchants = merchants.count()
    featured_merchants = merchants.filter(is_featured=True).count()

    context = {
        'venue': venue,
        'floors': floors,
        'merchants': merchants[:10],  # Show recent 10
        'total_merchants': total_merchants,
        'featured_merchants': featured_merchants,
    }
    return render(request, 'venues/owners/venue_dashboard.html', context)


@login_required
def venue_merchants(request, venue_id):
    """List all merchants for a venue"""
    venue = get_object_or_404(Venue, pk=venue_id)

    if not _check_venue_owner(request.user, venue):
        return render(request, 'venues/owners/portal_forbidden.html', status=403)

    merchants = Merchant.objects.filter(floor__venue=venue).select_related('floor', 'category').order_by('floor__level_order', 'name')

    context = {
        'venue': venue,
        'merchants': merchants,
    }
    return render(request, 'venues/owners/merchant_list.html', context)


@login_required
@require_http_methods(["GET", "POST"])
def merchant_add(request, venue_id):
    """Add a new merchant to a venue"""
    venue = get_object_or_404(Venue, pk=venue_id)

    if not _check_venue_owner(request.user, venue):
        return render(request, 'venues/owners/portal_forbidden.html', status=403)

    if request.method == "POST":
        form = MerchantForm(request.POST, request.FILES, venue=venue)
        if form.is_valid():
            merchant = form.save()
            messages.success(request, f'Merchant "{merchant.name}" added successfully!')
            return redirect('venue_merchants', venue_id=venue.id)
    else:
        form = MerchantForm(venue=venue)

    context = {
        'venue': venue,
        'form': form,
        'action': 'Add',
    }
    return render(request, 'venues/owners/merchant_form.html', context)


@login_required
@require_http_methods(["GET", "POST"])
def merchant_edit(request, venue_id, merchant_id):
    """Edit an existing merchant"""
    venue = get_object_or_404(Venue, pk=venue_id)
    merchant = get_object_or_404(Merchant, pk=merchant_id, floor__venue=venue)

    if not _check_venue_owner(request.user, venue):
        return render(request, 'venues/owners/portal_forbidden.html', status=403)

    if request.method == "POST":
        form = MerchantForm(request.POST, request.FILES, instance=merchant, venue=venue)
        if form.is_valid():
            merchant = form.save()
            messages.success(request, f'Merchant "{merchant.name}" updated successfully!')
            return redirect('venue_merchants', venue_id=venue.id)
    else:
        form = MerchantForm(instance=merchant, venue=venue)

    context = {
        'venue': venue,
        'form': form,
        'merchant': merchant,
        'action': 'Edit',
    }
    return render(request, 'venues/owners/merchant_form.html', context)


@login_required
@require_http_methods(["POST"])
def merchant_delete(request, venue_id, merchant_id):
    """Delete a merchant"""
    venue = get_object_or_404(Venue, pk=venue_id)
    merchant = get_object_or_404(Merchant, pk=merchant_id, floor__venue=venue)

    if not _check_venue_owner(request.user, venue):
        return render(request, 'venues/owners/portal_forbidden.html', status=403)

    merchant_name = merchant.name
    merchant.delete()
    messages.success(request, f'Merchant "{merchant_name}" deleted successfully!')
    return redirect('venue_merchants', venue_id=venue.id)


@login_required
@require_http_methods(["POST"])
def merchant_toggle_featured(request, venue_id, merchant_id):
    """Toggle featured status for a merchant"""
    venue = get_object_or_404(Venue, pk=venue_id)
    merchant = get_object_or_404(Merchant, pk=merchant_id, floor__venue=venue)

    if not _check_venue_owner(request.user, venue):
        return render(request, 'venues/owners/portal_forbidden.html', status=403)

    merchant.is_featured = not merchant.is_featured
    merchant.save()

    status = "featured" if merchant.is_featured else "unfeatured"
    messages.success(request, f'Merchant "{merchant.name}" {status}!')
    return redirect('venue_merchants', venue_id=venue.id)


@login_required
@require_http_methods(["GET", "POST"])
def floor_add(request, venue_id):
    """Add a new floor to a venue"""
    venue = get_object_or_404(Venue, pk=venue_id)

    if not _check_venue_owner(request.user, venue):
        return render(request, 'venues/owners/portal_forbidden.html', status=403)

    if request.method == "POST":
        form = FloorForm(request.POST)
        if form.is_valid():
            floor = form.save(commit=False)
            floor.venue = venue
            floor.save()
            messages.success(request, f'Floor "{floor.name}" added successfully!')
            return redirect('venue_dashboard', venue_id=venue.id)
    else:
        form = FloorForm()

    context = {
        'venue': venue,
        'form': form,
        'action': 'Add',
    }
    return render(request, 'venues/owners/floor_form.html', context)


@login_required
@require_http_methods(["GET", "POST"])
def floor_edit(request, venue_id, floor_id):
    """Edit an existing floor"""
    venue = get_object_or_404(Venue, pk=venue_id)
    floor = get_object_or_404(Floor, pk=floor_id, venue=venue)

    if not _check_venue_owner(request.user, venue):
        return render(request, 'venues/owners/portal_forbidden.html', status=403)

    if request.method == "POST":
        form = FloorForm(request.POST, instance=floor)
        if form.is_valid():
            floor = form.save()
            messages.success(request, f'Floor "{floor.name}" updated successfully!')
            return redirect('venue_dashboard', venue_id=venue.id)
    else:
        form = FloorForm(instance=floor)

    context = {
        'venue': venue,
        'form': form,
        'floor': floor,
        'action': 'Edit',
    }
    return render(request, 'venues/owners/floor_form.html', context)


@login_required
@require_http_methods(["POST"])
def floor_delete(request, venue_id, floor_id):
    """Delete a floor (only if no merchants on it)"""
    venue = get_object_or_404(Venue, pk=venue_id)
    floor = get_object_or_404(Floor, pk=floor_id, venue=venue)

    if not _check_venue_owner(request.user, venue):
        return render(request, 'venues/owners/portal_forbidden.html', status=403)

    if floor.merchants.exists():
        messages.error(request, f'Cannot delete floor "{floor.name}" - it has merchants. Please move or delete them first.')
    else:
        floor_name = floor.name
        floor.delete()
        messages.success(request, f'Floor "{floor_name}" deleted successfully!')

    return redirect('venue_dashboard', venue_id=venue.id)
