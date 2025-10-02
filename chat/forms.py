from django import forms

class SchemeQueryForm(forms.Form):
    query = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={
            'placeholder': 'Ask me anything about Government schemes',
            'class': 'form-control',
            'aria-label': 'Your text'
        })
    )
