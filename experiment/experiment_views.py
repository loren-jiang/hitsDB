from hitsDB.views_import import * #common imports for views
from .models import Experiment, Plate, Well, SubWell, Soak, Project, PlateType
from .tables import SoaksTable, ExperimentsTable
from django_tables2 import RequestConfig
import csv
from .exp_view_process import formatSoaks, ceiling_div, chunk_list, split_list, getWellIdx, getSubwellIdx
from import_ZINC.models import Library, Compound
from .forms import ExperimentModelForm, PlatesSetupMultiForm, ExpAsMultiForm, SoaksSetupMultiForm, ExpInitMultiForm, ExpInitDataMultiForm
from forms_custom.multiforms import MultiFormsView
from django.db.models import Count, F, Value
from .decorators import is_users_experiment 
from django.conf import settings
from s3.s3utils import myS3Client, myS3Resource, create_presigned_url
from s3.models import PrivateFileJSON

class MultipleFormsDemoView(MultiFormsView, LoginRequiredMixin):
    template_name = "experiment/exp_templates/exp_main.html"
    form_classes = { 
                    'expform': ExpAsMultiForm,
                    'initform': ExpInitDataMultiForm,
                    'platesform': PlatesSetupMultiForm,
                    'soaksform' : SoaksSetupMultiForm,
                    }
    form_arguments = {}
    success_urls = {}

    # overload to process request to properly instantiate multiforms with form arguments and success urls
    def dispatch(self, request, *args, **kwargs):
        # parse the request here ie.
        # populate form_arguments 
        user = request.user
        pk = kwargs.get('pk_exp', None)
        # ensure experiment is only accessible by owner
        if request.user != Experiment.objects.get(id=pk).owner:
            raise PermissionDenied
        invalid_form = kwargs.get('invalid_form', None)
        if invalid_form:
            self.invalid_form = invalid_form

        exp = user.experiments.get(id=pk)
        
        self.form_arguments['expform'] = {
                                        'user':user,
                                        'lib_qs':user.libraries.filter(),
                                        'exp': exp
                                    }
        self.form_arguments['initform'] = {
                                        'exp': exp, 
        }
        self.form_arguments['platesform'] = {
                                        'exp': exp
                                    }
        self.form_arguments['soaksform'] = {
                                        'exp': exp
                                    }
        # populate success_urls dictionary with urls
        exp_view_url = reverse_lazy('exp', kwargs={'pk_exp':pk})
        
        self.success_urls['expform'] = exp_view_url
        self.success_urls['initform'] = exp_view_url  
        self.success_urls['platesform'] = exp_view_url
        self.success_urls['soaksform'] = exp_view_url
        # call super
        return super(MultipleFormsDemoView, self).dispatch(request, *args, **kwargs)

    def expform_form_valid(self, form):
        pk = self.kwargs.get('pk_exp', None)
        cleaned_data = form.cleaned_data
        form_name = cleaned_data.pop('action')
        exp_qs = Experiment.objects.filter(id=pk) #should a qs of one and it should exist
        exp = exp_qs[0]
        fields = [key for key in cleaned_data]
        for field in fields:
            new_field_data = cleaned_data[field]
            old_field_data = getattr(exp, field)
            if (new_field_data != old_field_data):
                setattr(exp, field, new_field_data)
        exp.save(update_fields=fields)
        return HttpResponseRedirect(self.get_success_url(form_name))
    
    def initform_form_valid(self, form):
        pk = self.kwargs.get('pk_exp', None)
        cleaned_data = form.cleaned_data
        form_name = cleaned_data.pop('action')
        exp_qs = Experiment.objects.filter(id=pk) #should a qs of one and it should exist
        exp = exp_qs[0]
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
    
    def platesform_form_valid(self, form):
        pk = self.kwargs.get('pk_exp', None)
        cleaned_data = form.cleaned_data
        form_name = cleaned_data.pop('action')
        exp_qs = Experiment.objects.filter(id=pk) #should a qs of one and it should exist
        exp_qs.update(**cleaned_data)
        exp_qs[0].generateSrcDestPlates()
        return HttpResponseRedirect(self.get_success_url(form_name))
    
    def soaksform_form_valid(self, form):
        pk = self.kwargs.get('pk_exp', None)
        cleaned_data = form.cleaned_data
        form_name = cleaned_data.pop('action')
        exp_qs = Experiment.objects.filter(id=pk) #should a qs of one and it should exist
        # exp_qs.update(**cleaned_data)
        exp_qs[0].generateSoaks(cleaned_data['transferVol'],cleaned_data['soakOffsetX'],cleaned_data['soakOffsetY'] ) 
        return HttpResponseRedirect(self.get_success_url(form_name))
    
    def get_context_data(self, **kwargs):
        context = super(MultiFormsView, self).get_context_data(**kwargs)

        pk = self.kwargs.get('pk_exp', None)
        request = self.request
        exp = request.user.experiments.prefetch_related('plates','soaks','library').get(id=pk)
        soaks_table = exp.getSoaksTable(exc=[])
        RequestConfig(request, paginate={'per_page': 5}).configure(soaks_table)
        src_plates_table = exp.getSrcPlatesTable(exc=[])
        dest_plates_table = exp.getDestPlatesGUITable(exc=[])
        local_initData_path = ''
        s3_initData_path = ''
        if exp.initData:
            local_initData_path = str(exp.initData.local_upload)
            context['initData_local_url'] = '/media/' + local_initData_path

            s3_initData_path = str(exp.initData.upload)
            context['init_data_file_url'] = create_presigned_url(settings.AWS_STORAGE_BUCKET_NAME, 
                'media/private/' + s3_initData_path, 4000)
        context['exp'] = exp
        context['src_plates_table'] = src_plates_table
        context['dest_plates_table'] = dest_plates_table
        context['soaks_table'] = soaks_table
        context['plates_valid'] = exp.plates_valid
        context['current_step'] = exp.getCurrentStep
        context['soaks_valid'] = exp.soaks_valid
        
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
    
    # formattedSoaks = experiment.formattedSoaks(soaks_qs) #played around with caching
    context = {
        'show_path' : True,
        'pkUser': request.user.id,
        'experiment': experiment,
        'pkOwner': experiment.owner.id,
        'src_plates_table': src_plates_table,
        'dest_plates_table': dest_plates_table,
        # 'plates' : formattedSoaks, #rendering the plate grids takes too long and isn't useful; maybe we should just list plates?
        'soaks_table': soaks_table,
    }
    return render(request,'experiment.html', context)
    # else:
    #     return HttpResponse("Don't have permission") # should create a request denied template later!

#views experiment soaks as table
@is_users_experiment
@login_required(login_url="/login")
def soaks(request, pk_exp):
    pk = pk_exp
    exp = Experiment.objects.get(id=pk)
    # src_plate_ids = [p.id for p in exp.plates.filter(isSource=True)]
    soaks_table=exp.getSoaksTable()
    RequestConfig(request, paginate={'per_page': 50}).configure(soaks_table)
    data = {
        # we could further optimize this by just having on qs with combined annotations if needed
        'src_soaks_qs' : exp.soaks.select_related('src__plate','dest')
          .annotate(plate_id=F('src__plate_id'))
          .annotate(well_row=F('src__wellRowIdx'))
          .annotate(well_col=F('src__wellColIdx'))
          .order_by('src__plate_id','id'),

        'dest_soaks_qs' : exp.soaks.select_related('dest__parentWell__plate','src')
          .annotate(plate_id=F('dest__parentWell__plate_id'))
          .annotate(well_row=F('dest__parentWell__wellRowIdx'))
          .annotate(well_col=F('dest__parentWell__wellColIdx'))
          .annotate(parent_well=F('dest__parentWell_id'))
          .order_by('dest__parentWell__plate_id','well_row','id'),

        'soaks_table': soaks_table,
    }
    return render(request, 'experiment/exp_templates/soaks_table.html', data)

#views experiment plates as table
@is_users_experiment
@login_required(login_url="/login")
def plates(request, pk_exp):
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

@is_users_experiment
def soaks_csv_view(request,pk_exp ,pk_src_plate=None, pk_dest_plate=None):
    pk = pk_exp
    exp = get_object_or_404(Experiment, pk=pk)
    # dest_plate = get_object_or_404(Plate,pk_plate)
    qs = qs = exp.soaks.select_related("dest__parentWell__plate","src__plate").prefetch_related(
      ).order_by('id')
    if pk_dest_plate and pk_src_plate:
        qs = exp.soaks.select_related("dest__parentWell__plate","src__plate").prefetch_related(
      ).filter(src__plate_id=pk_src_plate, dest__parentWell__plate_id=pk_dest_plate)
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment;filename=exp_' + str(exp.id) + '_soaks' +  '.csv'
    writer = csv.writer(response)
    writer.writerow(["Source Plate Name","Source Well","Destination Plate Name","Destination Well","Transfer Volume",
                    "Destination Well X Offset","Destination Well Y Offset"]) #headers for csv
    for s in qs:
        s_dict = s.__dict__
        src_well = s.src
        dest_well = s.dest.parentWell
        src_plate_name = "Source[" + str(src_well.plate.plateIdxExp) + "]"
        src_well = src_well.name
        dest_plate_name = "Destination["  +str(dest_well.plate.plateIdxExp) + "]"
        dest_well = dest_well.name
        transfer_vol = s.transferVol
        x_offset = s.soakOffsetX
        y_offset = s.soakOffsetY
        writer.writerow([src_plate_name,src_well,dest_plate_name,dest_well,transfer_vol,x_offset,y_offset])
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