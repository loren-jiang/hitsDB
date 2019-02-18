#log/forms.py
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django import forms
from django.contrib.auth.models import User


# If you don't do this you cannot use Bootstrap CSS
class LoginForm(AuthenticationForm):
    
    class Meta:
        model = User
        fields = ("username", "password")
    # username = forms.CharField(label="Username", max_length=30, 
    #                            widget=forms.TextInput(attrs={'class': 'form-control', 'name': 'username'}))
    # password = forms.CharField(label="Password", max_length=30, 
    #                            widget=forms.TextInput(attrs={'class': 'form-control', 'name': 'password'}))

class RegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")


