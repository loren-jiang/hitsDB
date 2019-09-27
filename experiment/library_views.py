from .views_import import * #common imports for views
from django_tables2 import RequestConfig
from import_ZINC.models import Library, Compound
from .tables import LibrariesTable, CompoundsTable, ModalEditLibrariesTable, ExperimentsTable
from import_ZINC.filters import CompoundFilter, LibraryFilter
from django_tables2.views import SingleTableMixin
from django_filters.views import FilterView
from .decorators import is_users_library
from .forms import LibraryForm
from .models import Experiment
from .querysets import accessible_libs

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

@is_users_library
@login_required(login_url="/login")
def modify_lib_compounds(request, pk_lib):
    if request.method=="POST":
        form = request.POST
        compound_pks = form.getlist('selection') #list of compound pks
        compounds_qs = Compound.objects.filter(id__in=compound_pks)
        compounds = [c for c in compounds_qs]
        prev = request.META.get('HTTP_REFERER')
        print(prev)
        if form['btn']=="remove_compounds":
            compounds_qs.delete()
        if form['btn']=="deactivate_compounds":
            for c in compounds:
                c.active = False
            Compound.objects.bulk_update(compounds, ['active'])
        if form['btn']=="activate_compounds":
            for c in compounds:
                c.active = True
            Compound.objects.bulk_update(compounds, ['active'])
    # return redirect('lib', pk_lib=pk_lib)
    return redirect(prev)

@is_users_library
@login_required(login_url="/login")
def lib_compounds(request, pk_lib):
    # lib = get_object_or_404(Library, pk=pk_lib)
    lib_qs = Library.objects.filter(id=pk_lib)
    lib = lib_qs[0]
    expsTable = ExperimentsTable(data=lib.experiments.all(), exclude=['project', 'library', 'protein','owner','expChecked'],)
    compounds = lib.compounds.filter()
    compounds_filter = CompoundFilter(request.GET, queryset=compounds)
    table = CompoundsTable(compounds_filter.qs)
    RequestConfig(request, paginate={'per_page': 10}).configure(table)

    url_class = "compounds_edit_url"
    modal_id = "compounds_edit_modal"

    exc = list(ModalEditLibrariesTable.Meta.fields)
    libTable = ModalEditLibrariesTable(data=lib_qs, data_target=modal_id, a_class="btn btn-info " + url_class,
        exclude=exc, attrs={'th': {'id': 'lib_table_header'}})
    buttons = [
        {'id': 'remove_compounds', 'text': 'Remove Selected','class': 'btn-danger btn-confirm', 'msg':'Remove selected compounds from library?'},
        {'id': 'deactivate_compounds','text': 'Deactivate Selected','class': 'btn-secondary btn-confirm'},
        {'id': 'activate_compounds','text': 'Activate Selected','class': 'btn-secondary btn-confirm'},
        ]
    modals = [
        {'url_class': url_class, 'modal_id': modal_id, 'form_class': "compounds_edit_form"},
        {'url_class': 'update_compounds_from_file_url', 'modal_id': 'update_compounds_from_file_modal', 
        'form_class': "update_compounds_from_file_url_form"},
        ]
    data = {
        'expsTable': expsTable,
        'lib': lib,
        'libTable': libTable,
        'filter': {
            'filter': compounds_filter, 
            'form':compounds_filter.form,
            'filter_id': 'compounds_filter',
            'filter_form_id': 'compounds_filter_form',
            },
        'table': {
            'table': table,
            'table_id': 'compounds_table',
            'table_form_id': 'compounds_table_form',
            'form_action_url': reverse('modify_lib_compounds', kwargs={'pk_lib':pk_lib}),
            },
        'modals': {
            'modals': modals,
            'json': json.dumps(modals),
            },
        'btn': {
            'buttons': buttons,
            'json': json.dumps(buttons)
            },
    }
    return render(request, 'experiment/lib_templates/library_compounds.html', data)
    # return render(request, 'experiment/lib_templates/lib_compounds.html', data)

@is_users_library
@login_required(login_url="/login")
def lib_edit(request, pk_lib):
    lib = Library.objects.get(pk=pk_lib)
    init_form_data = {
        "name":lib.name,
        "description":lib.description,
        "supplier":lib.supplier
    }
    from import_ZINC.forms import UploadCompoundsNewLib
    form = LibraryForm(initial=init_form_data)
    if request.method == 'POST':
        print("AJAX")
        print(request.is_ajax())
        form = LibraryForm( request.POST, instance=lib)
        if request.POST.get('cancel', None):
            return redirect("libs")
        if form.is_valid() and form.has_changed():
            form.save()
        prev = request.META.get('HTTP_REFERER')
        if prev:
            return redirect(prev)
        return redirect("libs")

    context = {
        "arg":pk_lib,
        "form":form,
        "modal_title":"Edit Library",
        "action":reverse_lazy('lib_edit', kwargs={'pk_lib':pk_lib}), #should be view w/o arg
        "form_class":"lib_edit_form",
    }
    return render(request,'modals/modal_form.html', context)

@login_required(login_url="/login")
def libs(request):
    # user_libs_qs = request.user.libraries.all()
    user_libs_qs = accessible_libs(request.user)
    # libs_qs = Library.objects.filter(groups__in=request.user.groups.all()).union(
    url_class = "lib_edit_url"
    modal_id = "lib_edit_modal"
    libs_filter = LibraryFilter(data=request.GET, queryset=user_libs_qs, request=request)#, user=request.user)
    table = ModalEditLibrariesTable(data=libs_filter.qs, order_by="id", 
        data_target=modal_id, a_class="btn btn-info " + url_class)
    RequestConfig(request, paginate={'per_page': 5}).configure(table)
    buttons = [
        {'id': 'delete_libs', 'text': 'Delete Selected','class': 'btn-danger btn-confirm'},
        {'id': 'new_lib','text': 'New Library','class': 'btn-primary ' + 'new_lib_url', 
            'href':reverse('upload_file', kwargs={'form_class':"new_lib_form"})},
        ]
    modals = [
        {'url_class': url_class, 'modal_id': modal_id, 'form_class': "lib_edit_form"},
        {'url_class': 'new_lib_url', 'modal_id': 'new_lib_modal', 'form_class': "new_lib_form"},
        ]
    data = {
        'filter': {
            'filter': libs_filter, 
            'form':libs_filter.form,
            'filter_id': 'lib_filter',
            'filter_form_id': 'lib_filter_form',
            },
        'table': {
            'table': table,
            'table_id': 'lib_table',
            'table_form_id': 'lib_table_form',
            'form_action_url': reverse_lazy('modify_libs'),
            },
        'modals': {
            'modals': modals,
            'json': json.dumps(modals),
            },
        'btn': {
            'buttons': buttons,
            'json': json.dumps(buttons)
            },
    }
    return render(request,'experiment/lib_templates/libraries.html', data)
    # return render(request,'experiment/list_delete_table.html', data)

@login_required(login_url="/login")
def modify_libraries(request):
    if request.method=="POST":
        form = request.POST
        pks_libs = form.getlist('checked') #list of lib pks
        libs_qs = Library.objects.filter(id__in=pks_libs)
        # libs = [l for l in libs_qs]
        # for l in libs:
        #     .delete()

        if form['btn']=="delete_libs":
            libs_qs.delete()
        # if form['btn']=="deactivate_compounds":
        #     for c in compounds:
        #         c.active = False
        #     Compound.objects.bulk_update(compounds, ['active'])
        # if form['btn']=="activate_compounds":
        #     for c in compounds:
        #         c.active = True
        #     Compound.objects.bulk_update(compounds, ['active'])
    return redirect('libs')