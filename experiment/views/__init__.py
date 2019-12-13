from .experiment_views import *
from .library_views import *
from .soak_views import *
from .project_views import *

from hitsDB.views_import import * #common imports for views
from ..tables import get_user_projects, get_user_libraries, get_user_recent_exps
from django.views.generic.edit import UpdateView, View, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from my_utils.my_views import ModalCreateView, ModalEditView, ModifyFromTableView
from django.utils.decorators import method_decorator
from django.contrib import messages
from ..querysets import user_editable_experiments 

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

@method_decorator([login_required(login_url="/login"), ], name='dispatch')
class SecureProjectModifyFromTable(ModifyFromTableView):
    pass
    # def post(self, request, *args, **kwargs):
    #     prev = request.META.get('HTTP_REFERER')
    #     form = request.POST
        
    #     btn_id = form.get('btn', None)
    #     if btn_id and self.model_class:
    #         pks = form.getlist('checked') #list of model instance pks
    #         if btn_id=="delete_selected":
    #             self.delete_model_instances(request, pks, owner=request.user)
        
    #     return redirect(prev)

@method_decorator([login_required(login_url="/login"), ], name='dispatch')
class SecureExperimentModifyFromTable(ModifyFromTableView):
    def post(self, request, *args, **kwargs):
        prev = request.META.get('HTTP_REFERER')
        form = request.POST
        
        btn_id = form.get('btn', None)
        if btn_id and self.model_class:
            pks = form.getlist('checked') #list of model instance pks
            qs = self.model_class.objects.filter(id__in=pks)
            user_editable_qs = user_editable_experiments(request.user)
            # user_editable_qs = qs.filter(owner=request.user)
            if btn_id=="delete_selected":
                qs.intersection(user_editable_qs).delete()
            diff_qs = qs.difference(user_editable_qs)
            if diff_qs.exists():
                for p in diff_qs:
                    messages.error(request, "Could not delete '" + p.name + "' because you are not the owner.")
        return redirect(prev)

@method_decorator([login_required(login_url="/login"), ], name='dispatch')
class SecurePlateModifyFromTable(ModifyFromTableView):
    def post(self, request, *args, **kwargs):
        prev = request.META.get('HTTP_REFERER')
        form = request.POST
        
        btn_id = form.get('btn', None)
        if btn_id and self.model_class:
            pass
            # pks = form.getlist('checked') #list of model instance pks
            # qs = self.model_class.objects.filter(id__in=pks)
            # user_qs = qs.filter(owner=request.user)
            # if btn_id=="delete_selected":
            #     user_qs.delete()
            # diff_qs = qs.difference(user_qs)
            # if diff_qs.exists():
            #     for p in diff_qs:
            #         messages.error(request, "Could not delete project '" + p.name + "' because you are not the owner.")
        return redirect(prev)
