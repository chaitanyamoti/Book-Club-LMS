from django import forms
from .models import EmailPreference

class EmailPreferenceForm(forms.ModelForm):
    class Meta:
        model = EmailPreference
        fields = [
            'welcome_emails',
            'transaction_emails',
            'reading_emails',
            'community_emails',
            'marketing_emails',
            'frequency',
        ]
        widgets = {
            'welcome_emails': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'transaction_emails': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'reading_emails': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'community_emails': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'marketing_emails': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'frequency': forms.Select(attrs={'class': 'form-control'}),
        }
