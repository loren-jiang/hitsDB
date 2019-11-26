from django import forms
from .models import DropImage
from experiment.models import Soak

# crispy form imports
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, Div, Field, HTML, Button
from s3.forms import ImagesFieldForm

class DropImagesFieldForm(ImagesFieldForm):
    def clean(self):
        cleaned_data = super().clean() #call parent clean()
        files = cleaned_data['image_field']

class DropImageUploadForm(forms.ModelForm):
    class Meta:
        model = DropImage
        fields = ('upload', 'file_name')


class SoakGUIForm(forms.ModelForm):
    class Meta:
        model = Soak
        fields = ('soakOffsetX', 'soakOffsetY', 'soakVolume', 'well_x',
                  'well_y', 'well_radius', 'useSoak',)# 'src')
        labels = {
            'soakOffsetX': 'X (\u03BCm)',
            'soakOffsetY': 'Y (\u03BCm)',
            'soakVolume': 'Volume (\u03BCL)',
            'well_x': 'X (\u03BCm)',
            'well_y': 'Y (\u03BCm)',
            'well_radius': 'Radius (\u03BCm)',
            # 'src':'Source well'
        }

    def __init__(self, src_qs, *args, **kwargs):
        
        super().__init__(*args, **kwargs)
        # self.fields['src'].queryset = src_qs
        # self.initial['src'] = src_qs.first()
        # make form crispy
        self.helper = FormHelper()
        
        self.helper.layout = Layout(
            Row(Column(HTML("""
                            <h5><strong>Soak </strong>
                            <svg width="20" height="20">
                                <circle class="circle outer-circle" cx="10" cy="10" r="8" stroke={{soakCircleColor}} stroke-width="2" fill="" fill-opacity="0.0" />
                                <circle class="circle inner-circle" cx="10" cy="10" r="1" stroke={{soakCircleColor}} stroke-width="2" fill={{soakCircleColor}} fill-opacity="1.0" />
                            </svg>
                            </h5>
                        """),
                       css_class='col-md-3 mb-0'),
                Column('useSoak', css_class='col-md-3 mb-0'),
                # Column('src', css_class='col-md-3 mb-0'),
                css_class='form-row align-items-start'),
            Row(Column(HTML(
                """X: {{soakOffsetX}} | Y: {{soakOffsetY}} | Vol: {{soakVolume}} """
            ),
                       css_class='col'),
                css_class='form-row'),
            Row(Field('soakOffsetX',
                      wrapper_class='form-group col',
                      readonly=True),
                Field('soakOffsetY',
                      wrapper_class='form-group col',
                      readonly=True),
                Field('soakVolume',
                      wrapper_class='form-group col',
                      readonly=True),
                css_class='form-row'),
            Div(HTML("""<br>"""), css_class='form-row'),
            Row(Column(HTML("""<h5><strong>Well </strong>
                            <svg width="20" height="20">
                                <circle class="circle outer-circle" cx="10" cy="10" r="8" stroke={{wellCircleColor}} stroke-width="2" fill="" fill-opacity="0.0" />
                                <circle class="circle inner-circle" cx="10" cy="10" r="1" stroke={{wellCircleColor}} stroke-width="2" fill={{wellCircleColor}} fill-opacity="1.0" />
                            </svg></h5>"""),
                       css_class='col-md-4 mb-0'),
                css_class='form-row'),
            Row(Column(HTML(
                """X: {{targetWellX}} | Y: {{targetWellY}} | Radius: {{targetWellRadius}}  """
            ),
                       css_class='col'),
                css_class='form-row'),
            Row(Field('well_x',
                      wrapper_class='form-group col-md-4 mb-0',
                      readonly=True),
                Field('well_y',
                      wrapper_class='form-group col-md-4 mb-0',
                      readonly=True),
                Field('well_radius',
                      wrapper_class='form-group col-md-4 mb-0',
                      readonly=True),
                css_class='form-row'),
            Div(HTML("""<br>"""), css_class='form-row'),
            Div(css_id='soakVolume-slider', css_class='form-row'),
            # Row(
            #     Column('useSoak', css_class='slider round form-group col-md-4 mb-0'),
            #     css_class='switch'
            # ),
            Div(HTML("""<br>"""), css_class='form-row'),
            Row(
                Column(Submit('submit', 'Save'), css_class='col-md-3 mb-0'),
                Column(HTML("""
                    <button type="button" class="btn btn-secondary" data-toggle="modal" data-target="#myModal">
                                    Jump wells
                                </button>
                
                """
                            ), css_class='col-md-3 mb-0'),
                css_class='form-row align-items-start'),
            Div(HTML("""<br>"""), css_class='form-row'),
            Row(
                Column(HTML("""
                    <span>
                        Set soak on click
                        <input  type="checkbox" name="setSoakOnClick" id="setSoakOnClick" Checked><br>  
                    </span>

                    <span>
                        Next well on save
                        <input  type="checkbox" name="nextWellOnSave" id="nextWellOnSave" Checked><br>  
                    </span>

                    
                """), css_class='col-md-3-mb-0'),
                css_class='form-row align-items-start',
            )
            )
