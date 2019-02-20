#log/forms.py
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django import forms
from django.contrib.auth.models import User


# If you don't do this you cannot use Bootstrap CSS
class LoginForm(AuthenticationForm):
    
    class Meta:
        model = User
        fields = ("username", "password")


class RegistrationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

class EditUserForm(forms.ModelForm):
    password1 = forms.CharField(widget=forms.PasswordInput, label ="New password:")
    password2 = forms.CharField(widget=forms.PasswordInput, label ="Confirm new password:",
    help_text='Passwords must match.')
    
    def clean(self):
        form_data = self.cleaned_data
        if form_data['password1'] != form_data['password2']:
            self._errors["password1"] = ["Passwords do not match."] # Will raise a error message
            self._errors["password2"] = ["Passwords do not match."]
            del form_data['password1']
        return form_data

    class Meta:
        model = User
        fields = ('email',)#,'password') to be added
        

class RecoverUserForm(forms.ModelForm):
    username = forms.CharField(label='Username')
    # password = forms.CharField(label='Password') #is CharField right?
    
    def is_valid(self):
        users = User.objects.all()
        for user in users:
            if self.username == user.username:
                return True

        return False
    class Meta:
        model = User
        fields = ("username",)