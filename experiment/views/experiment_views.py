from hitsDB.views_import import * #common imports for views
from ..models import Experiment, Plate, Well, SubWell, Soak, Project, PlateType
from ..tables import SoaksTable, ExperimentsTable, ModalEditPlatesTable, DestPlatesForGUITable, ModalEditExperimentsTable
from django_tables2 import RequestConfig
from ..exp_view_process import formatSoaks, ceiling_div, chunk_list, split_list, getWellIdx, getSubwellIdx
from lib.models import Library, Compound
from ..forms import CreateSrcPlatesMultiForm, ExperimentForm, PlatesSetupMultiForm, \
    ExpAsMultiForm, SoaksSetupMultiForm, ExpInitDataMultiForm, PicklistMultiForm, PlateForm, RemovePlatesDropImagesForm
from forms_custom.multiforms import MultiFormsView
from django.db.models import Count, F, Value
from ..decorators import is_users_experiment, is_user_accessible_experiment, is_user_editable_experiment, \
    is_users_project, is_user_accessible_project, is_user_editable_project
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
from ..querysets import user_editable_plates, user_editable_experiments
from ..filters import PlateFilter, ExperimentFilter
from my_utils.utility_functions import reshape
from collections import OrderedDict
from ..utils.experiment_utils import revertToStep

@method_decorator([login_required(login_url="/login"), is_user_accessible_experiment], name='dispatch')
class MultiFormsExpView(MultiFormsView):
    template_name = "experiment/exp_templates/exp_main.html"
    form_classes = OrderedDict([
        ('expform', ExpAsMultiForm), #step 0
        ('initform', ExpInitDataMultiForm), #step 1
        ('platelibform', CreateSrcPlatesMultiForm), #step 2
        ('removedropimagesform', RemovePlatesDropImagesForm), #step 3
        # ('platesform', PlatesSetupMultiForm),
        ('soaksform', SoaksSetupMultiForm), #step 4
        ('picklistform', PicklistMultiForm) #step 5

    ])
    form_to_step_map = dict([(k,i) for i,k in enumerate(form_classes.keys())])
    # form_to_step_map['soaksform'] = 4
    # form_to_step_map['picklistform'] = 5
 
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
        self.exp = exp
        self.form_arguments['expform'] = {
                                        'user':user,
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
        self.success_urls['removedropimagesform'] = exp_view_url
        self.success_urls['soaksform'] = exp_view_url
        self.success_urls['picklistform'] = exp_view_url

        return super().dispatch(request, *args, **kwargs)

    def revertExp(self, exp, form_name):
        step = self.form_to_step_map[form_name]
        revertToStep(exp, step)

    def expform_form_valid(self, form):
        # pk = self.kwargs.get('pk_exp', None)
        cleaned_data = form.cleaned_data
        form_name = cleaned_data.pop('action')
        fields = [key for key in cleaned_data]
        exp = self.exp
        update_instance(exp, cleaned_data, fields=fields)
        messages.success(self.request, "Experiment " + exp.name + " updated.")
        return HttpResponseRedirect(reverse_lazy('exp', kwargs={'pk_proj': exp.project.id, 'pk_exp':exp.id}))
    
    def initform_form_valid(self, form):
        cleaned_data = form.cleaned_data
        form_name = cleaned_data.pop('action')
        exp = self.exp
        self.revertExp(exp, form_name)
        exp.destPlateType = PlateType.objects.get(name="Swiss MRC-3 96 well microplate") #TODO: ensure destPlateType is set for experiment
        f = cleaned_data['initDataFile']
        try:
            with transaction.atomic():
                kwargs = {'owner':exp.owner, 'upload':f, 'local_upload': f}
                # if settings.USE_LOCAL_STORAGE:
                #     kwargs.update({'local_upload':f})
                initData = PrivateFileJSON(**kwargs)
                initData.save()
                exp.initData = initData
                exp.save()  
            dest_plates_ids = [str(p.rockMakerId) for p in exp.plates.filter(isSource=False)]
            messages.success(self.request, "Experiment " + exp.name + " initialized with plates: " +
            ", ".join(dest_plates_ids))
        except Exception as e:
            print(e)

        return HttpResponseRedirect(self.get_success_url(form_name))
    
    def platelibform_form_valid(self, form):
        cleaned_data = form.cleaned_data
        form_name = cleaned_data.pop('action')
        exp = self.exp
        self.revertExp(exp, form_name)
        # try:
        templateSrcPlates = cleaned_data['templateSrcPlates']
        with transaction.atomic():
            if templateSrcPlates:
                exp.importTemplateSourcePlates(templateSrcPlates)
            
            else:
                f = TextIOWrapper(cleaned_data['plateLibDataFile'], self.request.encoding)
                exp.createSrcPlatesFromLibFile(cleaned_data['numSrcPlates'], f)
        src_plates = exp.plates.filter(isSource=True)
        if src_plates:
            for p in src_plates:
                p.owner = self.request.user
                p.save()
            messages.success(self.request, "Source plates " + ", ".join([str(p.name) for p in src_plates]) 
                + "created.")
        return HttpResponseRedirect(self.get_success_url(form_name))

    def removedropimagesform_form_valid(self, form):
        cleaned_data = form.cleaned_data
        form_name = cleaned_data.pop('action')
        exp = self.exp
        pks = self.request.POST.getlist('checked')
        with transaction.atomic():
            plates = [get_object_or_404(Plate, pk=p_pk) for p_pk in pks]
            for p in plates:
                p.removeDropImages()
            messages.success(self.request, "Removed drop images from plates: " + ", ".join([str(p) for p in plates]))
        self.revertExp(exp, form_name)
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
        cleaned_data = form.cleaned_data
        form_name = cleaned_data.pop('action')
        exp = self.exp
        self.revertExp(exp, form_name)
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
        # if cleaned_data['soakDate']:
        #     exp.desired_soak_date = cleaned_data['soakDate']
        #     exp.save()
        return HttpResponseRedirect(self.get_success_url(form_name))
    
    def picklistform_form_valid(self, form):
        pk = self.kwargs.get('pk_exp', None)
        cleaned_data = form.cleaned_data
        form_name = cleaned_data.pop('action')
        
        exp_qs = Experiment.objects.filter(id=pk) #should a qs of one and it should exist
        exp = exp_qs.first()
        self.revertExp(exp, form_name)
        f = cleaned_data['upload']
        kwargs = {'owner':self.request.user, 'upload': f, 'filename': f.name, 'local_upload': f}
        # if settings.USE_LOCAL_STORAGE:
        #     kwargs.update({'local_upload': f})
        picklist = PrivateFileCSV(**kwargs)
        picklist.save()
        exp.picklist = picklist
        exp.save()
        exp.processPicklist()
        return HttpResponseRedirect(self.get_success_url(form_name))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        invalid_form_name = context.get('invalid_form_name')
        error_step = 0
        if invalid_form_name:
            error_step = self.form_to_step_map[invalid_form_name]
        pk_proj = self.kwargs.get('pk_proj', None)
        pk = self.kwargs.get('pk_exp', None)
        request = self.request
        exp = request.user.experiments.prefetch_related('plates','soaks','library').get(id=pk)
        plates = exp.plates.all()
        soaks_table = exp.getSoaksTable(exc=[])
        RequestConfig(request, paginate={'per_page': 10}).configure(soaks_table)
        src_plates_table = exp.getSrcPlatesTable(exc=[])
        plateModalFormData = build_modal_form_data(Plate)
        src_plates_qs = plates.filter(isSource=True)
        dest_plates_qs = plates.filter(isSource=False)
        # src_plates_table = ModalEditPlatesTable(
        #     data=src_plates_qs,
        #     data_target=plateModalFormData['edit']['modal_id'], 
        #     a_class="btn btn-primary " + plateModalFormData['edit']['url_class'], 
        #     form_action='a',
        #     view_name='plate_edit',
        # )
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
                lst = local_initData_path.split('/')
                context['initData_local_url'] = '/media/' + local_initData_path
                context['initData_local'] = lst[len(lst) - 1]

            s3_initData_path = str(exp.initData.upload)
            if s3_initData_path:
                lst = s3_initData_path.split('/')
                context['initData_s3_url'] = create_presigned_url(settings.AWS_STORAGE_BUCKET_NAME, 
                    'media/private/' + s3_initData_path, 4000)
                context['initData_s3'] = lst[len(lst) - 1]
        local_picklist_path = ''
        s3_picklist_path = ''
        if exp.picklist:
            local_picklist_path = str(exp.picklist.local_upload)
            if local_picklist_path:
                lst = local_picklist_path.split('/')
                context['picklist_local_url'] = '/media/' + local_initData_path
                context['picklist_local'] = lst[len(lst) - 1]

            s3_picklist_path = str(exp.picklist.upload)
            if s3_picklist_path:
                context['picklist_s3_url'] = create_presigned_url(settings.AWS_STORAGE_BUCKET_NAME, 
                    'media/private/' + s3_picklist_path, 4000)
                lst = s3_picklist_path.split('/')
                context['picklist_s3'] = lst[len(lst) - 1]

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
        context['error_step'] = error_step
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

@is_user_editable_experiment
@login_required(login_url="/login")
@user_passes_test(user_base_tests)
def experiment(request, pk_exp):
    pk = pk_exp
    experiment = Experiment.objects.select_related(
        'owner').get(id=pk)
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
@is_user_editable_experiment
@login_required(login_url="/login")
@user_passes_test(user_base_tests)
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
from ..forms import WellPriorityForm
from my_utils.my_views import AjaxUpdateView
class WellUpdateView(AjaxUpdateView):
    model = Well
    form_class = WellPriorityForm
    success_url='/'

@login_required(login_url="/login")
@user_passes_test(user_base_tests)
def plate(request, pk_plate, pk_proj=None):
    
    from my_utils.constants import idx_to_letters_map, letters_to_idx_map
    p = get_object_or_404(Plate, pk=pk_plate) 
    if p:
        plateForm = PlateForm(instance=p)
        ### Handle PlateForm()
        if request.method=="POST":
            if request.is_ajax():
                pass
            else:
                plateForm = PlateForm(request.POST, instance=p)
                if plateForm.is_valid():
                    update_instance(p, plateForm.cleaned_data, plateForm.cleaned_data.keys())
                    messages.success(request, 'Plate ' + p.name + ' updated.')
                    return redirect('plate', pk_plate=p.pk)
        else:
            wells_qs = p.wells.select_related('compound','soak').prefetch_related('subwells').order_by('name')
            wells = [w for w in wells_qs]
            well_form_map = {}
            subwells = []
            for w in wells:
                subwells.extend([s for s in w.subwells.all()])
                well_form_map[w.id] = WellPriorityForm(instance=w)
            reshaped_wells = reshape(wells, (p.numRows, p.numCols))
            soaks_qs = Soak.objects.select_related('dest','src').filter(dest__in=subwells)
            soaks = [s for s in soaks_qs]
            subwellToSoakMap = dict([(s.dest.name, s) for s in soaks])
            context = {}
            from lib.tables import CompoundsTable, ModalEditCompoundsTable
            from lib.filters import CompoundFilter
            compoundsFilter = CompoundFilter(
                request.GET, queryset=p.compounds.all(),
                filter_id='compounds_filter', form_id='compounds_filter_form')
            compoundsTable = ModalEditCompoundsTable(
                data=compoundsFilter.qs,
                table_id='compounds_table',)
            RequestConfig(request, paginate={'per_page': 20}).configure(compoundsTable)
            context = build_filter_table_context(compoundsFilter, compoundsTable, [], [])
            context.update({
                'wellMatrix':reshaped_wells,
                'subwellToSoakMap': subwellToSoakMap,
                'plate':p,
                'idx_to_letters_map':idx_to_letters_map,
                'canEdit':True, 
                'well_form_map':well_form_map,
                'plateForm':plateForm, 
            })
        return render(request, 'experiment/exp_templates/plate.html', context)

@login_required(login_url="/login")
@user_passes_test(user_base_tests)
def plates(request, pk_exp=None):
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
@user_passes_test(user_base_tests)
def remove_drop_images_from_plates(request, pks, pk_exp):
    
    if request.method == "POST":
        for p in [get_object_or_404(Plate, pk=p_pk) for p_pk in pks]:
            if p:
                p.removeDropImages()
        return redirect('exp', pk_exp)



@is_user_accessible_project
@login_required(login_url="/login")
@user_passes_test(user_base_tests)
def proj_exps(request, pk_proj):
    proj = Project.objects.get(id=pk_proj)
    exps = proj.experiments.order_by('modified_date')
    return experiments(request, qs=exps)

@login_required(login_url="/login")
def experiments(request, qs=None):
    exp_qs = user_editable_experiments(request.user)
    if qs:
        exp_qs = qs
    modalFormData = build_modal_form_data(Experiment)
    expFilter = ExperimentFilter(
        data=request.GET,
        request=request, 
        queryset=exp_qs,
        filter_id='exp_filter',
        form_id='exp_filter_form',
    )
    table = ModalEditExperimentsTable(
        data=expFilter.qs.order_by('-modified_date'),
        data_target=modalFormData['edit']['modal_id'], 
        a_class="btn btn-primary " + modalFormData['edit']['url_class'], 
        table_id='exp_table',
        form_id='exp_table_form',
        form_action=reverse('modify_exps'),
        view_name='exp_edit',
        )   
    RequestConfig(request, paginate={'per_page': 5}).configure(table)
    buttons = [
        {'id': 'delete_selected', 'text': 'Delete Selected','class': 'btn-danger btn-confirm'},
        {'id': 'new_exp_btn','text': 'New Experiment','class': 'btn-primary ' + 'exp_new_url', 
            'href':reverse('exp_new')},
    ]
    modals = [
        modalFormData['new'],
        modalFormData['edit'],
        ]
    context = build_filter_table_context(expFilter, table, modals, buttons)

    return render(request,'experiment/exp_templates/experiments.html', context)#,{'experiments':})

@is_user_editable_experiment
@user_passes_test(user_base_tests)
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
@user_passes_test(user_base_tests)
def delete_experiments(request, pks, pk_proj=None):
    pks = pks.split('_')
    for pk in pks:
            if pk: #check if pk is not empty
                try:
                    exp = get_object_or_404(Experiment, pk=pk)
                    if (exp.owner.pk == request.user.pk):
                        exp.delete()
                        messages.success(request," ".join([type(exp).__name__, str(exp)]) + " deleted.")
                except:
                    break
    
    if pk_proj:
        return redirect('proj',pk_proj)
    else:
        return redirect('experiments')

@login_required(login_url="/login")
@user_passes_test(user_base_tests)
def remove_exps_from_proj(request, pks, pk_proj):
    pks = pks.split('_')
    pks = list(map(lambda s: Experiment.objects.get(id=s), pks))
    if pk_proj:
        proj = Project.objects.get(id=pk_proj)
        proj.experiments.remove(*pks)
    return redirect('experiments')


@is_user_editable_experiment
@login_required(login_url="/login")
@user_passes_test(user_base_tests)
def delete_exp_plates(request, pk_exp):
    pk = pk_exp
    exp = get_object_or_404(Experiment, pk=pk)
    for p in exp.plates.all():
        p.delete()
    return redirect('exp',pk)

@is_user_accessible_experiment
@user_passes_test(user_base_tests)
@login_required(login_url="/login")
def picklist_template_view(request,pk_exp, pk_proj=None):
    from my_utils.constants import subwell_map
    exp = get_object_or_404(Experiment, pk=pk_exp) 
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment;filename=' + str(exp.name) + '_picklist' +  '.csv'
    writer = csv.writer(response)
    for s in exp.usedSoaks:
        well_name, subwell_idx = s.dest.name.split('_')
        subwell_idx = int(subwell_idx)
        match = re.match(r"^[A-Z]\d{2}$", well_name, re.I)
        items = match.group()
        writer.writerow([exp.destPlateType, items[0], int(items[1:]), subwell_map[subwell_idx]])
    return response



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