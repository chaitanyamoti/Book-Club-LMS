from django import forms
from django.utils import timezone
from core.models import ReadingLog, Book, Transaction


class ReadingLogForm(forms.ModelForm):
    """Form for logging daily reading"""

    book = forms.ModelChoiceField(
        queryset=Book.objects.none(),
        empty_label="Select a book you're currently reading",
        widget=forms.Select(attrs={'class': 'form-select'}),
        help_text="Only books you have checked out will appear here"
    )

    class Meta:
        model = ReadingLog
        fields = ['book', 'read_today', 'pages_read', 'minutes_read', 'notes']
        widgets = {
            'read_today': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'pages_read': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'placeholder': 'Number of pages read today'
            }),
            'minutes_read': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'placeholder': 'Minutes spent reading'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Your thoughts, takeaways, or notes about today\'s reading...',
                'maxlength': 500
            }),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.book = kwargs.pop('book', None)
        super().__init__(*args, **kwargs)

        # Set queryset for book field to only show books the user has checked out
        if self.user:
            issued_books = Book.objects.filter(
                transaction__user=self.user,
                transaction__return_date__isnull=True,
                transaction__transaction_type='ISSUE'
            ).distinct()
            self.fields['book'].queryset = issued_books

        # Set initial values for today
        if self.user and self.book:
            today = timezone.now().date()
            existing_log = ReadingLog.objects.filter(
                user=self.user,
                book=self.book,
                log_date=today
            ).first()

            if existing_log:
                self.instance = existing_log
                self.fields['read_today'].initial = existing_log.read_today
                self.fields['pages_read'].initial = existing_log.pages_read
                self.fields['minutes_read'].initial = existing_log.minutes_read
                self.fields['notes'].initial = existing_log.notes

    def save(self, commit=True):
        """Override save to set user and book"""
        instance = super().save(commit=False)
        instance.user = self.user
        instance.book = self.book
        instance.log_date = timezone.now().date()

        if commit:
            instance.save()

        return instance


class BookProgressForm(forms.Form):
    """Form for updating book reading progress"""

    progress = forms.IntegerField(
        min_value=0,
        max_value=100,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '0-100'
        }),
        help_text="Percentage of book completed (0-100%)"
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.book = kwargs.pop('book', None)
        super().__init__(*args, **kwargs)

        # Set initial progress
        if self.user and self.book:
            latest_log = ReadingLog.objects.filter(
                user=self.user,
                book=self.book
            ).order_by('-log_date').first()

            if latest_log:
                self.fields['progress'].initial = latest_log.progress
