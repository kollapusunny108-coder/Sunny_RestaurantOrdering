from decimal import Decimal
import json
from django.test import TestCase, Client
from django.urls import reverse
from .models import Category, MenuItem, Order, OrderItem


class RestaurantPortalTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.category = Category.objects.create(name="Appetizers", icon="bi-egg-fried")
        self.item_avail = MenuItem.objects.create(
            category=self.category,
            name="Spring Rolls",
            description="Crispy rolls with sweet chili dip",
            price=Decimal("6.00"),
            is_vegetarian=True,
            is_available=True,
        )
        self.item_unavail = MenuItem.objects.create(
            category=self.category,
            name="Seasonal Truffles",
            description="Out of season",
            price=Decimal("15.00"),
            is_vegetarian=True,
            is_available=False,
        )

    def test_menu_view(self):
        response = self.client.get(reverse('restaurant:menu'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Spring Rolls")
        self.assertContains(response, "$6.00")

    def test_cart_add_and_data_api(self):
        # Add item to cart
        res = self.client.post(
            reverse('restaurant:cart_add'),
            json.dumps({'item_id': self.item_avail.id, 'quantity': 2}),
            content_type='application/json'
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['cart_count'], 2)
        self.assertEqual(data['subtotal'], '12.00')
        self.assertEqual(data['tax'], '0.60')  # 5% of 12.00
        self.assertEqual(data['grand_total'], '12.60')

        # Check cart data api
        data_res = self.client.get(reverse('restaurant:cart_data'))
        self.assertEqual(data_res.status_code, 200)
        cart_info = data_res.json()
        self.assertEqual(len(cart_info['items']), 1)
        self.assertEqual(cart_info['items'][0]['quantity'], 2)

    def test_cart_prevents_unavailable_item(self):
        res = self.client.post(
            reverse('restaurant:cart_add'),
            json.dumps({'item_id': self.item_unavail.id, 'quantity': 1}),
            content_type='application/json'
        )
        self.assertEqual(res.status_code, 400)
        self.assertIn('error', res.json())

    def test_checkout_server_side_calculation_and_cart_clearing(self):
        # 1. Put item in cart
        self.client.post(
            reverse('restaurant:cart_add'),
            json.dumps({'item_id': self.item_avail.id, 'quantity': 3}),
            content_type='application/json'
        )
        # 2. Checkout
        checkout_data = {
            'customer_name': 'Jane Doe',
            'customer_phone': '555-1234',
            'table_number': 'Table 5',
            'special_notes': 'Hot sauce please',
        }
        res = self.client.post(reverse('restaurant:checkout'), checkout_data)
        self.assertEqual(res.status_code, 302)  # Redirects to tracking

        # 3. Check Order created in DB
        order = Order.objects.get(customer_name='Jane Doe')
        self.assertEqual(order.table_number, 'Table 5')
        self.assertEqual(order.subtotal_amount, Decimal('18.00')) # 3 * 6.00
        self.assertEqual(order.tax_amount, Decimal('0.90'))       # 5% of 18.00
        self.assertEqual(order.total_amount, Decimal('18.90'))
        self.assertEqual(order.status, Order.STATUS_RECEIVED)

        # 4. Check OrderItem created
        self.assertEqual(order.items.count(), 1)
        order_item = order.items.first()
        self.assertEqual(order_item.menu_item, self.item_avail)
        self.assertEqual(order_item.quantity, 3)
        self.assertEqual(order_item.price, Decimal('6.00'))

        # 5. Check session cart was cleared
        session_cart = self.client.session.get('cart', {})
        self.assertEqual(session_cart, {})

    def test_kitchen_advance_status(self):
        order = Order.objects.create(
            customer_name="Test Customer",
            customer_phone="555-0000",
            table_number="Table 1",
            subtotal_amount=Decimal('10.00'),
            tax_amount=Decimal('0.50'),
            total_amount=Decimal('10.50'),
            status=Order.STATUS_RECEIVED,
        )
        # Advance 1: RECEIVED -> PREPARING
        res1 = self.client.post(
            reverse('restaurant:kitchen_update_status', args=[order.id]),
            json.dumps({'action': 'advance'}),
            content_type='application/json'
        )
        self.assertEqual(res1.status_code, 200)
        order.refresh_from_db()
        self.assertEqual(order.status, Order.STATUS_PREPARING)

        # Advance 2: PREPARING -> READY
        res2 = self.client.post(
            reverse('restaurant:kitchen_update_status', args=[order.id]),
            json.dumps({'action': 'advance'}),
            content_type='application/json'
        )
        self.assertEqual(res2.status_code, 200)
        order.refresh_from_db()
        self.assertEqual(order.status, Order.STATUS_READY)

        # Advance 3: READY -> COMPLETED
        res3 = self.client.post(
            reverse('restaurant:kitchen_update_status', args=[order.id]),
            json.dumps({'action': 'advance'}),
            content_type='application/json'
        )
        self.assertEqual(res3.status_code, 200)
        order.refresh_from_db()
        self.assertEqual(order.status, Order.STATUS_COMPLETED)

    def test_order_tracking_view_and_api(self):
        order = Order.objects.create(
            customer_name="Track Me",
            customer_phone="555-8888",
            table_number="Table 9",
            subtotal_amount=Decimal('10.00'),
            tax_amount=Decimal('0.50'),
            total_amount=Decimal('10.50'),
            status=Order.STATUS_PREPARING,
        )
        # View page
        res = self.client.get(reverse('restaurant:order_track', args=[order.id]))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "Track Me")
        self.assertContains(res, "Table 9")

        # API poll
        api_res = self.client.get(reverse('restaurant:order_status_api', args=[order.id]))
        self.assertEqual(api_res.status_code, 200)
        api_data = api_res.json()
        self.assertEqual(api_data['status'], 'PREPARING')
        self.assertEqual(api_data['status_step'], 2)
