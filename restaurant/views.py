import json
from decimal import Decimal
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.http import require_POST, require_GET
from django.views.decorators.csrf import ensure_csrf_cookie
from django.contrib import messages
from django.db import transaction
from django.urls import reverse
from django.utils import timezone

from .models import Category, MenuItem, Order, OrderItem
from .forms import OrderCheckoutForm, OrderStatusUpdateForm


def get_cart_details(session_cart):
    """
    Helper to resolve session cart items against MenuItem database records.
    Returns: (cart_items_list, subtotal, tax, grand_total, is_all_available, unavailable_names)
    """
    items_data = []
    subtotal = Decimal('0.00')
    tax_rate = Decimal('0.05')  # 5% restaurant sales tax
    is_all_available = True
    unavailable_names = []

    if not session_cart:
        return items_data, Decimal('0.00'), Decimal('0.00'), Decimal('0.00'), True, []

    item_ids = [int(k) for k in session_cart.keys() if str(k).isdigit()]
    db_items = MenuItem.objects.filter(id__in=item_ids)
    db_map = {item.id: item for item in db_items}

    for item_id_str, qty in session_cart.items():
        try:
            iid = int(item_id_str)
            qty = int(qty)
            if qty <= 0:
                continue
            if iid in db_map:
                item = db_map[iid]
                if not item.is_available:
                    is_all_available = False
                    unavailable_names.append(item.name)

                line_subtotal = item.price * qty
                subtotal += line_subtotal
                items_data.append({
                    'item': item,
                    'id': item.id,
                    'name': item.name,
                    'price': item.price,
                    'quantity': qty,
                    'subtotal': line_subtotal,
                    'image_url': item.image_url,
                    'is_vegetarian': item.is_vegetarian,
                    'is_available': item.is_available,
                    'category_name': item.category.name,
                })
        except (ValueError, TypeError):
            continue

    tax = round(subtotal * tax_rate, 2)
    grand_total = subtotal + tax

    return items_data, subtotal, tax, grand_total, is_all_available, unavailable_names


@ensure_csrf_cookie
def menu_view(request):
    """
    Main restaurant menu list grouped by category with filtering.
    Supports category filtering, vegetarian filter, and keyword search.
    """
    categories = Category.objects.all().prefetch_related('items')
    selected_category = request.GET.get('category', 'all')
    veg_only = request.GET.get('veg', '0') == '1'
    search_query = request.GET.get('q', '').strip()

    items = MenuItem.objects.select_related('category').all()

    if selected_category and selected_category != 'all':
        items = items.filter(category__slug=selected_category)

    if veg_only:
        items = items.filter(is_vegetarian=True)

    if search_query:
        items = items.filter(name__icontains=search_query) | items.filter(description__icontains=search_query)

    context = {
        'categories': categories,
        'menu_items': items,
        'selected_category': selected_category,
        'veg_only': veg_only,
        'search_query': search_query,
    }
    return render(request, 'restaurant/menu.html', context)


# --- CART API & VIEWS ---

@require_POST
def cart_add_api(request):
    """
    Add an item to the Django session cart.
    Accepts JSON or form-encoded POST.
    """
    try:
        data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
        item_id = int(data.get('item_id'))
        quantity = int(data.get('quantity', 1))
    except (ValueError, TypeError, json.JSONDecodeError):
        return JsonResponse({'error': 'Invalid request parameters'}, status=400)

    if quantity <= 0:
        return JsonResponse({'error': 'Quantity must be positive'}, status=400)

    try:
        menu_item = MenuItem.objects.get(id=item_id)
    except MenuItem.DoesNotExist:
        return JsonResponse({'error': 'Menu item not found'}, status=404)

    if not menu_item.is_available:
        return JsonResponse({'error': f"'{menu_item.name}' is currently unavailable."}, status=400)

    cart = request.session.get('cart', {})
    current_qty = cart.get(str(item_id), 0)
    cart[str(item_id)] = current_qty + quantity
    request.session['cart'] = cart
    request.session.modified = True

    # Calculate current totals
    items_data, subtotal, tax, grand_total, _, _ = get_cart_details(cart)
    cart_count = sum(cart.values())

    return JsonResponse({
        'success': True,
        'message': f"Added '{menu_item.name}' to cart.",
        'item_id': item_id,
        'item_qty': cart[str(item_id)],
        'cart_count': cart_count,
        'subtotal': f"{subtotal:.2f}",
        'tax': f"{tax:.2f}",
        'grand_total': f"{grand_total:.2f}",
    })


@require_POST
def cart_update_api(request):
    """
    Update item quantity in session cart.
    If quantity <= 0, removes the item.
    """
    try:
        data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
        item_id = int(data.get('item_id'))
        quantity = int(data.get('quantity'))
    except (ValueError, TypeError, json.JSONDecodeError):
        return JsonResponse({'error': 'Invalid request parameters'}, status=400)

    cart = request.session.get('cart', {})
    str_id = str(item_id)

    if quantity <= 0:
        if str_id in cart:
            del cart[str_id]
    else:
        try:
            menu_item = MenuItem.objects.get(id=item_id)
            if not menu_item.is_available:
                return JsonResponse({'error': f"'{menu_item.name}' is unavailable."}, status=400)
        except MenuItem.DoesNotExist:
            return JsonResponse({'error': 'Menu item not found'}, status=404)

        cart[str_id] = quantity

    request.session['cart'] = cart
    request.session.modified = True

    items_data, subtotal, tax, grand_total, _, _ = get_cart_details(cart)
    cart_count = sum(cart.values())

    return JsonResponse({
        'success': True,
        'cart_count': cart_count,
        'subtotal': f"{subtotal:.2f}",
        'tax': f"{tax:.2f}",
        'grand_total': f"{grand_total:.2f}",
        'item_id': item_id,
        'item_qty': cart.get(str_id, 0),
    })


@require_POST
def cart_remove_api(request):
    """
    Remove an item completely from the session cart.
    """
    try:
        data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
        item_id = int(data.get('item_id'))
    except (ValueError, TypeError, json.JSONDecodeError):
        return JsonResponse({'error': 'Invalid request parameters'}, status=400)

    cart = request.session.get('cart', {})
    str_id = str(item_id)
    if str_id in cart:
        del cart[str_id]
        request.session['cart'] = cart
        request.session.modified = True

    items_data, subtotal, tax, grand_total, _, _ = get_cart_details(cart)
    cart_count = sum(cart.values())

    return JsonResponse({
        'success': True,
        'cart_count': cart_count,
        'subtotal': f"{subtotal:.2f}",
        'tax': f"{tax:.2f}",
        'grand_total': f"{grand_total:.2f}",
    })


@require_POST
def cart_clear_api(request):
    """
    Clear all items from session cart.
    """
    request.session['cart'] = {}
    request.session.modified = True
    return JsonResponse({
        'success': True,
        'cart_count': 0,
        'subtotal': '0.00',
        'tax': '0.00',
        'grand_total': '0.00',
    })


@require_GET
def cart_data_api(request):
    """
    Returns complete cart payload for client-side dynamic rendering.
    """
    cart = request.session.get('cart', {})
    items_data, subtotal, tax, grand_total, is_available, unavail = get_cart_details(cart)

    formatted_items = []
    for it in items_data:
        formatted_items.append({
            'id': it['id'],
            'name': it['name'],
            'price': str(it['price']),
            'quantity': it['quantity'],
            'subtotal': f"{it['subtotal']:.2f}",
            'image_url': it['image_url'],
            'is_vegetarian': it['is_vegetarian'],
            'is_available': it['is_available'],
            'category': it['category_name'],
        })

    return JsonResponse({
        'items': formatted_items,
        'cart_count': sum(cart.values()),
        'subtotal': f"{subtotal:.2f}",
        'tax': f"{tax:.2f}",
        'grand_total': f"{grand_total:.2f}",
        'is_all_available': is_available,
        'unavailable_names': unavail,
    })


# --- CHECKOUT WORKFLOW ---

def cart_page_view(request):
    """
    Dedicated Cart & Review Page.
    """
    cart = request.session.get('cart', {})
    items_data, subtotal, tax, grand_total, is_available, unavail = get_cart_details(cart)

    form = OrderCheckoutForm()
    context = {
        'cart_items': items_data,
        'subtotal': subtotal,
        'tax': tax,
        'grand_total': grand_total,
        'is_available': is_available,
        'unavailable_names': unavail,
        'form': form,
    }
    return render(request, 'restaurant/checkout.html', context)


@require_POST
def checkout_submit(request):
    """
    Handles Order creation with strict server-side validation:
    1. Cart cannot be empty.
    2. Quantities must be positive integers.
    3. Unavailable items are rejected.
    4. Totals are computed and verified on the server.
    5. Clears session cart upon success.
    """
    cart = request.session.get('cart', {})
    if not cart:
        messages.error(request, "Your cart is empty. Please add items before checking out.")
        return redirect('restaurant:menu')

    form = OrderCheckoutForm(request.POST)
    if not form.is_valid():
        messages.error(request, "Please provide all required checkout fields correctly.")
        items_data, subtotal, tax, grand_total, is_avail, unavail = get_cart_details(cart)
        return render(request, 'restaurant/checkout.html', {
            'form': form,
            'cart_items': items_data,
            'subtotal': subtotal,
            'tax': tax,
            'grand_total': grand_total,
        })

    # Validate items and calculate server-side totals
    items_data, subtotal, tax, grand_total, is_all_available, unavail = get_cart_details(cart)

    if not items_data:
        messages.error(request, "No valid items in cart.")
        return redirect('restaurant:menu')

    if not is_all_available:
        messages.error(request, f"Some items are out of stock: {', '.join(unavail)}. Please update your cart.")
        return redirect('restaurant:cart_page')

    try:
        with transaction.atomic():
            # Create Order
            order = form.save(commit=False)
            order.subtotal_amount = subtotal
            order.tax_amount = tax
            order.total_amount = grand_total
            order.status = Order.STATUS_RECEIVED
            order.save()

            # Create OrderItem records with locked prices
            order_items = []
            for item_info in items_data:
                order_items.append(OrderItem(
                    order=order,
                    menu_item=item_info['item'],
                    quantity=item_info['quantity'],
                    price=item_info['price'],
                ))
            OrderItem.objects.bulk_create(order_items)

            # Clear session cart
            request.session['cart'] = {}
            request.session.modified = True

    except Exception as exc:
        messages.error(request, f"An error occurred while placing your order: {str(exc)}")
        return redirect('restaurant:cart_page')

    messages.success(request, f"Order #{order.id} placed successfully! The kitchen has received your order.")

    # Support JSON response for AJAX checkout modal or form
    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.content_type == 'application/json':
        return JsonResponse({
            'success': True,
            'order_id': order.id,
            'redirect_url': reverse('restaurant:order_track', kwargs={'order_id': order.id}),
        })

    return redirect('restaurant:order_track', order_id=order.id)


# --- ORDER TRACKING ---

def order_track_view(request, order_id=None):
    """
    Order tracking view by Order ID.
    If no ID is passed in URL, checks query params ?order_id= or shows search form.
    """
    lookup_id = order_id or request.GET.get('order_id')
    order = None

    if lookup_id:
        try:
            order = Order.objects.prefetch_related('items__menu_item').get(id=int(lookup_id))
        except (ValueError, Order.DoesNotExist):
            messages.error(request, f"Order #{lookup_id} not found. Please check your Order ID.")

    context = {
        'order': order,
        'search_id': lookup_id,
    }
    return render(request, 'restaurant/order_track.html', context)


@require_GET
def order_status_api(request, order_id):
    """
    API endpoint for auto-polling order status from client.
    """
    try:
        order = Order.objects.get(id=order_id)
        return JsonResponse({
            'success': True,
            'id': order.id,
            'status': order.status,
            'status_display': order.get_status_display(),
            'status_step': order.status_step,
            'badge_class': order.badge_class,
            'updated_at': order.updated_at.strftime("%I:%M %p"),
        })
    except Order.DoesNotExist:
        return JsonResponse({'error': 'Order not found'}, status=404)


# --- KITCHEN DASHBOARD ---

def kitchen_dashboard_view(request):
    """
    Kitchen dashboard showing Received -> Preparing -> Ready -> Completed.
    Staff can filter and update order status in real time.
    """
    status_filter = request.GET.get('status', 'active')
    orders_qs = Order.objects.prefetch_related('items__menu_item').all()

    # Calculate status counts for dashboard metric badges
    counts = {
        'all': orders_qs.count(),
        'active': orders_qs.filter(status__in=[Order.STATUS_RECEIVED, Order.STATUS_PREPARING, Order.STATUS_READY]).count(),
        'received': orders_qs.filter(status=Order.STATUS_RECEIVED).count(),
        'preparing': orders_qs.filter(status=Order.STATUS_PREPARING).count(),
        'ready': orders_qs.filter(status=Order.STATUS_READY).count(),
        'completed': orders_qs.filter(status=Order.STATUS_COMPLETED).count(),
    }

    if status_filter == 'active':
        filtered_orders = orders_qs.filter(status__in=[Order.STATUS_RECEIVED, Order.STATUS_PREPARING, Order.STATUS_READY])
    elif status_filter == 'all':
        filtered_orders = orders_qs
    elif status_filter.upper() in dict(Order.STATUS_CHOICES):
        filtered_orders = orders_qs.filter(status=status_filter.upper())
    else:
        filtered_orders = orders_qs

    context = {
        'orders': filtered_orders,
        'counts': counts,
        'status_filter': status_filter,
        'status_choices': Order.STATUS_CHOICES,
    }
    return render(request, 'restaurant/kitchen_dashboard.html', context)


@require_POST
def kitchen_update_status(request, order_id):
    """
    Update order status directly from kitchen dashboard.
    Supports Next-Step advancement or explicit status setting.
    """
    order = get_object_or_404(Order, id=order_id)

    # Allow both form POST and JSON body
    if request.content_type == 'application/json':
        try:
            body = json.loads(request.body)
            new_status = body.get('status')
        except json.JSONDecodeError:
            new_status = None
    else:
        new_status = request.POST.get('status')

    # Step transition shortcuts:
    action = request.POST.get('action') or (body.get('action') if request.content_type == 'application/json' else None)
    if action == 'advance':
        if order.status == Order.STATUS_RECEIVED:
            new_status = Order.STATUS_PREPARING
        elif order.status == Order.STATUS_PREPARING:
            new_status = Order.STATUS_READY
        elif order.status == Order.STATUS_READY:
            new_status = Order.STATUS_COMPLETED

    valid_statuses = [choice[0] for choice in Order.STATUS_CHOICES]
    if new_status in valid_statuses:
        order.status = new_status
        order.save()
        msg = f"Order #{order.id} status updated to {order.get_status_display()}."
        messages.success(request, msg)

        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.content_type == 'application/json':
            return JsonResponse({
                'success': True,
                'order_id': order.id,
                'new_status': order.status,
                'status_display': order.get_status_display(),
                'status_step': order.status_step,
                'badge_class': order.badge_class,
            })
    else:
        messages.error(request, "Invalid status choice.")
        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.content_type == 'application/json':
            return JsonResponse({'error': 'Invalid status'}, status=400)

    # Return redirect back to kitchen dashboard preserving filter
    referer = request.META.get('HTTP_REFERER')
    if referer:
        return redirect(referer)
    return redirect('restaurant:kitchen_dashboard')


@require_GET
def kitchen_orders_api(request):
    """
    API for kitchen dashboard to poll active orders and new count.
    """
    active_orders = Order.objects.filter(
        status__in=[Order.STATUS_RECEIVED, Order.STATUS_PREPARING, Order.STATUS_READY]
    ).prefetch_related('items__menu_item')

    orders_data = []
    for order in active_orders:
        orders_data.append({
            'id': order.id,
            'customer_name': order.customer_name,
            'table_number': order.table_number,
            'total_amount': str(order.total_amount),
            'status': order.status,
            'status_display': order.get_status_display(),
            'badge_class': order.badge_class,
            'created_at': order.created_at.strftime("%I:%M %p"),
            'items': [
                {
                    'name': it.menu_item.name,
                    'quantity': it.quantity,
                }
                for it in order.items.all()
            ],
            'notes': order.special_notes,
        })

    return JsonResponse({
        'count': len(orders_data),
        'orders': orders_data,
    })
