from django.contrib import admin
from .models import Category, MenuItem, Order, OrderItem


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'icon', 'slug', 'order')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)
    ordering = ('order', 'name')


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'is_vegetarian', 'is_available', 'preparation_time')
    list_filter = ('category', 'is_vegetarian', 'is_available')
    search_fields = ('name', 'description')
    list_editable = ('price', 'is_available', 'is_vegetarian')


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('menu_item', 'quantity', 'price', 'subtotal')

    def subtotal(self, instance):
        return f"${instance.subtotal:.2f}"


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer_name', 'table_number', 'total_amount', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('customer_name', 'customer_phone', 'table_number', 'id')
    list_editable = ('status',)
    inlines = [OrderItemInline]
    readonly_fields = ('created_at', 'updated_at', 'subtotal_amount', 'tax_amount', 'total_amount')
    ordering = ('-created_at',)
    actions = ['mark_as_preparing', 'mark_as_ready', 'mark_as_completed']

    @admin.action(description="Mark selected orders as Preparing")
    def mark_as_preparing(self, request, queryset):
        queryset.update(status=Order.STATUS_PREPARING)

    @admin.action(description="Mark selected orders as Ready")
    def mark_as_ready(self, request, queryset):
        queryset.update(status=Order.STATUS_READY)

    @admin.action(description="Mark selected orders as Completed")
    def mark_as_completed(self, request, queryset):
        queryset.update(status=Order.STATUS_COMPLETED)


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'menu_item', 'quantity', 'price')
    list_filter = ('order__status',)
