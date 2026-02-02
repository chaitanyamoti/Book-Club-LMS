from django import forms
from core.models import BookRequest, Book

class BookRequestForm(forms.ModelForm):
    class Meta:
        model = BookRequest
        fields = ['request_type', 'book', 'title', 'author', 'reason']
        widgets = {
            'request_type': forms.Select(attrs={'class': 'form-select', 'id': 'id_request_type'}),
            'book': forms.Select(attrs={'class': 'form-select', 'id': 'id_book'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Book Title', 'readonly': True}),
            'author': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Author Name', 'readonly': True}),
            'reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Why do you want this book?'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['book'].queryset = Book.objects.all()
        self.fields['book'].required = True
        self.fields['title'].required = False
        self.fields['author'].required = False
