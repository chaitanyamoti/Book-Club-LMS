from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse

# Ensure signals module is imported so handlers are registered
import users.signals  # noqa


class SignalsTests(TestCase):
    def test_user_profile_created_on_user_creation(self):
        user = User.objects.create_user(username='signaluser', password='p')
        self.assertTrue(hasattr(user, 'userprofile'))
        self.assertIsNotNone(user.userprofile)


class LoginViewTests(TestCase):
    def test_authenticated_user_redirected_from_login_page(self):
        """Test that authenticated users are redirected from login page"""
        # Create and login a user
        user = User.objects.create_user(username='testuser', email='test@example.com', password='password')
        self.client.login(username='testuser', password='password')

        # Try to access login page
        response = self.client.get(reverse('users:login'))

        # Should redirect to dashboard
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('core:dashboard'))

    def test_unauthenticated_user_can_access_login_page(self):
        """Test that unauthenticated users can access login page"""
        response = self.client.get(reverse('users:login'))

        # Should show login form
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/login.html')
