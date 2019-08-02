#experiment/forms.py
from django import forms
from django.contrib.auth.models import User, Group
from .models import Experiment, Plate, CrystalScreen, Project
from django.forms import ModelChoiceField
from django.contrib.admin.widgets import FilteredSelectMultiple

# simple form to edit Project fields (name, description)
class SimpleProjectForm(forms.ModelForm):
    class Media:
        # Django also includes a few javascript files necessary
        # for the operation of this form element. You need to
        # include <script src="/static/admin/js/jsi18n.js"></script>
        # in the template.
        css = {
            'all': ('/static/admin/css/widgets.css',)
        }
        js=('/static/admin/js/jsi18n.js',)
    class Meta:
        model = Project
        fields=("name","description",)

class ProjectForm(forms.ModelForm):
    class Media:
        # Django also includes a few javascript files necessary
        # for the operation of this form element. You need to
        # include <script src="/static/admin/js/jsi18n.js"></script>
        # in the template.
        css = {
            'all': ('/static/admin/css/widgets.css',)
        }
        js=('/static/admin/js/jsi18n.js',)

    class Meta:
        model = Project
        fields=('name','description','collaborators')

    def __init__(self, user, *args, **kwargs):
        super(ProjectForm, self).__init__(*args, **kwargs)
        collab_qs=User.objects.filter(groups__in=user.groups.all()).exclude(id=user.id)    
        # self.fields['collaborators'].queryset = collab_qs
        self.fields['collaborators'] = forms.ModelMultipleChoiceField(
            queryset=collab_qs,
            widget=FilteredSelectMultiple("User", 
                is_stacked=False, attrs={'rows':'5'}),
                required=False)


class NewExperimentForm(forms.ModelForm):
    # name = forms.CharField(max_length=30)
    # # library = models.CharField(max_length=30, unique=True) #need to create Library model
    description = forms.CharField(widget=forms.Textarea(), max_length=300)
    # protein = forms.CharField(max_length=30)
    # library = forms.ModelChoiceField(queryset=Library.objects.all(),initial=0)
    class Meta:
        model = Experiment
        fields = ("name", "description", "protein", "library",)

class SourcePlateForm(forms.ModelForm):
    class Meta:
        model = Plate
        fields = ("formatType",)

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
        required=False,
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
