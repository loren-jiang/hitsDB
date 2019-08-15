import django_tables2 as tables
from django_tables2.utils import A  # alias for Accessor
from .models import Project, Experiment, Soak, Plate
from import_ZINC.models import Compound, Library
from django.contrib.auth.models import User, Group
from django_tables2 import RequestConfig

class PlatesTable(tables.Table):
    upload_well_images = tables.LinkColumn(viewname='well_images_upload', args=[A('pk')], orderable=False, empty_values=())
    def render_upload_well_images(self):
        return 'Upload images'
    class Meta:
        model = Plate
        template_name = 'django_tables2/bootstrap-responsive.html'
        fields=('name','plateType','upload_well_images',)

class SoaksTable(tables.Table):
    # transferCompound = tables.Column()

    # def render_transferCompound(self, value):
    #     return '%s' % value.nameInternal
    class Meta:
        model = Soak 
        template_name = 'django_tables2/bootstrap-responsive.html'

class CollaboratorsTable(tables.Table):
    class Meta:
        model = User
        template_name = 'django_tables2/bootstrap-responsive.html'
        fields = ("username",)

class ExperimentsTable(tables.Table):
    name = tables.LinkColumn(viewname='exp', args=[A('pk')])
    expChecked = tables.CheckBoxColumn(accessor='pk',empty_values=())
    library = tables.Column(linkify=('lib',[A('pk')]))
    project = tables.Column(linkify=('proj',[A('project.pk')]))

    def render_dateTime(self, value):
        return formatDateTime(value)

    class Meta:
        model = Experiment 
        template_name = 'django_tables2/bootstrap-responsive.html'
        fields = ('name','project','library', 'dateTime','protein','owner','expChecked')
        empty_text = ("There are no experiments yet...")

class ProjectsTable(tables.Table):
    # name = tables.LinkColumn(viewname='proj', args=[A('pk')])
    name = tables.Column(linkify=('proj',[A('pk')]))
    expChecked = tables.CheckBoxColumn(accessor='pk',empty_values=(), verbose_name="expChecked")
    collaborators = tables.ManyToManyColumn()
    experiments = tables.ManyToManyColumn(separator=', ',verbose_name="Experiments",linkify_item=('exp',[A('pk')]))
    modify = tables.Column(verbose_name='', 
        orderable=False, 
        empty_values=(),
        linkify=('proj_edit', [A('pk')]), 
        attrs ={'a': {"class": "btn btn-info"} }
        # attrs={'a': {
        #                 "data-toggle":"modal", 
        #                 "data-target":"#projEditModal",
        #                 "class":"project_edit"
        #             }}#shoud be a button to a modal
        ) 
    
    def render_dateTime(self, value):
        return formatDateTime(value)
    
    def render_modify(self):
        return "Edit"
    class Meta:
        model = Project 
        template_name = 'django_tables2/bootstrap-responsive.html'
        fields = ('name','owner','dateTime','experiments','collaborators','expChecked','modify')

class LibrariesTable(tables.Table):
    name = tables.Column(linkify=('lib',[A('pk')]))
    numCompounds = tables.Column(accessor='numCompounds', empty_values=(), verbose_name="# compounds")

    class Meta:
        model=Library
        template_name = 'django_tables2/bootstrap-responsive.html'
        fields=('name','numCompounds','supplier')

class CompoundsTable(tables.Table):
    selection = tables.CheckBoxColumn(accessor='pk')

    class Meta:
        model=Compound
        template_name = 'django_tables2/bootstrap-responsive.html'
        fields=('zinc_id','smiles','selection')
        
# returns user projects as django tables 2 for home page
# argument should be request for pagination to work properly
def get_user_projects(request, exc=[], num_per_page=5):
    user_proj_qs = request.user.projects.all()
    user_collab_proj_qs = request.user.collab_projects.all()
    projectsTable = ProjectsTable(data=user_proj_qs.union(user_collab_proj_qs),exclude=exc)
    RequestConfig(request, paginate={'per_page': num_per_page}).configure(projectsTable)
    return projectsTable

def get_user_libraries(request, exc=[], num_per_page=5):
    # user_lib_qs = Library.objects.filter(owner_id=request.user.id)
    user_lib_qs = request.user.libraries.all()
    libsTable = LibrariesTable(data=user_lib_qs,exclude=exc,orderable=False)
    RequestConfig(request, paginate={'per_page': num_per_page}).configure(libsTable)
    return libsTable

def get_user_recent_exps(request, exc=[], num_per_page=5, num_exps=3):
    # recent_exps =[e.pk for e in  request.user.experiments.order_by('-dateTime')][:num_exps]
    qs = request.user.experiments.order_by('-dateTime')[:num_exps]
    # qs = Experiment.objects.filter(id__in=recent_exps)
    print(qs)
    table = ExperimentsTable(data=qs, exclude=exc,orderable=False)
    # RequestConfig(request,paginate={'per_page': num_per_page}).coorderable=Falsenfigure(table)
    return table

def formatDateTime(dt):
    return dt.date().strftime('%m/%d/%y')