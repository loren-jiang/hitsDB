from django import forms
from .models import PrivateFile, WellImage
from experiment.models import Plate
from django.core.exceptions import ValidationError

class PrivateFileUploadForm(forms.ModelForm):
    # bucket_key = forms.CharField(max_length=100)
    class Meta:
        model = PrivateFile
        fields=('upload',)

class PrivateImageUploadForm(forms.ModelForm):
    # bucket_key = forms.CharField(max_length=100)
    class Meta:
        model = WellImage
        fields=('upload','plate')

class ImagesFieldForm(forms.Form):
    image_field = forms.ImageField(widget=forms.ClearableFileInput(attrs={'multiple': True}))

    # def clean(self):
    #     cd = self.cleaned_data
    #     images = cd.get('image_field')
    #     return cd

class FilesFieldForm(forms.Form):
    file_field = forms.FileField(widget=forms.ClearableFileInput(attrs={'multiple': True}))