#experiment/forms.py
from django import forms
from django.contrib.auth.models import User, Group
from .models import Experiment, Plate, Ingredient, Project, PlateType, Soak, Well, SubWell
from django.forms import ModelChoiceField
from django.contrib.admin.widgets import FilteredSelectMultiple
from lib.models import Compound, Library
from django.core.exceptions import ValidationError

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
from my_utils.utility_functions import lists_diff, missing_list_elems
from django.core.validators import MaxValueValidator, MinValueValidator
from my_utils.my_forms import FormFieldPopoverMixin, MultiFormMixin
from my_utils.fields import GroupedMutlipleModelChoiceField, GroupedModelChoiceField
# crispy form imports
from crispy_forms.bootstrap import InlineField
from crispy_forms.layout import Submit
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, Div, Field, HTML, Button

class WellForm(forms.ModelForm):
    class Meta:
        model = Well
        fields = ['priority',]

class WellPriorityForm(WellForm):
    class Meta(WellForm.Meta):
        fields = ['priority',]

class PlateForm(forms.ModelForm):
    class Meta:
        model = Plate
        fields = ("name","isTemplate",)
    def __init__(self, *args, **kwargs):
        if kwargs.get('user'):
            self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if self.instance.isSource==False:
            self.fields.pop('isTemplate')

    def clean(self, *args, **kwargs):
        cd = self.cleaned_data
        if self.instance.isSource==False and cd.get('isTemplate'):
            self.add_error(None,
                    ValidationError(            
                        ('Destination plates cannot be templates.'),
                        code='invalid',
                    )
                )

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

    collaborators = GroupedMutlipleModelChoiceField(
                queryset=User.objects.order_by('profile__primary_group__name'),
                choices_groupby='profile.primary_group.__str__',
                required=False,
            )
    editors = GroupedMutlipleModelChoiceField(
                queryset=User.objects.order_by('profile__primary_group__name'),
                choices_groupby='profile.primary_group.__str__',
                required=False,
            )
    class Meta:
        model = Project
        fields=('name','description','collaborators', 'editors', 'owner')

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if self.user:
            self.fields['owner'] = forms.ModelChoiceField(queryset=User.objects.filter(id=self.user.id), initial=self.user.id, widget=forms.HiddenInput())  
            user_qs = User.objects.filter(groups__in=self.user.groups.all(), is_active=True).exclude(id=self.user.id)    
            self.fields['collaborators'] = GroupedMutlipleModelChoiceField(
                queryset=user_qs.order_by('profile__primary_group__name'),
                initial=[u for u in user_qs],
                choices_groupby='profile.primary_group.__str__',
                required=False,
            )
                # widget=forms.CheckboxSelectMultiple,
                # widget=FilteredSelectMultiple("User", 
                #     is_stacked=False, attrs={'rows':'5'}),
                #     )
            self.fields['editors'] = GroupedMutlipleModelChoiceField(
                queryset=user_qs,
                choices_groupby='profile.primary_group',
                required=False,
            )
                # widget=forms.CheckboxSelectMultiple,
                # widget=FilteredSelectMultiple("User", 
                #     is_stacked=False, attrs={'rows':'5'}),
                #     required=False
                #     )

class ExperimentForm(forms.ModelForm):
    description = forms.CharField(required=False, widget=forms.Textarea(), max_length=300)
    protein = forms.CharField(max_length=100, required=False)
    desired_soak_date = forms.DateTimeField(initial=timezone.now().strftime('%m/%d/%Y %H:%M'), 
        input_formats=['%m/%d/%Y %H:%M'], label="Desired soak date", required=False,
        help_text="Desired soak date")

    class Meta:
        model = Experiment
        fields = ("name","description", "desired_soak_date", "protein", "srcPlateType", "destPlateType","owner","project")
        
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.project = kwargs.pop('project', None)
        self.pk_proj = kwargs.pop('pk_proj', None)
        super().__init__(*args, **kwargs)
        if self.pk_proj:
            self.project = Project.objects.get(pk=self.pk_proj)
        srcPlateType_qs = PlateType.objects.filter(isSource=True)
        destPlateType_qs = PlateType.objects.filter(isSource=False) 
        if self.user:
            self.fields['owner'] = forms.ModelChoiceField(queryset=User.objects.filter(id=self.user.id), initial=self.user.id, widget=forms.HiddenInput())  

        self.fields['srcPlateType'] = forms.ModelChoiceField(queryset=srcPlateType_qs, 
            label="Source plate type",
            initial=srcPlateType_qs.first())
        self.fields['destPlateType'] = forms.ModelChoiceField(queryset=destPlateType_qs, 
            label="Destination plate type",
            initial=destPlateType_qs.first())

        exp = kwargs.get('instance', None)
        if exp and self.user:
            lib_id = exp.library_id
            qs = self.user.libraries.filter()
            self.fields['library'] = forms.ModelChoiceField(queryset=qs, initial=lib_id, required=False)
            self.fields['project'] = forms.ModelChoiceField(queryset=user_editable_projects(self.user), initial=exp.project.id)
        if self.project:
            self.fields['project'] = forms.ModelChoiceField(queryset=user_editable_projects(self.user), initial=self.project.id, widget=forms.HiddenInput())

# MultiForms -------------------------------------------------------------------------

class ProjAsMultiForm(MultiFormMixin, ProjectForm):
    pass

class ExpAsMultiForm(MultiFormMixin, ExperimentForm):

    # """populate form with current values"""
    # def __init__(self, user, lib_qs=None, *args, **kwargs):
    #     super(ExpAsMultiForm, self).__init__(*args, **kwargs)
    #     exp = kwargs.get('instance', None)
    #     if exp:
    #         lib_id = exp.library_id
    #         qs = user.libraries.filter()
    #         if lib_qs:
    #             qs = lib_qs
    #         self.fields['library'] = forms.ModelChoiceField(queryset=qs, initial=lib_id, required=False)
    #         self.fields['project'] = forms.ModelChoiceField(queryset=user_editable_projects(user), initial=exp.project.id)

    class Meta(ExperimentForm.Meta):
        fields = list(ExperimentForm.Meta.fields) + ['project']

class ExpInitDataMultiForm(FormFieldPopoverMixin, MultiFormMixin):
    initDataFile = forms.FileField(label="Initialization file [.json]",
            validators=[FileExtensionValidator(['json'])],
            help_text=".json file to initialize experiment",
            widget=forms.FileInput(attrs={'accept': ".json"}),
            )
    def __init__(self, exp, *args, **kwargs):
        self.exp = exp
        super(ExpInitDataMultiForm, self).__init__(*args,**kwargs)

    def clean_initDataFile(self):
        initDataFile = self.cleaned_data.get('initDataFile', None)
        required_plate_keys = ['plate_id', 'date_time', 'temperature', 'subwells']
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

                for p_id in plate_ids:
                    p = data_dict[p_id]
                    keys = p.keys()
                    missing_keys = missing_list_elems(required_plate_keys, keys)
                    if missing_keys:
                        self.add_error('initDataFile',
                            ValidationError(            
                                ('Plate in .json has missing keys %(value)s.'),
                                code='invalid',
                                params={'value': missing_keys},
                            )
                        )

            except (ValueError, OverflowError) as e:
                if issubclass(type(e), ValueError):
                    self.add_error('initDataFile','File given is not in correct .json format. Review instructions above.')
                if type(e) is OverflowError:
                    self.add_error('initDataFile','File is too big!')
            return initDataFile

class CreateSrcPlatesMultiForm(FormFieldPopoverMixin, MultiFormMixin):
    numSrcPlates = forms.IntegerField(required=False, label="Number of plates", help_text="Number of plates you wish to create")
    plateLibDataFile = forms.FileField(required=False, label="Source plate(s) file [.csv]", help_text=".csv file defining where compounds are in plate",
        validators=[FileExtensionValidator(['csv'])],widget=forms.FileInput(attrs={'accept': ".csv"}))
    # templateSrcPlates = forms.ModelMultipleChoiceField(
    #     queryset=Plate.objects.none(), 
    #     required=False, label="Template source plates",
    #     help_text="Source plates marked as 'template' from which to import")

    templateSrcPlates= GroupedMutlipleModelChoiceField(
        queryset=Plate.objects.none(),
        required=False, label="Template source plates",
        help_text="Source plates marked as 'template' from which to import",
        choices_groupby='experiment',)

    def __init__(self, exp, *args, **kwargs):
        template_qs = kwargs.pop('template_src_plates_qs')
        
        super().__init__(*args, **kwargs)
        if template_qs:
            self.fields['templateSrcPlates'].queryset = template_qs
        # make from crispy
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Div(
                Div(
                    HTML(
                        """
                        <h5 class="form-option-title collapse-btn collapsed" data-toggle="collapse" data-target="#option1-content"> 
                        Option 1: Import .csv file
                        </h5> 
                        """), 
                        css_class='card-header'
                    ),

                Div(
                    Div(
                        Row(
                            Column('numSrcPlates', css_class='col'),
                            Column('plateLibDataFile', css_class='col'),
                            css_class='form-row align-items-start',
                        ),
                        css_class='card-body'
                    ),
                    
                    css_class='collapse',
                    id='option1-content',
                ),
                css_class="card form-option",
            ),
            Div(
                Div(
                    HTML(
                        """
                        <h5 class="form-option-title collapse-btn collapsed" data-toggle="collapse" data-target="#option2-content"> 
                        Option 2: Copy from templates
                        </h5> 
                        """),
                        css_class='card-header'
                    ),
                Div(
                    Div(
                        Row(
                            Column('templateSrcPlates', css_class='col'),
                            css_class='form-row align-items-start',
                        ),
                        css_class='card-body'
                    ),
                    
                    css_class='collapse',
                    id='option2-content',
                ),
                css_class="card form-option",
            ),
            HTML("""<br>"""),
            Column('action', css_class='hidden'),
            Submit('submit', 'Submit')
        )
    def checkOptionOneValid(self):
        f = self.cleaned_data.get('plateLibDataFile')
        numSrcPlates = self.cleaned_data.get('numSrcPlates')
        headers_required =['zinc_id', 'well', 'plate_idx']
        plate_idxs = [] #list of unique plate_idx's
        if f:
            try:
                if f.size >= 2.5e6:
                    raise OverflowError
                headers = []
                content = []
                for c in f.chunks():
                    reader = csv.reader(str(c, encoding='utf-8').split('\n'), delimiter=',')
                    headers = next(reader)
                    headers_map = dict([(v,i) for i, v in enumerate(headers)])
                    try:
                        content.extend(headers)
                        for row in reader:    
                            plate_idx = int(row[headers_map['plate_idx']])
                            if plate_idx not in plate_idxs:
                                plate_idxs.append(plate_idx)
                            content.extend(row)
                    except KeyError:
                        pass # will be handled with headers_missing list below

                headers_missing = list(compress(headers_required, list(map(lambda h: not(h in headers), headers_required))))
                if headers_missing:
                    self.add_error('plateLibDataFile', 
                        ValidationError(            
                            ('Missing .csv headers %(value)s'),
                            code='invalid',
                            params={'value': headers_missing},
                        ))
                if [x+1 for x in range(numSrcPlates)] != [x for x in sorted(plate_idxs)]:
                    self.add_error('plateLibDataFile', 'Range of number of plates should match set of unique plate_idx')
                f.open() #have to reopen file after validation...or just send file contents
            except (ValueError, OverflowError) as e:
                if type(e) is OverflowError:
                    self.add_error('plateLibDataFile','File is too big!')
        
    def clean(self):
        cd = super().clean()
        numSrcPlates = cd.get('numSrcPlates', None)
        plateLibDataFile = cd.get('plateLibDataFile', None)
        templateSrcPlates = cd.get('templateSrcPlates', None)
        optionOneValid = all([numSrcPlates, plateLibDataFile])
        optionTwoValid = all([templateSrcPlates])
        if optionOneValid and optionTwoValid:
            self.add_error(None, "Please only fill out one option.")
        elif (not(optionOneValid) and not(optionTwoValid)):
            self.add_error(None,'Invalid form. Please choose only ONE of Option 1 or Option 2 and make sure all fields for whichever option are filled.')
        else:
            self.checkOptionOneValid()
        return cd

class RemovePlatesDropImagesForm(MultiFormMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

class PlatesSetupMultiForm(MultiFormMixin):
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

class SoaksSetupMultiForm(FormFieldPopoverMixin, MultiFormMixin):
    soakVolumeOverride = forms.IntegerField(required=False, label="Override Soak Volume (uL)", 
        validators=[MaxValueValidator(250), MinValueValidator(0)],
        help_text="soak volume to set for all soaks")
    # soakDate = forms.DateTimeField(initial=timezone.now().strftime('%m/%d/%Y %H:%M'), 
    #     input_formats=['%m/%d/%Y %H:%M'], label="Desired soak date", required=False,
    #     help_text="")

    def __init__(self, exp, *args, **kwargs):
        super().__init__(*args,**kwargs)

class PicklistMultiForm(MultiFormMixin, PrivateFileCSVForm):
    local_upload = forms.FileField(label="Local upload file [.csv]", widget=forms.HiddenInput(attrs={'accept': ".csv"}),
            validators=[FileExtensionValidator(['csv'])],required=False
            )
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
                            while not row[-1]:
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
                f.open()
    
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
        cd = super().clean()
        return cd
