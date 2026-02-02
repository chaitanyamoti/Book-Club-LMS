from django.db import models
from django.contrib.auth.models import User
from core.models import Book # Assuming Book model is in core app
from django.utils import timezone
from django.core.validators import MinValueValidator

class ReadingChallenge(models.Model):
    GOAL_TYPE_CHOICES = [
        ('BOOKS', 'Number of Books'),
        ('PAGES', 'Number of Pages'),
    ]

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    start_date = models.DateField(default=timezone.now)
    end_date = models.DateField()
    target_books = models.ManyToManyField(Book, blank=True, help_text="Specific books for this challenge")
    target_genres = models.CharField(max_length=255, blank=True, help_text="Comma-separated genres for this challenge")
    goal_type = models.CharField(max_length=10, choices=GOAL_TYPE_CHOICES, default='BOOKS')
    goal_value = models.IntegerField(default=1, validators=[MinValueValidator(1)])
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['-start_date']


class UserReadingChallenge(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    challenge = models.ForeignKey(ReadingChallenge, on_delete=models.CASCADE)
    start_date = models.DateField(default=timezone.now) # User's start date
    completed_date = models.DateField(null=True, blank=True)
    progress_books = models.IntegerField(default=0)
    progress_pages = models.IntegerField(default=0)
    is_completed = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username}'s progress in {self.challenge.name}"

    class Meta:
        unique_together = ('user', 'challenge')


class ReadingGroup(models.Model):
    name = models.CharField(max_length=200, unique=True)
    description = models.TextField(blank=True)
    admin = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='administered_groups')
    members = models.ManyToManyField(User, through='GroupMembership', related_name='reading_groups')
    current_book = models.ForeignKey(Book, on_delete=models.SET_NULL, null=True, blank=True)
    meeting_details = models.TextField(blank=True) # e.g., 'Every Tuesday, 7 PM, Zoom Link: ...'
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class GroupMembership(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    group = models.ForeignKey(ReadingGroup, on_delete=models.CASCADE)
    date_joined = models.DateField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'group')
