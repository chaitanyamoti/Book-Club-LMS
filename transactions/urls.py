from django.urls import path
from . import views

app_name = 'transactions'

urlpatterns = [
    path('', views.TransactionListView.as_view(), name='transaction_list'),
    path('issue/', views.issue_book, name='issue_book'),
    path('return/<int:pk>/', views.return_book, name='return_book'),
    path('extend/<int:pk>/', views.extend_due_date, name='extend_due_date'),
    path('scan-return/', views.scan_to_return, name='scan_to_return'),
    path('scan/<int:book_id>/', views.scan_and_transact, name='scan_and_transact'),
]