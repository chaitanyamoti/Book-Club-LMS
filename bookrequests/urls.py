from django.urls import path
from . import views

app_name = 'bookrequests'

urlpatterns = [
    path('', views.RequestListView.as_view(), name='request_list'),
    path('new/', views.RequestCreateView.as_view(), name='request_new'),
    path('<int:pk>/delete/', views.RequestDeleteView.as_view(), name='request_delete'),
]
