from django import forms
from .models import PrivateFile

class PrivateFileUploadForm(forms.ModelForm):
    class Meta:
        model = PrivateFile
        fields=('upload',)

