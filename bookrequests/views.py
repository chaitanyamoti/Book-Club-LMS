import json
from django.views.generic import ListView, CreateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib import messages
from core.models import BookRequest, Book
from .forms import BookRequestForm

class RequestListView(LoginRequiredMixin, ListView):
    model = BookRequest
    template_name = 'bookrequests/request_list.html'
    context_object_name = 'requests'

    def get_queryset(self):
        return BookRequest.objects.filter(user=self.request.user).order_by('-created_date')

class RequestCreateView(LoginRequiredMixin, CreateView):
    model = BookRequest
    form_class = BookRequestForm
    template_name = 'bookrequests/request_form.html'
    success_url = reverse_lazy('bookrequests:request_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        books = Book.objects.all()
        books_data = [{'id': book.id, 'title': book.title, 'author': book.author} for book in books]
        context['books_json'] = json.dumps(books_data)
        return context

    def form_valid(self, form):
        form.instance.user = self.request.user
        messages.success(self.request, 'Request submitted successfully.')
        return super().form_valid(form)

class RequestDeleteView(LoginRequiredMixin, DeleteView):
    model = BookRequest
    success_url = reverse_lazy('bookrequests:request_list')
    template_name = 'bookrequests/request_confirm_delete.html'

    def get_queryset(self):
        # Ensure user can only delete their own requests
        return BookRequest.objects.filter(user=self.request.user)

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Request cancelled.')
        return super().delete(request, *args, **kwargs)
