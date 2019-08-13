from django.contrib.auth.models import User, Group
from import_ZINC.models import Compound, Library
import django_filters

class LibCompoundFilter(django_filters.FilterSet):
    class Meta:
        model = Compound
        fields = ['zinc_id', 'molWeight', ]

class CompoundFilter(django_filters.FilterSet):
    class Meta:
        model = Compound
        fields = ['zinc_id', 'molWeight', 'libraries', ]