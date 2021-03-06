import django_tables2 as tables
from django_tables2.utils import A  # alias for Accessor
from .models import Project, Experiment, Soak, Plate
from lib.models import Compound, Library
from django.contrib.auth.models import User, Group
from django_tables2 import RequestConfig
from my_utils.my_tables import ModalFormMixin, ModalFormColumn, ModalFormColumn_, SelectionMixin, OrderableOffMixin
from django.db.models import Count, F, Value

class ModifyTable:
    attrs = {'class': 'table modify-table'}

class DestPlatesForGUITable(SelectionMixin, tables.Table):
    # upload_drop_images = tables.LinkColumn(verbose_name="Upload", viewname='drop_images_upload', args=[A('pk')], orderable=False, empty_values=())
    drop_images_GUI = tables.LinkColumn(verbose_name="GUI", viewname='imageGUI', 
        kwargs={'plate_id': A('pk'), 'user_id': A('experiment.owner.pk'), 'file_name': A('drop_images.first.file_name')}, 
        orderable=False, empty_values=(),
        )
    upload_drop_images = ModalFormColumn_(
        verbose_name='Drop Images',
        data_target='drop_images_upload_modal', 
        a_class='drop_images_upload btn btn-primary', 
        view_name='drop_images_upload_modal')
    name = tables.Column(verbose_name="RockMaker ID", accessor='rockMakerId')

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


class PlatesTable(OrderableOffMixin, tables.Table):
    name = tables.Column(orderable=True, linkify=True)

    class Meta:
        model = Plate
        template_name = 'django_tables2/bootstrap-responsive.html'
        fields=('name','plateType','plateIdxExp','isTemplate')

class ModalEditPlatesTable(ModalFormMixin, PlatesTable):
    class Meta(ModalFormMixin.Meta, PlatesTable.Meta):
        fields = ('name', 'plateType', 'isTemplate')

class SoaksTable(tables.Table):
    transferVol = tables.Column(accessor="transferVol")
    transferCompound = tables.Column(accessor='src.compound', linkify=True)
    # transferCompound = tables.Column(linkify=True, attrs={'a':{'target':'_blank'}})
    srcWell = tables.Column(accessor='src')
    destSubwell = tables.Column(accessor='dest')
    # selection = tables.CheckBoxColumn(accessor='pk',empty_values=())
    suggestedDataset = tables.Column(accessor='defaultDataset', orderable=False, verbose_name='Suggested dataset name')
    
    def render_srcWell(self, value):
        return value.id

    def render_destSubwell(self, value):
        return value.id

    class Meta:
        model = Soak 
        template_name = 'django_tables2/bootstrap-responsive.html'
        fields = ('id','transferVol','transferCompound','srcWell', 'destSubwell', 'dataset', 'suggestedDataset')

class ModalEditSoaksTable(SelectionMixin, ModalFormMixin, SoaksTable):
    class Meta(ModalFormMixin.Meta, SoaksTable.Meta):
        exclude = ()
        

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
    step = tables.Column(accessor='getCurrentStep', empty_values=(), orderable=False)

    def render_date_created(self, value):
        return formatDateTime(value)

    def render_date_modified(self, value):
        return formatDateTime(value)

    class Meta:
        model = Experiment 
        template_name = 'django_tables2/bootstrap-responsive.html'
        fields = ('name','project','step', 'library', 'created_date','modified_date','protein','owner','checked')
        empty_text = ("There are no experiments yet...")

class ModalEditExperimentsTable(SelectionMixin, ModalFormMixin, ExperimentsTable):
    class Meta(ModalFormMixin.Meta, ExperimentsTable.Meta):
        exclude = ()

class ProjectsTable(tables.Table):
    # name = tables.LinkColumn(viewname='proj', args=[A('pk')])
    name = tables.Column(linkify=('proj',[A('pk')]))
    collaborators = tables.ManyToManyColumn()
    editors = tables.ManyToManyColumn()
    experiments = tables.ManyToManyColumn(separator=', ',verbose_name="Experiments",
        linkify_item=('exp',{'pk_proj':A('project.pk'),'pk_exp':A('pk')}))
    # checked = tables.CheckBoxColumn(accessor='pk',empty_values=(), verbose_name="checked")

    def render_date_modified(self, value):
        return formatDateTime(value)
    
    def render_date_created(self, value):
        return formatDateTime(value)

    class Meta:
        model = Project 
        template_name = 'django_tables2/bootstrap-responsive.html'
        fields = ['name','owner','created_date','modified_date','experiments','collaborators','editors',]

class ModalEditProjectsTable(SelectionMixin, ModalFormMixin, ProjectsTable):
    class Meta(ProjectsTable.Meta):
        fields = ProjectsTable.Meta.fields

class LibrariesTable(tables.Table):
    name = tables.Column(linkify=('lib',[A('pk')]))
    id = tables.Column(accessor='id')
    numCompounds = tables.Column(accessor='numCompounds', empty_values=(), verbose_name="# compounds")
    # checked = tables.CheckBoxColumn(accessor='pk',empty_values=())

    class Meta:
        model=Library
        template_name = 'django_tables2/bootstrap-responsive.html'
        fields=('name','owner','numCompounds','supplier',)
        # exclude=('id',)

class ModalEditLibrariesTable(SelectionMixin, ModalFormMixin, LibrariesTable):
    class Meta(LibrariesTable.Meta):
        fields = LibrariesTable.Meta.fields

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


class ModalEditCompoundsTable(ModalFormMixin, CompoundsTable):
    class Meta(ModalFormMixin.Meta, CompoundsTable.Meta):
        pass






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
    table = ExperimentsTable(data=qs, exclude=exc,orderable=False)
    # RequestConfig(request,paginate={'per_page': num_per_page}).coorderable=Falsenfigure(table)
    return table

def formatDateTime(dt):
    return dt.date().strftime('%m/%d/%y')