from django.contrib.auth.models import User, Group
from import_ZINC.models import Compound, Library
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
    lib_users = User.objects.filter(groups__in=user.groups.all())
    return lib_users

class LibraryFilter(django_filters.FilterSet):
    owner = django_filters.ModelChoiceFilter(field_name='owner', queryset=library_users)
    
    class Meta:
        model = Library
        fields={
            'name':['icontains',],
            'supplier':['icontains',],
            # 'owner':['exact'],
        }
 
    # def __init__(self, user=None, *args, **kwargs):
    #         super(LibraryFilter, self).__init__(*args, **kwargs)
    #         # You need to override the method in the filter's form field
    #         #print(user.groups.all())
    #         self.filters['owner'].queryset = User.objects.filter(groups__in=user.groups.all())
    #         # self.filters['thon_group'].field.label_from_instance = lambda obj: obj.user.last_name