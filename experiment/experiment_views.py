from .views_import import * #common imports for views
from .models import Experiment, Plate, Well, SubWell, Soak, Project
from .tables import SoaksTable, ExperimentsTable
from django_tables2 import RequestConfig
import csv
from .exp_view_process import formatSoaks, ceiling_div, chunk_list, split_list, getWellIdx, getSubwellIdx
from import_ZINC.models import Library, Compound
from .forms import ExperimentModelForm, PlatesSetupMultiForm, ExperimentAsMultiForm, SoaksSetupMultiForm
from forms_custom.multiforms import MultiFormsView
from django.db.models import Count, F, Value
from .decorators import is_users_experiment 

class MultipleFormsDemoView(MultiFormsView):
    template_name = "experiment/exp_templates/cbv_multiple_forms.html"
    form_classes = {
                    'expform': ExperimentAsMultiForm,
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
        self.form_arguments['platesform'] = {
                                        'exp': exp
                                    }
        self.form_arguments['soaksform'] = {
                                        'exp': exp
                                    }
        # populate success_urls dictionary with urls
        exp_view_url = reverse_lazy('exp', kwargs={'pk_exp':pk})
        self.success_urls['expform'] = exp_view_url
        self.success_urls['platesform'] = exp_view_url
        self.success_urls['soaksform'] = exp_view_url
        # call super
        return super(MultipleFormsDemoView, self).dispatch(request, *args, **kwargs)

    # def get_soaksform_initial(self):
    #     pk = self.kwargs.get('pk', None)
    #     exp = Experiment.objects.get(id=pk)
    #     transferVol = 25
    #     soakOffsetX = 0
    #     soakOffsetY = 0
    #     if exp.soaks.count():
    #         s = exp.soaks.all()[0]
    #         transferVol = s.transferVol
    #         soakOffsetX = s.soakOffsetX
    #         soakOffsetY = s.soakOffsetY
    #     data = {
    #         'action': 'soaksform',
    #         'transferVol': transferVol,
    #         'soakOffsetX': soakOffsetX, 
    #         'soakOffsetY': soakOffsetX,
    #     }
    #     return data
            
    def expform_form_valid(self, form):
        pk = self.kwargs.get('pk_exp', None)
        cleaned_data = form.cleaned_data
        form_name = cleaned_data.pop('action')
        self.success_urls[form_name] = reverse_lazy('exp', kwargs={'pk_exp':pk})
        exp_qs = Experiment.objects.filter(id=pk) #should a qs of one and it should exist
        exp = exp_qs[0]
        fields = [key for key in cleaned_data]
        for field in fields:
            setattr(exp, field, cleaned_data[field])
        exp.save(update_fields=fields)
        # exp_qs.update(**cleaned_data)
        return HttpResponseRedirect(self.get_success_url(form_name))
    
    def platesform_form_valid(self, form):
        pk = self.kwargs.get('pk_exp', None)
        cleaned_data = form.cleaned_data
        form_name = cleaned_data.pop('action')
        self.success_urls[form_name] = reverse_lazy('exp', kwargs={'pk_exp':pk})
        exp_qs = Experiment.objects.filter(id=pk) #should a qs of one and it should exist
        exp_qs.update(**cleaned_data)
        exp_qs[0].generateSrcDestPlates()
        return HttpResponseRedirect(self.get_success_url(form_name))
    
    def soaksform_form_valid(self, form):
        pk = self.kwargs.get('pk_exp', None)
        cleaned_data = form.cleaned_data
        form_name = cleaned_data.pop('action')
        self.success_urls[form_name] = reverse_lazy('exp', kwargs={'pk_exp':pk})
        exp_qs = Experiment.objects.filter(id=pk) #should a qs of one and it should exist
        # exp_qs.update(**cleaned_data)
        exp_qs[0].generateSoaks(cleaned_data['transferVol'],cleaned_data['soakOffsetX'],cleaned_data['soakOffsetY'] ) 
        return HttpResponseRedirect(self.get_success_url(form_name))
    
    def get_context_data(self, **kwargs):
        pk = self.kwargs.get('pk_exp', None)
        request = self.request
        exp = request.user.experiments.prefetch_related('plates','soaks','library').get(id=pk)
        soaks_table = exp.getSoaksTable(exc=[])
        RequestConfig(request, paginate={'per_page': 5}).configure(soaks_table)
        src_plates_table = exp.getSrcPlatesTable(exc=[])
        dest_plates_table = exp.getDestPlatesTable(exc=[])
        context = super(MultiFormsView, self).get_context_data(**kwargs)
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
    if experiment_is_users(request.user, experiment):
        soaks_table = experiment.getSoaksTable(exc=[])
        RequestConfig(request, paginate={'per_page': 5}).configure(soaks_table)
        src_plates_table = experiment.getSrcPlatesTable(exc=[])
        dest_plates_table = experiment.getDestPlatesTable(exc=[])
        
        # formattedSoaks = experiment.formattedSoaks(soaks_qs) #played around with caching
        data = {
            'show_path' : True,
            'pkUser': request.user.id,
            'experiment': experiment,
            'pkOwner': experiment.owner.id,
            'src_plates_table': src_plates_table,
            'dest_plates_table': dest_plates_table,
            # 'plates' : formattedSoaks, #rendering the plate grids takes too long and isn't useful; maybe we should just list plates?
            'soaks_table': soaks_table,
        }
        return render(request,'experiment.html', data)
    else:
        return HttpResponse("Don't have permission") # should create a request denied template later!

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
    return render(request,'experiments.html',data)#,{'experiments':})

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

# This seems like it should be rewritten -- 'sub' models should ideally be created on post_save signal
class NewExp(TemplateView):
    template_name = 'new_experiment.html'

    def get(self, request, *args, **kwargs):
        lstLibraries = []
        lstLibCompounds = []
        userGroups = request.user.groups.all()
        accessibleLibraries = Library.objects.filter(groups__in=userGroups)
        libs_dict = {}
        for lib in accessibleLibraries:
            libs_dict[lib.name] = serialize('json',lib.compounds.order_by('id'),
                fields=('nameInternal','smiles','molWeight'),cls=DjangoJSONEncoder)
        return self.render_to_response({
            'aform': NewExperimentForm(prefix='aform_pre'),
            'bform': PlateSetupForm(prefix='bform_pre'),
            'libs_dict': libs_dict,
                },)

    def post(self, request, *args, **kwargs):
        pk_proj = kwargs['pk_proj']
        aform = _get_form(request, NewExperimentForm, 'aform_pre')
        bform = _get_form(request, PlateSetupForm, 'bform_pre')
        go_to_div = False
        if aform.is_bound and aform.is_valid():
            form_data = aform.cleaned_data
            exp = Experiment()
            # exp = aform.save(commit=False)
            exp.name = form_data['name']
            exp.description = form_data['description']
            exp.protein = form_data['protein']
            exp.library = form_data['library']
            exp.owner = request.user
            if pk_proj:
                exp.project = get_object_or_404(Project,pk=pk_proj)
            exp.save()
            # go to next step in new_experiment.html
            go_to_div = "list-plates"

        elif bform.is_bound and bform.is_valid():
            with transaction.atomic(): #wont commit until block is successfully executed. 
                # Process bform and render response
                form_data = bform.cleaned_data
                crystal_locations = [int(idx) for idx in form_data['crystal_locations']]
                screen = form_data['dest_plate_screen']
                src_plate = form_data['source_plate']
                src_plate_id = src_plate.id
                # dest_plate = form_data['dest_plate']
                num_src_wells = src_plate.numCols * src_plate.numRows
                exp = form_data['experiment']

                ##--------------------
                
                exp_compounds = exp.library.compounds.order_by('id')
                num_compounds = exp_compounds.count()
                num_src_plates = ceiling_div(num_compounds,num_src_wells)
                # list_src_plates = [Plate() for k in range(num_src_plates)]
                # list_src_wells = [Well() for k in range(num_compounds)]
                list_src_plates = [None for k in range(num_src_plates)]
                list_src_wells = [None for k in range(num_compounds)]
                # list_src_wells = [None] * num_compounds

                for i in range(num_src_plates):
                    list_src_plates[i] = make_instance_from_dict(model_to_dict(src_plate),
                        Plate)
                    copy_plate = list_src_plates[i]
                    copy_plate.experiment_id = exp.pk
                    copy_plate.isTemplate = False #dont want to pollute template plates
                    copy_plate.plateIdxExp = i+1

                Plate.objects.bulk_create(list_src_plates) #creates pks
                wells = src_plate.wells.values().order_by('id')
                well_idx = 0
                for p in list_src_plates:
                    #make new copies of wells as
                    new_wells = [None for k in range(num_src_wells)]
                    j = 0
                    for w in wells:
                        new_wells[j] = make_instance_from_dict(w, Well)
                        copy_well = new_wells[j]
                        # copy_well = copy_instance(wells[j], new_wells[j])
                        copy_well.plate_id = p.pk #relates new well with new plate
                        j += 1
                        try:
                            list_src_wells[well_idx] = copy_well
                            well_idx += 1
                        except: #breaks out of loop if index out of range exception
                            break

                Well.objects.bulk_create(list_src_wells)

                #------- DEST PLATES ----------
                dest_plate = form_data['dest_plate']
                dest_plate_id = dest_plate.id
                num_dest_wells = dest_plate.numCols * dest_plate.numRows
                num_dest_plates = ceiling_div(num_compounds,num_dest_wells * len(crystal_locations)) #ceiling division, max num of plates, we can delete empty ones later
                list_dest_subwells = [None] * num_compounds
                list_dest_wells = [None]*num_dest_plates*num_dest_wells
                list_dest_plates = [None] * num_dest_plates


                for j in range(num_dest_plates):
                    list_dest_plates[j] = make_instance_from_dict(model_to_dict(dest_plate),
                        Plate)
                    copy_plate = list_dest_plates[j]
                    copy_plate.experiment_id = exp.pk
                    copy_plate.isTemplate = False #dont want to pollute template plates
                    copy_plate.plateIdxExp = j+1

                Plate.objects.bulk_create(list_dest_plates)

                wells = dest_plate.wells.values().order_by('id')
                well_idx = 0
                for i in range(num_dest_plates):
                    #make new copies of wells as
                    copy_plate = list_dest_plates[i]
                    new_wells = [None for k in range(num_dest_wells)]
                    j = 0
                    for w in wells:
                        new_wells[j] = make_instance_from_dict(w, Well)
                        copy_well = new_wells[j]
                        # copy_well = copy_instance(wells[j], new_wells[j])
                        copy_well.plate_id = copy_plate.pk #relates new well with new plate
                        j += 1
                        try:
                            list_dest_wells[well_idx] = copy_well
                            well_idx += 1
                        except: #breaks out of loop if index out of range exception
                            break

                Well.objects.bulk_create(list_dest_wells)

                # template dest_plate subwells
                subwells = dest_plate.wells.first().subwells.order_by('idx').values()
                num_subwells = subwells.count()
                subwell_idx = 0

                for w in list_dest_wells:
                    new_subwells = [None]*num_subwells
                    k = 0
                    for s in subwells:
                        new_subwells[k] = make_instance_from_dict(s,SubWell)
                        copy_subwell = new_subwells[k]
                        copy_subwell.parentWell_id = w.pk
                        k += 1
                        try:
                            if s['idx'] in crystal_locations:

                                list_dest_subwells[subwell_idx] = copy_subwell
                                subwell_idx += 1
                        except:
                            break

                SubWell.objects.bulk_create(list_dest_subwells)
                # src_wells_qs = Well.objects.filter(plate__experiment_id=exp.id
                #     ).filter(plate__isSource=True).order_by('id').prefetch_related('compounds')
                # dest_subwells_qs = SubWell.objects.filter(parentWell__plate__experiment_id=exp.id
                #     ).filter(parentWell__plate__isSource=False).order_by('id').prefetch_related('compounds')

                # zipped_lst= list(zip(exp_compounds, src_wells_qs,dest_subwells_qs))
                ct = 0
                list_soaks = [None]*num_compounds
                for compound in exp_compounds:
                # for compound, src_well, dest_subwell in zipped_lst:
                    src_well = list_src_wells[ct]
                    src_well.compounds.add(compound)
                    # src_well_plate_idx = src_well.plate.plateIdxExp

                    dest_subwell = list_dest_subwells[ct]

                    dest_subwell.compounds.add(compound)
                    dest_subwell.hasCrystal = True
                    soak = Soak(experiment=exp,src=src_well,dest=dest_subwell,
                            transferCompound=compound)
                    # soak.save()
                    list_soaks[ct] = soak
                    ct += 1
                Soak.objects.bulk_create(list_soaks)
                go_to_div = "list-crystals"

        # elif cform.is_bound and cform.is_valid():
        #     form_data = cform.cleaned_data

        data = {'aform': aform, 'bform': bform, 'go_to_div': go_to_div,}
        return self.render_to_response(data)


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