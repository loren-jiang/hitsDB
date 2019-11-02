import os
from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible

def validate_file_extension(value):
    import os
    ext = os.path.splitext(value.name)[1]  # [0] returns path+filename
    valid_extensions = ['.csv', '.json' ]
    if not ext.lower() in valid_extensions:
        raise ValidationError(u'Must be .csv or .json file.')

@deconstructible
class validate_prefix(object):
    def __init__(self, prefix):
        self.prefix = prefix

    def __call__(self, value):
        if not str(value).startswith(self.prefix):
            raise ValidationError(u'Does not have the right prefix.')

    def __eq__(self, other):
        return self.prefix == other.prefix