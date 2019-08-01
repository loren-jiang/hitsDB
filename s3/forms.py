from django import forms
from .models import PrivateFile

class PrivateFileUploadForm(forms.ModelForm):
    # bucket_key = forms.CharField(max_length=100)
    class Meta:
        model = PrivateFile
        fields=('upload','bucket_key')

# class PrivateFolderUploadForm(forms.Form):
#     folder_path = forms.FilePathField(path="../",allow_folders=True, allow_files=False)
#     class Meta:
#         model = PrivateFile
#         fields=('folder_path',)

class FileFieldForm(forms.Form):
    file_field = forms.FileField(widget=forms.ClearableFileInput(attrs={'multiple': True}))