from django import forms

class MultiFormMixin(forms.Form):
    action = forms.CharField(max_length=60, widget=forms.HiddenInput())

class FormFieldPopoverMixin(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            help_text = self.fields[field].help_text
            self.fields[field].help_text = None
            if help_text != '':
                self.fields[field].widget.attrs.update({'class':'has-popover', 'data-content':help_text, 'data-placement':'right', 'data-container':'body'})   