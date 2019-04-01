#experiment/forms.py
from django import forms
from django.contrib.auth.models import User, Group
from .models import Experiment, Plate, CrystalScreen, Library, Project
from django.forms import ModelChoiceField
 
class NewProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields=('name','description','collaborators')

    def __init__(self, user, *args, **kwargs):
        super(NewProjectForm, self).__init__(*args, **kwargs)
        collaborators=User.objects.filter(groups__in=user.groups.all()).exclude(id=user.id)    
        self.fields['collaborators'].queryset = collaborators


class NewExperimentForm(forms.ModelForm):
    # name = forms.CharField(max_length=30)
    # # library = models.CharField(max_length=30, unique=True) #need to create Library model
    description = forms.CharField(widget=forms.Textarea(), max_length=300)
    # protein = forms.CharField(max_length=30)
    # library = forms.ModelChoiceField(queryset=Library.objects.all(),initial=0)
    class Meta:
        model = Experiment
        fields = ("name", "description", "protein", "library",)

class PlateSetupForm(forms.Form):
    source_plate = forms.ModelChoiceField(queryset=Plate.objects
        .prefetch_related('wells')
        .filter(isTemplate=True)
        .filter(isSource=True), 
        label="Source plate",
        initial=0)
    dest_plate = forms.ModelChoiceField(queryset=Plate.objects
        .prefetch_related('wells')
        .filter(isTemplate=True)
        .filter(isSource=False), 
        label="Destination plate",
        initial=0)
    dest_plate_screen = forms.ModelChoiceField(queryset=CrystalScreen.objects.all(), 
        initial=0)
    experiment = forms.ModelChoiceField(
        queryset=Experiment.objects
        .prefetch_related('plates','library__compounds')
        .order_by('-dateTime'),
        initial=0
        )

    crystal_choices = (
        (1,'Subwell 1'),
        (2,'Subwell 2'),
        (3,'Subwell 3'),
        )
    crystal_locations = forms.MultipleChoiceField(choices=crystal_choices)
    filetype_choices = (
        ('.pdf','PDF'),
        ('.csv','CSV'),
        )
    export_filetype = forms.ChoiceField(choices=filetype_choices)
