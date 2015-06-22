from django import forms
from django.contrib.auth.models import User

from reddit.models import Submission


class UserForm(forms.ModelForm):
    username = forms.CharField(widget=forms.TextInput(
        attrs=
        {'class': "form-control",
         'placeholder': "Username",
         'required': '',
         'autofocus': ''}),
        max_length=12,
        min_length=3,
        required=True)
    password = forms.CharField(widget=forms.PasswordInput(
        attrs=
        {'class': "form-control",
         'placeholder': "Password",
         'required': ''}),
        min_length=4,
        required=True)

    class Meta:
        model = User
        fields = ('username', 'password')


class SubmissionForm(forms.ModelForm):
    title = forms.CharField(widget=forms.TextInput(
        attrs={'class': "form-control",
               'placeholder': "Submission title"}),
        required=True, min_length=1)

    url = forms.URLField(widget=forms.URLInput(
        attrs={'class': "form-control",
               'placeholder': "(Optional) http:///www.example.com"}),
        required=False)

    text = forms.CharField(widget=forms.Textarea(
        attrs={
            'class': "form-control",
            'rows': "3",
            'placeholder': "Optional text"}),
        required=False)

    class Meta:
        model = Submission
        fields = ('title', 'url', 'text')
