from django.urls import path
from . import views

app_name = 'reading'

urlpatterns = [
    path('', views.ReadingLogView.as_view(), name='reading_log'),
    path('add/', views.create_reading_log, name='create_reading_log'),
    path('add/<int:book_id>/', views.create_reading_log, name='create_reading_log_for_book'),
    path('stats/', views.reading_stats, name='reading_stats'),
    path('challenges/<int:pk>/', views.challenge_detail_view, name='challenge_detail'),
    path('challenges/<int:pk>/join/', views.join_challenge_view, name='join_challenge'),
    path('groups/<int:pk>/', views.group_detail_view, name='group_detail'),
    path('groups/<int:pk>/invite/<int:user_id>/', views.invite_to_group_view, name='invite_to_group'),
]