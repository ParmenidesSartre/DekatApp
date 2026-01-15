from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.urls import reverse


def login_choice(request):
    return render(request, 'accounts/login_choice.html')


def signup_choice(request):
    return render(request, 'accounts/signup_choice.html')


def login_customer(request):
    return redirect(f"{reverse('account_login')}?next=/feed/")


def login_venue(request):
    return redirect(f"{reverse('account_login')}?next=/owners/")


def signup_customer(request):
    return redirect(f"{reverse('account_signup')}?role=CUSTOMER")


def signup_venue(request):
    return redirect(f"{reverse('account_signup')}?role=VENUE")


@login_required
def profile(request):
    profile_obj = request.user.userprofile
    if request.method == "POST":
        profile_obj.latitude = float(request.POST.get('latitude') or 0) if request.POST.get('latitude') else None
        profile_obj.longitude = float(request.POST.get('longitude') or 0) if request.POST.get('longitude') else None
        profile_obj.save(update_fields=['latitude', 'longitude'])
        return redirect('profile')
    return render(request, 'accounts/profile.html', {'profile': profile_obj})
