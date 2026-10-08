"""
Script to create default superuser and seed initial menu data for local & Render deployments.
"""
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")
django.setup()

from django.contrib.auth import get_user_model
from restaurant.models import Category, MenuItem, Order, OrderItem
from decimal import Decimal

User = get_user_model()


def create_superuser():
    username = os.environ.get("DJANGO_SUPERUSER_USERNAME", "admin")
    email = os.environ.get("DJANGO_SUPERUSER_EMAIL", "admin@example.com")
    password = os.environ.get("DJANGO_SUPERUSER_PASSWORD", "admin123")

    if not User.objects.filter(username=username).exists():
        print(f"Creating superuser '{username}'...")
        User.objects.create_superuser(username=username, email=email, password=password)
        print(f"Superuser '{username}' created successfully.")
    else:
        print(f"Superuser '{username}' already exists.")


def seed_menu_data():
    if Category.objects.exists() and MenuItem.objects.exists():
        print("Menu data already exists. Skipping seed.")
        return

    print("Seeding initial categories and menu items...")

    categories_data = [
        {"name": "Appetizers", "icon": "bi-egg-fried", "order": 1},
        {"name": "Main Course", "icon": "bi-fire", "order": 2},
        {"name": "Desserts", "icon": "bi-cake2", "order": 3},
        {"name": "Beverages", "icon": "bi-cup-straw", "order": 4},
    ]

    category_objs = {}
    for cat in categories_data:
        obj, _ = Category.objects.get_or_create(
            name=cat["name"],
            defaults={"icon": cat["icon"], "order": cat["order"]}
        )
        category_objs[cat["name"]] = obj

    menu_items_data = [
        # Appetizers
        {
            "category": "Appetizers",
            "name": "Crispy Truffle Fries",
            "description": "Hand-cut Idaho potatoes tossed in aromatic white truffle oil, grated aged parmesan, and fresh rosemary with garlic aioli.",
            "price": Decimal("8.99"),
            "is_vegetarian": True,
            "is_available": True,
            "image_url": "https://images.unsplash.com/photo-1576107232684-1279f3908594?auto=format&fit=crop&w=700&q=80",
            "preparation_time": 10,
        },
        {
            "category": "Appetizers",
            "name": "Artisanal Bruschetta",
            "description": "Toasted ciabatta rubbed with garlic, topped with heirloom vine tomatoes, fresh buffalo mozzarella, basil, and balsamic reduction glaze.",
            "price": Decimal("10.50"),
            "is_vegetarian": True,
            "is_available": True,
            "image_url": "https://images.unsplash.com/photo-1572695157366-5e585ab2b69f?auto=format&fit=crop&w=700&q=80",
            "preparation_time": 12,
        },
        {
            "category": "Appetizers",
            "name": "Smoked BBQ Chicken Wings",
            "description": "Hickory slow-smoked crispy chicken wings glazed in honey chipotle BBQ sauce, served with crisp celery and blue cheese dip.",
            "price": Decimal("12.99"),
            "is_vegetarian": False,
            "is_available": True,
            "image_url": "https://images.unsplash.com/photo-1567620832903-9fc6debc209f?auto=format&fit=crop&w=700&q=80",
            "preparation_time": 15,
        },
        {
            "category": "Appetizers",
            "name": "Golden Calamari Fritti",
            "description": "Tender Monterey calamari rings flash-fried to golden perfection, served with spicy marinara and charred lemon wedges.",
            "price": Decimal("13.50"),
            "is_vegetarian": False,
            "is_available": True,
            "image_url": "https://images.unsplash.com/photo-1599488615731-7e5c2823ff28?auto=format&fit=crop&w=700&q=80",
            "preparation_time": 12,
        },

        # Main Course
        {
            "category": "Main Course",
            "name": "Prime Wagyu Bacon Burger",
            "description": "Half-pound grilled Wagyu beef patty, applewood smoked bacon, caramelized onions, sharp cheddar, and secret sauce on brioche.",
            "price": Decimal("17.99"),
            "is_vegetarian": False,
            "is_available": True,
            "image_url": "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?auto=format&fit=crop&w=700&q=80",
            "preparation_time": 18,
        },
        {
            "category": "Main Course",
            "name": "Creamy Fettuccine Alfredo",
            "description": "Al dente egg fettuccine tossed in a rich velvet parmesan cream reduction with crushed black pepper and fresh garden parsley.",
            "price": Decimal("15.50"),
            "is_vegetarian": True,
            "is_available": True,
            "image_url": "https://images.unsplash.com/photo-1645112411341-6c4fd023714a?auto=format&fit=crop&w=700&q=80",
            "preparation_time": 15,
        },
        {
            "category": "Main Course",
            "name": "Wood-Fired Margherita Pizza",
            "description": "Neapolitan sourdough crust, San Marzano tomato sauce, fresh fior di latte mozzarella, fragrant basil leaves, and extra virgin olive oil.",
            "price": Decimal("16.00"),
            "is_vegetarian": True,
            "is_available": True,
            "image_url": "https://images.unsplash.com/photo-1604382355076-af4b0eb60143?auto=format&fit=crop&w=700&q=80",
            "preparation_time": 16,
        },
        {
            "category": "Main Course",
            "name": "Pan-Seared Atlantic Salmon",
            "description": "Wild-caught salmon filet seared crispy skin-on, nestled on lemon-dill asparagus risotto with caper beurre blanc sauce.",
            "price": Decimal("22.50"),
            "is_vegetarian": False,
            "is_available": True,
            "image_url": "https://images.unsplash.com/photo-1467003909585-2f8a72700288?auto=format&fit=crop&w=700&q=80",
            "preparation_time": 20,
        },
        {
            "category": "Main Course",
            "name": "Garden Harvest Buddha Bowl",
            "description": "Warm organic quinoa, roasted sweet potatoes, avocado, crisp chickpeas, purple cabbage, and tahini turmeric dressing.",
            "price": Decimal("14.50"),
            "is_vegetarian": True,
            "is_available": True,
            "image_url": "https://images.unsplash.com/photo-1540420773420-3366772f4999?auto=format&fit=crop&w=700&q=80",
            "preparation_time": 12,
        },

        # Desserts
        {
            "category": "Desserts",
            "name": "Molten Chocolate Lava Cake",
            "description": "Warm Belgian dark chocolate cake with a molten flowing ganache center, dusted in cocoa and served with vanilla bean gelato.",
            "price": Decimal("9.50"),
            "is_vegetarian": True,
            "is_available": True,
            "image_url": "https://images.unsplash.com/photo-1606313564200-e75d5e30476c?auto=format&fit=crop&w=700&q=80",
            "preparation_time": 12,
        },
        {
            "category": "Desserts",
            "name": "Classic Venetian Tiramisu",
            "description": "Savoiardi ladyfingers soaked in dark espresso and marsala wine, layered with fluffy mascarpone cream and Valrhona cocoa.",
            "price": Decimal("8.50"),
            "is_vegetarian": True,
            "is_available": True,
            "image_url": "https://images.unsplash.com/photo-1571877227200-a0d98ea607e9?auto=format&fit=crop&w=700&q=80",
            "preparation_time": 8,
        },
        {
            "category": "Desserts",
            "name": "New York Berry Cheesecake",
            "description": "Velvety baked cream cheesecake on a buttery graham cracker crust, topped with macerated wild berries and mint.",
            "price": Decimal("8.00"),
            "is_vegetarian": True,
            "is_available": True,
            "image_url": "https://images.unsplash.com/photo-1533134242443-d4fd215305ad?auto=format&fit=crop&w=700&q=80",
            "preparation_time": 8,
        },

        # Beverages
        {
            "category": "Beverages",
            "name": "Signature Cold Brew Coffee",
            "description": "Single-origin Arabica beans steeped for 20 hours, poured over ice with a velvety Madagascar vanilla sweet cream cap.",
            "price": Decimal("5.50"),
            "is_vegetarian": True,
            "is_available": True,
            "image_url": "https://images.unsplash.com/photo-1517701550927-30cf4ba1dba5?auto=format&fit=crop&w=700&q=80",
            "preparation_time": 5,
        },
        {
            "category": "Beverages",
            "name": "Passionfruit Mint Mocktail",
            "description": "Fresh muddled passionfruit pulp, fresh garden mint, Persian lime juice, and sparkling soda water over crushed ice.",
            "price": Decimal("6.50"),
            "is_vegetarian": True,
            "is_available": True,
            "image_url": "https://images.unsplash.com/photo-1513558161293-cdaf765ed2fd?auto=format&fit=crop&w=700&q=80",
            "preparation_time": 5,
        },
        {
            "category": "Beverages",
            "name": "Berry Hibiscus Iced Tea",
            "description": "Artisan brewed hibiscus herbal tea infused with raspberry purée, sweetened with agave and garnished with fresh lemon.",
            "price": Decimal("4.99"),
            "is_vegetarian": True,
            "is_available": True,
            "image_url": "https://images.unsplash.com/photo-1556679343-c7306c1976bc?auto=format&fit=crop&w=700&q=80",
            "preparation_time": 5,
        },
    ]

    for item_data in menu_items_data:
        cat_obj = category_objs[item_data["category"]]
        MenuItem.objects.get_or_create(
            name=item_data["name"],
            defaults={
                "category": cat_obj,
                "description": item_data["description"],
                "price": item_data["price"],
                "is_vegetarian": item_data["is_vegetarian"],
                "is_available": item_data["is_available"],
                "image_url": item_data["image_url"],
                "preparation_time": item_data["preparation_time"],
            }
        )

    print(f"Seeded {len(categories_data)} categories and {len(menu_items_data)} menu items successfully.")

    # Create 1 sample demo order for Kitchen Dashboard and Tracking showcase
    if not Order.objects.exists():
        burger = MenuItem.objects.filter(name="Prime Wagyu Bacon Burger").first()
        fries = MenuItem.objects.filter(name="Crispy Truffle Fries").first()
        coldbrew = MenuItem.objects.filter(name="Signature Cold Brew Coffee").first()

        if burger and fries and coldbrew:
            subtotal = burger.price + fries.price + coldbrew.price
            tax = round(subtotal * Decimal('0.05'), 2)
            total = subtotal + tax

            demo_order = Order.objects.create(
                customer_name="Alex Morgan",
                customer_phone="+1 555-0142",
                table_number="Table 7",
                special_notes="Extra napkins please! Medium-rare burger.",
                subtotal_amount=subtotal,
                tax_amount=tax,
                total_amount=total,
                status=Order.STATUS_PREPARING,
            )
            OrderItem.objects.create(order=demo_order, menu_item=burger, quantity=1, price=burger.price)
            OrderItem.objects.create(order=demo_order, menu_item=fries, quantity=1, price=fries.price)
            OrderItem.objects.create(order=demo_order, menu_item=coldbrew, quantity=1, price=coldbrew.price)
            print(f"Created sample Order #{demo_order.id} for Table 7.")


if __name__ == "__main__":
    create_superuser()
    seed_menu_data()
