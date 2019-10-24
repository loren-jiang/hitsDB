from django import forms
from .models import DropImage
from experiment.models import Soak

# crispy form imports
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, Div, Field

class DropImageUploadForm(forms.ModelForm):
    class Meta:
        model = DropImage
        fields=('upload', 'file_name')

class SoakGUIForm(forms.ModelForm):
    class Meta:
        model = Soak
        fields = ('soakOffsetX', 'soakOffsetY', 'soakVolume',  'well_x', 'well_y', 'well_radius', 'useSoak')
        labels = {
            'soakOffsetX': 'Soak Center X (\u03BCm)',
            'soakOffsetY': 'Soak Center Y (\u03BCm)',
            'soakVolume': 'Soak Volume (\u03BCL)',
            'well_x': 'Well Center X (\u03BCm)',
            'well_y': 'Well Center Y (\u03BCm)',
            'well_radius': 'Well Radius (\u03BCm)',
            
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # make form crispy
        self.helper = FormHelper()
        
        self.helper.layout = Layout(
            Row(
                Field('soakOffsetX', wrapper_class='form-group col-md-4 mb-0', readonly=True, title="hh"),
                Field('soakOffsetY', wrapper_class='form-group col-md-4 mb-0', readonly=True),
                Field('soakVolume', wrapper_class='form-group col-md-4 mb-0', readonly=True),
                css_class='form-row'
            ),
            Row(
                css_id='soakVolume-slider'
            ),
            Row(
                Field('well_x', wrapper_class='form-group col-md-4 mb-0', readonly=True),
                Field('well_y', wrapper_class='form-group col-md-4 mb-0', readonly=True),
                Field('well_radius', wrapper_class='form-group col-md-4 mb-0', readonly=True),
                css_class='form-row'
            ),
            # Row(
            #     Column('useSoak', css_class='slider round form-group col-md-4 mb-0'),
            #     css_class='switch'
            # ),
            'useSoak',
        )
        self.helper.add_input(Submit('submit', 'Save'))