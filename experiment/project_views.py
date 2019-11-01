from hitsDB.views_import import * #common imports for views
from .models import Experiment, Plate, Well, SubWell, Soak, Project
from .tables import SoaksTable, ExperimentsTable, LibrariesTable, ProjectsTable, ModalEditProjectsTable
from django_tables2 import RequestConfig
from .exp_view_process import formatSoaks, ceiling_div, chunk_list, split_list, getWellIdx, getSubwellIdx
from import_ZINC.models import Library, Compound
from .forms import ExperimentModelForm, ProjectForm, SimpleProjectForm, ExpAsMultiForm
from django.contrib.auth.mixins import LoginRequiredMixin
from .decorators import is_users_project
from my_utils.orm_functions import make_instance_from_dict, copy_instance
from .querysets import user_accessible_projects


# PROJECT VIEWS ------------------------------------------------------------------
class ProjectView(LoginRequiredMixin, TemplateView):
    login_url = '/login'
    template_name = 'project.html'

    def get_data(self, pk_proj):
        proj = Project.objects.get(pk=pk_proj)
        data = {
            'show_path': True,
            'experimentsTable': proj.getExperimentsTable(),
            'proj':proj,
            'pk_proj':pk_proj,
            'librariesTable': proj.getLibrariesTable(),
            'collaboratorsTable' :proj.getCollaboratorsTable(),
            'form': ExperimentModelForm()
        }
        return data
    def get(self,request,*args,**kwargs):
        return self.render_to_response(self.get_data(self.kwargs['pk']))

    def post(self,request,*args,**kwargs):
        form = ExperimentModelForm(request.POST)
        data = self.get_data(self.kwargs['pk'])
        if form.is_valid():
            exp = form.save(commit=False)
            # form_data = form.cleaned_data
            exp.project = data['proj']
            exp.owner = request.user
            exp.save()

        return self.render_to_response(data)

@is_users_project
@login_required(login_url="/login")
def project(request, pk_proj):
    proj = Project.objects.get(pk=pk_proj)
    form = ExperimentModelForm()
    data = {
                'experimentsTable': proj.getExperimentsTable(exc=['project']),
                'pk_proj':pk_proj,
                'librariesTable': proj.getLibrariesTable(),
                'collaboratorsTable' :proj.getCollaboratorsTable(),
                'form':form,
            }

    if request.method == 'POST':
        form = ExperimentModelForm(request.POST)
        if form.is_valid():
            exp = form.save(commit=False)
            form_data = form.cleaned_data
            exp.project = Project.objects.get(id=pk_proj)
            exp.owner = request.user
            exp.save()
        return redirect('proj',pk_proj=pk_proj)

    return render(request,'experiment/proj_templates/project.html',data)
    # else:
    #     return HttpResponse("Don't have permission") # should create a request denied template later!

# returns user projects as django tables 2 for home page
# argument should be request for pagination to work properly
def get_user_projects(request, exc=[]):
    user_proj_qs = request.user.projects.all()
    user_collab_proj_qs = request.user.collab_projects.all()
    projectsTable = ProjectsTable(data=user_proj_qs.union(user_collab_proj_qs),exclude=exc)
    RequestConfig(request, paginate={'per_page': 5}).configure(projectsTable)
    return projectsTable

@login_required(login_url="/login")
@user_passes_test(user_base_tests)
def projects(request):
    # projectsTable = ModalEditProjectsTable(user_accessible_projects(request.user))
    projectsTable = ProjectsTable(user_accessible_projects(request.user))
    RequestConfig(request, paginate={'per_page': 20}).configure(projectsTable)
    data = {"projectsTable": projectsTable} 
    
    form = ProjectForm(user=request.user)
    data['form'] = form

    if request.method == 'POST':
        form = ProjectForm(request.user,request.POST)
        if form.is_valid():
            proj = form.save(commit=False)
            form_data = form.cleaned_data
            proj.owner = request.user
            proj.save()
            for c in form_data['collaborators']:
                proj.collaborators.add(c)
        return redirect('projects')
    return render(request, 'experiment/proj_templates/projects.html', data)

# edit project fields like name, description, and collaborators (any more?)
@is_users_project
@login_required(login_url="/login")
def project_edit(request,pk_proj):
    proj = Project.objects.get(pk=pk_proj)
    init_form_data = {
        "name":proj.name,
        "description":proj.description,
    }
    
    if request.method == 'POST':
        form = ProjectForm(request.user, request.POST, instance=proj)
        if form.is_valid() and form.has_changed():
            form.save()
        return redirect(reverse("proj",args=[pk_proj]))
    else:
        form = ProjectForm(request.user,initial=init_form_data,instance=proj)
    data = {
        "arg":pk_proj,
        "form":form,
    }
    return render(request,'project_edit.html', data)#,{'experiments':})

# edit simple project fields like name and description
@is_users_project
@login_required(login_url="/login")
def project_edit_simple(request,pk_proj):
    proj = Project.objects.get(pk=pk_proj)
    init_form_data = {
        "name":proj.name,
        "description":proj.description,

    }
    form = SimpleProjectForm(initial=init_form_data)
    if request.method == 'POST':
        form = SimpleProjectForm( request.POST, instance=proj)
        if request.POST.get('cancel', None):
            return redirect("projects")
        if form.is_valid() and form.has_changed():
            form.save()
        return redirect("projects")

    data = {
        "arg":pk_proj,
        "form":form,
        "modal_title":"Edit Project",
        "action":"/proj/simple_edit/", #should be view w/o arg
        "form_class":"proj_edit-form",
    }
    return render(request,'modal_form.html', data)#,{'experiments':})

# delete projects
@login_required(login_url="/login")
def delete_projects(request, pks):
    pks = pks.split('_')
    for pk in pks:
        if pk: #check if pk is not empty
            try:
                proj = get_object_or_404(Project, pk=pk)
                if proj.owner.pk == request.user.pk:
                    proj.delete()
            except:
                break
    return redirect('projects')


# PROJECT Library VIEWS ------------------------------------------------------------------
@is_users_project
@login_required(login_url="/login")
def proj_lib(request, pk_proj, pk_lib):
    return lib(request, pk_lib)

@is_users_project
@login_required(login_url="/login")
def proj_libs(request, pk_proj):
    exps = Experiment.objects.filter(project_id=pk_proj)
    libs_qs = Library.objects.filter(experiments__in=exps)
    table=LibrariesTable(libs_qs)
    RequestConfig(request, paginate={'per_page': 5}).configure(table)
    data = {
        'librariesTable': table,
    }
    return render(request,'libraries.html', data)

# retrieves the libraries assoc with experiments in a certain proj
def get_proj_exps_libs(request, pk_proj):
    exps = Experiment.objects.filter(project_id=pk_proj)
    libs_qs = Library.objects.filter(experiments__in=exps).union(
        Library.objects.filter(isTemplate=True))
    experimentsTable = ExperimentsTable(exps)
    libsTable = LibrariesTable(libs_qs)
    RequestConfig(request, paginate={'per_page': 5}).configure(experimentsTable)
    RequestConfig(request, paginate={'per_page': 5}).configure(libsTable)
    page_data = {
            'experimentsTable': experimentsTable,
            'pk_proj':pk_proj,
            'librariesTable': libsTable,
        }
    return page_data

def get_user_libraries(request, exc=[]):
    user_lib_qs = Library.objects.filter(owner_id=request.user.id)
    libsTable = LibrariesTable(data=user_lib_qs,exclude=exc)
    RequestConfig(request, paginate={'per_page': 5}).configure(libsTable)
    return libsTable

# PROJECT Experment VIEWS ------------------------------------------------------------------

#list all experiments in project
@is_users_project
def proj_exps(request, pk_proj):
    proj = Project.objects.get(id=pk_proj)
    exps = proj.experiments.filter()
    data = {
        'exps':exps,
    }
    return render(request, 'experiment/exp_templates/experiments.html', data)

#delete experiments in project
@login_required(login_url="/login")
def del_proj_exps(request, pk_proj, pks_exp):
    pks = pks.split('_')
    for pk in pks:
            if pk: #check if pk is not empty
                try:
                    exp = get_object_or_404(Experiment, pk=pk)
                    if (exp.owner.pk == request.user.pk):
                        exp.delete()
                except:
                    break
    if pk_proj:
        return redirect('proj',pk_proj)
    else:
        return redirect('experiments')

@login_required(login_url="/login")
def delete_experiments(request, pks, pk_proj=None):
    pks = pks.split('_')
    for pk in pks:
            if pk: #check if pk is not empty
                try:
                    exp = get_object_or_404(Experiment, pk=pk)
                    if (exp.owner.pk == request.user.pk):
                        exp.delete()
                except:
                    break
    if pk_proj:
        return redirect('proj',pk_proj)
    else:
        return redirect('experiments')

def _get_form(request, formcls, prefix):
    data = request.POST if prefix in request.POST else None
    return formcls(data, prefix=prefix)

# class NewExp(TemplateView):
#     template_name = 'new_experiment.html'
#     def get(self, request, *args, **kwargs):
#         lstLibraries = []
#         lstLibCompounds = []
#         userGroups = request.user.groups.all()
#         accessibleLibraries = Library.objects.filter(groups__in=userGroups)
#         libs_dict = {}
#         for lib in accessibleLibraries:
#             libs_dict[lib.name] = serialize('json',lib.compounds.order_by('id'),
#                 fields=('nameInternal','smiles','molWeight'),cls=DjangoJSONEncoder)
#         return self.render_to_response({
#             'aform': NewExperimentForm(prefix='aform_pre'),
#             'bform': PlateSetupForm(prefix='bform_pre'),
#             'libs_dict': libs_dict,
#                 },)

#     def post(self, request, *args, **kwargs):
#         pk_proj = kwargs['pk_proj']
#         aform = _get_form(request, NewExperimentForm, 'aform_pre')
#         bform = _get_form(request, PlateSetupForm, 'bform_pre')
#         go_to_div = False
#         if aform.is_bound and aform.is_valid():
#             form_data = aform.cleaned_data
#             exp = Experiment()
#             # exp = aform.save(commit=False)
#             exp.name = form_data['name']
#             exp.description = form_data['description']
#             exp.protein = form_data['protein']
#             exp.library = form_data['library']
#             exp.owner = request.user
#             if pk_proj:
#                 exp.project = get_object_or_404(Project,pk=pk_proj)
#             exp.save()
#             # go to next step in new_experiment.html
#             go_to_div = "list-plates"

#         elif bform.is_bound and bform.is_valid():
#             with transaction.atomic(): #wont commit until block is successfully executed. 
#                 # Process bform and render response
#                 form_data = bform.cleaned_data
#                 crystal_locations = [int(idx) for idx in form_data['crystal_locations']]
#                 screen = form_data['dest_plate_screen']
#                 src_plate = form_data['source_plate']
#                 src_plate_id = src_plate.id
#                 # dest_plate = form_data['dest_plate']
#                 num_src_wells = src_plate.numCols * src_plate.numRows
#                 exp = form_data['experiment']

#                 ##--------------------
                
#                 exp_compounds = exp.library.compounds.order_by('id')
#                 num_compounds = exp_compounds.count()
#                 num_src_plates = ceiling_div(num_compounds,num_src_wells)
#                 # list_src_plates = [Plate() for k in range(num_src_plates)]
#                 # list_src_wells = [Well() for k in range(num_compounds)]
#                 list_src_plates = [None for k in range(num_src_plates)]
#                 list_src_wells = [None for k in range(num_compounds)]
#                 # list_src_wells = [None] * num_compounds

#                 for i in range(num_src_plates):
#                     list_src_plates[i] = make_instance_from_dict(model_to_dict(src_plate),
#                         Plate)
#                     copy_plate = list_src_plates[i]
#                     copy_plate.experiment_id = exp.pk
#                     copy_plate.isTemplate = False #dont want to pollute template plates
#                     copy_plate.plateIdxExp = i+1

#                 Plate.objects.bulk_create(list_src_plates) #creates pks
#                 wells = src_plate.wells.values().order_by('id')
#                 well_idx = 0
#                 for p in list_src_plates:
#                     #make new copies of wells as
#                     new_wells = [None for k in range(num_src_wells)]
#                     j = 0
#                     for w in wells:
#                         new_wells[j] = make_instance_from_dict(w, Well)
#                         copy_well = new_wells[j]
#                         # copy_well = copy_instance(wells[j], new_wells[j])
#                         copy_well.plate_id = p.pk #relates new well with new plate
#                         j += 1
#                         try:
#                             list_src_wells[well_idx] = copy_well
#                             well_idx += 1
#                         except: #breaks out of loop if index out of range exception
#                             break

#                 Well.objects.bulk_create(list_src_wells)

#                 #------- DEST PLATES ----------
#                 dest_plate = form_data['dest_plate']
#                 dest_plate_id = dest_plate.id
#                 num_dest_wells = dest_plate.numCols * dest_plate.numRows
#                 num_dest_plates = ceiling_div(num_compounds,num_dest_wells * len(crystal_locations)) #ceiling division, max num of plates, we can delete empty ones later
#                 list_dest_subwells = [None] * num_compounds
#                 list_dest_wells = [None]*num_dest_plates*num_dest_wells
#                 list_dest_plates = [None] * num_dest_plates


#                 for j in range(num_dest_plates):
#                     list_dest_plates[j] = make_instance_from_dict(model_to_dict(dest_plate),
#                         Plate)
#                     copy_plate = list_dest_plates[j]
#                     copy_plate.experiment_id = exp.pk
#                     copy_plate.isTemplate = False #dont want to pollute template plates
#                     copy_plate.plateIdxExp = j+1

#                 Plate.objects.bulk_create(list_dest_plates)

#                 wells = dest_plate.wells.values().order_by('id')
#                 well_idx = 0
#                 for i in range(num_dest_plates):
#                     #make new copies of wells as
#                     copy_plate = list_dest_plates[i]
#                     new_wells = [None for k in range(num_dest_wells)]
#                     j = 0
#                     for w in wells:
#                         new_wells[j] = make_instance_from_dict(w, Well)
#                         copy_well = new_wells[j]
#                         # copy_well = copy_instance(wells[j], new_wells[j])
#                         copy_well.plate_id = copy_plate.pk #relates new well with new plate
#                         j += 1
#                         try:
#                             list_dest_wells[well_idx] = copy_well
#                             well_idx += 1
#                         except: #breaks out of loop if index out of range exception
#                             break

#                 Well.objects.bulk_create(list_dest_wells)

#                 # template dest_plate subwells
#                 subwells = dest_plate.wells.first().subwells.order_by('idx').values()
#                 num_subwells = subwells.count()
#                 subwell_idx = 0

#                 for w in list_dest_wells:
#                     new_subwells = [None]*num_subwells
#                     k = 0
#                     for s in subwells:
#                         new_subwells[k] = make_instance_from_dict(s,SubWell)
#                         copy_subwell = new_subwells[k]
#                         copy_subwell.parentWell_id = w.pk
#                         k += 1
#                         try:
#                             if s['idx'] in crystal_locations:

#                                 list_dest_subwells[subwell_idx] = copy_subwell
#                                 subwell_idx += 1
#                         except:
#                             break

#                 SubWell.objects.bulk_create(list_dest_subwells)
#                 # src_wells_qs = Well.objects.filter(plate__experiment_id=exp.id
#                 #     ).filter(plate__isSource=True).order_by('id').prefetch_related('compounds')
#                 # dest_subwells_qs = SubWell.objects.filter(parentWell__plate__experiment_id=exp.id
#                 #     ).filter(parentWell__plate__isSource=False).order_by('id').prefetch_related('compounds')

#                 # zipped_lst= list(zip(exp_compounds, src_wells_qs,dest_subwells_qs))
#                 ct = 0
#                 list_soaks = [None]*num_compounds
#                 for compound in exp_compounds:
#                 # for compound, src_well, dest_subwell in zipped_lst:
#                     src_well = list_src_wells[ct]
#                     src_well.compounds.add(compound)
#                     # src_well_plate_idx = src_well.plate.plateIdxExp

#                     dest_subwell = list_dest_subwells[ct]

#                     dest_subwell.compounds.add(compound)
#                     dest_subwell.hasCrystal = True
#                     soak = Soak(experiment=exp,src=src_well,dest=dest_subwell,
#                             transferCompound=compound)
#                     # soak.save()
#                     list_soaks[ct] = soak
#                     ct += 1
#                 Soak.objects.bulk_create(list_soaks)
#                 go_to_div = "list-crystals"

#         data = {'aform': aform, 'bform': bform, 'go_to_div': go_to_div,}
#         return self.render_to_response(data)
