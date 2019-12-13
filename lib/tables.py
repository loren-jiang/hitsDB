import django_tables2 as tables
from django_tables2.utils import A  # alias for Accessor
from django_tables2 import RequestConfig
from my_utils.my_tables import ModalFormMixin, ModalFormColumn, SelectionMixin
from .models import Library, Compound

class LibrariesTable(tables.Table):
    name = tables.Column(linkify=('lib',[A('pk')]))
    id = tables.Column(accessor='id')
    numCompounds = tables.Column(accessor='numCompounds', empty_values=(), verbose_name="# compounds")
    # checked = tables.CheckBoxColumn(accessor='pk',empty_values=())

    class Meta:
        model=Library
        template_name = 'django_tables2/bootstrap-responsive.html'
        fields=['name','owner','numCompounds','supplier',]
        exclude=['id',]

class ModalEditLibrariesTable(SelectionMixin, ModalFormMixin, LibrariesTable):
    class Meta(LibrariesTable.Meta):
        fields = LibrariesTable.Meta.fields

class CompoundsTable(tables.Table):
    selection = tables.CheckBoxColumn(accessor='pk')
    zinc_id = tables.Column(accessor='zinc_id', linkify=True, attrs={'a':{"target":"_blank"}})
    
    class Meta:
        model=Compound  
        template_name = 'django_tables2/bootstrap-responsive.html'


class ModalEditCompoundsTable(ModalFormMixin, CompoundsTable):
    class Meta(ModalFormMixin.Meta, CompoundsTable.Meta):
        exclude=()


