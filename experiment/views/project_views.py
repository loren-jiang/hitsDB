from hitsDB.views_import import * #common imports for views
from ..models import Experiment, Plate, Well, SubWell, Soak, Project
from ..tables import SoaksTable, ExperimentsTable, LibrariesTable, ProjectsTable, ModalEditProjectsTable
from django_tables2 import RequestConfig
from ..exp_view_process import formatSoaks, ceiling_div, chunk_list, split_list, getWellIdx, getSubwellIdx
from lib.models import Library, Compound
from ..forms import ExperimentForm, ProjectForm, SimpleProjectForm, ExpAsMultiForm, ProjAsMultiForm
from django.contrib.auth.mixins import LoginRequiredMixin
from ..decorators import is_users_project, is_user_accessible_project, is_user_editable_project
from my_utils.orm_functions import make_instance_from_dict, copy_instance
from ..querysets import user_accessible_projects
from my_utils.views_helper import build_filter_table_context, build_modal_form_data
from ..filters import ProjectFilter
from .experiment_views import experiments
from my_utils.my_views import MultiFormsView
from collections import OrderedDict
from my_utils.orm_functions import update_instance

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

@method_decorator([login_required(login_url="/login"), is_user_editable_project], name='dispatch')
class MultiFormsProjView(MultiFormsView):
    template_name = "experiment/proj_templates/project.html"
    form_classes = OrderedDict([
        ('projform', ProjAsMultiForm),
        ('newexpform', ExpAsMultiForm), 
    ])
    form_arguments = {}
    success_urls = {}

    # overload to process request to properly update multiforms with form arguments and success urls
    def dispatch(self, request, *args, **kwargs):
        user = request.user
        pk_proj = kwargs.get('pk_proj', None)
        proj = get_object_or_404(Project, pk=pk_proj) 
        self.request = request
        self.proj = proj
        self.form_arguments['projform'] = {
                                        'user':user,
                                        'instance':proj,
                                    }
        self.form_arguments['newexpform'] = {
            'user':user,
            'project':proj,
        }
        
        success = reverse_lazy('proj', kwargs=kwargs)
        self.success_urls['projform'] = success
        self.success_urls['newexpform'] = success  
        return super().dispatch(request, *args, **kwargs)
    
    def projform_form_valid(self, form):
        pk = self.kwargs.get('pk_proj', None)
        cleaned_data = form.cleaned_data
        form_name = cleaned_data.pop('action')
        update_instance(self.proj, cleaned_data)
        return HttpResponseRedirect(reverse_lazy('proj', kwargs={'pk_proj': pk,}))
    
    def newexpform_form_valid(self, form):
        pk = self.kwargs.get('pk_proj', None)
        cleaned_data = form.cleaned_data
        form_name = cleaned_data.pop('action')
        form = ExperimentForm(self.request.POST)
        if form.is_valid():
            exp = form.save(commit=False)
            exp.project = Project.objects.get(id=pk)
            exp.owner = self.request.user
            exp.save()
        return redirect('proj',pk_proj=pk)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        expForm = ExperimentForm()
        projForm = ProjectForm(user=self.request.user, instance=self.proj)
        context.update({
                'experimentsTable': self.proj.getExperimentsTable(exc=['project']),
                'pk_proj':self.proj.id,
                'librariesTable': self.proj.getLibrariesTable(),
                'collaboratorsTable' :self.proj.getCollaboratorsTable(),
                'expForm':expForm,
                'projForm':projForm,
            }
        )
        return context


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
@user_passes_test(user_base_tests)
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
