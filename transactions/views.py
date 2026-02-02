import json
from datetime import timedelta
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.contrib import messages
from core.models import Transaction, Book
from .forms import IssueBookForm, ReturnBookForm, ExtendDueDateForm
from django.utils import timezone
from django.http import JsonResponse
from notifications.utils_new import send_book_returned_email, send_book_issued_email # Import new email utility

from django.utils.decorators import method_decorator

@method_decorator(login_required, name='dispatch')
class TransactionListView(ListView):
    model = Transaction
    template_name = 'transactions/transaction_list.html'
    context_object_name = 'transactions'

    def get_queryset(self):
        """
        Admins/staff see all transactions.
        Regular members see only their own transactions.
        """
        if self.request.user.is_staff or self.request.user.is_superuser:
            return Transaction.objects.all().order_by('-issue_date')
        return Transaction.objects.filter(user=self.request.user).order_by('-issue_date')


@login_required
def issue_book(request):
    if request.method == 'POST':
        form = IssueBookForm(request.POST, request=request)
        if form.is_valid():
            book = form.cleaned_data['book']
            user_profile = form.cleaned_data['user']
            due_date = form.cleaned_data['due_date']
            admin_notes = form.cleaned_data['admin_notes']

            # Create transaction (signals will manage book availability)
            tx = Transaction.objects.create(
                book=book,
                user=user_profile.user,
                transaction_type='ISSUE',
                due_date=due_date,
                created_by=request.user,
                admin_notes=admin_notes
            )
            send_book_issued_email(tx) # Send book issued email

            messages.success(request, f'Book "{book.title}" issued to {user_profile.user.username}.')
            return redirect('transactions:transaction_list')
    else:
        form = IssueBookForm()

    return render(request, 'transactions/issue_book.html', {'form': form})


@login_required
def return_book(request, pk):
    tx = get_object_or_404(Transaction, pk=pk)

    # Check if the current user owns this transaction
    if tx.user != request.user:
        messages.error(request, 'You do not have permission to return this book.')
        return redirect('transactions:transaction_list')

    # Check if the book is already returned
    if tx.return_date:
        messages.error(request, 'This book has already been returned.')
        return redirect('transactions:transaction_list')

    if request.method == 'POST':
        form = ReturnBookForm(request.POST)
        if form.is_valid():
            condition_notes = form.cleaned_data['condition_notes']
            tx.return_date = timezone.now().date()
            tx.condition_notes = condition_notes
            tx.transaction_type = 'RETURN'
            tx.save()  # Signals will update book availability
            send_book_returned_email(tx) # Send book returned email

            messages.success(request, f'Book "{tx.book.title}" returned successfully.')
            return redirect('transactions:transaction_list')
    else:
        form = ReturnBookForm()

    return render(request, 'transactions/return_book.html', {'form': form, 'transaction': tx})

from core.utils import get_club_setting

@login_required
def extend_due_date(request, pk):
    tx = get_object_or_404(Transaction, pk=pk)

    # Check if the current user owns this transaction
    if tx.user != request.user:
        messages.error(request, 'You do not have permission to extend the due date for this book.')
        return redirect('transactions:transaction_list')

    # Check if the book is already returned
    if tx.return_date:
        messages.error(request, 'This book has already been returned.')
        return redirect('transactions:transaction_list')

    max_renewals = int(get_club_setting('MAX_RENEWALS_PER_LOAN', 2))
    renewal_period_days = int(get_club_setting('RENEWAL_PERIOD_DAYS', 7))

    if tx.renewed_count >= max_renewals:
        messages.error(request, f'Book "{tx.book.title}" has reached its maximum renewal limit ({max_renewals}).')
        return redirect('transactions:transaction_list')

    if request.method == 'POST':
        form = ExtendDueDateForm(request.POST, current_due_date=tx.due_date)
        if form.is_valid():
            new_due_date = form.cleaned_data['new_due_date']

            tx.due_date = new_due_date
            tx.renewed_count += 1
            tx.save()

            messages.success(request, f'Due date for "{tx.book.title}" extended to {new_due_date}.')
            return redirect('transactions:transaction_list')
    else:
        # Initial form display, set initial new_due_date based on current due_date + renewal period
        initial_new_due_date = tx.due_date + timedelta(days=renewal_period_days)
        form = ExtendDueDateForm(initial={'new_due_date': initial_new_due_date}, current_due_date=tx.due_date)

    return render(request, 'transactions/extend_due_date.html', {'form': form, 'transaction': tx})

@login_required
def scan_to_return(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            book_id = data.get('book_id')
            
            # Find the open transaction for the given book ID
            transaction = Transaction.objects.filter(book__id=book_id, return_date__isnull=True).first()

            if transaction:
                transaction.return_date = timezone.now().date()
                transaction.transaction_type = 'RETURN' # Set transaction type to RETURN
                transaction.save()
                send_book_returned_email(transaction) # Send book returned email
                
                # The signal should handle the available_copies update
                
                return JsonResponse({'success': True, 'message': f'Book "{transaction.book.title}" returned successfully.'})
            else:
                return JsonResponse({'success': False, 'message': 'No open transaction found for this book.'})
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'message': 'Invalid JSON.'})
    return render(request, 'transactions/scan_to_return.html')

from core.utils import get_club_setting

@login_required
def scan_and_transact(request, book_id):
    user = request.user
    message = ""
    error = ""
    book = None 

    try:
        with transaction.atomic():
            # Lock the book row for the duration of the transaction
            book = Book.objects.select_for_update().get(id=book_id)

            # Check for an open 'ISSUE' transaction for this book and user
            open_transaction = Transaction.objects.filter(book=book, user=user, return_date__isnull=True).first()

            if open_transaction:
                # A transaction exists, so this is a return.
                open_transaction.return_date = timezone.now().date()
                open_transaction.transaction_type = 'RETURN'
                open_transaction.save()
                send_book_returned_email(open_transaction) # Send book returned email
                # The post_save signal handles book availability update

                message = f"You have successfully returned '{book.title}'."
                messages.success(request, message)

            else:
                # No open transaction found, so this is a new issue.
                if book.available_copies > 0:
                    loan_period_days = int(get_club_setting('LOAN_PERIOD_DAYS', 14))
                    due_date = timezone.now().date() + timedelta(days=loan_period_days)
                    tx = Transaction.objects.create(
                        book=book,
                        user=user,
                        transaction_type='ISSUE',
                        due_date=due_date,
                        created_by=user
                    )
                    send_book_issued_email(tx) # Send book issued email

                    message = f"You have successfully checked out '{book.title}'. It is due on {due_date.strftime('%Y-%m-%d')}."
                    messages.success(request, message)
                else:
                    error = f"'{book.title}' is currently unavailable for checkout."
                    messages.error(request, error)

    except Book.DoesNotExist:
        error = "The scanned book does not exist."
        messages.error(request, error)
    except Exception as e:
        error = f"An unexpected error occurred: {e}"
        messages.error(request, error)


    # Render a result page
    return render(request, 'transactions/scan_result.html', {'message': message, 'error': error, 'book': book})