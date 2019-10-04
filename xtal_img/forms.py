from django import forms
from .models import DropImage
from experiment.models import Soak

# crispy form imports
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column

class DropImageUploadForm(forms.ModelForm):
    class Meta:
        model = DropImage
        fields=('upload', 'well_name')

class SoakGUIForm(forms.ModelForm):
    class Meta:
        model = Soak
        fields = ('soakOffsetX', 'soakOffsetY', 'transferVol',  'targetWellX', 'targetWellY', 'targetWellRadius', 'useSoak')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # make form crispy
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('soakOffsetX', css_class='form-group col-md-4 mb-0'),
                Column('soakOffsetY', css_class='form-group col-md-4 mb-0'),
                Column('transferVol', css_class='form-group col-md-4 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('targetWellX', css_class='form-group col-md-4 mb-0'),
                Column('targetWellY', css_class='form-group col-md-4 mb-0'),
                Column('targetWellRadius', css_class='form-group col-md-4 mb-0'),
                css_class='form-row'
            ),
            # Row(
            #     Column('useSoak', css_class='slider round form-group col-md-4 mb-0'),
            #     css_class='switch'
            # ),
            'useSoak',
            # Submit('submit', 'Save')
        )