from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
from django.shortcuts import render
from .forms import UploadCompoundsNewLib, UploadCompoundsFromJSON
from .models import Library, Compound
import json
from django.db import transaction, DatabaseError
from itertools import compress
from my_utils.orm_functions import bulk_add
from io import TextIOWrapper
from django.db import transaction
from django.core.exceptions import ValidationError
from django.urls import reverse, reverse_lazy
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.forms.utils import ErrorList
from hitsDB.views_import import * #common imports for views
from my_utils.my_views import ModalCreateView, ModalEditView, ModifyFromTableView
from django.contrib import messages
from .decorators import is_users_library

from hitsDB.views_import import * #common imports for views
from django_tables2 import RequestConfig
from .tables import LibrariesTable, CompoundsTable, ModalEditLibrariesTable, ModalEditCompoundsTable
from experiment.tables import ExperimentsTable
from .filters import CompoundFilter, LibraryFilter
from django_tables2.views import SingleTableMixin
from django_filters.views import FilterView
from .forms import LibraryForm
from .querysets import user_accessible_libs
from my_utils.views_helper import build_filter_table_context, build_modal_form_data


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
@user_passes_test(user_base_tests)
def modify_lib_compounds(request, pk_lib):
    if request.method=="POST":
        form = request.POST
        compound_pks = form.getlist('selection') #list of compound pks
        compounds_qs = Compound.objects.filter(id__in=compound_pks)
        compounds = [c for c in compounds_qs]
        prev = request.META.get('HTTP_REFERER')
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
    return redirect(prev)

@is_users_library
@login_required(login_url="/login")
@user_passes_test(user_base_tests)
def lib_compounds(request, pk_lib):
    lib_qs = Library.objects.filter(id=pk_lib)
    lib = lib_qs.first()
    expsTable = ExperimentsTable(data=lib.experiments.all(), exclude=['project', 'library', 'protein','owner','checked'],)
    compounds = lib.compounds.filter()
    compounds_filter = CompoundFilter(
        data=request.GET, 
        queryset=compounds,
        filter_id='compounds_filter', 
        form_id='compounds_filter_form'
        )
    table = ModalEditCompoundsTable(
        exclude=['id', 'chemicalName','chemicalFormula', 'smiles', 'zincURL', ],
        data=compounds_filter.qs,
        table_id='compounds_table',
        form_id='compounds_table_form',
        form_action=reverse('modify_lib_compounds', kwargs={'pk_lib':pk_lib}),
        )
    RequestConfig(request, paginate={'per_page': 10}).configure(table)

    url_class = "compounds_edit_url"
    modal_id = "compounds_edit_modal"

    exc = list(ModalEditLibrariesTable.Meta.fields) 
    libTable = ModalEditLibrariesTable(data=lib_qs, data_target=modal_id, a_class="btn btn-primary " + url_class,
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
    context = build_filter_table_context(compounds_filter, table, modals, buttons)
    context.update({
        'expsTable': expsTable,
        'lib': lib,
        'libTable': libTable,
    })
    # context = {
    #     'expsTable': expsTable,
    #     'lib': lib,
    #     'libTable': libTable,
    #     'filter': {
    #         'filter': compounds_filter, 
    #         'form':compounds_filter.form,
    #         'filter_id': compounds_filter.filter_id, 
    #         'filter_form_id': compounds_filter.form_id,
    #         },
    #     'table': {
    #         'table': table,
    #         'table_id': table.table_id,
    #         'table_form_id': table.form_id,
    #         'form_action_url': table.form_action,
    #         },
    #     'modals': {
    #         'modals': modals,
    #         'json': json.dumps(modals),
    #         },
    #     'btn': {
    #         'buttons': buttons,
    #         'json': json.dumps(buttons)
    #         },
    # }
    return render(request, 'experiment/lib_templates/library_compounds.html', context)

@is_users_library
@login_required(login_url="/login")
@user_passes_test(user_base_tests)
def lib_edit(request, pk_lib):
    lib = Library.objects.get(pk=pk_lib)
    form_data = {
        "name":lib.name,
        "description":lib.description,
        "supplier":lib.supplier
    }
    form = LibraryForm(initial=form_data)
    if request.method == 'POST':
        form = LibraryForm( request.POST, instance=lib)
        if request.POST.get('cancel', None):
            return redirect("libs")
        if form.is_valid():
            form.save()
            data = {'result':'success'}
            return JsonResponse(data, status=200)
        else:
            data = {'result':'failure'}
            data.update({'errors':form.errors.as_json()})
            return JsonResponse(data, status=403)
        # prev = request.META.get('HTTP_REFERER')
        # if prev:
        #     return redirect(prev)
        # return redirect("libs")

    context = {
        "arg":pk_lib,
        "form":form,
        "modal_title":"Edit Library",
        "action":reverse('lib_edit', kwargs={'pk_lib':pk_lib}), #should be view w/o arg
        "form_class": Library.getModalFormData()['edit']['form_class'],
        "use_ajax":True,
    }
    return render(request,'modals/modal_form.html', context)

@login_required(login_url="/login")
@user_passes_test(user_base_tests)
def libs(request):
    user_libs_qs = user_accessible_libs(request.user)
    # modalFormData = Library.getModalFormData()
    modalFormData = build_modal_form_data(Library)
    libs_filter = LibraryFilter(
        data=request.GET, 
        request=request, 
        queryset=user_libs_qs,
        filter_id='lib_filter',
        form_id='lib_filter_form'
        )
    table = ModalEditLibrariesTable(
        data=libs_filter.qs.order_by('-modified_date'), 
        order_by="id", 
        data_target=modalFormData['edit']['modal_id'], 
        a_class="btn btn-primary " + modalFormData['edit']['url_class'],
        table_id='lib_table',
        form_id='lib_table_form', 
        form_action=reverse('modify_libs'),
        view_name='lib_edit')
    
    RequestConfig(request, paginate={'per_page': 5}).configure(table)
    buttons = [
        {'id': 'delete_selected', 'text': 'Delete Selected','class': 'btn-danger btn-confirm'},
        # modalFormData['new']['button']
        {'id': 'new_lib_btn','text': 'New Library','class': 'btn-primary ' + 'lib_new_url', 
            'href':reverse('lib_new', kwargs={'form_class':"lib_new_form"})},
        ]
    modals = [
        modalFormData['edit'],
        modalFormData['new'],
        ]
    context = build_filter_table_context(libs_filter, table, modals, buttons)
    return render(request,'experiment/lib_templates/libraries.html', context)

@login_required(login_url="/login")
@user_passes_test(user_base_tests)
def modify_libs(request):
    prev = request.META.get('HTTP_REFERER')
    if request.method=="POST":
        form = request.POST
        btn_id = form['btn']
        if btn_id:
            pks_libs = form.getlist('checked') #list of lib pks
            libs_qs = Library.objects.filter(id__in=pks_libs)
            if btn_id=="delete_libs":
                libs_qs.delete()
    return redirect(prev)

# upload file (.csv or .json), create new library, and import compounds 
def upload_file(request):
    if request.method == 'POST':
        form = UploadCompoundsNewLib(request.POST, request.FILES,user=request.user)
        if form.is_valid():
            f = TextIOWrapper(request.FILES['file'], encoding=request.encoding)
            lib_name = form.cleaned_data['name'] #assumes lib_name is unique
            new_lib = Library(name=lib_name, owner=request.user)
            context = {'form':form}
   
            try:
                with transaction.atomic():
                    new_lib.save()
                    relations, created, existed = new_lib.newCompoundsFromFile(f)
                    context.update({
                        "createdCompounds":created,
                        "exisitingCompounds":existed,
                    })
            except Exception as e:
                context['form']._errors['file'] = [repr(e)]
            return render(request, 'upload_file.html', context)
    else:
        form = UploadCompoundsNewLib(user=request.user)
    return render(request, 'upload_file.html', {'form': form})

# upload file (.csv or .json), create new library, and import compounds 
@login_required(login_url="/login")
@user_passes_test(user_base_tests)
def new_lib_from_file(request, form_class="new_lib_form"):
    context = {
        "form":UploadCompoundsNewLib(user=request.user),
        "modal_title":"New Library",
        "action":reverse('lib_new', kwargs={'form_class':form_class}), 
        "form_class":form_class,
        "use_ajax":True, 
    }
    if request.method == 'POST':# and request.is_ajax():
        form = UploadCompoundsNewLib(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            cd = form.cleaned_data
            fi = cd.pop('file')
            cd.update({'owner':request.user})
            new_lib = Library(**cd)
            if fi: #if file is not None
                f = TextIOWrapper(fi, encoding=request.encoding)
                try:
                    with transaction.atomic():
                        new_lib.save()
                        relations, created, existed = new_lib.newCompoundsFromFile(f)
                        context.update({
                            "createdCompounds":created,
                            "exisitingCompounds":existed,
                        })
                except KeyError as e:
                    errors = form._errors.setdefault('file', ErrorList())
                    errors.append(u"Error processing file. Double check .csv contains the right formatting and column headers.")
                    data = {'result':'failure'}
                    data.update({'errors':form.errors.as_json()})
                    return JsonResponse(data, status=403)
            else:
                new_lib.save()            
            data = {'result':'success'}
            return JsonResponse(data, status=200)

        else:
            data = {'result':'failure'}
            data.update({'errors':form.errors.as_json()})
            return JsonResponse(data, status=403)
            # return render(request, 'modals/modal_form.html', context)
        context.update({'form':form})
    if request.method == 'GET':
        return render(request, 'modals/modal_form.html', context)

# upload file (.csv or .json) and import compounds with existing library
# deletes library compounds and associates new compounds
def update_library(request):
    pass

@method_decorator([login_required(login_url="/login"), is_users_library] , name='dispatch')
class SecureLibraryModalEdit(ModalEditView):
    pass

@method_decorator([login_required(login_url="/login"), ] , name='dispatch')
class SecureLibraryModalCreate(ModalCreateView):
    pass

@method_decorator([login_required(login_url="/login"), ], name='dispatch')
class SecureLibraryModifyFromTable(ModifyFromTableView):
    def post(self, request, *args, **kwargs):
        prev = request.META.get('HTTP_REFERER')
        form = request.POST
        btn_id = form['btn']
        if btn_id:
            pks = form.getlist('checked') #list of model instance pks
            qs = self.model_class.objects.filter(id__in=pks)
            user_qs = qs.filter(owner=request.user)
            if btn_id=="delete_selected":
                user_qs.delete()
        diff_qs = qs.difference(user_qs)
        if diff_qs.exists():
            for p in diff_qs:
                messages.error(request, "Could not delete project '" + p.name + "' because you are not the owner.")
        return redirect(prev)
