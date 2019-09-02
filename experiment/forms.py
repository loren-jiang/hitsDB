#experiment/forms.py
from django import forms
from django.contrib.auth.models import User, Group
from .models import Experiment, Plate, CrystalScreen, Project, PlateType, Soak
from django.forms import ModelChoiceField
from django.contrib.admin.widgets import FilteredSelectMultiple
from import_ZINC.models import Compound, Library
from django.core.exceptions import ValidationError
from crispy_forms.bootstrap import InlineField
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit

class SoakForm(forms.ModelForm):
    class Meta:
        model = Soak
        fields = ("transferVol","transferCompound")

    def __init__(self, exp=None, *args, **kwargs):
        super(SoakForm, self).__init__(*args, **kwargs)
        if exp:
            setattr(self.fields["transferCompound"], "queryset", exp.library.compounds.filter())
            # self.fields['transferCompound'] = forms.ModelChoiceField(queryset=exp.library.compounds.filter(),
            #     initial=self.instance.transferCompound)

class LibraryForm(forms.ModelForm):
    class Meta:
        model = Library
        fields=("name","description","supplier",)

class MultipleForm(forms.Form):
    action = forms.CharField(max_length=60, widget=forms.HiddenInput())

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
            
        collab_qs=User.objects.filter(groups__in=user.groups.all()).exclude(id=user.id)    
        # self.fields['collaborators'].queryset = collab_qs
        self.fields['collaborators'] = forms.ModelMultipleChoiceField(
            queryset=collab_qs,
            widget=FilteredSelectMultiple("User", 
                is_stacked=False, attrs={'rows':'5'}),
                required=False)


class ExperimentModelForm(forms.ModelForm):
    description = forms.CharField(widget=forms.Textarea(), max_length=300)
    class Meta:
        model = Experiment
        fields = ("name", "description", "protein", "library",)
        

class SourcePlateForm(forms.ModelForm):
    class Meta:
        model = Plate
        fields = ("formatType",)

# MultiForms -------------------------------------------------------------------------

class ExperimentAsMultiForm(MultipleForm):
    # name = forms.CharField(max_length=30)
    # description = forms.CharField(widget=forms.Textarea(), max_length=300)
    # description = forms.CharField(max_length=300)
    # protein = forms.CharField(max_length=30)
    # library = forms.ModelChoiceField(queryset=Library.objects.all(),initial=0, required=False)

    """populate form with current values"""
    def __init__(self, user, exp, lib_qs=None, *args, **kwargs):
        super(ExperimentAsMultiForm, self).__init__(*args, **kwargs)
        self.fields['name'] = forms.CharField(max_length=30, initial=getattr(exp,'name'))
        self.fields['description'] = forms.CharField(max_length=300, initial=getattr(exp,'description'))
        self.fields['protein'] = forms.CharField(max_length=30, initial=getattr(exp,'protein'))
        lib_id = getattr(exp,'library_id')
        qs = user.libraries.filter()
        if lib_qs:
            qs = lib_qs
        self.fields['library'] = forms.ModelChoiceField(queryset=qs, initial=lib_id, 
                required=False, empty_label="-----", widget=forms.Select)
    
    # put form validation here 
    def clean(self):
        cd = self.cleaned_data
        cd_copy = cd.copy()
        fields = [k for k in self.fields]
        # if len(cd['name']) < 3:
        #     self._errors['name'] = ["Name not greater than 3 chars."]
        for key in cd_copy:
            if not key in fields:
                cd.pop(key)
        return cd

class PlateSetupForm(MultipleForm):
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
        initial=0, #CHANGE THIS!!!!!!!!!!
        widget=forms.HiddenInput()
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

class PlatesSetupMultiForm(MultipleForm):

    subwells = (
        (1,'1'),
        (2,'2'),
        (3,'3'),
        )
    # subwell_locations = forms.MultipleChoiceField(widget=forms.CheckboxSelectMultiple, choices=subwells)
    # subwell_locations = forms.MultipleChoiceField(choices=subwells)

    def __init__(self, exp, *args, **kwargs):
        super(PlatesSetupMultiForm, self).__init__(*args, **kwargs)
        self.fields['srcPlateType'] = forms.ModelChoiceField(queryset=PlateType.objects
            .filter(isSource=True), 
            label="Source plate type",
            initial=exp.srcPlateType)
        self.fields['destPlateType'] = forms.ModelChoiceField(queryset=PlateType.objects
            .filter(isSource=False), 
            label="Destination plate type",
            initial=exp.destPlateType)
        subwells = [1]
        if exp.subwell_locations:
            subwells = exp.subwell_locations
        self.fields['subwell_locations'] = forms.MultipleChoiceField(choices=self.subwells, initial=subwells)
        # self.fields['subwell_locations'] = forms.MultipleChoiceField(choices=self.subwells, initial=subwells, widget=forms.CheckboxSelectMultiple)

    def clean(self):
        cd = self.cleaned_data
        try:
            if len(cd['subwell_locations']) < 1:
                self._errors['subwell_locations'] = ["Must select at least one subwell."]
        except KeyError:
            raise ValidationError('Must select at least one subwell.')
        cd_copy = cd.copy()
        fields = [k for k in self.fields]
        for key in cd_copy:
            if not key in fields:
                cd.pop(key)
        
        return cd

class SoaksSetupMultiForm(MultipleForm):
    def __init__(self, exp, *args, **kwargs):
        super(SoaksSetupMultiForm, self).__init__(*args,**kwargs)
        transferVol = 25
        soakOffsetX = 0
        soakOffsetY = 0
        if exp.soaks.count():
            s = exp.soaks.all()[0]
            transferVol = s.transferVol
            soakOffsetX = s.soakOffsetX
            soakOffsetY = s.soakOffsetY
        self.fields['transferVol'] = forms.IntegerField(initial=transferVol)
        self.fields['soakOffsetX'] = forms.DecimalField(max_digits=10, decimal_places=2,initial=soakOffsetX)
        self.fields['soakOffsetY'] = forms.DecimalField(max_digits=10, decimal_places=2,initial=soakOffsetY)
    
    def clean(self):
        cd = self.cleaned_data
        if cd['transferVol'] <= 0:
            self._errors['transferVol'] = ["Must be positive."]
        cd_copy = cd.copy()
        fields = [k for k in self.fields]
        for key in cd_copy:
            if not key in fields:
                cd.pop(key)
        return cd

