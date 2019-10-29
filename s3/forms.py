from django import forms
from .models import PrivateFile
from experiment.models import Plate
from django.core.exceptions import ValidationError

class PrivateFileUploadForm(forms.ModelForm):
    # bucket_key = forms.CharField(max_length=100)
    class Meta:
        model = PrivateFile
        fields=('upload',)

class ImagesFieldForm(forms.Form):
    image_field = forms.ImageField(widget=forms.ClearableFileInput(attrs={'multiple': True}))
    use_local = forms.BooleanField(required=False)

class FilesFieldForm(forms.Form):
    file_field = forms.FileField(widget=forms.ClearableFileInput(attrs={'multiple': True}))