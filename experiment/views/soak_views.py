from hitsDB.views_import import * #common imports for views
from ..models import Experiment, Soak
from ..filters import SoakFilter
from django_tables2 import RequestConfig
from ..tables import SoaksTable, ModalEditSoaksTable
from django.db.models import F
from ..decorators import is_users_experiment
from ..forms import SoakForm
from django.utils import timezone
import csv
from my_utils.utility_functions import reshape, insert_every_nth
from my_utils.constants import idx_to_letters_map

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

@is_users_experiment
@login_required(login_url="/login")
def soak_transfers(request, pk_exp, pk_proj=None):
    exp = get_object_or_404(Experiment, pk=pk_exp)
    src_plate_type = exp.srcPlateType
    dest_plate_type = exp.destPlateType
    src_plates = exp.plates.filter(isSource=True).prefetch_related('wells')
    dest_plates = exp.plates.filter(isSource=False).prefetch_related('wells__subwells')
    src_wells = [w for w in exp.srcWells.select_related('plate', 'compound', 'soak')]
    dest_subwells = [s_w for s_w in exp.destSubwells.select_related('parentWell__plate', 'soak')]
    src_wells_reshaped = reshape(src_wells, (src_plates.count(), src_plate_type.numRows, src_plate_type.numCols))
    dest_subwells_reshaped = reshape(dest_subwells, (dest_plates.count(), dest_plate_type.numRows, dest_plate_type.numCols, dest_plate_type.numSubwells))
  
    soaks_qs = exp.soaks.select_related('src__plate','dest__parentWell__plate','transferCompound')
    src_dest_map = {}
    dest_src_map = {}

    for soak in soaks_qs:
        dest_src_map[soak.dest.id] = soak.src.id
        src_dest_map[soak.src.id] = soak.dest.id

    context = {
        # we could further optimize this by just having on qs with combined annotations if needed
        'src_wells':src_wells_reshaped, 
        'dest_subwells':dest_subwells_reshaped,
        'src_plates':src_plates,
        'dest_plates':dest_plates,
        'dest_src_map':dest_src_map,
        'src_dest_map':src_dest_map,
        'idx_to_letters_map':idx_to_letters_map,
    }
    return render(request, 'experiment/soak_templates/soak_transfers.html', context)

#view for soaks with filtering and editing soak data
@is_users_experiment
@login_required(login_url="/login")
def soaks(request, pk_exp, pk_proj):
    url_class = "soak_edit_url"
    modal_id = "soak_edit_modal"
    exp = get_object_or_404(Experiment, pk=pk_exp)
    soaks_qs = exp.soaks.select_related('src__plate','dest__parentWell__plate','transferCompound')
    soaks_filter = SoakFilter(request.GET, queryset=soaks_qs)
    table = ModalEditSoaksTable(data=soaks_filter.qs, order_by="id", 
        data_target=modal_id, a_class="btn btn-primary " + url_class)
    # soaks_table=exp.getSoaksTable()
    RequestConfig(request, paginate={'per_page': 25}).configure(table)
    
    context = {
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
    return render(request, 'experiment/soak_templates/soaks.html', context)

@is_users_experiment
def soaks_csv_view(request, pk_proj, pk_exp, pk_src_plate='', pk_dest_plate=''):
    pk = pk_exp
    exp = get_object_or_404(Experiment, pk=pk)
    exp.soak_export_date = timezone.now()
    exp.save()
    # dest_plate = get_object_or_404(Plate,pk_plate)
    qs = qs = exp.soaks.select_related("dest__parentWell__plate","src__plate").prefetch_related(
      ).order_by('id')
    if pk_dest_plate and pk_src_plate:
        qs = exp.soaks.select_related("dest__parentWell__plate","src__plate").prefetch_related(
      ).filter(src__plate_id=pk_src_plate, dest__parentWell__plate_id=pk_dest_plate)
    response = HttpResponse(content_type='text/csv')
    prefix = ''
    if pk_src_plate and pk_dest_plate:
        prefix = 'pair_' + pk_src_plate + '_' + pk_dest_plate + '_'
    response['Content-Disposition'] = 'attachment;filename=' + prefix + str(exp.name) + '_soaks' +  '.csv'
    writer = csv.writer(response)
    headers = ["Source Plate Name","Source Well","Destination Plate Name","Destination Well","Transfer Volume",
                    "Destination Well X Offset","Destination Well Y Offset"] 
    writer.writerow(headers) #headers for csv
    rows = []
    for s in qs:
        src_well = s.src
        dest_well = s.dest.parentWell
        src_plate_name = "Source[" + str(src_well.plate.plateIdxExp) + "]"
        src_well = src_well.name
        dest_plate_name = "Destination["  +str(dest_well.plate.plateIdxExp) + "]"
        dest_well = dest_well.name
        transfer_vol = s.soakVolume
        x_offset = round(s.offset_XY_um[0]*100)/100
        y_offset = round(s.offset_XY_um[1]*100)/100
        rows.append([src_plate_name,src_well,dest_plate_name,dest_well,transfer_vol,x_offset,y_offset])
    for r in sorted(rows, key=lambda x: ( x[headers.index("Source Plate Name")],x[headers.index("Source Well")])):
        writer.writerow(r)
    return response
