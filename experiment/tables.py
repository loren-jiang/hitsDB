import django_tables2 as tables
from django_tables2.utils import A  # alias for Accessor
from .models import Soak, Compound, Experiment, Project, Library

class SoaksTable(tables.Table):
    # transferCompound = tables.Column()

    # def render_transferCompound(self, value):
    #     return '%s' % value.nameInternal

    class Meta:
        model = Soak 
        template_name = 'django_tables2/bootstrap-responsive.html'

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
    experiments = tables.ManyToManyColumn(separator='|',verbose_name="Experiments",linkify_item=True,)

    class Meta:
        model = Project 
        template_name = 'django_tables2/bootstrap-responsive.html'
        fields = ('name','owner','dateTime','experiments','collaborators')

class LibrariesTable(tables.Table):
    class Meta:
        model=Library
        template_name = 'django_tables2/bootstrap-responsive.html'
        