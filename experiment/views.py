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
from .tables import SoaksTable, ExperimentsTable, ProjectsTable, LibrariesTable
from django_tables2 import RequestConfig
from djqscsv import render_to_csv_response
from copy import deepcopy


# Create your views here.
login_required(login_url="login/")
def libraries(request):
    libs_qs = Library.objects.filter(groups__in=request.user.groups.all()).union(
        Library.objects.filter(isTemplate=True))
    table=LibrariesTable(libs_qs)
    RequestConfig(request, paginate={'per_page': 5}).configure(table)
    data = {
        'LibrariesTable': table,
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
        'LibrariesTable': table,
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
    proj = Project.objects.prefetch_related( 
        'experiments').get(pk=pk)
    experimentsTable = ExperimentsTable(proj.experiments.all())
    RequestConfig(request, paginate={'per_page': 5}).configure(experimentsTable)
    data = {
        'experimentsTable': experimentsTable,
        'pk_proj':pk,
    }
    return render(request,'project.html',data)#,{'experiments':})

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
def delete_experiments(request, pks):
    pks = pks.split('/')
    print(pks)
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
        form = NewProjectForm(request.POST)
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

def _get_form(request, formcls, prefix):

    data = request.POST if prefix in request.POST else None
    return formcls(data, prefix=prefix)

class MyView(TemplateView):
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
                list_src_wells = [None] * num_compounds
                well_idx = 0
                for i in range(num_src_plates):
                    copy_plate = deepcopy(src_plate)
                    wells = copy_plate.wells.prefetch_related('compounds')
                    #creates copy of template source plate
                    copy_plate.pk = None
                    copy_plate.isTemplate = False #dont want to pollute template plates
                    copy_plate.plateIdxExp = i+1
                    copy_plate.save()

                    #make new copies of wells as
                    # new_wells = [None]*num_src_wells
                    for well in wells:
                        w = well
                        w.pk = None
                        w.plate_id = copy_plate.pk #relates new well with new plate
                        w.save()
                        try:
                            list_src_wells[well_idx] = w
                            well_idx += 1
                        except: #breaks out of loop if index out of range exception
                            break
                        
                    # plate = Plate.create384SourcePlate(name=exp.name + "_source_" +str(i+1))
                    exp.plates.add(copy_plate)

                dest_plate = form_data['dest_plate']
                dest_plate_id = dest_plate.id
                # dest_plate = form_data['dest_plate']
                num_dest_wells = dest_plate.numCols * dest_plate.numRows
                num_dest_plates = ceiling_div(num_compounds,num_dest_wells * len(crystal_locations)) #ceiling division, max num of plates, we can delete empty ones later
                list_dest_subwells = [None] * num_compounds
                subwell_idx = 0

                for j in range(num_dest_plates):
                    copy_plate = deepcopy(dest_plate)
                    wells = copy_plate.wells.prefetch_related('compounds','subwells')
                    #creates copy of template source plate
                    copy_plate.pk = None
                    copy_plate.isTemplate = False #dont want to pollute template plates
                    copy_plate.plateIdxExp = j+1
                    copy_plate.save()
                    
                    #make new copies of wells as
                    for well in wells:
                        w = well
                        subwells = w.subwells.prefetch_related('compounds')
                        w.pk = None
                        w.plate_id = copy_plate.pk #relates new well with new plate
                        w.crystal_screen_id = screen.pk
                        w.save()

                        #create subwell copies
                        for sub in subwells:
                            s = sub
                            s.pk = None
                            s.parentWell_id = w.pk
                            s.save()
                            try:
                                if s.idx in crystal_locations:
                                    list_dest_subwells[subwell_idx] = s
                                    subwell_idx += 1
                            except: #breaks out of loop if index out of range exception
                                break   
                    exp.plates.add(copy_plate)
               
                ct = 0
                for compound in exp_compounds:
                    src_well = list_src_wells[ct]
                    src_well.compounds.add(compound)
                    # src_well_plate_idx = src_well.plate.plateIdxExp

                    dest_subwell = list_dest_subwells[ct]

                    dest_subwell.compounds.add(compound)
                    dest_subwell.hasCrystal = True
                    dest_subwell.save()
                    soak = Soak(experiment=exp,src=src_well,dest=dest_subwell,
                            transferCompound=compound)
                    soak.save()
                    ct += 1

                go_to_div = "list-crystals"

        # elif cform.is_bound and cform.is_valid():
        #     form_data = cform.cleaned_data
        data = {'aform': aform, 'bform': bform, 'go_to_div': go_to_div,}
        return self.render_to_response(data)

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
                list_src_wells = [None] * num_compounds
                well_idx = 0
                for i in range(num_src_plates):
                    copy_plate = deepcopy(src_plate)
                    wells = copy_plate.wells.prefetch_related('compounds')
                    #creates copy of template source plate
                    copy_plate.pk = None
                    copy_plate.isTemplate = False #dont want to pollute template plates
                    copy_plate.plateIdxExp = i+1
                    copy_plate.save()

                    #make new copies of wells as
                    # new_wells = [None]*num_src_wells
                    for well in wells:
                        w = well
                        w.pk = None
                        w.plate_id = copy_plate.pk #relates new well with new plate
                        w.save()
                        try:
                            list_src_wells[well_idx] = w
                            well_idx += 1
                        except: #breaks out of loop if index out of range exception
                            break
                        
                    # plate = Plate.create384SourcePlate(name=exp.name + "_source_" +str(i+1))
                    exp.plates.add(copy_plate)

                dest_plate = form_data['dest_plate']
                dest_plate_id = dest_plate.id
                # dest_plate = form_data['dest_plate']
                num_dest_wells = dest_plate.numCols * dest_plate.numRows
                num_dest_plates = ceiling_div(num_compounds,num_dest_wells * len(crystal_locations)) #ceiling division, max num of plates, we can delete empty ones later
                list_dest_subwells = [None] * num_compounds
                subwell_idx = 0

                for j in range(num_dest_plates):
                    copy_plate = deepcopy(dest_plate)
                    wells = copy_plate.wells.prefetch_related('compounds','subwells')
                    #creates copy of template source plate
                    copy_plate.pk = None
                    copy_plate.isTemplate = False #dont want to pollute template plates
                    copy_plate.plateIdxExp = j+1
                    copy_plate.save()
                    
                    #make new copies of wells as
                    for well in wells:
                        w = well
                        subwells = w.subwells.prefetch_related('compounds')
                        w.pk = None
                        w.plate_id = copy_plate.pk #relates new well with new plate
                        w.crystal_screen_id = screen.pk
                        w.save()

                        #create subwell copies
                        for sub in subwells:
                            s = sub
                            s.pk = None
                            s.parentWell_id = w.pk
                            s.save()
                            try:
                                if s.idx in crystal_locations:
                                    list_dest_subwells[subwell_idx] = s
                                    subwell_idx += 1
                            except: #breaks out of loop if index out of range exception
                                break   
                    exp.plates.add(copy_plate)
               
                ct = 0
                for compound in exp_compounds:
                    src_well = list_src_wells[ct]
                    src_well.compounds.add(compound)
                    # src_well_plate_idx = src_well.plate.plateIdxExp

                    dest_subwell = list_dest_subwells[ct]

                    dest_subwell.compounds.add(compound)
                    dest_subwell.hasCrystal = True
                    dest_subwell.save()
                    soak = Soak(experiment=exp,src=src_well,dest=dest_subwell,
                            transferCompound=compound)
                    soak.save()
                    ct += 1

                go_to_div = "list-crystals"

        # elif cform.is_bound and cform.is_valid():
        #     form_data = cform.cleaned_data
        data = {'aform': aform, 'bform': bform, 'go_to_div': go_to_div,}
        return self.render_to_response(data)