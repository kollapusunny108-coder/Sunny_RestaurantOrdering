# Smart Restaurant Food Ordering & Kitchen Dashboard

A modern, full-stack restaurant ordering portal and real-time kitchen operations dashboard built with **Django 5.x**, **Bootstrap 5**, **JavaScript (ES6+)**, and **SQLite (db.sqlite3)**, configured for deployment on **Render**.

---

## 🍽️ Features

- **Responsive Food Menu**: Categorized dishes with dietary badges (Vegetarian 🌱 vs Non-Vegetarian), preparation time tags, prices, and high-res food imagery.
- **Dynamic Category Filtering**: Filter between *Appetizers*, *Main Course*, *Desserts*, and *Beverages*, with an instant *Pure Veg* toggle and search filter.
- **Interactive Shopping Cart**:
  - Slide-out offcanvas drawer accessible across all pages with live badge counter.
  - Subtotal, 5% restaurant sales tax, and grand total calculations.
  - Synchronized browser `localStorage` and Django session cart.
- **Server-Side Validated Checkout**:
  - Server verifies item availability and recalculates prices before saving.
  - Generates atomic `Order` and `OrderItem` records.
  - Clears session cart upon order placement.
- **Live 4-Stage Order Tracker**:
  - Track orders by ID: `Received` → `Preparing` → `Ready` → `Completed`.
  - Auto-polls status every 5 seconds without page reloads.
- **Kitchen Operations Dashboard (`/kitchen/`)**:
  - Live order tickets with itemized quantities, table numbers, and chef notes.
  - 1-click status advancement buttons (*Start Cooking* → *Mark Ready* → *Complete*).
  - Audio chime notification and 10s auto-refresh for incoming tickets.
- **Django Admin Portal (`/admin/`)**:
  - Full management of categories, menu items, orders, and inline line items.

---

## 🗂️ Project Structure

```text
├── manage.py
├── requirements.txt
├── render.yaml
├── create_superuser.py
├── README.md
├── .gitignore
├── mysite/
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
└── restaurant/
    ├── admin.py
    ├── apps.py
    ├── context_processors.py
    ├── forms.py
    ├── models.py
    ├── tests.py
    ├── urls.py
    ├── views.py
    ├── migrations/
    │   └── 0001_initial.py
    ├── templates/
    │   └── restaurant/
    │       ├── base.html
    │       ├── menu.html
    │       ├── checkout.html
    │       ├── order_track.html
    │       └── kitchen_dashboard.html
    └── static/
        ├── css/
        │   └── style.css
        └── js/
            ├── cart.js
            ├── kitchen.js
            └── main.js
```

---

## 🚀 Local Quickstart

1. **Activate Virtual Environment**:
   ```bash
   # Windows
   .\venv\Scripts\activate

   # macOS / Linux
   source venv/bin/activate
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run Migrations & Seed Sample Data**:
   ```bash
   python manage.py migrate
   python create_superuser.py
   ```
   *Default Admin:* `username: admin` | `password: admin123`

4. **Run Unit Tests**:
   ```bash
   python manage.py test
   ```

5. **Start Development Server**:
   ```bash
   python manage.py runserver
   ```
   Open [http://127.0.0.1:8000/](http://127.0.0.1:8000/) in your browser.

---

## ☁️ Render Deployment Instructions

This repository includes a pre-configured `render.yaml` blueprint.

1. **Push to GitHub**:
   ```bash
   git add .
   git commit -m "Initial commit for Render deployment"
   git branch -M main
   git push -u origin main
   ```

2. **Deploy on Render**:
   - Go to [dashboard.render.com](https://dashboard.render.com/).
   - Click **New +** → **Blueprint**.
   - Select your GitHub repository (`Sunny_RestaurantOrdering`).
   - Render automatically reads `render.yaml`, configures Python 3.11, runs migrations, executes `create_superuser.py`, and starts Gunicorn with WhiteNoise.

3. **Manual Setup Alternative**:
   - **Environment**: Python
   - **Build Command**: `pip install -r requirements.txt && python manage.py collectstatic --no-input && python manage.py migrate && python create_superuser.py`
   - **Start Command**: `python manage.py migrate && python create_superuser.py && gunicorn mysite.wsgi:application`
   - **Environment Variables**:
     - `RENDER`: `True`
     - `SECRET_KEY`: `<your-random-secret-key>`
     - `DJANGO_SUPERUSER_USERNAME`: `admin`
     - `DJANGO_SUPERUSER_PASSWORD`: `admin123`
