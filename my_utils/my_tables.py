import django_tables2 as tables
from django_tables2.utils import A  # alias for Accessor
from django_tables2 import RequestConfig

def ModalFormColumn(data_target, a_class, view_name, verbose_name='', orderable=False, accessor='pk'):
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

class ModalFormMixin(tables.Table):
    """
    Table mixin to create 'modify' column which links to a modal edit form for the model instance
    """
    def render_modify(self, value):
        return "Edit"

    class Meta:
        attrs = {'class': 'table modify-table'}

    def __init__(self, *args, **kwargs):
        self.table_id = kwargs.pop('table_id', '')
        self.form_id =  kwargs.pop('form_id', '')
        self.data_target =  kwargs.pop('data_target', '')
        self.a_class =  kwargs.pop('a_class', '')
        self.form_action = kwargs.pop('form_action', '')
        self.view_name = kwargs.pop('view_name','')

        if all([self.data_target, self.a_class, self.form_action, self.view_name]):
            modify = ModalFormColumn(**{
                'data_target': self.data_target, 
                'a_class': self.a_class,
                'view_name': self.view_name
            })
            kwargs.update(
                {
                    'extra_columns':[('modify',modify)],
                })
        super( ModalFormMixin, self ).__init__(*args, **kwargs)