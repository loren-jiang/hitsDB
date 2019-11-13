from hitsDB.views_import import * #common imports for views
from ..models import Experiment, Soak
from ..filters import SoakFilter
from django_tables2 import RequestConfig
from ..tables import SoaksTable, ModalEditSoaksTable
from django.db.models import F
from ..decorators import is_users_experiment
from ..forms import SoakForm
# from . import ModalEdit

# class SoakEdit(ModalEdit):
#     pk_url_kwarg = 'pk_soak'
#     modal_title = 'Edit Soak'
#     form_tag_class = "soak_edit_form"
#     queryset = Soak.objects.filter()
#     # fields = ('transferCompound', 'transferVol') #if form_class is used, then cant use fields
#     form_class = SoakForm

#     def get_success_url(self):
#         return self.request.META.get('HTTP_REFERER')

#     def get_context_data(self,*args, **kwargs):
#         context = super(SoakEdit, self).get_context_data(*args, **kwargs)
#         s = context['soak']
#         context.update ({
#           "arg":kwargs.get('pk_soak',None),
#           "form":self.form_class(instance=s, exp=s.experiment), #overrides ModelForm
#           "modal_title":self.modal_title,
#           "action":self.request.path, #should be view w/o arg
#           "form_class":self.form_tag_class,
#         })
#         return context

@login_required(login_url="/login")
def soak_edit(request, pk_soak):
    soak = Soak.objects.get(pk=pk_soak)
    exp = soak.experiment
    # init_form_data = {
    #     "transferVol":soak.transferVol,
    # }
    # form = SoakForm(initial=init_form_data)
    form = SoakForm(instance=soak, exp=exp)
    if request.method == 'POST':
        form = SoakForm(data=request.POST, instance=soak)
        if request.POST.get('cancel', None):
            return redirect(request.path)
        if form.is_valid() and form.has_changed():
            form.save()
        prev = request.META.get('HTTP_REFERER')
        if prev:
            return redirect(prev)
        return redirect(request.path)

    data = {
        "arg":pk_soak,
        "form":form,
        "modal_title":"Edit Soak",
        "action":reverse_lazy('soak_edit', kwargs={'pk_soak':pk_soak}), #should be view w/o arg
        "form_class":"soak_edit_form",
    }
    return render(request,'modals/modal_form.html', data)

#view for soaks with filtering and editing soak data
@is_users_experiment
@login_required(login_url="/login")
def soaks(request, pk_proj, pk_exp):
    url_class = "soak_edit_url"
    modal_id = "soak_edit_modal"
    exp = get_object_or_404(Experiment, pk=pk_exp)
    soaks_qs = exp.soaks.select_related('src__plate','dest__parentWell__plate','transferCompound')
    soaks_filter = SoakFilter(request.GET, queryset=soaks_qs)
    table = ModalEditSoaksTable(data=soaks_filter.qs, order_by="id", 
        data_target=modal_id, a_class="btn btn-primary " + url_class)
    # soaks_table=exp.getSoaksTable()
    RequestConfig(request, paginate={'per_page': 25}).configure(table)
    
    data = {
        'filter': soaks_filter,
        'table': table,
        # we could further optimize this by just having on qs with combined annotations if needed
        'src_soaks_qs' : soaks_qs
          .annotate(plate_id=F('src__plate_id'))
          .annotate(well_row=F('src__wellRowIdx'))
          .annotate(well_col=F('src__wellColIdx'))
          .order_by('src__plate_id','id'),

        'dest_soaks_qs' : soaks_qs
          .annotate(plate_id=F('dest__parentWell__plate_id'))
          .annotate(well_row=F('dest__parentWell__wellRowIdx'))
          .annotate(well_col=F('dest__parentWell__wellColIdx'))
          .annotate(parent_well=F('dest__parentWell_id'))
          .order_by('dest__parentWell__plate_id','well_row','id'),
        'table_id':"soaks_table",
        'filter_form_id':'soaks_filter_form',
        'table_form_id':'soaks_table_form',
        'url_class': url_class,
        'modal_id': modal_id,
        'form_class':"soak_edit_form", # this should match form_class in soak_edit(request, pk_soak) function view
        # 'form_action_url': reverse_lazy('libs_delete'),
        
    }
    return render(request, 'experiment/soak_templates/soaks.html', data)