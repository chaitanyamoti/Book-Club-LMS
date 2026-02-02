from django.views.generic import ListView
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.contrib import messages
from core.models import ReadingLog, Book
from django.utils import timezone
from datetime import timedelta
from django import forms

class ReadingLogForm(forms.ModelForm):
    class Meta:
        model = ReadingLog
        fields = ['book', 'log_date', 'read_today', 'pages_read', 'minutes_read', 'notes', 'progress']
        widgets = {
            'log_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }

@method_decorator(login_required, name='dispatch')
class ReadingLogView(ListView):
    model = ReadingLog
    template_name = 'reading/reading_log.html'
    context_object_name = 'logs'

    def get_queryset(self):
        # Only show logs for current user
        return ReadingLog.objects.filter(user=self.request.user).order_by('-log_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Calculate totals for quick stats
        user_logs = ReadingLog.objects.filter(user=self.request.user)
        context['total_pages_read'] = user_logs.aggregate(total=Sum('pages_read'))['total'] or 0
        context['total_minutes_read'] = user_logs.aggregate(total=Sum('minutes_read'))['total'] or 0

        return context


from django.shortcuts import get_object_or_404

@login_required
def create_reading_log(request, book_id=None):
    initial_data = {}
    if book_id:
        book = get_object_or_404(Book, id=book_id)
        initial_data['book'] = book

    if request.method == 'POST':
        form = ReadingLogForm(request.POST)
        if form.is_valid():
            rl = form.save(commit=False)
            rl.user = request.user
            rl.save()

            # Update Streak
            try:
                profile = request.user.userprofile
                today = timezone.now().date()
                last_read = profile.last_reading_date

                if last_read == today:
                    pass  # Already counted for today
                elif last_read == today - timedelta(days=1):
                    profile.streak_days += 1
                else:
                    profile.streak_days = 1  # Reset streak

                if profile.streak_days > profile.longest_streak:
                    profile.longest_streak = profile.streak_days

                profile.last_reading_date = today
                profile.save()
                messages.success(request, f'Reading log added. Current streak: {profile.streak_days} days!')
            except Exception as e:
                # Fallback if profile doesn't exist or other error
                messages.success(request, 'Reading log added.')

            return redirect('reading:reading_log')
    else:
        form = ReadingLogForm(initial=initial_data)

    return render(request, 'reading/reading_log_form.html', {'form': form})


from django.db.models import Sum
from .models import ReadingChallenge, UserReadingChallenge, ReadingGroup, GroupMembership
from notifications.utils_new import send_challenge_invitation_email, send_reading_group_invitation_email
from django.contrib.auth.models import User # Import User model

@login_required
def reading_stats(request):
    """Render a page with reading statistics for the current user."""
    user_logs = ReadingLog.objects.filter(user=request.user)
    
    # Calculate stats using efficient database queries
    total_days = user_logs.values('log_date').distinct().count()
    total_minutes = user_logs.aggregate(total=Sum('minutes_read'))['total'] or 0
    
    context = {
        'total_days': total_days,
        'total_minutes': total_minutes,
        'total_books': user_logs.values('book').distinct().count(),
    }
    return render(request, 'reading/reading_stats.html', context)

@login_required
def challenge_detail_view(request, pk):
    challenge = get_object_or_404(ReadingChallenge, pk=pk)
    # Placeholder logic
    return render(request, 'reading/challenge_detail.html', {'challenge': challenge})

@login_required
def join_challenge_view(request, pk):
    challenge = get_object_or_404(ReadingChallenge, pk=pk)
    # Placeholder logic
    user_challenge, created = UserReadingChallenge.objects.get_or_create(user=request.user, challenge=challenge)
    if created:
        send_challenge_invitation_email(request.user, challenge)
        messages.success(request, f"You have joined the '{challenge.name}' challenge!")
    else:
        messages.info(request, f"You are already part of the '{challenge.name}' challenge.")
    return redirect('reading:challenge_detail', pk=pk)

@login_required
def group_detail_view(request, pk):
    group = get_object_or_404(ReadingGroup, pk=pk)
    if request.method == 'POST':
        username = request.POST.get('username')
        try:
            user_to_invite = User.objects.get(username=username)
            return redirect('reading:invite_to_group', pk=group.pk, user_id=user_to_invite.pk)
        except User.DoesNotExist:
            messages.error(request, f"User '{username}' not found.")
    return render(request, 'reading/group_detail.html', {'group': group})

@login_required
def invite_to_group_view(request, pk, user_id):
    group = get_object_or_404(ReadingGroup, pk=pk)
    user_to_invite = get_object_or_404(User, pk=user_id)
    # Placeholder logic
    send_reading_group_invitation_email(user_to_invite, group)
    messages.success(request, f"Invitation sent to {user_to_invite.username} to join '{group.name}'.")
    return redirect('reading:group_detail', pk=pk)
