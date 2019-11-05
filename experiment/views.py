from hitsDB.views_import import * #common imports for views
from experiment.tables import get_user_projects, get_user_libraries, get_user_recent_exps
from django.views.generic.edit import UpdateView, View, CreateView

# Create your views here.
@login_required(login_url="/login")
@user_passes_test(user_base_tests)
def home(request):
    projectsTable = get_user_projects(request, exc=["owner","id","checked"]) #takes in request
    libsTable = get_user_libraries(request, exc=["checked",])
    recentExpsTable = get_user_recent_exps(request, exc=["owner","checked"])

    data = {
        'user':request.user,
        'projectsTable':projectsTable,
        'libsTable':libsTable,
        'recentExpsTable':recentExpsTable,
    }

    return render(request,"experiment/home_templates/home.html", data)


class AjaxableResponseMixin: 
    #taken from https://docs.djangoproject.com/en/2.2/topics/class-based-views/generic-editing/#ajax-example
    """
    Mixin to add AJAX support to a form.
    Must be used with an object-based FormView (e.g. CreateView)
    """
    def form_invalid(self, form):
        response = super().form_invalid(form)
        if self.request.is_ajax():
            data = {'result':'failure'}
            data.update({'errors':form.errors.as_json()})
            print(data['errors'])
            return JsonResponse(data, status=400)
        else:
            return response

    def form_valid(self, form):
        # We make sure to call the parent's form_valid() method because
        # it might do some processing (in the case of CreateView, it will
        # call form.save() for example).
        response = super().form_valid(form)
        if self.request.is_ajax():
            data = {'result':'success'}
            data.update({
                'pk': self.object.pk,
            })
            return JsonResponse(data)
        else:
            return response

class ModalCreateView(AjaxableResponseMixin, LoginRequiredMixin, CreateView):
    template_name = 'modals/modal_form.html'

    def get_initial(self, *args, **kwargs):
        initial = super(ModalCreateView, self).get_initial(*args, **kwargs)
        return initial

    def get_form_kwargs(self, *args, **kwargs):
        kwargs = super(ModalCreateView, self).get_form_kwargs(*args, **kwargs) #put your view name in the super
        user = self.request.user
        if user:
            kwargs['user'] = user
        return kwargs

    def get_context_data(self, *args, **kwargs):
        context = super(ModalCreateView, self).get_context_data(*args, **kwargs)
        context.update({
            "modal_title":"New " + self.form_class.Meta.model.model_name ,
            "action": self.form_class.Meta.model.newInstanceUrl(), 
            "use_ajax":True, 
        })
        return context 

class ModalEditView(AjaxableResponseMixin, LoginRequiredMixin, UpdateView):
    template_name = 'modals/modal_form.html'
    
    def get_context_data(self, *args, **kwargs):
        pk = self.object.pk
        modalFormData = self.object.getModalFormData()
        context = super(ModalEditView, self).get_context_data(*args, **kwargs)
        context.update(
            {
            "arg":pk,
            "modal_title":"Edit " + self.form_class.Meta.model.model_name,
            # "modal_title":"Edit | Last modified: %s" % self.object.modified_date,
            'action':self.object.editInstanceUrl,
            # 'action': modalFormData['edit']['view'],
            # "action":reverse('lib_edit', kwargs={'pk_lib':pk}), 
            "form_class": modalFormData['edit']['form_class'],
            "use_ajax":True,
        })
        return context

class ModifyFromTableView(LoginRequiredMixin, View):
    pass

# general class view for editing model; pass in form, initial data, etc. (see library_views.py lib_edit)     
class ModalEdit(LoginRequiredMixin, UpdateView):
    template_name = 'modals/modal_form.html'
    