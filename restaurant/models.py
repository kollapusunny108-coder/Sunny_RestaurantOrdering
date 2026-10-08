from django.db import models
from django.utils.text import slugify


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    icon = models.CharField(
        max_length=50, 
        blank=True, 
        default='bi-egg-fried',
        help_text='Bootstrap icon class name, e.g. bi-egg-fried, bi-cup-straw, bi-cake2'
    )
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    order = models.PositiveIntegerField(default=0, help_text='Display ordering priority')

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['order', 'name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class MenuItem(models.Model):
    category = models.ForeignKey(
        Category, 
        on_delete=models.CASCADE, 
        related_name='items'
    )
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    is_vegetarian = models.BooleanField(default=False)
    is_available = models.BooleanField(default=True)
    image_url = models.URLField(max_length=500, blank=True, default='')
    preparation_time = models.PositiveIntegerField(
        default=15, 
        help_text='Estimated preparation time in minutes'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['category', 'name']

    def __str__(self):
        return f"{self.name} (${self.price})"


class Order(models.Model):
    STATUS_RECEIVED = 'RECEIVED'
    STATUS_PREPARING = 'PREPARING'
    STATUS_READY = 'READY'
    STATUS_COMPLETED = 'COMPLETED'
    STATUS_CANCELLED = 'CANCELLED'

    STATUS_CHOICES = [
        (STATUS_RECEIVED, 'Received'),
        (STATUS_PREPARING, 'Preparing'),
        (STATUS_READY, 'Ready'),
        (STATUS_COMPLETED, 'Completed'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]

    customer_name = models.CharField(max_length=100)
    customer_phone = models.CharField(max_length=20, blank=True)
    table_number = models.CharField(
        max_length=20, 
        help_text='Table number or order type (e.g. Table 4, Takeout)'
    )
    special_notes = models.TextField(blank=True)
    subtotal_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default=STATUS_RECEIVED
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Order #{self.id} - Table {self.table_number} ({self.get_status_display()})"

    @property
    def formatted_id(self):
        return f"#{self.id:04d}"

    @property
    def total_items_count(self):
        return sum(item.quantity for item in self.items.all())

    @property
    def status_step(self):
        steps = {
            self.STATUS_RECEIVED: 1,
            self.STATUS_PREPARING: 2,
            self.STATUS_READY: 3,
            self.STATUS_COMPLETED: 4,
            self.STATUS_CANCELLED: 0,
        }
        return steps.get(self.status, 1)

    @property
    def badge_class(self):
        classes = {
            self.STATUS_RECEIVED: 'bg-primary',
            self.STATUS_PREPARING: 'bg-warning text-dark',
            self.STATUS_READY: 'bg-info text-dark',
            self.STATUS_COMPLETED: 'bg-success',
            self.STATUS_CANCELLED: 'bg-danger',
        }
        return classes.get(self.status, 'bg-secondary')


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order, 
        on_delete=models.CASCADE, 
        related_name='items'
    )
    menu_item = models.ForeignKey(
        MenuItem, 
        on_delete=models.CASCADE, 
        related_name='order_items'
    )
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(
        max_digits=8, 
        decimal_places=2, 
        help_text='Price per unit at time of order'
    )

    def __str__(self):
        return f"{self.quantity}x {self.menu_item.name} for Order #{self.order_id}"

    @property
    def subtotal(self):
        return self.quantity * self.price
