#log/forms.py
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django import forms
from django.contrib.auth.models import User, Group
from django.contrib.auth.password_validation import get_default_password_validators, validate_password
from django.conf import settings

class LoginForm(AuthenticationForm):
    class Meta:
        model = User
        fields = ("username", "password")

class RegistrationForm(UserCreationForm):
    email = forms.EmailField(max_length=200, help_text='Required')
    _groups = forms.ModelMultipleChoiceField(queryset = Group.objects.all().exclude(name='Admin'),
        label="Groups")
    class Meta:
        model = User
        fields = ("username", "_groups","email", "password1", "password2")

class EditUserForm(forms.ModelForm):
    password1 = forms.CharField(required=False, widget=forms.PasswordInput, label ="New password:")
    password2 = forms.CharField(required=False, widget=forms.PasswordInput, label ="Confirm new password:",
        help_text='Passwords must match.')
    
    def clean(self):
        form_data = self.cleaned_data
        validate_password(form_data['password1'], password_validators=get_default_password_validators())
        if form_data['password1'] != form_data['password2']:
            self._errors["password1"] = ["Passwords do not match."] # Will raise a error message
            self._errors["password2"] = ["Passwords do not match."]
            del form_data['password1']
        return form_data

    class Meta:
        model = User
        fields = ('username','email',)#,'password') to be added


class RecoverUserForm(forms.ModelForm):
    username = forms.CharField(label='Username')

    def clean(self):
        # users = User.objects.all()
        form_data = self.cleaned_data
        try:
            user = User.objects.get(username__exact=form_data['username'])
        except(User.DoesNotExist):
            user = None

        if not user:
            self._errors["username"] = ["No matching username found."]
            del form_data['username']
        return form_data

    class Meta:
        model = User
        fields = ("username",)