#log/forms.py
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django import forms
from django.contrib.auth.models import User, Group
from django.contrib.auth.password_validation import get_default_password_validators, validate_password
from django.conf import settings
from django.contrib.auth import authenticate
# crispy form imports
from crispy_forms.bootstrap import InlineField
from crispy_forms.layout import Submit
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, Div, Field, HTML, Button

class LoginForm(AuthenticationForm):
 
    class Meta:
        model = User
        fields = ("username", "password")
    
    

class RegistrationForm(UserCreationForm):
    email = forms.EmailField(max_length=200, help_text='Required')
    primary_group = forms.ModelChoiceField(queryset=Group.objects.all(), required=False, label="Primary Group")
   
    class Meta:
        model = User
        fields = ("username","email", "groups","primary_group","password1", "password2")


class EditUserForm(forms.ModelForm):
    password1 = forms.CharField(required=False, widget=forms.PasswordInput, label ="New password:")
    password2 = forms.CharField(required=False, widget=forms.PasswordInput, label ="Confirm new password:",
        help_text='Passwords must match.')
    primary_group = forms.ModelChoiceField(queryset=Group.objects.all(), required=False, label="Primary Group")

    def clean(self):
        form_data = super().clean()
        form_data = self.cleaned_data
        if form_data['password1'] or form_data['password2']:
            validate_password(form_data['password1'], password_validators=get_default_password_validators())
            if form_data['password1'] != form_data['password2']:
                self._errors["password1"] = ["Passwords do not match."] # Will raise a error message
                self._errors["password2"] = ["Passwords do not match."]
                del form_data['password1']
            return form_data
    def __init__(self, *args, **kwargs):   
        self.instance = kwargs.get('instance', None)
        self.user = User.objects.get(id=self.instance.id)
        super().__init__(*args, **kwargs)
        # self.fields['primary_group'].queryset = self.user.groups.all()
        self.fields['primary_group'].initial = self.user.profile.primary_group     
        self.helper = FormHelper()
        col_class = 'col col-md-8'
        self.helper.layout = Layout(
            Row(
                Column(
                    Row(
                        Column('username', css_class='col col-md-5'),
                        Column('email', css_class='col col-md-5'),
                        css_class='align-items-start',
                    ),
                    css_class=col_class
                ),
                
                css_class='form-row justify-content-center',
            ),
            Row(
                Column(
                    Row(
                        Column('groups', css_class='col col-md-5'),
                        Column('primary_group', css_class='col col-md-5'),
                        css_class='align-items-start',
                    ),
                    css_class=col_class
                ),
                
                css_class='form-row justify-content-center',
            ),
            Row(
                Column(
                    Row(
                        Column('password1', css_class='col col-md-5'),
                        Column('password2', css_class='col col-md-5'),
                        css_class='align-items-start',
                    ),
                    css_class=col_class
                ),
                
                css_class='form-row justify-content-center',
            ),
            Row(
                Column(
                    Submit('submit', 'Save'), 
                    HTML("""<a class="btn btn-danger" href= {% url 'deactivate_user' %}> Deactivate user </a>"""),
                    css_class=col_class
                ),
                css_class='form-row justify-content-center',
                # css_class='form-row align-items-start'
            ),
            
        )

    class Meta:
        model = User
        fields = ('username','email','groups', 'primary_group', 'password1', 'password2')



class RecoverUserForm(forms.ModelForm):
    username = forms.CharField(label='Username')

    def clean(self):
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