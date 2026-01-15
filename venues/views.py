from django.core.paginator import Paginator # Import this
from django.shortcuts import render, get_object_or_404
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.db.utils import OperationalError
from django.db.models import Q
from .models import Venue
from merchants.models import Merchant, MerchantCategory, MerchantFollow, MerchantUpdate
from .forms import VenueLeadForm, VenueCreateForm
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
    venues = Venue.objects.filter(is_active=True).order_by('name')
    return render(request, 'venues/venue_list.html', {'venues': venues})

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
