from hitsDB.views_import import * #common imports for views
from experiment.tables import get_user_projects, get_user_libraries, get_user_recent_exps
from django.views.generic.edit import UpdateView

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

# general class view for editing model; pass in form, initial data, etc. (see library_views.py lib_edit)     
class ModalEdit(UpdateView, LoginRequiredMixin):
    template_name = 'modals/modal_form.html'
    