from django import forms
from core.models import Book
from .utils import validate_isbn


class BookForm(forms.ModelForm):
    """Form for creating and updating books"""

    class Meta:
        model = Book
        fields = [
            'title', 'author', 'isbn', 'genre', 'description',
            'cover_image', 'cover_url', 'total_copies'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter book title'}),
            'author': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter author name'}),
            'isbn': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter ISBN (optional)'}),
            'genre': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Enter book description'}),
            'cover_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'Enter cover image URL (optional)'}),
            'total_copies': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set available copies to total copies for new books
        if not self.instance.pk:
            self.fields['total_copies'].initial = 1

    def clean_isbn(self):
        """Validate ISBN format"""
        isbn = self.cleaned_data.get('isbn')
        if isbn and not validate_isbn(isbn):
            raise forms.ValidationError('Invalid ISBN format. Please enter a valid ISBN-10 or ISBN-13.')
        return isbn

    def clean(self):
        """Custom validation"""
        cleaned_data = super().clean()
        cover_image = cleaned_data.get('cover_image')
        cover_url = cleaned_data.get('cover_url')

        # Ensure at least one cover option is provided
        if not cover_image and not cover_url:
            raise forms.ValidationError('Please provide either a cover image or cover URL.')

        return cleaned_data

    def save(self, commit=True):
        """Override save to set available copies"""
        instance = super().save(commit=False)
        if not instance.pk:  # New book
            instance.available_copies = instance.total_copies
        instance.save()
        return instance
