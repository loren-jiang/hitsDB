from django.contrib.auth.decorators import login_required
from django_tables2 import RequestConfig
from django.shortcuts import render, redirect, get_object_or_404
from import_ZINC.models import Library, Compound
from .tables import LibrariesTable, CompoundsTable


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

login_required(login_url="/login")
def libraries(request):
    libs_qs = Library.objects.filter(groups__in=request.user.groups.all()).union(
        Library.objects.filter(isTemplate=True))
    table=LibrariesTable(libs_qs)
    RequestConfig(request, paginate={'per_page': 5}).configure(table)
    data = {
        'librariesTable': table,
    }
    return render(request,'libraries.html', data)