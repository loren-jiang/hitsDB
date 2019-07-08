import django_tables2 as tables
from django_tables2.utils import A  # alias for Accessor
from .models import Project, Experiment, Soak, Plate
from import_ZINC.models import Compound, Library
from django.contrib.auth.models import User, Group

class PlatesTable(tables.Table):

    class Meta:
        model = Plate
        template_name = 'django_tables2/bootstrap-responsive.html'

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

    class Meta:
        model = Experiment 
        template_name = 'django_tables2/bootstrap-responsive.html'
        fields = ('name', 'library', 'dateTime','protein','owner','expChecked')
        empty_text = ("There are no experiments yet...")

class ProjectsTable(tables.Table):
    name = tables.LinkColumn(viewname='proj', args=[A('pk')])
    expChecked = tables.CheckBoxColumn(accessor='pk',empty_values=())
    collaborators = tables.ManyToManyColumn()
    experiments = tables.ManyToManyColumn(separator=', ',verbose_name="Experiments",linkify_item=True,)
    id = tables.LinkColumn(verbose_name='Modify',text="Edit", 
        viewname='proj_edit_simple', args=[A('pk')], 
        attrs={'a': {
                        "data-toggle":"modal", 
                        "data-target":"#projEditModal",
                        "class":"project_edit"
                    }}) #shoud be a button to a modal
    
    class Meta:
        model = Project 
        template_name = 'django_tables2/bootstrap-responsive.html'
        fields = ('name','owner','dateTime','experiments','collaborators',)

class LibrariesTable(tables.Table):
    name = tables.LinkColumn(viewname='lib_compounds', args=[A('pk')])

    class Meta:
        model=Library
        template_name = 'django_tables2/bootstrap-responsive.html'
        fields=('name',)


class CompoundsTable(tables.Table):
    class Meta:
        model=Compound
        template_name = 'django_tables2/bootstrap-responsive.html'
        fields=('nameInternal','smiles')
        