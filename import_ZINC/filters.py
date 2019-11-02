from django.contrib.auth.models import User, Group
from lib.models import Compound, Library
import django_filters

class CompoundFilter(django_filters.FilterSet):
    molWeightLTE = django_filters.NumberFilter("molWeight", lookup_expr="lte", label="MW &le;")
    molWeightGTE = django_filters.NumberFilter("molWeight", lookup_expr="gte", label="MW &ge;")
    class Meta:
        model = Compound
        fields = {
            'zinc_id':['icontains', ],
        }

def library_users(request):
    if request is None:
        return User.objects.none()
    user = request.user
    lib_users = User.objects.filter(groups__in=user.groups.all()).union(User.objects.filter(id=user.id))
    return lib_users

class LibraryFilter(django_filters.FilterSet):

    owner = django_filters.ModelChoiceFilter(field_name='owner', queryset=library_users)
    class Meta:
        model = Library
        # exclude = []

        fields={
            'name':['icontains',],
            'supplier':['icontains',],
        }
    def __init__(self, *args, **kwargs):
        self.filter_id = kwargs.pop('filter_id', '')
        self.form_id = kwargs.pop('form_id', '')
        super(LibraryFilter, self ).__init__(*args, **kwargs)