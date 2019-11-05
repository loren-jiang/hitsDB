from django import forms
from .models import Library, Compound
from .validators import validate_file_extension
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User, Group

class LibraryForm(forms.ModelForm):
    description = forms.CharField(required=False, widget=forms.Textarea(), max_length=300)
    supplier = forms.CharField(required=False, max_length=100)
    class Meta:
        model = Library
        fields=("name","description","supplier","owner")

    def __init__(self, *args, **kwargs):
        if kwargs.get('user'):
            self.user = kwargs.pop('user', None)
        super(LibraryForm, self).__init__(*args, **kwargs)
        if self.user:
            self.fields['owner'] = forms.ModelChoiceField(queryset=User.objects.filter(id=self.user.id), initial=self.user.id, widget=forms.HiddenInput()) 

        

class UploadCompoundsFromJSON(forms.Form):
    file = forms.FileField()

    def clean(self):
        cd = self.cleaned_data
        file_name = cd['file']
        return cd

class UploadCompoundsNewLib(LibraryForm):
    file = forms.FileField(validators=[validate_file_extension], required=False)
    # form_class = "new_lib_form ajax_form"

    def __init__(self, *args, **kwargs):
        super(UploadCompoundsNewLib, self).__init__(*args, **kwargs)


    # def clean(self):
    #     cd = self.cleaned_data
    #     lib_name = cd['name']
    #     user = self.request.user
    #     if user.libraries.filter(name=lib_name).exists():
    #         self.add_error('name',forms.ValidationError('Library name already exists.', code='invalid'))
    #     return cd

# class UploadCompoundsNewLib(forms.ModelForm):
#     file = forms.FileField(validators=[validate_file_extension], required=False)
#     # form_class = "new_lib_form ajax_form"
#     def __init__(self, *args, **kwargs):
#         self.request = kwargs.pop('request', None) #need to remove 'request' 
#         super(UploadCompoundsNewLib, self).__init__(*args, **kwargs)

#     class Meta:
#         model = Library
#         fields = ("name","description","supplier")

#     def clean(self):
#         cd = self.cleaned_data
#         lib_name = cd['name']
#         user = self.request.user
#         # check if library with lib_name already exists
#         if user.libraries.filter(name=lib_name).exists():
#             # ValidationError()
#             self.add_error('name',forms.ValidationError('Library name already exists.', code='invalid'))
#             # self._errors['name'] = "Library name already exists. Please rename."
#             # del cd['library']
#         return cd