import django_tables2 as tables
from django_tables2.utils import A  # alias for Accessor
from django_tables2 import RequestConfig

class OrderableOffMixin(tables.Table):
    def __init__(self, *args, **kwargs):
        orderable_off = kwargs.pop('orderable_off', False)
        super().__init__(*args, **kwargs)
        if orderable_off:
            self._orderable=False
            for k,v in self.columns.columns.items():
                setattr(v.column, 'orderable', False)

class ModalFormColumn_(tables.Column):
    def __init__(self, *args, **kwargs):
        kwargs.update({
            'orderable':False,
            'empty_values':(),
        })
        data_target = kwargs.pop('data_target', '')
        a_class = kwargs.pop('a_class', '')
        view_name = kwargs.pop('view_name', '')
        accessor = kwargs.pop('accessor', 'pk')
        if all([data_target, a_class, view_name, accessor]):
            kwargs.update({
                'linkify':(view_name, [A(accessor)]),
                'attrs': {
                            'a': {
                                "data-toggle":"modal", 
                                "data-target":"#" + data_target,
                                "class":a_class
                            }
                        }
            })
        super().__init__(*args, **kwargs)
    def render(self, value):
        return value

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
        pass
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
            extra_columns = kwargs.get('extra_columns', [])
            extra_columns.append(('modify',modify))
            attrs = kwargs.get('attrs', {})
            attrs_class = attrs.get('class', '')
            attrs_class += ' table modify-table'
            attrs_class = clean_css_class_string(attrs_class)
            attrs.update({
                'class': attrs_class,
            })
            kwargs.update(
                {
                    'extra_columns':extra_columns,
                    'attrs': attrs,
                })
        super( ModalFormMixin, self ).__init__(*args, **kwargs)

from my_utils.utility_functions import clean_css_class_string
class SelectionMixin(tables.Table):
    
    def __init__(self, *args, **kwargs):
        accessor = kwargs.get('accessor', 'pk')
        checked = tables.CheckBoxColumn(accessor=accessor,empty_values=(), verbose_name="checked")
        attrs = kwargs.get('attrs', {})
        attrs_class = attrs.get('class', '')
        attrs_class += ' table select-table'
        attrs_class = clean_css_class_string(attrs_class)
        attrs.update({
            'class': attrs_class,
        })
        extra_columns = kwargs.get('extra_columns', [])
        extra_columns.append(('checked', checked))
        kwargs.update(
                {
                    'extra_columns':extra_columns,
                    'attrs' : attrs,#{'class': 'table modify-table select-table'}
                })
        super().__init__(*args, **kwargs)