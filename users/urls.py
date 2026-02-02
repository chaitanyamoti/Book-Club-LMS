from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'users'

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('<int:user_id>/', views.public_profile_view, name='public_profile'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('settings/', views.settings_view, name='settings'),

    # Security & Profile Management
    path('password-change/', views.password_change_view, name='password_change'),
    path('email-change/', views.email_change_view, name='email_change'),
    path('avatar-upload/', views.avatar_upload_view, name='avatar_upload'),
    path('notification-preferences/', views.notification_preferences_view, name='notification_preferences'),
    path('session-management/', views.session_management_view, name='session_management'),
    path('audit-log/', views.audit_log_view, name='audit_log'),
    path('account-deletion/', views.account_deletion_view, name='account_deletion'),

    # Admin views
    path('admin/users/', views.user_list_view, name='user_list'),
    path('admin/users/<int:user_id>/toggle/', views.toggle_user_status, name='toggle_user_status'),
    path('admin/users/<int:user_id>/role/', views.change_user_role, name='change_user_role'),

    # Password reset
    path('password_reset/', auth_views.PasswordResetView.as_view(
        template_name='registration/password_reset.html',
        email_template_name='registration/password_reset_email.html',
        subject_template_name='registration/password_reset_subject.txt'
    ), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='registration/password_reset_done.html'
    ), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='registration/password_reset_confirm.html'
    ), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name='registration/password_reset_complete.html'
    ), name='password_reset_complete'),
]
