from django.contrib.auth.models import User, Group
from .models import Soak
import django_filters

class SoakFilter(django_filters.FilterSet):
    srcWell = django_filters.CharFilter(field_name='src__id')#, lookup_expr='contains')
    destSubwell = django_filters.CharFilter(field_name='dest__id')#, lookup_expr='contains')
    srcPlateIdx = django_filters.NumberFilter(field_name='src__plate__plateIdxExp')
    wellName = django_filters.CharFilter(field_name="src__name")
    class Meta:
        model = Soak
        fields = ('id','transferCompound', 'srcWell','destSubwell')

