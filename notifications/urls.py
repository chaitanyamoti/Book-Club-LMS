from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    path('', views.notifications_dashboard, name='dashboard'),
    path('send_welcome/', views.send_welcome, name='send_welcome'),
    path('send_overdue/', views.send_overdue, name='send_overdue'),
    path('announcements/', views.AnnouncementListView.as_view(), name='announcement_list'),
    path('inbox/', views.UserNotificationListView.as_view(), name='inbox'),
    path('track-open/<uuid:email_log_uuid>/', views.track_email_open, name='track_email_open'),
    path('track-click/<uuid:email_log_uuid>/<str:redirect_url_base64>/', views.track_click, name='track_click'),
]