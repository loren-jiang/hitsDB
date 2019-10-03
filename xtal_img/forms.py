from django import forms
from .models import DropImage

class DropImageUploadForm(forms.ModelForm):
    class Meta:
        model = DropImage
        fields=('upload', 'well_name')