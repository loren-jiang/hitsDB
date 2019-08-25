from .views_import import * #common imports for views
from .models import Experiment
from .filters import SoakFilter
from django_tables2 import RequestConfig
from .tables import SoaksTable
from django.db.models import F
from .decorators import is_users_experiment


#view for soaks with filtering and editing soak data
@is_users_experiment
@login_required(login_url="/login")
def soaks(request, pk_proj, pk_exp):
    exp = get_object_or_404(Experiment, pk=pk_exp)
    soaks_qs = exp.soaks.select_related('src__plate','dest__parentWell__plate','transferCompound')
    soaks_filter = SoakFilter(request.GET, queryset=soaks_qs)
    table = SoaksTable(soaks_filter.qs)
    # soaks_table=exp.getSoaksTable()
    RequestConfig(request, paginate={'per_page': 50}).configure(table)

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
        
    }
    return render(request, 'experiment/soak_templates/soaks.html', data)