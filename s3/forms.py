from django import forms
from .models import PrivateFile, PrivateFileCSV, PrivateFileJSON
from experiment.models import Plate
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User, Group
from django.core.validators import FileExtensionValidator


class PrivateFileUploadForm(forms.ModelForm):
    # bucket_key = forms.CharField(max_length=100)
    class Meta:
        model = PrivateFile
        fields=('upload','local_upload')
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.user = user
            self.fields['owner'] = forms.ModelChoiceField(queryset=User.objects.filter(id=self.user.id), 
                initial=self.user.id, widget=forms.HiddenInput())

# class PrivateFileCSVForm(PrivateFileUploadForm):
#     class Meta(PrivateFileUploadForm.Meta):
#         model = PrivateFileCSV

class PrivateFileCSVForm(forms.ModelForm):
    upload = forms.FileField(label="Initialization file [.csv]",
            validators=[FileExtensionValidator(['csv'])], required=False
            )
    local_upload = forms.FileField(label="Initialization file [.csv]",
            validators=[FileExtensionValidator(['csv'])],required=False
            )
    class Meta:
        model = PrivateFileCSV
        fields=('upload', 'local_upload')
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.user = user
            self.fields['owner'] = forms.ModelChoiceField(queryset=User.objects.filter(id=self.user.id), 
                initial=self.user.id, widget=forms.HiddenInput())
                

class PrivateFileJSONForm(PrivateFileUploadForm):
    class Meta(PrivateFileUploadForm.Meta):
        model = PrivateFileJSON

class ImagesFieldForm(forms.Form):
    image_field = forms.ImageField(widget=forms.ClearableFileInput(attrs={'multiple': True}))
    use_local = forms.BooleanField(required=False, initial=True, widget=forms.HiddenInput()) #TODO: remove hidden widget eventually

class FilesFieldForm(forms.Form):
    file_field = forms.FileField(widget=forms.ClearableFileInput(attrs={'multiple': True}))