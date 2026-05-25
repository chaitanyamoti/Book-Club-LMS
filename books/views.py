from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.shortcuts import render, redirect
from django.db.models import Q
from core.models import Book
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin # Import these mixins
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import JsonResponse, HttpResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
import json, csv, qrcode
from io import BytesIO
from .forms import BookForm


@login_required
def generate_qr_view(request, book_id):
    """Generate a QR code on the fly and return it as an image response."""
    book = get_object_or_404(Book, id=book_id)
    
    # Generate the absolute URL for the transaction page
    path = reverse_lazy('transactions:scan_and_transact', args=[book.id])
    
    from django.conf import settings
    domain = getattr(settings, 'RENDER_EXTERNAL_HOSTNAME', None)
    if domain:
        url = f"https://{domain}{path}"
    else:
        # Get host from request if not on Render
        url = request.build_absolute_uri(path)
    
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    
    return HttpResponse(buffer.getvalue(), content_type="image/png")


@method_decorator(login_required(login_url='users:login'), name='dispatch')
class BookListView(ListView):
    model = Book
    template_name = 'books/book_list.html'
    context_object_name = 'books'
    paginate_by = 12

    def get_queryset(self):
        qs = super().get_queryset().filter(status='AVAILABLE')
        q = self.request.GET.get('q')
        if q:
            qs = qs.filter(Q(title__icontains=q) | Q(author__icontains=q) | Q(isbn__icontains=q))
        return qs


@method_decorator(login_required(login_url='users:login'), name='dispatch')
class BookDetailView(DetailView):
    model = Book
    template_name = 'books/book_detail.html'
    context_object_name = 'book'


# Create and Update views for registering books

class StaffRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser
    
    def handle_no_permission(self):
        # Redirect to the dashboard or a permission denied page if not staff/superuser
        return redirect('core:dashboard')


class BookCreateView(StaffRequiredMixin, CreateView): # Apply the mixin
    model = Book
    form_class = BookForm
    template_name = 'books/book_form.html'
    success_url = reverse_lazy('books:book_table')


class BookUpdateView(StaffRequiredMixin, UpdateView): # Apply the mixin
    model = Book
    form_class = BookForm
    template_name = 'books/book_form.html'
    success_url = reverse_lazy('books:book_table')


@login_required
def book_table(request):
    """Display all books in an excel-like table. If ?export=csv provided, return CSV."""
    # Ensure only staff can access this view
    if not (request.user.is_staff or request.user.is_superuser):
        return redirect('core:dashboard') # Redirect non-staff to dashboard

    qs = Book.objects.all().order_by('id')

    # Export CSV
    if request.GET.get('export') == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="books_export.csv"'
        writer = csv.writer(response)
        headers = ['id', 'title', 'author', 'isbn', 'genre', 'total_copies', 'available_copies', 'status']
        writer.writerow(headers)
        for b in qs:
            writer.writerow([b.id, b.title, b.author, b.isbn, b.genre, b.total_copies, b.available_copies, b.status])
        return response

    return render(request, 'books/book_table.html', {'books': qs})


from django.forms.models import model_to_dict

@login_required
@csrf_exempt
def book_table_update(request):
    """Accept JSON POST of changed rows and update books accordingly."""
    # Ensure only staff can access this view
    if not (request.user.is_staff or request.user.is_superuser):
        return JsonResponse({'error': 'Permission denied'}, status=403)

    if request.method != 'POST':
        return HttpResponseBadRequest('Invalid method')

    try:
        payload = json.loads(request.body.decode('utf-8'))
    except json.JSONDecodeError:
        return HttpResponseBadRequest('Invalid JSON')

    updated = []
    errors = []
    for row in payload.get('rows', []):
        bid = row.get('id')
        if not bid:
            continue
        
        try:
            book = get_object_or_404(Book, pk=bid)
            
            # Prepare data for validation by combining existing data with new data
            form_data = model_to_dict(book)
            form_data.update(row)

            # Type casting for integers from the row before validation
            for int_fld in ('total_copies', 'available_copies'):
                if int_fld in row:
                    try:
                        form_data[int_fld] = int(form_data[int_fld])
                    except (ValueError, TypeError):
                        errors.append({'id': bid, 'field': int_fld, 'error': 'invalid_int'})
                        continue
            
            form = BookForm(instance=book, data=form_data)
            
            if form.is_valid():
                form.save()
                updated.append(book.id)
            else:
                errors.append({'id': bid, 'errors': form.errors})
                
        except Book.DoesNotExist:
            errors.append({'id': bid, 'errors': 'Book not found.'})
        except Exception as e:
            errors.append({'id': bid, 'errors': str(e)})

    return JsonResponse({'updated': updated, 'errors': errors})
