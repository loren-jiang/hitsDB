from django.contrib.auth.models import User, Group
from .models import Soak, Project, Plate, Experiment
import django_filters
from .querysets import user_collaborators

# Callables may also be defined out of the class scope.
def filter_not_empty(queryset, name, value):
    lookup = '__'.join([name, 'isnull'])
    return queryset.filter(**{lookup: False})

class CustomFilterMixin:
    def __init__(self, *args, **kwargs):
        self.filter_id = kwargs.pop('filter_id', '')
        self.form_id = kwargs.pop('form_id', '')
        self.request = getattr(kwargs, 'request', None)
        super().__init__(*args, **kwargs)
        
class ExperimentFilter(CustomFilterMixin, django_filters.FilterSet):
    class Meta:
        model = Experiment
        fields = {
            'name':['icontains'],
            'owner':['exact'],
        }

class SoakFilter(django_filters.FilterSet):
    srcWell = django_filters.CharFilter(field_name='src__id')#, lookup_expr='contains')
    destSubwell = django_filters.CharFilter(field_name='dest__id')#, lookup_expr='contains')
    srcPlateIdx = django_filters.NumberFilter(field_name='src__plate__plateIdxExp')
    wellName = django_filters.CharFilter(field_name="src__name")
    class Meta:
        model = Soak
        fields = ('id','transferCompound', 'srcWell','destSubwell')

def collaborators(request):
    if request is None:
        return User.objects.none()
    return user_collaborators(request.user)

class ProjectFilter(CustomFilterMixin, django_filters.FilterSet):

    collaborators = django_filters.ModelMultipleChoiceFilter(queryset=collaborators)
    class Meta:
        model = Project
        fields = {
            'name':['icontains'], 
            'owner':['exact'],
            }

class PlateFilter(CustomFilterMixin, django_filters.FilterSet):
    # isTemplate = django_filters.BooleanFilter(field_name='isTemplate', method=filter_not_empty)
    class Meta:
        model = Plate
        fields = {
            'name':['icontains'],
            'isTemplate':['exact'],
            'plateType__name':['icontains'],
        }   