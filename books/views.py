from django.views.generic import ListView, DetailView
from django.shortcuts import render
from django.db.models import Q
from core.models import Book


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


class BookDetailView(DetailView):
    model = Book
    template_name = 'books/book_detail.html'
    context_object_name = 'book'


# Create and Update views for registering books
from django.views.generic import CreateView, UpdateView
from django.urls import reverse_lazy
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import JsonResponse, HttpResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
import json, csv
from .forms import BookForm


@method_decorator(login_required, name='dispatch')
class BookCreateView(CreateView):
    model = Book
    form_class = BookForm
    template_name = 'books/book_form.html'
    success_url = reverse_lazy('books:book_table')


@method_decorator(login_required, name='dispatch')
class BookUpdateView(UpdateView):
    model = Book
    form_class = BookForm
    template_name = 'books/book_form.html'
    success_url = reverse_lazy('books:book_table')


@login_required
def book_table(request):
    """Display all books in an excel-like table. If ?export=csv provided, return CSV."""
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
