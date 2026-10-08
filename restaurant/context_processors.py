from .models import MenuItem

def cart_context(request):
    """
    Provides global access to the session cart data, item count, and subtotal.
    """
    cart = request.session.get('cart', {})
    cart_count = 0
    cart_subtotal = 0.0

    # cart format: {str(item_id): int(quantity)}
    if cart:
        item_ids = [int(item_id) for item_id in cart.keys() if item_id.isdigit()]
        menu_items = MenuItem.objects.filter(id__in=item_ids)
        items_by_id = {item.id: item for item in menu_items}

        for item_id_str, qty in cart.items():
            try:
                iid = int(item_id_str)
                if iid in items_by_id:
                    cart_count += qty
                    cart_subtotal += float(items_by_id[iid].price) * qty
            except (ValueError, TypeError):
                continue

    tax = round(cart_subtotal * 0.05, 2)  # 5% restaurant sales tax
    grand_total = round(cart_subtotal + tax, 2)

    return {
        'session_cart': cart,
        'cart_count': cart_count,
        'cart_subtotal': f"{cart_subtotal:.2f}",
        'cart_tax': f"{tax:.2f}",
        'cart_grand_total': f"{grand_total:.2f}",
    }
