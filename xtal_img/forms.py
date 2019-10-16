from django import forms
from .models import DropImage
from experiment.models import Soak

# crispy form imports
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, Div, Field

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
                Field('soakOffsetX', wrapper_class='form-group col-md-4 mb-0', readonly=True),
                Field('soakOffsetY', wrapper_class='form-group col-md-4 mb-0', readonly=True),
                Field('transferVol', wrapper_class='form-group col-md-4 mb-0', readonly=True),
                css_class='form-row'
            ),
            Row(
                css_id='transferVol-slider'
            ),
            Row(
                Field('targetWellX', wrapper_class='form-group col-md-4 mb-0', readonly=True),
                Field('targetWellY', wrapper_class='form-group col-md-4 mb-0', readonly=True),
                Field('targetWellRadius', wrapper_class='form-group col-md-4 mb-0', readonly=True),
                css_class='form-row'
            ),
            # Row(
            #     Column('useSoak', css_class='slider round form-group col-md-4 mb-0'),
            #     css_class='switch'
            # ),
            'useSoak',
        )
        self.helper.add_input(Submit('submit', 'Save'))