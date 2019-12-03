from hitsDB.views_import import * #common imports for views
from ..models import Experiment, Plate, Well, SubWell, Soak, Project
from ..tables import SoaksTable, ExperimentsTable, LibrariesTable, ProjectsTable, ModalEditProjectsTable
from django_tables2 import RequestConfig
from ..exp_view_process import formatSoaks, ceiling_div, chunk_list, split_list, getWellIdx, getSubwellIdx
from lib.models import Library, Compound
from ..forms import ExperimentForm, ProjectForm, SimpleProjectForm, ExpAsMultiForm
from django.contrib.auth.mixins import LoginRequiredMixin
from ..decorators import is_users_project, is_user_accessible_project, is_user_editable_project
from my_utils.orm_functions import make_instance_from_dict, copy_instance
from ..querysets import user_accessible_projects
from my_utils.views_helper import build_filter_table_context, build_modal_form_data
from ..filters import ProjectFilter
from .experiment_views import experiments

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
            'form': ExperimentForm()
        }
        return data
    def get(self,request,*args,**kwargs):
        return self.render_to_response(self.get_data(self.kwargs['pk']))

    def post(self,request,*args,**kwargs):
        form = ExperimentForm(request.POST)
        data = self.get_data(self.kwargs['pk'])
        if form.is_valid():
            exp = form.save(commit=False)
            # form_data = form.cleaned_data
            exp.project = data['proj']
            exp.owner = request.user
            exp.save()

        return self.render_to_response(data)
#TODO
# @method_decorator([login_required(login_url="/login"), is_user_editable_project], name='dispatch')
# class MultiFormsProjView(MultiFormsView):
#     template_name = "experiment/proj_templates/project.html"
#     form_classes = OrderedDict([
#         ('projform', ProjectForm), #step 0
#         ('newexpform', ExperimentForm), #step 1
#     ])
#     form_to_step_map = dict([(k,i) for i,k in enumerate(form_classes.keys())])
#     form_arguments = {}
#     success_urls = {}

#     # overload to process request to properly update multiforms with form arguments and success urls
#     def dispatch(self, request, *args, **kwargs):
#         user = request.user
#         pk_proj = kwargs.get('pk_proj', None)
#         proj = get_object_or_404(Project, pk_proj) 
        
#         self.form_arguments['projform'] = {
#                                         'user':user,
#                                         'instance':proj,
#                                     }
#         self.form_arguments['newexpform'] = {
#                                         'exp': exp, 
#                                         # 'instance':exp,
#         }
        
#         # populate success_urls dictionary with urls
#         exp_view_url = reverse_lazy('exp', kwargs=kwargs)
        
#         self.success_urls['expform'] = exp_view_url
#         self.success_urls['initform'] = exp_view_url  
#         self.success_urls['platelibform'] = exp_view_url
#         # self.success_urls['platesform'] = exp_view_url
#         self.success_urls['soaksform'] = exp_view_url
#         self.success_urls['picklistform'] = exp_view_url

#         return super().dispatch(request, *args, **kwargs)
    
#     def expform_form_valid(self, form):
#         pk = self.kwargs.get('pk_exp', None)
#         cleaned_data = form.cleaned_data
#         form_name = cleaned_data.pop('action')
#         exp_qs = Experiment.objects.filter(id=pk) #should a qs of one and it should exist
#         exp = exp_qs.first()
#         fields = [key for key in cleaned_data]
#         update_instance(exp, fields, cleaned_data)
#         return HttpResponseRedirect(reverse_lazy('exp', kwargs={'pk_proj': exp.project.id, 'pk_exp':exp.id}))
    
#     def initform_form_valid(self, form):
#         pk = self.kwargs.get('pk_exp', None)
#         cleaned_data = form.cleaned_data
#         form_name = cleaned_data.pop('action')
#         exp_qs = Experiment.objects.filter(id=pk) #should a qs of one and it should exist
#         exp = exp_qs.first()
#         exp.destPlateType = PlateType.objects.get(name="Swiss MRC-3 96 well microplate") #TODO: ensure destPlateType is set for experiment
#         f = cleaned_data['initDataFile']
#         useS3 = False
#         try:
#             with transaction.atomic():
#                 kwargs = {}
#                 if useS3:
#                     kwargs = {'owner':exp.owner, 'upload':f}
#                 else:
#                     kwargs = {'owner':exp.owner, 'local_upload':f}
#                 initData = PrivateFileJSON(**kwargs)
#                 initData.save()
#                 exp.initData = initData
#                 exp.save()  
#         except Exception as e:
#             print(e)
#             pass

#         return HttpResponseRedirect(self.get_success_url(form_name))
    
#     def platelibform_form_valid(self, form):
#         pk = self.kwargs.get('pk_exp', None)
#         cleaned_data = form.cleaned_data
#         form_name = cleaned_data.pop('action')
#         exp_qs = Experiment.objects.filter(id=pk) #should a qs of one and it should exist
#         exp = exp_qs.first()
#         lib = exp.library #TODO: ensure library is tied to experiment beforehand
#         # try:
#         templateSrcPlates = cleaned_data['templateSrcPlates']
#         if templateSrcPlates:
#             exp.importTemplateSourcePlates(templateSrcPlates)
#             # plates = exp.makeSrcPlates(len(templateSrcPlates))
#             # for p1, p2 in zip(plates, templateSrcPlates):
#             #     p1.copyCompoundsFromOtherPlate(p2)
#         else:
#             f = TextIOWrapper(cleaned_data['plateLibDataFile'], self.request.encoding)
#             with transaction.atomic():
#                 exp.createSrcPlatesFromLibFile(cleaned_data['numSrcPlates'], f)
  
#         return HttpResponseRedirect(self.get_success_url(form_name))

#     # def platesform_form_valid(self, form):
#     #     pk = self.kwargs.get('pk_exp', None)
#     #     cleaned_data = form.cleaned_data
#     #     form_name = cleaned_data.pop('action')
#     #     exp_qs = Experiment.objects.filter(id=pk) #should a qs of one and it should exist
#     #     exp_qs.update(**cleaned_data)
#     #     exp_qs.first().generateSrcDestPlates()
#     #     return HttpResponseRedirect(self.get_success_url(form_name))
    
#     def soaksform_form_valid(self, form):
#         pk = self.kwargs.get('pk_exp', None)
#         cleaned_data = form.cleaned_data
#         form_name = cleaned_data.pop('action')
#         exp_qs = Experiment.objects.filter(id=pk) #should a qs of one and it should exist
#         exp = exp_qs.first()
#         src_wells = [w for w in exp.srcWellsWithCompounds]
#         soaks = [s for s in exp.usedSoaks]
#         if form.data.get('match'):
#             exp.matchSrcWellsToSoaks(src_wells, soaks)
#         if form.data.get('interleave'):
#             exp.interleaveSrcWellsToSoaks(src_wells, soaks)
#         if cleaned_data['soakVolumeOverride']:
#             for s in soaks:
#                 s.soakVolume = cleaned_data['soakVolumeOverride']
#             Soak.objects.bulk_update(soaks, fields=('soakVolume',))
#         if cleaned_data['soakDate']:
#             exp.desired_soak_date = cleaned_data['soakDate']
#             exp.save()
#         return HttpResponseRedirect(self.get_success_url(form_name))
    
#     def picklistform_form_valid(self, form):
#         pk = self.kwargs.get('pk_exp', None)
#         cleaned_data = form.cleaned_data
#         form_name = cleaned_data.pop('action')
        
#         exp_qs = Experiment.objects.filter(id=pk) #should a qs of one and it should exist
#         exp = exp_qs.first()

#         f = PrivateFileCSV(**cleaned_data)
#         f.save()
#         exp.picklist = f
#         exp.save()
#         return HttpResponseRedirect(self.get_success_url(form_name))

#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         invalid_form_name = context.get('invalid_form_name')
#         step = 0
#         if invalid_form_name:
#             step = self.form_to_step_map[invalid_form_name]
#         pk_proj = self.kwargs.get('pk_proj', None)
#         pk = self.kwargs.get('pk_exp', None)
#         request = self.request
#         exp = request.user.experiments.prefetch_related('plates','soaks','library').get(id=pk)
#         plates = exp.plates.all()
#         soaks_table = exp.getSoaksTable(exc=[])
#         RequestConfig(request, paginate={'per_page': 5}).configure(soaks_table)
#         src_plates_table = exp.getSrcPlatesTable(exc=[])
#         plateModalFormData = build_modal_form_data(Plate)
#         src_plates_qs = plates.filter(isSource=True)
#         dest_plates_qs = plates.filter(isSource=False)
#         src_plates_table = ModalEditPlatesTable(
#             data=src_plates_qs,
#             data_target=plateModalFormData['edit']['modal_id'], 
#             a_class="btn btn-primary " + plateModalFormData['edit']['url_class'], 
#             form_action='a',
#             view_name='plate_edit',

#         )
#         # dest_plates_table = DestPlatesForGUITable(
#         #     data=exp.plates.filter(isSource=False), 
#         #     data_target="",
#         #     a_class="btn btn-primary ",
#         #     form_action='a',
#         #     view_name='drop_images_upload',
#         #     exclude=[],
#         #     )
#         dest_plates_table = exp.getDestPlatesGUITable(exc=[])
#         local_initData_path = ''
#         s3_initData_path = ''
#         if exp.initData:
#             local_initData_path = str(exp.initData.local_upload)
#             if local_initData_path:
#                 lst_path = local_initData_path.split('/')
#                 context['initData_local_url'] = '/media/' + local_initData_path
#                 context['initData_local'] = lst_path[len(lst_path) - 1]

#             s3_initData_path = str(exp.initData.upload)
#             if s3_initData_path:
#                 context['init_data_file_url'] = create_presigned_url(settings.AWS_STORAGE_BUCKET_NAME, 
#                     'media/private/' + s3_initData_path, 4000)
#         plateDict = dict(zip([p.id for p in plates],[p for p in plates]))
#         platePairs = exp.getSoakPlatePairs()
#         src_dest_plate_pairs = {}
#         for pair in platePairs:
#             src_dest_plate_pairs[pair] = {
#                 'href':reverse_lazy('soaks_csv_view', 
#                     kwargs={
#                         'pk_proj':pk_proj,
#                         'pk_exp':pk,
#                         'pk_src_plate':pair[0].id,
#                         'pk_dest_plate':pair[1].id,
#                     }),
#                 'src': pair[0],
#                 'dest': pair[1],

#             }

#         current_step =  exp.getCurrentStep
#         context['dest_plates_qs'] = dest_plates_qs
#         context['error_step'] = step
#         context['exp'] = exp
#         context['src_plates_table'] = src_plates_table
#         context['dest_plates_table'] = dest_plates_table
#         context['soaks_table'] = soaks_table
#         context['platesValid'] = exp.platesValid
#         context['current_step'] = current_step
#         context['soaksValid'] = exp.soaksValid
#         context['soaks_download'] = reverse('soaks_csv_view', kwargs={'pk_proj': pk_proj, 'pk_exp':exp.id})
#         context['rockMakerIds'] = [p.rockMakerId for p in exp.plates.filter(rockMakerId__isnull=False)]
#         context['incompleted_steps'] = [i+1 for i in range(current_step)]
#         context['picklist_template_download'] = reverse('picklist_template', kwargs={'pk_exp':exp.id, 'pk_proj':pk_proj})
#         context['src_dest_plate_pairs'] = src_dest_plate_pairs
#         context['plateDict']= plateDict
#         return context


@is_user_editable_project
@login_required(login_url="/login")
def project(request, pk_proj):
    proj = get_object_or_404(Project, pk=pk_proj)
    form = ExperimentForm()
    projForm = ProjectForm(user=request.user, instance=proj)
    context = {
                'experimentsTable': proj.getExperimentsTable(exc=['project']),
                'pk_proj':pk_proj,
                'librariesTable': proj.getLibrariesTable(),
                'collaboratorsTable' :proj.getCollaboratorsTable(),
                'form':form,
                'projForm':projForm,
            }

    if request.method == 'POST':
        form = ExperimentForm(request.POST)
        if form.is_valid():
            exp = form.save(commit=False)
            exp.project = Project.objects.get(id=pk_proj)
            exp.owner = request.user
            exp.save()
        return redirect('proj',pk_proj=pk_proj)

    return render(request,'experiment/proj_templates/project.html', context)
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
def modfiy_projs(request):
    prev = request.META.get('HTTP_REFERER')
    if request.method=="POST":
        form = request.POST
        btn_id = form['btn']
        if btn_id:
            pks = form.getlist('checked') #list of model instance pks
            qs = Project.objects.filter(id__in=pks)
            if btn_id=="delete_selected":
                qs.delete()
    return redirect(prev)

@login_required(login_url="/login")
@user_passes_test(user_base_tests)
def projects(request):
    # modalFormData = Project.getModalFormData()
    modalFormData = build_modal_form_data(Project)
    projectFilter = ProjectFilter(
        data=request.GET,
        request=request, 
        queryset=user_accessible_projects(request.user),
        filter_id='proj_filter',
        form_id='proj_filter_form',
    )
    table = ModalEditProjectsTable(
        data=projectFilter.qs.order_by('-modified_date'),
        data_target=modalFormData['edit']['modal_id'], 
        a_class="btn btn-primary " + modalFormData['edit']['url_class'], 
        table_id='proj_table',
        form_id='proj_table_form',
        form_action=reverse('modify_projs'),
        view_name='proj_edit',

        )
    RequestConfig(request, paginate={'per_page': 20}).configure(table)
    data = {"projectsTable": table} 
    
    form = ProjectForm(user=request.user)
    data['form'] = form
    buttons = [
        {'id': 'delete_selected', 'text': 'Delete Selected','class': 'btn-danger btn-confirm'},
        {'id': 'new_proj_btn','text': 'New Project','class': 'btn-primary ' + 'proj_new_url', 
            'href':reverse('proj_new')},
        ]
    modals = [
        modalFormData['edit'],
        modalFormData['new'],
        ]
    context = build_filter_table_context(projectFilter, table, modals, buttons)

    return render(request, 'experiment/proj_templates/projects.html', context)

@login_required(login_url="/login")
@user_passes_test(user_base_tests)
def project_new(request):
    form = ProjectForm(request.user, initial={'owner':request.user})
    prev_url = request.META.get('HTTP_REFERER')
    curr_url = request.path_info
    if request.method == 'POST':
        form = ProjectForm(request.user, request.POST, initial={'owner':request.user})
        if form.is_valid():
            form.save()
            if request.is_ajax():
                redirect(prev_url)
            return HttpResponseRedirect(curr_url)
    context = {
        'form':form,
    }
    return render(request, 'modals/modal_form.html', context)    

# edit project fields like name, description, and collaborators (any more?)
@is_users_project
@login_required(login_url="/login")
@user_passes_test(user_base_tests)
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
@user_passes_test(user_base_tests)
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
    return render(request,'modals/modal_form.html', data)#,{'experiments':})

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

# PROJECT Experment VIEWS ------------------------------------------------------------------

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
