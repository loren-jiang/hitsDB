from django.contrib.auth.decorators import login_required
from django_tables2 import RequestConfig
from django.shortcuts import render, redirect, get_object_or_404
from import_ZINC.models import Library, Compound
from .tables import LibrariesTable, CompoundsTable
from import_ZINC.filters import LibCompoundFilter, CompoundFilter
from django.urls import reverse
from django_tables2.views import SingleTableMixin
from django_filters.views import FilterView

# @login_required(login_url="/login")
# def user_compounds(request):
#     user_libs = request.user.libraries.all()
#     compounds = Compound.objects.filter(libraries__in=user_libs)
#     compound_filter = CompoundFilter(request.GET, queryset=compounds)
#     return render(request, 'experiment/lib_templates/lib_compounds_search.html', {'filter': compound_filter})

class UserCompoundsFilterView(SingleTableMixin, FilterView):
    table_class = CompoundsTable
    model = Compound
    template_name = 'experiment/lib_templates/lib_compounds_search.html'
    filterset_class = CompoundFilter

@login_required(login_url="/login")
def lib_compounds_search(request, pk_lib):
    lib = get_object_or_404(Library, pk=pk_lib)
    compounds = lib.compounds.all()
    compound_filter = LibCompoundFilter(request.GET, queryset=compounds)
    return render(request, 'experiment/lib_templates/lib_compounds_search.html', {'filter': compound_filter})

@login_required(login_url="/login")
def lib_compounds(request, pk_lib):
    lib = get_object_or_404(Library, pk=pk_lib)
    compounds = lib.compounds.all()
    table=CompoundsTable(compounds)
    RequestConfig(request, paginate={'per_page': 25}).configure(table)
    data = {
        'CompoundsTable': table,
    }
    return render(request,'lib_compounds.html', data)

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