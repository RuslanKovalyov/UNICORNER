from django.shortcuts import render
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q
from .models import DomainRank


def search_view(request):
    """Handle search requests"""
    query = request.GET.get('q', '')
    
    # For now, just print to console (placeholder for future functionality)
    if query:
        print(f"Search query received: {query}")
    
    context = {
        'query': query,
    }
    
    return render(request, 'search/search.html', context)


def crawler_dashboard(request):
    """
    Real-time dashboard showing crawler progress and domain rankings
    """
    # Get filter parameters
    show_processed = request.GET.get('processed', 'all')  # all, yes, no
    search_query = request.GET.get('search', '')
    page_num = request.GET.get('page', 1)
    
    # Base queryset
    domains = DomainRank.objects.using('search_db').all()
    
    # Filter by processing status
    if show_processed == 'yes':
        domains = domains.filter(processed=True)
    elif show_processed == 'no':
        domains = domains.filter(processed=False)
    
    # Filter by search query
    if search_query:
        domains = domains.filter(domain__icontains=search_query)
    
    # Order by rank descending
    domains = domains.order_by('-rank', 'processed', 'domain')
    
    # Pagination
    paginator = Paginator(domains, 50)  # 50 domains per page
    page_obj = paginator.get_page(page_num)
    
    # Statistics
    total_domains = DomainRank.objects.using('search_db').count()
    processed_count = DomainRank.objects.using('search_db').filter(processed=True).count()
    pending_count = total_domains - processed_count
    
    # Top domains
    top_domains = DomainRank.objects.using('search_db').order_by('-rank')[:10]
    
    # Recent activity (latest processed domains)
    recent_processed = DomainRank.objects.using('search_db').filter(
        processed=True
    ).order_by('-updated_at')[:5]
    
    context = {
        'page_obj': page_obj,
        'total_domains': total_domains,
        'processed_count': processed_count,
        'pending_count': pending_count,
        'top_domains': top_domains,
        'recent_processed': recent_processed,
        'show_processed': show_processed,
        'search_query': search_query,
    }
    
    return render(request, 'search/crawler_dashboard.html', context)


def crawler_api(request):
    """
    JSON API for real-time data updates
    """
    # Statistics
    total_domains = DomainRank.objects.using('search_db').count()
    processed_count = DomainRank.objects.using('search_db').filter(processed=True).count()
    pending_count = total_domains - processed_count
    
    # Top 10 domains
    top_domains = list(DomainRank.objects.using('search_db').order_by('-rank')[:10].values(
        'domain', 'rank', 'processed', 'updated_at'
    ))
    
    # Recent activity
    recent = list(DomainRank.objects.using('search_db').filter(
        processed=True
    ).order_by('-updated_at')[:5].values(
        'domain', 'rank', 'updated_at'
    ))
    
    # Currently being processed (recently updated, not processed)
    currently_processing = DomainRank.objects.using('search_db').filter(
        processed=False
    ).order_by('-updated_at').first()
    
    return JsonResponse({
        'stats': {
            'total_domains': total_domains,
            'processed_count': processed_count,
            'pending_count': pending_count,
        },
        'top_domains': top_domains,
        'recent_activity': recent,
        'currently_processing': {
            'domain': currently_processing.domain if currently_processing else None,
            'rank': currently_processing.rank if currently_processing else 0,
        }
    })
