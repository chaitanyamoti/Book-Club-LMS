from django.shortcuts import render
from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from core.models import Book, Transaction, UserProfile, ReadingLog
from notifications.models import Announcement # Import Announcement model


from django.db.models import Q # New Import

class HomeView(TemplateView):
    template_name = 'home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.now()
        context['announcements'] = Announcement.objects.filter(
            is_active=True, 
            display_on_homepage=True,
            pub_date__lte=today,
        ).filter( # Apply Q objects in a separate filter call
            Q(end_date__isnull=True) | Q(end_date__gte=today)
        ).order_by('-pub_date')[:3]
        return context


@login_required
def dashboard(request):
    """
    Shows a personalized dashboard for the logged-in user, including their
    currently checked-out books and any overdue items.
    """
    # Fetch all of the user's transactions that are still open (book not returned)
    open_transactions = Transaction.objects.filter(
        user=request.user,
        return_date__isnull=True
    ).order_by('due_date')

    # From the open transactions, filter out the ones that are overdue
    overdue_transactions = open_transactions.filter(
        due_date__lt=timezone.now().date()
    )

    today = timezone.now()
    announcements = Announcement.objects.filter(
        is_active=True,
        display_on_homepage=True,
        pub_date__lte=today,
    ).filter( # Apply Q objects in a separate filter call
        Q(end_date__isnull=True) | Q(end_date__gte=today)
    ).order_by('-pub_date')[:3]

    # Get available books for the dashboard
    available_books = Book.objects.filter(available_copies__gt=0)[:8]

    # Get latest reading progress for each issued book
    reading_progress = {}
    for tx in open_transactions:
        latest_log = ReadingLog.objects.filter(
            user=request.user,
            book=tx.book
        ).order_by('-log_date').first()
        reading_progress[tx.book.id] = latest_log

    context = {
        'open_transactions': open_transactions,
        'overdue_transactions': overdue_transactions,
        'announcements': announcements,
        'available_books': available_books,
        'reading_progress': reading_progress,
    }
    return render(request, 'dashboard/dashboard.html', context)


class AdminDashboardView(TemplateView):
    template_name = 'dashboard/admin_dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Book circulation analytics
        total_books = Book.objects.count()
        available_books = Book.objects.filter(status='AVAILABLE').count()
        issued_books = Book.objects.filter(status='ISSUED').count()
        overdue_books = Transaction.objects.filter(
            return_date__isnull=True,
            due_date__lt=timezone.now().date()
        ).count()

        # User statistics
        total_members = UserProfile.objects.filter(is_active=True).count()
        active_members = Transaction.objects.filter(
            return_date__isnull=True
        ).values('user').distinct().count()

        # Transaction statistics (last 30 days)
        thirty_days_ago = timezone.now() - timezone.timedelta(days=30)
        recent_issues = Transaction.objects.filter(
            transaction_type='ISSUE',
            issue_date__gte=thirty_days_ago
        ).count()
        recent_returns = Transaction.objects.filter(
            transaction_type='RETURN',
            return_date__gte=thirty_days_ago
        ).count()

        # Popular books (most issued)
        popular_books = Book.objects.annotate(
            issue_count=models.Count('transaction')
        ).filter(transaction__transaction_type='ISSUE').order_by('-issue_count')[:10]

        # Recent activity
        recent_transactions = Transaction.objects.all().order_by('-issue_date')[:10]

        # System alerts
        alerts = []
        if overdue_books > 0:
            alerts.append({
                'type': 'warning',
                'message': f'{overdue_books} books are currently overdue',
                'action': 'View Overdue Books'
            })
        if available_books < total_books * 0.1:  # Less than 10% available
            alerts.append({
                'type': 'info',
                'message': 'Low book availability - consider adding more books',
                'action': 'Add Books'
            })

        context.update({
            'total_books': total_books,
            'available_books': available_books,
            'issued_books': issued_books,
            'overdue_books': overdue_books,
            'total_members': total_members,
            'active_members': active_members,
            'recent_issues': recent_issues,
            'recent_returns': recent_returns,
            'popular_books': popular_books,
            'recent_transactions': recent_transactions,
            'alerts': alerts,
        })

        return context


class MemberDashboardView(TemplateView):
    template_name = 'dashboard/member_dashboard.html'


@login_required
def dashboard_data(request):
    # Return basic stats as JSON (for JS dashboard)
    total_books = Book.objects.count()
    total_members = UserProfile.objects.filter(is_active=True).count()
    total_issues = Transaction.objects.filter(transaction_type='ISSUE').count()
    overdue_count = Transaction.objects.filter(return_date__isnull=True, due_date__lt=timezone.now().date()).count()

    data = {
        'total_books': total_books,
        'total_members': total_members,
        'total_issues': total_issues,
        'overdue_count': overdue_count,
    }
    return JsonResponse(data)


@login_required
def bulk_mark_available(request):
    """Bulk mark books as available (admin only)."""
    if not request.user.is_staff:
        return JsonResponse({'error': 'Permission denied'}, status=403)

    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    # Mark books that are issued but have been returned as available
    # This is a simplified version - in reality you'd have more complex logic
    updated = 0
    try:
        # Books that are marked as ISSUED but have all copies returned
        issued_books = Book.objects.filter(status='ISSUED')
        for book in issued_books:
            active_transactions = Transaction.objects.filter(
                book=book,
                return_date__isnull=True
            ).count()
            if active_transactions == 0:
                book.status = 'AVAILABLE'
                book.save()
                updated += 1
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'updated': updated})


@login_required
def bulk_generate_qr(request):
    """Bulk generate QR codes for books (admin only)."""
    if not request.user.is_staff:
        return JsonResponse({'error': 'Permission denied'}, status=403)

    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    generated = 0
    try:
        from books.utils import generate_qr_code
        books_without_qr = Book.objects.filter(qr_code='')
        for book in books_without_qr:
            if not book.qr_code:
                generate_qr_code(book)
                book.save()
                generated += 1
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'generated': generated})
