from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy


class AdminRequiredMixin(UserPassesTestMixin):
    """Mixin to require admin role"""
    def test_func(self):
        return self.request.user.userprofile.role == 'ADMIN'

    def handle_no_permission(self):
        return redirect('dashboard')


class MemberRequiredMixin(UserPassesTestMixin):
    """Mixin to require member role"""
    def test_func(self):
        return self.request.user.userprofile.role in ['ADMIN', 'MEMBER']

    def handle_no_permission(self):
        return redirect('login')
