from hitsDB.views_import import * #common imports for views
from ..models import Experiment, Plate, Well, SubWell, Soak, Project, PlateType
from ..tables import SoaksTable, ExperimentsTable, ModalEditPlatesTable, DestPlatesForGUITable
from django_tables2 import RequestConfig
from ..exp_view_process import formatSoaks, ceiling_div, chunk_list, split_list, getWellIdx, getSubwellIdx
from lib.models import Library, Compound
from ..forms import CreateSrcPlatesMultiForm, ExperimentModelForm, PlatesSetupMultiForm, \
    ExpAsMultiForm, SoaksSetupMultiForm, ExpInitDataMultiForm, PicklistMultiForm
from forms_custom.multiforms import MultiFormsView
from django.db.models import Count, F, Value
from ..decorators import is_users_experiment, is_user_accessible_experiment
from django.conf import settings
from s3.s3utils import myS3Client, myS3Resource, create_presigned_url
from s3.models import PrivateFileJSON, PrivateFileCSV
from io import TextIOWrapper
from my_utils.orm_functions import update_instance
from django.utils import timezone
import csv
import re
from django.views.generic.edit import UpdateView
from my_utils.views_helper import build_filter_table_context, build_modal_form_data
from ..querysets import user_editable_plates
from ..filters import PlateFilter
from my_utils.utility_functions import reshape
from collections import OrderedDict

class MultiFormsExpView(MultiFormsView, LoginRequiredMixin):
    template_name = "experiment/exp_templates/exp_main.html"
    form_classes = OrderedDict([
        ('expform', ExpAsMultiForm), #step 0
        ('initform', ExpInitDataMultiForm), #step 1
        ('platelibform', CreateSrcPlatesMultiForm), #step 2
        # ('platesform', PlatesSetupMultiForm),
        ('soaksform', SoaksSetupMultiForm), #step 4
        ('picklistform', PicklistMultiForm) #step 5

    ])
    form_to_step_map = dict([(k,i) for i,k in enumerate(form_classes.keys())])
    form_to_step_map['soaksform'] = 4
    form_to_step_map['picklistform'] = 5
    # form_classes = { 
    #                 'expform': ExpAsMultiForm,
    #                 'platelibform': CreateSrcPlatesMultiForm,
    #                 'initform': ExpInitDataMultiForm,
    #                 'platesform': PlatesSetupMultiForm,
    #                 'soaksform' : SoaksSetupMultiForm,
    #                 'picklistform': PicklistMultiForm,
    #                 }
    form_arguments = {}
    success_urls = {}

    # overload to process request to properly update multiforms with form arguments and success urls
    def dispatch(self, request, *args, **kwargs):
        user = request.user
        pk_exp = kwargs.get('pk_exp', None)
        pk_proj = kwargs.get('pk_proj', None)
        # ensure experiment is only accessible by owner
        if request.user != Experiment.objects.get(id=pk_exp).owner:
            raise PermissionDenied

        exp = user.experiments.get(id=pk_exp)
        
        self.form_arguments['expform'] = {
                                        'user':user,
                                        'lib_qs':user.libraries.filter(),
                                        'instance':exp
                                    }
        self.form_arguments['initform'] = {
                                        'exp': exp, 
                                        # 'instance':exp,
        }
        self.form_arguments['platelibform'] = {
                                            'exp': exp,
                                            'template_src_plates_qs': user_editable_plates(user).filter(isSource=True, isTemplate=True),
                                            # 'instance':exp,
                                    }
        # self.form_arguments['platesform'] = {
        #                                 'exp': exp,
        #                                 # 'instance':exp,
        #                             }
        self.form_arguments['soaksform'] = {
                                        'exp': exp,
                                        # 'instance':exp,
                                    }
        self.form_arguments['picklistform'] = {
                                        'user': user,
                                        'instance':exp,
                                    }
        # populate success_urls dictionary with urls
        exp_view_url = reverse_lazy('exp', kwargs=kwargs)
        
        self.success_urls['expform'] = exp_view_url
        self.success_urls['initform'] = exp_view_url  
        self.success_urls['platelibform'] = exp_view_url
        # self.success_urls['platesform'] = exp_view_url
        self.success_urls['soaksform'] = exp_view_url
        self.success_urls['picklistform'] = exp_view_url

        return super().dispatch(request, *args, **kwargs)
    
    def expform_form_valid(self, form):
        pk = self.kwargs.get('pk_exp', None)
        cleaned_data = form.cleaned_data
        form_name = cleaned_data.pop('action')
        exp_qs = Experiment.objects.filter(id=pk) #should a qs of one and it should exist
        exp = exp_qs.first()
        fields = [key for key in cleaned_data]
        update_instance(exp, fields, cleaned_data)
        return HttpResponseRedirect(reverse_lazy('exp', kwargs={'pk_proj': exp.project.id, 'pk_exp':exp.id}))
    
    def initform_form_valid(self, form):
        pk = self.kwargs.get('pk_exp', None)
        cleaned_data = form.cleaned_data
        form_name = cleaned_data.pop('action')
        exp_qs = Experiment.objects.filter(id=pk) #should a qs of one and it should exist
        exp = exp_qs.first()
        exp.destPlateType = PlateType.objects.get(name="Swiss MRC-3 96 well microplate") #TODO: ensure destPlateType is set for experiment
        f = cleaned_data['initDataFile']
        useS3 = False
        try:
            with transaction.atomic():
                kwargs = {}
                if useS3:
                    kwargs = {'owner':exp.owner, 'upload':f}
                else:
                    kwargs = {'owner':exp.owner, 'local_upload':f}
                initData = PrivateFileJSON(**kwargs)
                initData.save()
                exp.initData = initData
                exp.save()  
        except Exception as e:
            print(e)
            pass

        return HttpResponseRedirect(self.get_success_url(form_name))
    
    def platelibform_form_valid(self, form):
        pk = self.kwargs.get('pk_exp', None)
        cleaned_data = form.cleaned_data
        form_name = cleaned_data.pop('action')
        exp_qs = Experiment.objects.filter(id=pk) #should a qs of one and it should exist
        exp = exp_qs.first()
        lib = exp.library #TODO: ensure library is tied to experiment beforehand
        # try:
        templateSrcPlates = cleaned_data['templateSrcPlates']
        if templateSrcPlates:
            exp.importTemplateSourcePlates(templateSrcPlates)
            # plates = exp.makeSrcPlates(len(templateSrcPlates))
            # for p1, p2 in zip(plates, templateSrcPlates):
            #     p1.copyCompoundsFromOtherPlate(p2)
        else:
            f = TextIOWrapper(cleaned_data['plateLibDataFile'], self.request.encoding)
            with transaction.atomic():
                exp.createSrcPlatesFromLibFile(cleaned_data['numSrcPlates'], f)
  
        return HttpResponseRedirect(self.get_success_url(form_name))

    # def platesform_form_valid(self, form):
    #     pk = self.kwargs.get('pk_exp', None)
    #     cleaned_data = form.cleaned_data
    #     form_name = cleaned_data.pop('action')
    #     exp_qs = Experiment.objects.filter(id=pk) #should a qs of one and it should exist
    #     exp_qs.update(**cleaned_data)
    #     exp_qs.first().generateSrcDestPlates()
    #     return HttpResponseRedirect(self.get_success_url(form_name))
    
    def soaksform_form_valid(self, form):
        pk = self.kwargs.get('pk_exp', None)
        cleaned_data = form.cleaned_data
        form_name = cleaned_data.pop('action')
        exp_qs = Experiment.objects.filter(id=pk) #should a qs of one and it should exist
        exp = exp_qs.first()
        src_wells = [w for w in exp.srcWellsWithCompounds]
        soaks = [s for s in exp.usedSoaks]
        if form.data.get('match'):
            exp.matchSrcWellsToSoaks(src_wells, soaks)
        if form.data.get('interleave'):
            exp.interleaveSrcWellsToSoaks(src_wells, soaks)
        if cleaned_data['soakVolumeOverride']:
            for s in soaks:
                s.soakVolume = cleaned_data['soakVolumeOverride']
            Soak.objects.bulk_update(soaks, fields=('soakVolume',))
        if cleaned_data['soakDate']:
            exp.desired_soak_date = cleaned_data['soakDate']
            exp.save()
        return HttpResponseRedirect(self.get_success_url(form_name))
    
    def picklistform_form_valid(self, form):
        pk = self.kwargs.get('pk_exp', None)
        cleaned_data = form.cleaned_data
        form_name = cleaned_data.pop('action')
        
        exp_qs = Experiment.objects.filter(id=pk) #should a qs of one and it should exist
        exp = exp_qs.first()

        f = PrivateFileCSV(**cleaned_data)
        f.save()
        exp.picklist = f
        exp.save()
        return HttpResponseRedirect(self.get_success_url(form_name))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        invalid_form_name = context.get('invalid_form_name')
        step = 0
        if invalid_form_name:
            step = self.form_to_step_map[invalid_form_name]
        pk_proj = self.kwargs.get('pk_proj', None)
        pk = self.kwargs.get('pk_exp', None)
        request = self.request
        exp = request.user.experiments.prefetch_related('plates','soaks','library').get(id=pk)
        plates = exp.plates.all()
        soaks_table = exp.getSoaksTable(exc=[])
        RequestConfig(request, paginate={'per_page': 5}).configure(soaks_table)
        src_plates_table = exp.getSrcPlatesTable(exc=[])
        plateModalFormData = build_modal_form_data(Plate)
        src_plates_qs = plates.filter(isSource=True)
        dest_plates_qs = plates.filter(isSource=False)
        src_plates_table = ModalEditPlatesTable(
            data=src_plates_qs,
            data_target=plateModalFormData['edit']['modal_id'], 
            a_class="btn btn-primary " + plateModalFormData['edit']['url_class'], 
            form_action='a',
            view_name='plate_edit',

        )
        # dest_plates_table = DestPlatesForGUITable(
        #     data=exp.plates.filter(isSource=False), 
        #     data_target="",
        #     a_class="btn btn-primary ",
        #     form_action='a',
        #     view_name='drop_images_upload',
        #     exclude=[],
        #     )
        dest_plates_table = exp.getDestPlatesGUITable(exc=[])
        local_initData_path = ''
        s3_initData_path = ''
        if exp.initData:
            local_initData_path = str(exp.initData.local_upload)
            if local_initData_path:
                lst_path = local_initData_path.split('/')
                context['initData_local_url'] = '/media/' + local_initData_path
                context['initData_local'] = lst_path[len(lst_path) - 1]

            s3_initData_path = str(exp.initData.upload)
            if s3_initData_path:
                context['init_data_file_url'] = create_presigned_url(settings.AWS_STORAGE_BUCKET_NAME, 
                    'media/private/' + s3_initData_path, 4000)
        plateDict = dict(zip([p.id for p in plates],[p for p in plates]))
        platePairs = exp.getSoakPlatePairs()
        src_dest_plate_pairs = {}
        for pair in platePairs:
            src_dest_plate_pairs[pair] = {
                'href':reverse_lazy('soaks_csv_view', 
                    kwargs={
                        'pk_proj':pk_proj,
                        'pk_exp':pk,
                        'pk_src_plate':pair[0].id,
                        'pk_dest_plate':pair[1].id,
                    }),
                'src': pair[0],
                'dest': pair[1],

            }

        current_step =  exp.getCurrentStep
        context['dest_plates_qs'] = dest_plates_qs
        context['error_step'] = step
        context['exp'] = exp
        context['src_plates_table'] = src_plates_table
        context['dest_plates_table'] = dest_plates_table
        context['soaks_table'] = soaks_table
        context['platesValid'] = exp.platesValid
        context['current_step'] = current_step
        context['soaksValid'] = exp.soaksValid
        context['soaks_download'] = reverse('soaks_csv_view', kwargs={'pk_proj': pk_proj, 'pk_exp':exp.id})
        context['rockMakerIds'] = [p.rockMakerId for p in exp.plates.filter(rockMakerId__isnull=False)]
        context['incompleted_steps'] = [i+1 for i in range(current_step)]
        context['picklist_template_download'] = reverse('picklist_template', kwargs={'pk_exp':exp.id, 'pk_proj':pk_proj})
        context['src_dest_plate_pairs'] = src_dest_plate_pairs
        context['plateDict']= plateDict
        return context

#checks if project is the user's
def experiment_is_users(user, e):
    projects_with_exp = user.projects.filter(experiments__in=[e.id]) 
    return projects_with_exp.count() > 0 

@is_users_experiment
@login_required(login_url="/login")
def experiment(request, pk_exp):
    pk = pk_exp
    experiment = Experiment.objects.select_related(
        'owner').get(id=pk)
    # if experiment_is_users(request.user, experiment):
    soaks_table = experiment.getSoaksTable(exc=[])
    RequestConfig(request, paginate={'per_page': 5}).configure(soaks_table)
    src_plates_table = experiment.getSrcPlatesTable(exc=[])
    dest_plates_table = experiment.getDestPlatesTable(exc=[])
    
    context = {
        'show_path' : True,
        'pkUser': request.user.id,
        'experiment': experiment,
        'pkOwner': experiment.owner.id,
        'src_plates_table': src_plates_table,
        'dest_plates_table': dest_plates_table,
        'soaks_table': soaks_table,
    }
    return render(request,'experiment.html', context)
    # else:
    #     return HttpResponse("Don't have permission") # should create a request denied template later!

#views experiment soaks as table
# @is_users_experiment
# @login_required(login_url="/login")
# def soaks(request, *args, **kwargs):
#     pk = kwargs.get('pk_exp', None)
#     exp = Experiment.objects.get(id=pk)
#     # src_plate_ids = [p.id for p in exp.plates.filter(isSource=True)]
#     soaks_table=exp.getSoaksTable()
#     RequestConfig(request, paginate={'per_page': 50}).configure(soaks_table)
#     data = {
#         # we could further optimize this by just having on qs with combined annotations if needed
#         'src_soaks_qs' : exp.soaks.select_related('src__plate','dest')
#           .annotate(plate_id=F('src__plate_id'))
#           .annotate(well_row=F('src__wellRowIdx'))
#           .annotate(well_col=F('src__wellColIdx'))
#           .order_by('src__plate__plateIdxExp','src__name'),

#         'dest_soaks_qs' : exp.soaks.select_related('dest__parentWell__plate','src')
#           .annotate(plate_id=F('dest__parentWell__plate_id'))
#           .annotate(well_row=F('dest__parentWell__wellRowIdx'))
#           .annotate(well_col=F('dest__parentWell__wellColIdx'))
#           .annotate(parent_well=F('dest__parentWell_id'))
#           .order_by('dest__parentWell__plate__plateIdxExp','dest__parentWell__name','dest__idx'),

#         'soaks_table': soaks_table,
#     }
#     return render(request, 'experiment/exp_templates/soaks_table.html', data)

class PlateUpdate(UpdateView):
    model = Plate
    fields = ['isTemplate']
    template_name = 'experiment/exp_templates/plate_update.html'
    def get_success_url(self):
        return reverse('plate_edit', kwargs={'pk_plate':self.object.pk})

#views experiment plates as table
@is_users_experiment
@login_required(login_url="/login")
def exp_plates(request, pk_exp):
    pk = pk_exp
    experiment = Experiment.objects.get(id=pk)
    plates_table=experiment.getDestPlatesTable(exc=["id","xPitch","yPitch","plateHeight","plateWidth","plateLength",
        "wellDepth", "xOffsetA1","yOffsetA1","experiment","isSource","isTemplate","isCustom"])
    RequestConfig(request, paginate={'per_page': 10}).configure(plates_table)
    data = {
        'plates_table': plates_table,
    }
    return render(request, 'experiment/exp_templates/plates_table.html', data)

@login_required(login_url="/login")
@user_passes_test(user_base_tests)
def plate(request, pk_plate, pk_proj=None):

    p = get_object_or_404(Plate, pk=pk_plate)
    if p:
        wells_qs = p.wells.select_related('compound','soak').prefetch_related('subwells').order_by('name')
        wells = [w for w in wells_qs]
        subwells = []
        for w in wells:
            subwells.extend([s for s in w.subwells.all()])

        reshaped_wells = reshape(wells, (p.numRows, p.numCols))
        soaks_qs = Soak.objects.select_related('dest','src').filter(dest__in=subwells)
        soaks = [s for s in soaks_qs]
        subwellToSoakMap = dict([(s.dest.name, s) for s in soaks])
        # print(subwellToSoakMap)
        # print([s.dest.name for s in soaks])
        context = {
            'wellMatrix':reshaped_wells,
            'subwellToSoakMap': subwellToSoakMap,
            'plate':p,
        }
        return render(request, 'experiment/exp_templates/plate.html', context)
        # return HttpResponse(str(pk_plate))

@login_required(login_url="/login")
@user_passes_test(user_base_tests)
def plates(request):
    modalFormData = build_modal_form_data(Plate)
    plateFilter = PlateFilter(
        data=request.GET,
        request=request, 
        queryset=user_editable_plates(request.user),
        filter_id='proj_filter',
        form_id='proj_filter_form',
    )
    table = ModalEditPlatesTable(
        data=plateFilter.qs.order_by('-modified_date'),
        data_target=modalFormData['edit']['modal_id'], 
        a_class="btn btn-primary " + modalFormData['edit']['url_class'], 
        table_id='plate_table',
        form_id='plate_table_form',
        form_action=reverse('modify_plates'),
        view_name='plate_edit',

        )
    RequestConfig(request, paginate={'per_page': 20}).configure(table)
    
    buttons = []
    modals = [
        modalFormData['edit'],
        ]
    context = build_filter_table_context(plateFilter, table, modals, buttons)

    return render(request, 'experiment/proj_templates/projects.html', context)

@login_required(login_url="/login")
def experiments(request):
    experimentsTable = ExperimentsTable(request.user.experiments.all())
    RequestConfig(request, paginate={'per_page': 5}).configure(experimentsTable)
    data = {
        'experimentsTable': experimentsTable,
    }
    return render(request,'experiment/exp_templates/experiments.html',data)#,{'experiments':})

@is_users_experiment
@login_required(login_url="/login")
def delete_experiment(request, pk_exp):
    pk = pk_exp
    experiment = get_object_or_404(Experiment, pk=pk)
    pk_proj = experiment.project.id
    experiment.delete()
    if pk_proj:
        return redirect('proj',pk_proj=pk_proj)
    else:
        return redirect('experiments')
    
@login_required(login_url="/login")
def delete_experiments(request, pks_exp, pk_proj=None):
    pks = pks_exp
    if pk_proj:
        pks = pks.split('/')
        for pk in pks:
            if pk: #check if pk is not empty
                try:
                    exp = get_object_or_404(Experiment, pk=pk)
                    if (exp.owner == request.user):
                        exp.delete()
                except:
                    break
        return redirect('proj',pk_proj)
    else:
        pks = pks.split('/')
        for pk in pks:
            if pk: #check if pk is not empty
                try:
                    exp = get_object_or_404(Experiment, pk=pk)
                    if (exp.owner.pk == request.user.pk):
                        exp.delete()
                except:
                    break
        return redirect('experiments')

@is_users_experiment
@login_required(login_url="/login")
def delete_exp_plates(request, pk_exp):
    pk = pk_exp
    exp = get_object_or_404(Experiment, pk=pk)
    for p in exp.plates.all():
        p.delete()
    return redirect('exp',pk)

@is_user_accessible_experiment
def picklist_template_view(request,pk_exp, pk_proj=None):
    from my_utils.constants import subwell_map
    exp = get_object_or_404(Experiment, pk=pk_exp) 
    # well_map = exp.destPlateType.wellDict

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment;filename=' + str(exp.name) + '_picklist' +  '.csv'
    writer = csv.writer(response)
    for s in exp.usedSoaks:
        well_name, subwell_idx = s.dest.name.split('_')
        subwell_idx = int(subwell_idx)
        # well_props = well_map[well_name]
        # print(well_name)
        match = re.match(r"^[A-Z]\d{2}$", well_name, re.I)
        items = match.group()
        writer.writerow([exp.destPlateType, items[0], int(items[1:]), subwell_map[subwell_idx]])
    return response


# @is_users_experiment
# def soaks_csv_view(request,pk_exp ,pk_src_plate=None, pk_dest_plate=None):
#     pk = pk_exp
#     exp = get_object_or_404(Experiment, pk=pk)
#     exp.exported_time = timezone.now()
#     exp.save()
#     # dest_plate = get_object_or_404(Plate,pk_plate)
#     qs = qs = exp.soaks.select_related("dest__parentWell__plate","src__plate").prefetch_related(
#       ).order_by('id')
#     if pk_dest_plate and pk_src_plate:
#         qs = exp.soaks.select_related("dest__parentWell__plate","src__plate").prefetch_related(
#       ).filter(src__plate_id=pk_src_plate, dest__parentWell__plate_id=pk_dest_plate)
#     response = HttpResponse(content_type='text/csv')
#     response['Content-Disposition'] = 'attachment;filename=' + str(exp.name) + '_soaks' +  '.csv'
#     writer = csv.writer(response)
#     headers = ["Source Plate Name","Source Well","Destination Plate Name","Destination Well","Transfer Volume",
#                     "Destination Well X Offset","Destination Well Y Offset"] 
#     writer.writerow(headers) #headers for csv
#     rows = []
#     for s in qs:
#         s_dict = s.__dict__
#         src_well = s.src
#         dest_well = s.dest.parentWell
#         src_plate_name = "Source[" + str(src_well.plate.plateIdxExp) + "]"
#         src_well = src_well.name
#         dest_plate_name = "Destination["  +str(dest_well.plate.plateIdxExp) + "]"
#         dest_well = dest_well.name
#         transfer_vol = s.soakVolume
#         x_offset = round(s.offset_XY_um[0]*100)/100
#         y_offset = round(s.offset_XY_um[1]*100)/100
#         rows.append([src_plate_name,src_well,dest_plate_name,dest_well,transfer_vol,x_offset,y_offset])
#     for r in sorted(rows, key=lambda x: ( x[headers.index("Source Plate Name")],x[headers.index("Source Well")])):
#         writer.writerow(r)
#     return response



# ----------------- HELPER functions --------------------------
def make_instance_from_dict(instance_model_a_as_dict,model_a):
    try:
        del instance_model_a_as_dict['id']
    except KeyError:
        pass
    # instance_model_a_as_dict.pop('id') #pops id so we dont copy primary keys
    return model_a(**instance_model_a_as_dict)

def copy_instance(instance_of_model_a,instance_of_model_b):
    for field in instance_of_model_a._meta.fields:
        if field.primary_key == True:
            continue  # don't want to clone the PK
        setattr(instance_of_model_b, field.name, getattr(instance_of_model_a, field.name))
            # instance_of_model_b.save()
    return instance_of_model_b

def _get_form(request, formcls, prefix):

    data = request.POST if prefix in request.POST else None
    return formcls(data, prefix=prefix)