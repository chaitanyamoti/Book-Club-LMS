from django import forms
from django.utils import timezone
from django.core.exceptions import ValidationError
from core.models import Book, UserProfile, Transaction

class IssueBookForm(forms.Form):
    book = forms.ModelChoiceField(queryset=Book.objects.filter(available_copies__gt=0))
    user = forms.ModelChoiceField(queryset=UserProfile.objects.all())
    due_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    admin_notes = forms.CharField(widget=forms.Textarea, required=False)

    def clean_due_date(self):
        due_date = self.cleaned_data['due_date']
        today = timezone.now().date()

        if due_date <= today:
            raise ValidationError("Due date must be after today's date.")

        return due_date

class ReturnBookForm(forms.Form):
    condition_notes = forms.CharField(widget=forms.Textarea, required=False)

class ExtendDueDateForm(forms.Form):
    new_due_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )

class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['book', 'user', 'transaction_type', 'due_date', 'return_date', 'admin_notes', 'condition_notes']
        widgets = {
            'due_date': forms.DateInput(attrs={'type': 'date'}),
            'return_date': forms.DateInput(attrs={'type': 'date'}),
        }
