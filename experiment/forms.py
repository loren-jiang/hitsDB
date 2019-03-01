#experiment/forms.py
from django import forms
from django.contrib.auth.models import User
from .models import Experiment

class NewExperimentForm(forms.ModelForm):
    # name = forms.CharField(max_length=30)
    # # library = models.CharField(max_length=30, unique=True) #need to create Library model
    description = forms.CharField(widget=forms.Textarea(), max_length=300)
    # protein = forms.CharField(max_length=30)

    class Meta:
        model = Experiment
        fields = ("name", "description", "protein")