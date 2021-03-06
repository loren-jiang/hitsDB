from django import forms
from .models import PrivateFile, PrivateFileCSV, PrivateFileJSON
from experiment.models import Plate
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User, Group
from django.core.validators import FileExtensionValidator
from django.conf import settings 

class ImageFilePathField(forms.FilePathField, forms.ImageField):
    pass

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
    upload = forms.FileField(label="Upload file [.csv]", widget=forms.FileInput(attrs={'accept': ".csv"}),
            validators=[FileExtensionValidator(['csv'])], required=True, 
            )
    local_upload = forms.FileField(label="Local upload file [.csv]", widget=forms.FileInput(attrs={'accept': ".csv"}),
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

# class PrivateFileJSONForm(PrivateFileUploadForm):
#     class Meta(PrivateFileUploadForm.Meta):
#         model = PrivateFileJSON

class PrivateFileJSONForm(forms.ModelForm):
    upload = forms.FileField(label="Upload file [.json]", widget=forms.FileInput(attrs={'accept': ".json"}),
            validators=[FileExtensionValidator(['json'])], required=False, 
            )
    local_upload = forms.FileField(label="Local upload file [.json]", widget=forms.FileInput(attrs={'accept': ".json"}),
            validators=[FileExtensionValidator(['json'])],required=False
            )
    class Meta:
        model = PrivateFileJSON
        fields=('upload', 'local_upload')
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.user = user
            self.fields['owner'] = forms.ModelChoiceField(queryset=User.objects.filter(id=self.user.id), 
                initial=self.user.id, widget=forms.HiddenInput())

class ImagesFieldForm(forms.Form):
    # image_field = ImageFilePathField(path=settings.BASE_DIR)
    image_field = forms.ImageField(widget=forms.ClearableFileInput(attrs={'multiple': True}))
    use_local = forms.BooleanField(required=False, initial=True, widget=forms.HiddenInput()) #TODO: remove hidden widget eventually

class FilesFieldForm(forms.Form):
    file_field = forms.FileField(widget=forms.ClearableFileInput(attrs={'multiple': True}))

