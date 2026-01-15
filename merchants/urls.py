from django.urls import path

from . import views


urlpatterns = [
    path('<slug:slug>/items/', views.venue_item_search, name='venue_item_search'),
    path('<slug:slug>/items/<int:product_id>/', views.product_detail, name='product_detail'),
    path('merchant/portal/', views.merchant_portal, name='merchant_portal'),
    path('merchant/portal/products/new/', views.merchant_product_create, name='merchant_product_create'),
]
