from django.shortcuts import render, get_object_or_404
from django.db.models import Q, Sum, Count
from django.contrib.auth.decorators import user_passes_test
from django.contrib.admin.views.decorators import staff_member_required
from .models import Supplier, Category, Stock
from .auth import staff_required


@staff_required
def warehouse_dashboard(request):
    """Main dashboard view showing overview of warehouse status"""
    suppliers = Supplier.objects.filter(is_active=True).annotate(
        stock_count=Count('stocks', filter=Q(stocks__is_active=True))
    )
    
    categories = Category.objects.all().annotate(
        stock_count=Count('stocks', filter=Q(stocks__is_active=True))
    )
    
    # Summary statistics
    total_stocks = Stock.objects.filter(is_active=True).count()
    low_stock_items = Stock.objects.filter(is_active=True, needs_reorder=True).count()
    out_of_stock = Stock.objects.filter(is_active=True, current_quantity=0).count()
    total_value = Stock.objects.filter(is_active=True).aggregate(
        total=Sum('current_quantity') * Sum('unit_price')
    )['total'] or 0
    
    context = {
        'suppliers': suppliers,
        'categories': categories,
        'stats': {
            'total_stocks': total_stocks,
            'low_stock_items': low_stock_items,
            'out_of_stock': out_of_stock,
            'total_value': total_value,
            'has_reorder_items': low_stock_items > 0,  # Add this flag
        }
    }
    return render(request, 'warehouse/dashboard.html', context)


@staff_required
def supplier_list(request):
    """List all suppliers with their stock counts"""
    suppliers = Supplier.objects.filter(is_active=True).annotate(
        stock_count=Count('stocks', filter=Q(stocks__is_active=True)),
        low_stock_count=Count('stocks', filter=Q(stocks__is_active=True, stocks__needs_reorder=True))
    ).order_by('name')
    
    context = {'suppliers': suppliers}
    return render(request, 'warehouse/supplier_list.html', context)


@staff_required
def supplier_detail(request, supplier_id):
    """Show stocks for a specific supplier"""
    supplier = get_object_or_404(Supplier, id=supplier_id, is_active=True)
    
    # Get filter parameters
    category_filter = request.GET.get('category')
    search_query = request.GET.get('search')
    stock_status = request.GET.get('status')
    
    # Start with supplier's active stocks
    stocks = Stock.objects.filter(supplier=supplier, is_active=True).select_related('category')
    
    # Apply filters
    if category_filter:
        stocks = stocks.filter(category__name=category_filter)
    
    if search_query:
        stocks = stocks.filter(
            Q(name__icontains=search_query) | 
            Q(description__icontains=search_query)
        )
    
    if stock_status == 'low':
        stocks = stocks.filter(needs_reorder=True)
    elif stock_status == 'out':
        stocks = stocks.filter(current_quantity=0)
    elif stock_status == 'in_stock':
        stocks = stocks.filter(current_quantity__gt=0, needs_reorder=False)
    
    stocks = stocks.order_by('category__name', 'name')
    
    # Get categories for filter dropdown
    categories = Category.objects.filter(stocks__supplier=supplier, stocks__is_active=True).distinct()
    
    context = {
        'supplier': supplier,
        'stocks': stocks,
        'categories': categories,
        'current_category': category_filter,
        'current_search': search_query,
        'current_status': stock_status,
    }
    return render(request, 'warehouse/supplier_detail.html', context)


@staff_required
def stock_list(request):
    """List all stocks with filtering options"""
    stocks = Stock.objects.filter(is_active=True).select_related('supplier', 'category')
    
    # Get filter parameters
    supplier_filter = request.GET.get('supplier')
    category_filter = request.GET.get('category')
    search_query = request.GET.get('search')
    stock_status = request.GET.get('status')
    
    # Apply filters
    if supplier_filter:
        stocks = stocks.filter(supplier_id=supplier_filter)
    
    if category_filter:
        stocks = stocks.filter(category__name=category_filter)
    
    if search_query:
        stocks = stocks.filter(
            Q(name__icontains=search_query) | 
            Q(description__icontains=search_query) |
            Q(supplier__name__icontains=search_query)
        )
    
    if stock_status == 'low':
        stocks = stocks.filter(needs_reorder=True)
    elif stock_status == 'out':
        stocks = stocks.filter(current_quantity=0)
    elif stock_status == 'in_stock':
        stocks = stocks.filter(current_quantity__gt=0, needs_reorder=False)
    
    stocks = stocks.order_by('supplier__name', 'category__name', 'name')
    
    # Get filter options
    suppliers = Supplier.objects.filter(is_active=True, stocks__is_active=True).distinct()
    categories = Category.objects.filter(stocks__is_active=True).distinct()
    
    context = {
        'stocks': stocks,
        'suppliers': suppliers,
        'categories': categories,
        'current_supplier': supplier_filter,
        'current_category': category_filter,
        'current_search': search_query,
        'current_status': stock_status,
    }
    return render(request, 'warehouse/stock_list.html', context)


@staff_required
def reorder_list(request):
    """Show items that need reordering"""
    stocks = Stock.objects.filter(
        is_active=True, 
        needs_reorder=True
    ).select_related('supplier', 'category').order_by('supplier__name', 'name')
    
    # Group by supplier for easier ordering
    suppliers_with_reorders = {}
    for stock in stocks:
        supplier = stock.supplier
        if supplier not in suppliers_with_reorders:
            suppliers_with_reorders[supplier] = []
        suppliers_with_reorders[supplier].append(stock)
    
    context = {
        'stocks': stocks,
        'suppliers_with_reorders': suppliers_with_reorders,
    }
    return render(request, 'warehouse/reorder_list.html', context)
