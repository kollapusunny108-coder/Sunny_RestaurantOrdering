from django.urls import path
from . import views

app_name = 'restaurant'

urlpatterns = [
    # Customer Menu & Ordering
    path('', views.menu_view, name='menu'),
    path('cart/', views.cart_page_view, name='cart_page'),
    path('checkout/', views.checkout_submit, name='checkout'),
    
    # Order Tracking
    path('track/', views.order_track_view, name='order_track_search'),
    path('track/<int:order_id>/', views.order_track_view, name='order_track'),
    
    # Kitchen Dashboard
    path('kitchen/', views.kitchen_dashboard_view, name='kitchen_dashboard'),
    path('kitchen/order/<int:order_id>/status/', views.kitchen_update_status, name='kitchen_update_status'),
    
    # JSON APIs (Cart, Live Polling & Dashboard)
    path('api/cart/add/', views.cart_add_api, name='cart_add'),
    path('api/cart/update/', views.cart_update_api, name='cart_update'),
    path('api/cart/remove/', views.cart_remove_api, name='cart_remove'),
    path('api/cart/clear/', views.cart_clear_api, name='cart_clear'),
    path('api/cart/data/', views.cart_data_api, name='cart_data'),
    path('api/order/<int:order_id>/status/', views.order_status_api, name='order_status_api'),
    path('api/kitchen/orders/', views.kitchen_orders_api, name='kitchen_orders_api'),
]
