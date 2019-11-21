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
from .querysets import user_accessible_projects, user_editable_projects
import csv
from io import TextIOWrapper
from itertools import compress
from s3.forms import PrivateFileUploadForm, PrivateFileCSVForm
from .querysets import user_editable_projects, user_editable_plates
from my_utils.utility_functions import lists_diff 


# crispy form imports
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, Div, Field, HTML, Button

class PlateForm(forms.ModelForm):
    class Meta:
        model = Plate
        fields = ("name","isTemplate",)

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
        exp = kwargs.get('instance', None)
        if exp:
            lib_id = exp.library_id
            qs = user.libraries.filter()
            if lib_qs:
                qs = lib_qs
            self.fields['library'] = forms.ModelChoiceField(queryset=qs, initial=lib_id, required=False)
            self.fields['project'] = forms.ModelChoiceField(queryset=user_editable_projects(user), initial=exp.project.id)

    class Meta(ExperimentModelForm.Meta):
        fields = list(ExperimentModelForm.Meta.fields) + ['project']

class ExpInitDataMultiForm(MultipleForm):
    initDataFile = forms.FileField(label="Initialization file [.json]",
            validators=[FileExtensionValidator(['json'])],
            )
    def __init__(self, exp, *args, **kwargs):
        self.exp = exp
        super(ExpInitDataMultiForm, self).__init__(*args,**kwargs)

    def clean(self):
        cleaned_data = super().clean()
        initDataFile = cleaned_data.get('initDataFile', None)
        if initDataFile:
            try:
                if initDataFile.size >= 2.5e6:
                    raise OverflowError

                data_json = ""
                for c in initDataFile.chunks():
                    data_json += str(c, encoding='utf-8').replace("'", "\"")
                data_dict = json.loads(data_json)
                plate_ids = data_dict.keys()
                existing_ids = []
                exp_dest_plate_ids = [p.rockMakerId for p in self.exp.plates.filter(isSource=False)]
                for p_id in plate_ids:
                    if Plate.objects.filter(rockMakerId=p_id).exists() and p_id not in exp_dest_plate_ids:
                        existing_ids.append(p_id)
                if existing_ids:
                    self.add_error('initDataFile',
                        ValidationError(            
                            ('Plate with RockMaker ID %(value)s already exist(s) and are not in current experiment.'),
                            code='invalid',
                            params={'value': existing_ids},
                        )
                    )

            except (ValueError, OverflowError) as e:
                if issubclass(type(e), ValueError):
                    self.add_error('initDataFile','File given is not in correct .json format. Review instructions above.')
                if type(e) is OverflowError:
                    self.add_error('initDataFile','File is too big!')

class CreateSrcPlatesMultiForm(MultipleForm):
    numSrcPlates = forms.IntegerField(required=False, label="Number of plates")
    plateLibDataFile = forms.FileField(required=False, label="Source plate(s) file [.csv]",
        validators=[FileExtensionValidator(['csv'])],)
    templateSrcPlates = forms.ModelMultipleChoiceField(
        queryset=Plate.objects.filter(isSource=True, isTemplate=True), 
        required=False, label="Template source plates")

    def __init__(self, exp, *args, **kwargs):
        # super(CreateSrcPlatesMultiForm, self).__init__(*args, **kwargs)
        super().__init__(*args, **kwargs)
        # make from crispy
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column(HTML("""<h5>Option 1</h5>"""), css_class='col')
            ),
            Row(
                Column('numSrcPlates', css_class='col'),
                Column('plateLibDataFile', css_class='col'),
                css_class='form-row align-items-start'
            ),
            Row(
                Column(HTML("""<h5>Option 2</h5>"""), css_class='col')
            ),
            Row(
                Column('templateSrcPlates', css_class='col'),
                css_class='form-row align-items-start'
            ),
            Column('action', css_class='hidden'),
            Submit('submit', 'Submit')
        )
    def clean_plateLibDataFile(self):
        f = self.cleaned_data.get('plateLibDataFile')
        headers_required =['zinc_id', 'well', 'plate_idx']
        if f:
            try:
                if f.size >= 2.5e6:
                    raise OverflowError
                i = 0
                headers = []
                for c in f.chunks():
                    reader = csv.reader(str(c, encoding='utf-8').split('\n'), delimiter=',')
                    if (i==0):
                        headers = next(reader)
                    i += 1
                headers_missing = list(compress(headers_required, list(map(lambda h: not(h in headers), headers_required))))
                if headers_missing:
                    self.add_error('plateLibDataFile', 
                        ValidationError(            
                            ('Missing .csv headers %(value)s'),
                            code='invalid',
                            params={'value': headers_missing},
                        ))
            except (ValueError, OverflowError) as e:
                if type(e) is OverflowError:
                    self.add_error('plateLibDataFile','File is too big!')
        f.open() #have to reopen file after validation...or just send file contents
        return f

    def clean(self):
        cd = super().clean()
        numSrcPlates = cd.get('numSrcPlates', None)
        plateLibDataFile = cd.get('plateLibDataFile', None)
        templateSrcPlates = cd.get('templateSrcPlates', None)

        fromFile = numSrcPlates and plateLibDataFile
        fromTemplates = templateSrcPlates

        if not(fromFile or fromTemplates) or (fromFile and fromTemplates):
            self.add_error(None,'Please choose only ONE option.')

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

class PicklistMultiForm(MultipleForm, PrivateFileCSVForm):
    def __init__(self, *args, **kwargs):
        super(PicklistMultiForm, self).__init__(*args, **kwargs)
        exp = kwargs.get('instance', None)
        if exp:
            self.exp = exp

    def uploaded_file_clean(self, f=None):
        from my_utils.constants import picklist_map
        if f:
            try:
                if f.size >= 2.5e6:
                    raise OverflowError
                plate_ids = {}
                for c in f.chunks():
                    reader = csv.reader(str(c, encoding='utf-8').split('\n'), delimiter=',')
                    
                    for row in reader:
                        if row:
                            while row[-1]:
                                row.pop()
                            if len(row) < 4:
                                self.add_error(None,
                                    ValidationError(            
                                        ('Missing columns. See instructions.'),
                                        code='invalid',
                                    )
                                )
                            if len(row) > len(picklist_map.keys()):
                                self.add_error(None,
                                    ValidationError(            
                                        ('Number of columns is greater than number of accepted input columns. See instructions.'),
                                        code='invalid',
                                    ))
                            plate_id = row[1]
                            print(plate_id)
                            if not(plate_ids.get(plate_id)):
                                plate_ids[plate_id] = plate_id
                editable_plate_qs = user_editable_plates(self.exp.owner).filter(rockMakerId__in=plate_ids.keys())
                rockMaker_ids = [p.rockMakerId for p in editable_plate_qs]
                missing_ids = lists_diff(rockMaker_ids, plate_ids.keys())
                if not(editable_plate_qs.exists()):
                    self.add_error(None,
                        ValidationError(            
                                    ("Plate IDs %(value)s are not user-accessible RockMaker IDs in database."),
                                    code='invalid',
                                    params={'value': missing_ids},
                            )) 
        
    
            except (ValueError, OverflowError) as e:
                if type(e) is OverflowError:
                    self.add_error(None,'File is too large.')
        return f

    def clean_upload(self):
        f = self.cleaned_data.get('upload')
        if f:
            f = self.uploaded_file_clean(f)
        return f
    
    def clean_local_upload(self):
        f = self.cleaned_data.get('local_upload')
        if f:
            f= self.uploaded_file_clean(f)
        return f
    def clean(self):
        cd = super(PrivateFileCSVForm, self).clean()
        print(self.__dict__)
        print(cd)
        return cd
    pass

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

