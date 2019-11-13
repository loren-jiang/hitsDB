#experiment/forms.py
from django import forms
from django.contrib.auth.models import User, Group
from .models import Experiment, Plate, Ingredient, Project, PlateType, Soak
from django.forms import ModelChoiceField
from django.contrib.admin.widgets import FilteredSelectMultiple
from lib.models import Compound, Library
from django.core.exceptions import ValidationError
from crispy_forms.bootstrap import InlineField
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from django.core.validators import FileExtensionValidator
from django.utils import timezone
import json
from json.decoder import JSONDecodeError

class SoakForm(forms.ModelForm):
    class Meta:
        model = Soak
        fields = ("soakVolume","transferCompound")

    def __init__(self, exp=None, *args, **kwargs):
        super(SoakForm, self).__init__(*args, **kwargs)
        if exp:
            setattr(self.fields["transferCompound"], "queryset", exp.library.compounds.filter())
            # self.fields['transferCompound'] = forms.ModelChoiceField(queryset=exp.library.compounds.filter(),
            #     initial=self.instance.transferCompound)

class LibraryForm(forms.ModelForm):
    description = forms.CharField(required=False, widget=forms.Textarea(), max_length=300)
    class Meta:
        model = Library
        fields=("name","description","supplier",)

    # def __init__(self, *args, **kwargs):
        # self.form_class = kwargs.pop("form_class", None)
        # super(LibraryForm, self).__init__(*args, **kwargs)

class MultipleForm(forms.Form):
    action = forms.CharField(max_length=60, widget=forms.HiddenInput())

# simple form to edit Project fields (name, description)
class SimpleProjectForm(forms.ModelForm):
    class Media:
        css = {
            'all': ('/static/admin/css/widgets.css',)
        }
        js=('/static/admin/js/jsi18n.js',)
    class Meta:
        model = Project
        fields=("name","description",)

class ProjectForm(forms.ModelForm):
    class Media:
        css = {
            'all': ('/static/admin/css/widgets.css',)
        }
        js = ('/static/admin/js/jsi18n.js',)

    class Meta:
        model = Project
        fields=('name','description','collaborators', 'owner')

    def __init__(self, *args, **kwargs):
        if kwargs.get('user'):
            self.user = kwargs.pop('user', None)
        super(ProjectForm, self).__init__(*args, **kwargs)
        if self.user:
            self.fields['owner'] = forms.ModelChoiceField(queryset=User.objects.filter(id=self.user.id), initial=self.user.id, widget=forms.HiddenInput())  
            collab_qs=User.objects.filter(groups__in=self.user.groups.all(), is_active=True).exclude(id=self.user.id)    
            self.fields['collaborators'] = forms.ModelMultipleChoiceField(
                queryset=collab_qs,
                # widget=forms.CheckboxSelectMultiple,
                widget=FilteredSelectMultiple("User", 
                    is_stacked=False, attrs={'rows':'5'}),
                    required=False
                    )


class ExperimentModelForm(forms.ModelForm):
    description = forms.CharField(required=False, widget=forms.Textarea(), max_length=300)
    protein = forms.CharField(max_length=100, required=False)
    
    class Meta:
        model = Experiment
        fields = ("name","description", "protein", "srcPlateType", "destPlateType","library",)
        
    def __init__(self, *args, **kwargs):
        super(ExperimentModelForm, self).__init__(*args, **kwargs)
        srcPlateType_qs = PlateType.objects.filter(isSource=True)
        destPlateType_qs = PlateType.objects.filter(isSource=False)
        self.fields['srcPlateType'] = forms.ModelChoiceField(queryset=srcPlateType_qs, 
            label="Source plate type",
            initial=srcPlateType_qs.first())
        self.fields['destPlateType'] = forms.ModelChoiceField(queryset=destPlateType_qs, 
            label="Destination plate type",
            initial=destPlateType_qs.first())
        
            


# MultiForms -------------------------------------------------------------------------

class ExpAsMultiForm(MultipleForm, ExperimentModelForm):

    """populate form with current values"""
    def __init__(self, user, lib_qs=None, *args, **kwargs):
        super(ExpAsMultiForm, self).__init__(*args, **kwargs)
        # self.fields['name'] = forms.CharField(max_length=30, initial=getattr(exp,'name'))
        # self.fields['description'] = forms.CharField(max_length=300, initial=getattr(exp,'description'), required=False)
        # self.fields['protein'] = forms.CharField(max_length=30, initial=getattr(exp,'protein'), required=False)
        # self.fields['srcPlateType'] = forms.ModelChoiceField(queryset=PlateType.objects
        #     .filter(isSource=True), 
        #     label="Source plate type",
        #     initial=exp.srcPlateType)
        # self.fields['destPlateType'] = forms.ModelChoiceField(queryset=PlateType.objects
        #     .filter(isSource=False), 
        #     label="Destination plate type",
        #     initial=exp.destPlateType)
        exp = getattr(kwargs, 'instance', None)
        if exp:
            lib_id = getattr(exp,'library')
            qs = user.libraries.filter()
            if lib_qs:
                qs = lib_qs
            self.fields['library'] = forms.ModelChoiceField(queryset=qs, initial=lib_id, required=False)

    class Meta(ExperimentModelForm.Meta):
        fields = list(ExperimentModelForm.Meta.fields) + ['project']
    

    # put form validation here 
    # def clean(self, *args, **kwargs):
    #     cd =  super(ExpAsMultiForm, self).clean(*args, **kwargs)
    # #     # cd = self.cleaned_data
    # #     cd_copy = cd.copy()
    # #     fields = [k for k in self.fields]
    #     if len(cd['name']) < 3:
    #         self._errors['name'] = ["Name not greater than 3 chars."]
    # #     for key in cd_copy:
    # #         if not key in fields:
    # #             cd.pop(key)
    #     return cd

class ExpInitDataMultiForm(MultipleForm):
    initDataFile = forms.FileField(label="File upload",
            validators=[FileExtensionValidator(['json'])],
            widget=forms.FileInput)
    def __init__(self, exp, *args, **kwargs):
        self.exp = exp
        super(ExpInitDataMultiForm, self).__init__(*args,**kwargs)
        # self.fields['initDataFile'] = forms.FileField(label="File upload",
        #     validators=[FileExtensionValidator(['json'])])
    def clean(self):
        cleaned_data = super().clean()
        initDataFile = cleaned_data.get('initDataFile')
        if initDataFile:
            try:
                data_json = ""
                for c in initDataFile.chunks():
                    data_json += str(c, encoding='utf-8').replace("'", "\"")
                data_dict = json.loads(data_json)
                plate_ids = data_dict.keys()
                existing_ids = []
                for p_id in plate_ids:
                    if Plate.objects.filter(rockMakerId=p_id).exists():
                        existing_ids.append(p_id)
                if existing_ids:
                    raise ValidationError('Plate with RockMaker ID(s) %s already exist(s).' % (str(existing_ids)))

            except (ValueError, OverflowError) as e:
                if issubclass(type(e), ValueError):
                    raise ValidationError('File given is not in correct .json format. Review instructions above.')
                if type(e) is OverflowError:
                    raise ValidationError('File is too big!')

class CreateSrcPlatesMultiForm(MultipleForm):
    numSrcPlates = forms.IntegerField(required=False)
    plateLibDataFile = forms.FileField(required=False)
    templateSrcPlates = forms.ModelMultipleChoiceField(
        queryset=Plate.objects.filter(isSource=True, isTemplate=True), 
        required=False)

    def __init__(self, exp, *args, **kwargs):
        super(CreateSrcPlatesMultiForm, self).__init__(*args, **kwargs)
    def clean(self):
        cd = self.cleaned_data
        fromFile = cd['numSrcPlates'] and cd['plateLibDataFile']
        fromTemplates = cd['templateSrcPlates']
        if not(fromFile or fromTemplates):
            self.add_error(None,'Please choose one option.')

        return cd

class PlatesSetupMultiForm(MultipleForm):
    subwells = (
        (1,'1'),
        (2,'2'),
        (3,'3'),
        )

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
    soakVolumeOverride = forms.IntegerField(required=False, label="Override Soak Volume")
    soakDate = forms.DateTimeField(initial=timezone.now().strftime('%m/%d/%Y %H:%M'), 
        input_formats=['%m/%d/%Y %H:%M'], label="Desired soak date", required=False)

    def __init__(self, exp, *args, **kwargs):
        super(SoaksSetupMultiForm, self).__init__(*args,**kwargs)
# class SoaksSetupMultiForm(MultipleForm):
#     def __init__(self, exp, *args, **kwargs):
#         super(SoaksSetupMultiForm, self).__init__(*args,**kwargs)
#         soakVolume = 25
#         soakOffsetX = 0
#         soakOffsetY = 0
#         if exp.soaks.count():
#             s = exp.soaks.all()[0]
#             soakVolume = s.soakVolume
#             soakOffsetX = s.soakOffsetX
#             soakOffsetY = s.soakOffsetY
#         self.fields['soakVolume'] = forms.IntegerField(initial=soakVolume)
#         self.fields['soakOffsetX'] = forms.DecimalField(max_digits=10, decimal_places=2,initial=soakOffsetX)
#         self.fields['soakOffsetY'] = forms.DecimalField(max_digits=10, decimal_places=2,initial=soakOffsetY)
    
#     def clean(self):
#         cd = self.cleaned_data
#         if cd['soakVolume'] <= 0:
#             self._errors['soakVolume'] = ["Must be positive."]
#         cd_copy = cd.copy()
#         fields = [k for k in self.fields]
#         for key in cd_copy:
#             if not key in fields:
#                 cd.pop(key)
#         return cd

