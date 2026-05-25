from django.urls import path
from . import views

app_name = 'books'

urlpatterns = [
    path('', views.BookListView.as_view(), name='book_list'),
    path('<int:pk>/', views.BookDetailView.as_view(), name='book_detail'),
    path('add/', views.BookCreateView.as_view(), name='book_add'),
    path('edit/<int:pk>/', views.BookUpdateView.as_view(), name='book_edit'),
    path('qr/<int:book_id>/', views.generate_qr_view, name='generate_qr'),
    path('table/', views.book_table, name='book_table'),
    path('table/update/', views.book_table_update, name='book_table_update'),
]