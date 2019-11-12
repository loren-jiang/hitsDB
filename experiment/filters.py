from django.contrib.auth.models import User, Group
from .models import Soak, Project
import django_filters
from .querysets import user_collaborators

class CustomFilterMixin:
    def __init__(self, *args, **kwargs):
        self.filter_id = kwargs.pop('filter_id', '')
        self.form_id = kwargs.pop('form_id', '')
        self.request = getattr(kwargs, 'request', None)
        super(CustomFilterMixin, self).__init__(*args, **kwargs)
        

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
