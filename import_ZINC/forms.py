from django import forms
from .models import Library, Compound
from .validators import validate_file_extension

class UploadCompoundsFromJSON(forms.Form):
    file = forms.FileField()

    def clean(self):
        cd = self.cleaned_data
        file_name = cd['file']
        return cd

class UploadCompoundsNewLib(forms.ModelForm):
    file = forms.FileField(validators=[validate_file_extension])
    name = forms.CharField(max_length=30, min_length=3)
    
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super(UploadCompoundsNewLib, self).__init__(*args, **kwargs)

    class Meta:
        model = Library
        fields = ("name","description","supplier")

    def clean(self):
        cd = self.cleaned_data
        lib_name = cd['name']
        user = self.request.user
        # check if library with lib_name already exists
        if user.libraries.filter(name=lib_name).exists():
            self._errors['name'] = ["Library name already exists. Please rename."]
            # del cd['library']
        return cd