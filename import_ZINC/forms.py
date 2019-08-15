from django import forms
from .models import Library, Compound

class UploadCompoundsFromJSON(forms.Form):
    file = forms.FileField()

    def clean(self):
	    cd = self.cleaned_data
	    file_name = cd['file']
	    return cd

class UploadCompoundsNewLib(forms.ModelForm):
    file = forms.FileField()
    name = forms.CharField(max_length=30, min_length=3)
    
    class Meta:
    	model = Library
    	fields = ("name","description","supplier")

    def clean(self):
	    cd = self.cleaned_data
	    lib_name = cd['name']

	    # check if library with lib_name already exists
	    if Library.objects.filter(name=lib_name).exists():
	        self._errors['name'] = ["Library name already exists. Please rename."]
	        # del cd['library']
	    return cd