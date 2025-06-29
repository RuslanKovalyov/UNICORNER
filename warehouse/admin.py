from django.contrib import admin
from django.db.models import Count, Q
from .models import Supplier, Category, Stock
from .forms import CategoryForm, StockForm


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ['name', 'contact_person', 'email', 'phone', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'contact_person', 'email']
    list_editable = ['is_active']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'is_active')
        }),
        ('Contact Details', {
            'fields': ('contact_person', 'email', 'phone', 'address')
        }),
        ('Additional Information', {
            'fields': ('notes',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    form = CategoryForm
    list_display = ['name', 'description', 'stock_count']
    search_fields = ['name', 'description']
    
    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            stock_count=Count('stocks', filter=Q(stocks__is_active=True))
        )
    
    def stock_count(self, obj):
        return obj.stock_count
    stock_count.short_description = 'Active Stock Items'
    stock_count.admin_order_field = 'stock_count'


@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    form = StockForm
    list_display = [
        'name', 'category', 'supplier', 'current_quantity', 'minimum_quantity', 'unit', 
        'unit_price', 'get_stock_status', 'needs_reorder', 'is_active'
    ]
    list_filter = [
        'category', 'supplier', 'unit', 'needs_reorder', 'is_active', 'created_at'
    ]
    search_fields = ['name', 'description', 'supplier__name']
    list_editable = ['current_quantity', 'minimum_quantity', 'unit_price', 'is_active']
    readonly_fields = ['needs_reorder', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'category', 'supplier', 'is_active')
        }),
        ('Stock Details', {
            'fields': ('current_quantity', 'minimum_quantity', 'unit', 'unit_price')
        }),
        ('Status', {
            'fields': ('needs_reorder',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('category', 'supplier')

    actions = ['mark_for_reorder', 'unmark_for_reorder']

    def mark_for_reorder(self, request, queryset):
        updated = queryset.update(needs_reorder=True)
        self.message_user(request, f"{updated} items marked for reorder.")
    mark_for_reorder.short_description = "Mark selected items for reorder"

    def unmark_for_reorder(self, request, queryset):
        updated = queryset.update(needs_reorder=False)
        self.message_user(request, f"{updated} items unmarked for reorder.")
    unmark_for_reorder.short_description = "Unmark selected items for reorder"

    def get_stock_status(self, obj):
        return obj.stock_status
    get_stock_status.short_description = 'Status'
    get_stock_status.admin_order_field = 'current_quantity'

    def get_total_value(self, obj):
        return f"₪{obj.total_value:.2f}"
    get_total_value.short_description = 'Total Value'
