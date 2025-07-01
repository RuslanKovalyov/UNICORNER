from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q, Sum, Count, F
from django.contrib.auth.decorators import user_passes_test
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.urls import reverse
from django.http import JsonResponse
from .models import Supplier, Category, Stock
from .forms import StockQuantityFormSet
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
    
    # Calculate total inventory value correctly: sum of (quantity * price) for each item
    total_value = Stock.objects.filter(is_active=True).aggregate(
        total=Sum(F('current_quantity') * F('unit_price'))
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
    """List all stocks with filtering options and inline editing"""
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
    
    # Handle POST request for inline editing
    if request.method == 'POST':
        # Check if this is an AJAX request for individual stock update
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' and request.POST.get('action') == 'save_single':
            try:
                stock_id = request.POST.get('stock_id')
                new_quantity = request.POST.get('quantity')
                
                # Validate inputs
                if not stock_id or new_quantity is None:
                    return JsonResponse({'success': False, 'error': 'Missing required data'})
                
                # Get the stock object
                stock = Stock.objects.get(id=stock_id, is_active=True)
                
                # Update the quantity
                stock.current_quantity = float(new_quantity)
                stock.save()
                
                return JsonResponse({'success': True, 'message': 'Stock updated successfully'})
                
            except Stock.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Stock item not found'})
            except ValueError:
                return JsonResponse({'success': False, 'error': 'Invalid quantity value'})
            except Exception as e:
                return JsonResponse({'success': False, 'error': str(e)})
        
        # Handle regular form submission (save all)
        else:
            formset = StockQuantityFormSet(request.POST, queryset=stocks)
            if formset.is_valid():
                updated_count = 0
                for form in formset:
                    if form.has_changed():
                        form.save()
                        updated_count += 1
                
                if updated_count > 0:
                    messages.success(request, f'Successfully updated {updated_count} stock quantities.')
                else:
                    messages.info(request, 'No changes were made.')
                
                # Rebuild the URL with current filters to maintain state after redirect
                base_url = reverse('warehouse:stock_list')
                params = []
                if supplier_filter:
                    params.append(f'supplier={supplier_filter}')
                if category_filter:
                    params.append(f'category={category_filter}')
                if search_query:
                    params.append(f'search={search_query}')
                if stock_status:
                    params.append(f'status={stock_status}')
                
                if params:
                    redirect_url = f"{base_url}?{'&'.join(params)}"
                else:
                    redirect_url = base_url
                
                return redirect(redirect_url)
            else:
                messages.error(request, 'There were errors in the form. Please check your input.')
    else:
        formset = StockQuantityFormSet(queryset=stocks)
    
    # Get filter options
    suppliers = Supplier.objects.filter(is_active=True, stocks__is_active=True).distinct()
    categories = Category.objects.filter(stocks__is_active=True).distinct()
    
    context = {
        'stocks': stocks,
        'formset': formset,
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
    
    # Group by supplier for easier ordering and calculate totals
    suppliers_with_reorders = {}
    grand_total = 0
    
    for stock in stocks:
        supplier = stock.supplier
        if supplier not in suppliers_with_reorders:
            suppliers_with_reorders[supplier] = {
                'stocks': [],
                'total_cost': 0,
                'total_items': 0
            }
        
        # Calculate suggested order quantity (2x minimum)
        suggested_quantity = stock.minimum_quantity * 2
        estimated_cost = suggested_quantity * stock.unit_price
        
        # Add calculated fields to stock object
        stock.suggested_quantity = suggested_quantity
        stock.estimated_cost = estimated_cost
        
        suppliers_with_reorders[supplier]['stocks'].append(stock)
        suppliers_with_reorders[supplier]['total_cost'] += estimated_cost
        suppliers_with_reorders[supplier]['total_items'] += 1
        grand_total += estimated_cost
    
    context = {
        'stocks': stocks,
        'suppliers_with_reorders': suppliers_with_reorders,
        'grand_total': grand_total,
    }
    return render(request, 'warehouse/reorder_list.html', context)
