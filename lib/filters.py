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
    def __init__(self, *args, **kwargs):
        self.filter_id = kwargs.pop('filter_id', '')
        self.form_id = kwargs.pop('form_id', '')
        super(CompoundFilter, self ).__init__(*args, **kwargs)

class LibraryFilter(django_filters.FilterSet):

    owner = django_filters.ModelChoiceFilter(
        queryset=lambda request: User.objects.filter(groups__in=request.user.groups.all()) if request else None
        )

    class Meta:
        model = Library
        # exclude = []

        fields={
            'name':['icontains',],
            'supplier':['icontains',],
            'owner':['exact',]
        }
    def __init__(self, *args, **kwargs):
        self.filter_id = kwargs.pop('filter_id', '')
        self.form_id = kwargs.pop('form_id', '')
        super(LibraryFilter, self ).__init__(*args, **kwargs)