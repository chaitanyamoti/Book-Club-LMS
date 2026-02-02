from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/admin/', views.AdminDashboardView.as_view(), name='admin_dashboard'),
    path('dashboard/member/', views.MemberDashboardView.as_view(), name='member_dashboard'),
    path('dashboard/data/', views.dashboard_data, name='dashboard_data'),
    path('bulk_mark_available/', views.bulk_mark_available, name='bulk_mark_available'),
    path('bulk_generate_qr/', views.bulk_generate_qr, name='bulk_generate_qr'),
]
