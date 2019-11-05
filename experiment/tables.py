import django_tables2 as tables
from django_tables2.utils import A  # alias for Accessor
from .models import Project, Experiment, Soak, Plate
from lib.models import Compound, Library
from django.contrib.auth.models import User, Group
from django_tables2 import RequestConfig

class ModifyTable:
    attrs = {'class': 'table modify-table'}

class DestPlatesForGUITable(tables.Table):
    upload_drop_images = tables.LinkColumn(verbose_name="Upload", viewname='drop_images_upload', args=[A('pk')], orderable=False, empty_values=())
    drop_images_GUI = tables.LinkColumn(verbose_name="GUI", viewname='imageGUI', 
        kwargs={'plate_id': A('pk'), 'user_id': A('experiment.owner.pk'), 'file_name': A('drop_images.first.file_name')}, orderable=False, empty_values=())

    def render_upload_drop_images(self):
        return 'Upload'

    def render_drop_images_GUI(self, record):
    
        if Plate.objects.get(id=record.id).drop_images.count():
            return 'GUI'
        return ''

    class Meta:
        model = Plate
        template_name = 'django_tables2/bootstrap-responsive.html'
        fields=('name','plateType','upload_drop_images','drop_images_GUI')

class PlatesTable(tables.Table):
    # upload_drop_images = tables.LinkColumn(verbose_name="Upload", viewname='drop_images_upload', args=[A('pk')], orderable=False, empty_values=())
    
    # def render_upload_drop_images(self):
    #     return 'Upload'
    class Meta:
        model = Plate
        template_name = 'django_tables2/bootstrap-responsive.html'
        fields=('name','plateType',)

class SoaksTable(tables.Table):
    transferVol = tables.Column(accessor="transferVol")
    transferCompound = tables.Column(linkify=True, attrs={'a':{'target':'_blank'}})
    srcWell = tables.Column(accessor='src')
    destSubwell = tables.Column(accessor='dest')
    selection = tables.CheckBoxColumn(accessor='pk',empty_values=())

    def render_srcWell(self, value):
        return value.id

    def render_destSubwell(self, value):
        return value.id

    class Meta:
        model = Soak 
        template_name = 'django_tables2/bootstrap-responsive.html'
        fields = ('id','transferVol','transferCompound','srcWell', 'destSubwell','selection')

def modifyColumn(data_target, a_class, view_name, verbose_name='', orderable=False, accessor='pk'):
    return tables.Column(verbose_name=verbose_name, 
                orderable=orderable, 
                empty_values=(),
                linkify=(view_name, [A(accessor)]), 
                attrs={'a': {
                                "data-toggle":"modal", 
                                "data-target":"#" + data_target,
                                "class":a_class
                            }
                    })

class ModalEditSoaksTable(SoaksTable):
    def render_modify(self, value):
        return "Edit"

    def __init__(self, data_target=None, a_class=None, *args, **kwargs):
        if data_target and a_class:
            modify = tables.Column(verbose_name='', 
                orderable=False, 
                empty_values=(),
                linkify=('soak_edit', [A('pk')]), 
                attrs={'a': {
                                "data-toggle":"modal", 
                                "data-target":"#" + data_target,
                                "class":a_class
                            }}#shoud be a button to a modal
                ) 
            kwargs.update({'extra_columns':[('modify',modify)]})
        super( ModalEditSoaksTable, self ).__init__(*args, **kwargs)

    class Meta(SoaksTable.Meta, ModifyTable):
        exclude=('id',)
        # attrs = {'class': 'modify-table'}
        

class CollaboratorsTable(tables.Table):
    class Meta:
        model = User
        template_name = 'django_tables2/bootstrap-responsive.html'
        fields = ("username",)

class ExperimentsTable(tables.Table):
    name = tables.Column(linkify=('exp',{'pk_proj':A('project.pk'),'pk_exp':A('pk')}))
    checked = tables.CheckBoxColumn(accessor='pk',empty_values=())
    library = tables.Column(linkify=('lib',[A('library.pk')]))
    project = tables.Column(linkify=('proj',[A('project.pk')]))

    def render_date_created(self, value):
        return formatDateTime(value)

    def render_date_modified(self, value):
        return formatDateTime(value)

    class Meta:
        model = Experiment 
        template_name = 'django_tables2/bootstrap-responsive.html'
        fields = ('name','project','library', 'created_date','modified_date','protein','owner','checked')
        empty_text = ("There are no experiments yet...")

class ProjectsTable(tables.Table):
    # name = tables.LinkColumn(viewname='proj', args=[A('pk')])
    name = tables.Column(linkify=('proj',[A('pk')]))
    checked = tables.CheckBoxColumn(accessor='pk',empty_values=(), verbose_name="checked")
    collaborators = tables.ManyToManyColumn()
    experiments = tables.ManyToManyColumn(separator=', ',verbose_name="Experiments",
        linkify_item=('exp',{'pk_proj':A('project.pk'),'pk_exp':A('pk')}))
    
    def render_date_modified(self, value):
        return formatDateTime(value)
    
    def render_date_created(self, value):
        return formatDateTime(value)

    class Meta:
        model = Project 
        template_name = 'django_tables2/bootstrap-responsive.html'
        fields = ('name','owner','created_date','modified_date','experiments','collaborators','checked')

class ModalEditProjectsTable(ProjectsTable):
    def render_modify(self):
        return "Edit"

    def __init__(self, data_target=None, a_class=None, *args, **kwargs):
        
        if data_target and a_class:
            modify = modifyColumn(**{
                'data_target': data_target, 
                'a_class': a_class,
                'view_name': "proj_edit"
            })
            kwargs.update({'extra_columns':[('modify',modify)]})
        super( ModalEditProjectsTable, self ).__init__(*args, **kwargs)
        

    class Meta(ProjectsTable.Meta, ModifyTable):
        exclude = ()

class LibrariesTable(tables.Table):
    name = tables.Column(linkify=('lib',[A('pk')]))
    id = tables.Column(accessor='id')
    numCompounds = tables.Column(accessor='numCompounds', empty_values=(), verbose_name="# compounds")
    checked = tables.CheckBoxColumn(accessor='pk',empty_values=())

    class Meta:
        model=Library
        template_name = 'django_tables2/bootstrap-responsive.html'
        fields=('name','owner','numCompounds','supplier','checked')
        exclude=('id',)

    
class ModalEditLibrariesTable(LibrariesTable):
    def render_modify(self, value):
        return "Edit"

    # def __init__(self, data_target=None, a_class=None, form_action=None, *args, **kwargs):
    def __init__(self, *args, **kwargs):
        self.table_id = kwargs.pop('table_id', '')
        self.form_id =  kwargs.pop('form_id', '')
        self.data_target =  kwargs.pop('data_target', '')
        self.a_class =  kwargs.pop('a_class', '')
        self.form_action = kwargs.pop('form_action', '')

        if self.data_target and self.a_class and self.form_action:
            modify = tables.Column(verbose_name='', 
                orderable=False, 
                empty_values=(),
                linkify=('lib_edit', [A('pk')]), 
                attrs={'a': {
                                "data-toggle":"modal", 
                                "data-target":"#" + self.data_target,
                                "class": self.a_class
                            }}#shoud be a button to a modal
                ) 
            kwargs.update({'extra_columns':[('modify',modify)]})
        super( ModalEditLibrariesTable, self ).__init__(*args, **kwargs)
        

    class Meta(LibrariesTable.Meta, ModifyTable):
        exclude=()

class CompoundsTable(tables.Table):
    selection = tables.CheckBoxColumn(accessor='pk')
    zinc_id = tables.Column(accessor='zinc_id', linkify=True, attrs={'a':{"target":"_blank"}})
    
    class Meta(ModifyTable):
        model=Compound
        exclude=()

    def __init__(self, *args, **kwargs):
        self.table_id = kwargs.pop('table_id', '')
        self.form_id =  kwargs.pop('form_id', '')
        self.data_target =  kwargs.pop('data_target', '')
        self.a_class =  kwargs.pop('a_class', '')
        self.form_action = kwargs.pop('form_action', '')
        super(CompoundsTable, self ).__init__(*args, **kwargs)


        






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
    # recent_exps =[e.pk for e in  request.user.experiments.order_by('-modified_date')][:num_exps]
    qs = request.user.experiments.order_by('-modified_date')[:num_exps]
    # qs = Experiment.objects.filter(id__in=recent_exps)
    #print(qs)
    table = ExperimentsTable(data=qs, exclude=exc,orderable=False)
    # RequestConfig(request,paginate={'per_page': num_per_page}).coorderable=Falsenfigure(table)
    return table

def formatDateTime(dt):
    return dt.date().strftime('%m/%d/%y')