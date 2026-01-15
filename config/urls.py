"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from venues import views as venue_views
from accounts import views as accounts_views
from django.conf import settings             # <-- Import this
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')), 
    path('login/', accounts_views.login_choice, name='login_choice'),
    path('login/customer/', accounts_views.login_customer, name='login_customer'),
    path('login/venue/', accounts_views.login_venue, name='login_venue'),
    path('signup/', accounts_views.signup_choice, name='signup_choice'),
    path('signup/customer/', accounts_views.signup_customer, name='signup_customer'),
    path('signup/venue/', accounts_views.signup_venue, name='signup_venue'),
    path('profile/', accounts_views.profile, name='profile'),
    path('', venue_views.home, name='home'),
    path('', include('merchants.urls')),
    path('venues/', venue_views.venue_list, name='venue_list'),
    path('owners/', venue_views.owners, name='owners'),
    path('owners/demo/', venue_views.owners_demo, name='owners_demo'),
    path('owners/portal/', venue_views.venue_portal, name='venue_portal'),
    path('owners/portal/new/', venue_views.venue_create, name='venue_create'),
    # Venue Management URLs
    path('owners/venue/<int:venue_id>/', venue_views.venue_dashboard, name='venue_dashboard'),
    path('owners/venue/<int:venue_id>/merchants/', venue_views.venue_merchants, name='venue_merchants'),
    path('owners/venue/<int:venue_id>/merchants/add/', venue_views.merchant_add, name='merchant_add'),
    path('owners/venue/<int:venue_id>/merchants/<int:merchant_id>/edit/', venue_views.merchant_edit, name='merchant_edit'),
    path('owners/venue/<int:venue_id>/merchants/<int:merchant_id>/delete/', venue_views.merchant_delete, name='merchant_delete'),
    path('owners/venue/<int:venue_id>/merchants/<int:merchant_id>/toggle-featured/', venue_views.merchant_toggle_featured, name='merchant_toggle_featured'),
    path('owners/venue/<int:venue_id>/floors/add/', venue_views.floor_add, name='floor_add'),
    path('owners/venue/<int:venue_id>/floors/<int:floor_id>/edit/', venue_views.floor_edit, name='floor_edit'),
    path('owners/venue/<int:venue_id>/floors/<int:floor_id>/delete/', venue_views.floor_delete, name='floor_delete'),
    path('feed/', venue_views.user_feed, name='user_feed'),
    path('pricing/', venue_views.pricing, name='pricing'),
    path('faq/', venue_views.faq, name='faq'),
    path('terms/', venue_views.terms, name='terms'),
    path('<slug:slug>/m/<int:merchant_id>/', venue_views.merchant_detail, name='merchant_detail'),
    path('<slug:slug>/m/<int:merchant_id>/follow/', venue_views.toggle_merchant_follow, name='merchant_follow'),
    path('<slug:slug>/m/<int:merchant_id>/updates/', venue_views.merchant_updates, name='merchant_updates'),
    path('<slug:slug>/', venue_views.venue_directory, name='venue_directory'),
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
