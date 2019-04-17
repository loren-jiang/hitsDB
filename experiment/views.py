from django.contrib.auth.models import User, Group
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from .forms import NewExperimentForm, PlateSetupForm, NewProjectForm
from .models import Experiment, Library, Compound, Plate, Well, SubWell, Soak, Project
from django.contrib.auth.decorators import login_required
from django.core.serializers.json import DjangoJSONEncoder
from django.core.serializers import serialize
from django.views.generic.base import TemplateView
from django.db import transaction
from .helper_fxns import ceiling_div, chunk_list, split_list, formatSoaks
from .tables import SoaksTable, ExperimentsTable, ProjectsTable, LibrariesTable, CompoundsTable
from django_tables2 import RequestConfig
from djqscsv import render_to_csv_response
from copy import deepcopy
from django.forms.models import model_to_dict


# Create your views here.
login_required(login_url="login/")
def lib_compounds(request, pk_lib):
    lib = get_object_or_404(Library, pk=pk_lib)
    compounds = lib.compounds.all()
    table=CompoundsTable(compounds)
    RequestConfig(request, paginate={'per_page': 25}).configure(table)
    data = {
        'CompoundsTable': table,
    }
    return render(request,'lib_compounds.html', data)

login_required(login_url="login/")
def libraries(request):
    libs_qs = Library.objects.filter(groups__in=request.user.groups.all()).union(
        Library.objects.filter(isTemplate=True))
    table=LibrariesTable(libs_qs)
    RequestConfig(request, paginate={'per_page': 5}).configure(table)
    data = {
        'librariesTable': table,
    }
    return render(request,'libraries.html', data)

@login_required(login_url="login/")
def proj_libraries(request, pk_proj):
    exps = Experiment.objects.filter(project_id=pk_proj)
    libs_qs = Library.objects.filter(experiments__in=exps).union(
        Library.objects.filter(isTemplate=True))
    table=LibrariesTable(libs_qs)
    RequestConfig(request, paginate={'per_page': 5}).configure(table)
    data = {
        'librariesTable': table,
    }
    return render(request,'libraries.html', data)

@login_required(login_url="login/")
def experiment(request, pk):
    experiment = Experiment.objects.select_related(
        'owner').get(id=pk)
    source_plates = experiment.plates.filter(isSource=True)
    dest_plates = experiment.plates.filter(isSource=False)
    num_src_plates = len(source_plates)
    num_dest_plates = len(dest_plates)
    soaks_qs = Soak.objects.filter(experiment=experiment
        ).select_related('dest__parentWell__plate','src__plate','transferCompound__library').order_by('id')
    table=SoaksTable(soaks_qs)
    RequestConfig(request, paginate={'per_page': 5}).configure(table)

    formattedSoaks = formatSoaks(soaks_qs,
        num_src_plates,num_dest_plates)

    data = {
        'pkUser': request.user.id,
        'experiment': experiment,
        'pkOwner': experiment.owner.id,

        # 'sourcePlates': [parsePlate(p) for p in source_plates],
        # 'destPlates': [parsePlate(p) for p in dest_plates],

        'plates' : formattedSoaks,
        'soaks': table,
    }
    return render(request,'experiment.html', data)


@login_required(login_url="login/")
def project(request, pk):
    pk_proj = pk
    exps = Experiment.objects.filter(project_id=pk_proj)
    libs_qs = Library.objects.filter(experiments__in=exps).union(
        Library.objects.filter(isTemplate=True))
    experimentsTable = ExperimentsTable(exps)
    libsTable = LibrariesTable(libs_qs)
    RequestConfig(request, paginate={'per_page': 5}).configure(experimentsTable)
    RequestConfig(request, paginate={'per_page': 5}).configure(libsTable)
    page_data = [{
            'experimentsTable': experimentsTable,
            'pk_proj':pk,
            'librariesTable': libsTable,
        }]
    data = page_data

    form = NewProjectForm(user=request.user)
    data[0]['form'] = form

    #     return render(request, "projects.html", data[0])
    if request.method == 'POST':
        form = NewProjectForm(request.user, request.POST)
        if form.is_valid():
            proj = form.save(commit=False)
            form_data = form.cleaned_data
            proj.owner = request.user
            proj.save()
            for c in form_data['collaborators']:
                print(c)
                proj.collaborators.add(c)

            # return something?
        data[0] = page_data
        data[0]['form'] = form

    return render(request,'project.html',data[0])#,{'experiments':})

@login_required(login_url="login/")
def delete_projects(request, pks):
    pks = pks.split('/')
    print(pks)
    for pk in pks:
        if pk: #check if pk is not empty
            try:
                proj = get_object_or_404(Project, pk=pk)
                proj.delete()
            except:
                break
    return redirect('projects')

@login_required(login_url="login/")
def experiments(request):
    experimentsTable = ExperimentsTable(request.user.experiments.all())
    RequestConfig(request, paginate={'per_page': 5}).configure(experimentsTable)
    data = {
        'experimentsTable': experimentsTable,
    }
    return render(request,'experiments.html',data)#,{'experiments':})

@login_required(login_url="login/")
def delete_experiment(request, pk):
    experiment = get_object_or_404(Experiment, pk=pk)
    experiment.delete()
    return redirect('experiments')

@login_required(login_url="login/")
def delete_experiments(request, pks, pk_proj=None):
    if pk_proj:
        pks = pks.split('/')
        for pk in pks:
            if pk: #check if pk is not empty
                try:
                    experiment = get_object_or_404(Experiment, pk=pk)
                    experiment.delete()
                except:
                    break
        return redirect('proj',pk_proj)
    else:
        pks = pks.split('/')
        for pk in pks:
            if pk: #check if pk is not empty
                try:
                    experiment = get_object_or_404(Experiment, pk=pk)
                    experiment.delete()
                except:
                    break
        return redirect('experiments')

def get_user_projects(request):
    user_proj_qs = request.user.projects.all()
    user_collab_proj_qs = request.user.collab_projects.all()
    projectsTable = ProjectsTable(user_proj_qs.union(user_collab_proj_qs))
    RequestConfig(request, paginate={'per_page': 5}).configure(projectsTable)
    return {
        'projectsTable': projectsTable,
    }
@login_required(login_url="login/")
def projects(request):
    data = [get_user_projects(request)]
    form = NewProjectForm(user=request.user)
    data[0]['form'] = form
    # if request.method == 'GET':

    #     return render(request, "projects.html", data[0])
    if request.method == 'POST':
        form = NewProjectForm(request.user,request.POST)
        if form.is_valid():
            proj = form.save(commit=False)
            form_data = form.cleaned_data
            proj.owner = request.user
            proj.save()
            for c in form_data['collaborators']:
                print(c)
                proj.collaborators.add(c)

            # return something?
        data[0] = get_user_projects(request)
        data[0]['form'] = form

    return render(request, 'projects.html', data[0])



@login_required(login_url="login/")
def delete_exp_plates(request, pk):
    exp = get_object_or_404(Experiment, pk=pk)
    for p in exp.plates.all():
        p.delete()
    return redirect('exp',pk)

# pk is experiment pk
def soaks_csv_view(request,pk):
    exp = get_object_or_404(Experiment, pk=pk)
    # qs = Soak.objects.filter(experiment=exp).values('transferCompound__nameInternal')
    qs = Soak.objects.filter(experiment=exp).values()
    return render_to_csv_response(qs
        )
def make_instance_from_dict(instance_model_a_as_dict,model_a):
    try:
        del instance_model_a_as_dict['id']
    except KeyError:
        pass
    # instance_model_a_as_dict.pop('id') #pops id so we dont copy primary keys
    # print(instance_model_a_as_dict)
    return model_a(**instance_model_a_as_dict)

def copy_instance(instance_of_model_a,instance_of_model_b):
    for field in instance_of_model_a._meta.fields:
        if field.primary_key == True:
            continue  # don't want to clone the PK
        setattr(instance_of_model_b, field.name, getattr(instance_of_model_a, field.name))
            # instance_of_model_b.save()
    return instance_of_model_b

def _get_form(request, formcls, prefix):

    data = request.POST if prefix in request.POST else None
    return formcls(data, prefix=prefix)

class NewExp(TemplateView):
    template_name = 'new_experiment.html'

    def get(self, request, *args, **kwargs):
        lstLibraries = []
        lstLibCompounds = []
        userGroups = request.user.groups.all()
        accessibleLibraries = Library.objects.filter(groups__in=userGroups)
        libs_dict = {}
        for lib in accessibleLibraries:
            libs_dict[lib.name] = serialize('json',lib.compounds.order_by('id'),
                fields=('nameInternal','smiles','molWeight'),cls=DjangoJSONEncoder)
        return self.render_to_response({
            'aform': NewExperimentForm(prefix='aform_pre'),
            'bform': PlateSetupForm(prefix='bform_pre'),
            'libs_dict': libs_dict,

                },)


    def post(self, request, *args, **kwargs):
        pk_proj = kwargs['pk_proj']
        aform = _get_form(request, NewExperimentForm, 'aform_pre')
        bform = _get_form(request, PlateSetupForm, 'bform_pre')
        go_to_div = False
        if aform.is_bound and aform.is_valid():
            form_data = aform.cleaned_data
            exp = Experiment()
            # exp = aform.save(commit=False)
            exp.name = form_data['name']
            exp.description = form_data['description']
            exp.protein = form_data['protein']
            exp.library = form_data['library']
            exp.owner = request.user
            if pk_proj:
                exp.project = get_object_or_404(Project,pk=pk_proj)
            exp.save()
            # go to next step in new_experiment.html
            go_to_div = "list-plates"

        elif bform.is_bound and bform.is_valid():
            with transaction.atomic(): #wont commit until block is successfully executed. 18 sec --> 12 sec performance boost
                # Process bform and render response
                form_data = bform.cleaned_data
                crystal_locations = [int(idx) for idx in form_data['crystal_locations']]
                screen = form_data['dest_plate_screen']

                src_plate = form_data['source_plate']
                src_plate_id = src_plate.id
                # dest_plate = form_data['dest_plate']
                num_src_wells = src_plate.numCols * src_plate.numRows
                exp = form_data['experiment']
                exp_compounds = exp.library.compounds.order_by('id')
                num_compounds = exp_compounds.count()
                num_src_plates = ceiling_div(num_compounds,num_src_wells)
                # list_src_plates = [Plate() for k in range(num_src_plates)]
                # list_src_wells = [Well() for k in range(num_compounds)]
                list_src_plates = [None for k in range(num_src_plates)]
                list_src_wells = [None for k in range(num_compounds)]
                # list_src_wells = [None] * num_compounds

                for i in range(num_src_plates):
                    list_src_plates[i] = make_instance_from_dict(model_to_dict(src_plate),
                        Plate)
                    copy_plate = list_src_plates[i]
                    copy_plate.experiment_id = exp.pk
                    copy_plate.isTemplate = False #dont want to pollute template plates
                    copy_plate.plateIdxExp = i+1

                Plate.objects.bulk_create(list_src_plates) #creates pks
                wells = src_plate.wells.values().order_by('id')
                well_idx = 0
                for p in list_src_plates:
                    #make new copies of wells as
                    new_wells = [None for k in range(num_src_wells)]
                    j = 0
                    for w in wells:
                        new_wells[j] = make_instance_from_dict(w, Well)
                        copy_well = new_wells[j]
                        # copy_well = copy_instance(wells[j], new_wells[j])
                        copy_well.plate_id = p.pk #relates new well with new plate
                        j += 1
                        try:
                            list_src_wells[well_idx] = copy_well
                            well_idx += 1
                        except: #breaks out of loop if index out of range exception
                            break

                Well.objects.bulk_create(list_src_wells)

                #------- DEST PLATES ----------
                dest_plate = form_data['dest_plate']
                dest_plate_id = dest_plate.id
                num_dest_wells = dest_plate.numCols * dest_plate.numRows
                num_dest_plates = ceiling_div(num_compounds,num_dest_wells * len(crystal_locations)) #ceiling division, max num of plates, we can delete empty ones later
                list_dest_subwells = [None] * num_compounds
                list_dest_wells = [None]*num_dest_plates*num_dest_wells
                list_dest_plates = [None] * num_dest_plates


                for j in range(num_dest_plates):
                    list_dest_plates[j] = make_instance_from_dict(model_to_dict(dest_plate),
                        Plate)
                    copy_plate = list_dest_plates[j]
                    copy_plate.experiment_id = exp.pk
                    copy_plate.isTemplate = False #dont want to pollute template plates
                    copy_plate.plateIdxExp = j+1

                Plate.objects.bulk_create(list_dest_plates)

                wells = dest_plate.wells.values().order_by('id')
                well_idx = 0
                for i in range(num_dest_plates):
                    #make new copies of wells as
                    copy_plate = list_dest_plates[i]
                    new_wells = [None for k in range(num_dest_wells)]
                    j = 0
                    for w in wells:
                        new_wells[j] = make_instance_from_dict(w, Well)
                        copy_well = new_wells[j]
                        # copy_well = copy_instance(wells[j], new_wells[j])
                        copy_well.plate_id = copy_plate.pk #relates new well with new plate
                        j += 1
                        try:
                            list_dest_wells[well_idx] = copy_well
                            well_idx += 1
                        except: #breaks out of loop if index out of range exception
                            break

                Well.objects.bulk_create(list_dest_wells)

                # template dest_plate subwells
                subwells = dest_plate.wells.first().subwells.order_by('idx').values()
                num_subwells = subwells.count()
                subwell_idx = 0

                for w in list_dest_wells:
                    new_subwells = [None]*num_subwells
                    k = 0
                    for s in subwells:
                        new_subwells[k] = make_instance_from_dict(s,SubWell)
                        copy_subwell = new_subwells[k]
                        copy_subwell.parentWell_id = w.pk
                        k += 1
                        try:
                            if s['idx'] in crystal_locations:

                                list_dest_subwells[subwell_idx] = copy_subwell
                                subwell_idx += 1
                        except:
                            break

                SubWell.objects.bulk_create(list_dest_subwells)
                # src_wells_qs = Well.objects.filter(plate__experiment_id=exp.id
                #     ).filter(plate__isSource=True).order_by('id').prefetch_related('compounds')
                # dest_subwells_qs = SubWell.objects.filter(parentWell__plate__experiment_id=exp.id
                #     ).filter(parentWell__plate__isSource=False).order_by('id').prefetch_related('compounds')

                # zipped_lst= list(zip(exp_compounds, src_wells_qs,dest_subwells_qs))
                ct = 0
                list_soaks = [None]*num_compounds
                for compound in exp_compounds:
                # for compound, src_well, dest_subwell in zipped_lst:
                    src_well = list_src_wells[ct]
                    src_well.compounds.add(compound)
                    # src_well_plate_idx = src_well.plate.plateIdxExp

                    dest_subwell = list_dest_subwells[ct]

                    dest_subwell.compounds.add(compound)
                    dest_subwell.hasCrystal = True
                    soak = Soak(experiment=exp,src=src_well,dest=dest_subwell,
                            transferCompound=compound)
                    # soak.save()
                    list_soaks[ct] = soak
                    ct += 1
                Soak.objects.bulk_create(list_soaks)
                go_to_div = "list-crystals"

        # elif cform.is_bound and cform.is_valid():
        #     form_data = cform.cleaned_data
        data = {'aform': aform, 'bform': bform, 'go_to_div': go_to_div,}
        return self.render_to_response(data)
