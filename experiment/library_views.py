from .views_import import * #common imports for views
from django_tables2 import RequestConfig
from import_ZINC.models import Library, Compound
from .tables import LibrariesTable, CompoundsTable
from import_ZINC.filters import LibCompoundFilter, CompoundFilter
from django_tables2.views import SingleTableMixin
from django_filters.views import FilterView

@login_required(login_url="/login")
def user_compounds(request):
    user_libs = request.user.libraries.all()
    compounds = Compound.objects.filter(libraries__in=user_libs)
    compounds_table = CompoundsTable(compounds)
    RequestConfig(request, paginate={'per_page': 25}).configure(compounds_table)
    compound_filter = CompoundFilter(request.GET, queryset=compounds)
    data = {
        'filter':compound_filter,
        'form_id':"filter-form",
        'table':compounds_table,
        "table_id": "compounds_table",
        # "delete_url": reverse('delete_compounds',kwargs={'pks':''})
    }
    return render(request, 'experiment/list_delete_table.html', data)

# generic viewset is kinda meh since it doesn't allow get_context_data to extend...
class UserCompoundsFilterView(SingleTableMixin, FilterView):
    table_class = CompoundsTable
    model = Compound
    template_name = 'experiment/list_delete_table.html'
    filterset_class = CompoundFilter


@login_required(login_url="/login")
def lib_compounds(request, pk_lib):
    lib = get_object_or_404(Library, pk=pk_lib)
    compounds = lib.compounds.all()
    compounds_filter = LibCompoundFilter(request.GET, queryset=compounds)
    table = CompoundsTable(compounds_filter.qs)
    RequestConfig(request, paginate={'per_page': 25}).configure(table)
    data = {
        'filter': compounds_filter,
        'table':table,
        }
    return render(request, 'experiment/lib_templates/lib_compounds.html', data)

# @login_required(login_url="/login")
# def lib_compounds(request, pk_lib):
#     lib = get_object_or_404(Library, pk=pk_lib)
#     compounds = lib.compounds.all()
#     table=CompoundsTable(compounds)
#     RequestConfig(request, paginate={'per_page': 25}).configure(table)
#     data = {
#         'CompoundsTable': table,
#     }
#     return render(request,'lib_compounds.html', data)

@login_required(login_url="/login")
def libraries(request):
    user_libs_qs = request.user.libraries.all()
    # libs_qs = Library.objects.filter(groups__in=request.user.groups.all()).union(
    #     Library.objects.filter(isTemplate=True))
    # table=LibrariesTable(libs_qs)
    table=LibrariesTable(user_libs_qs)
    RequestConfig(request, paginate={'per_page': 5}).configure(table)
    data = {
        'librariesTable': table,
    }
    return render(request,'libraries.html', data)