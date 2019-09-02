from .views_import import * #common imports for views
from experiment.tables import get_user_projects, get_user_libraries, get_user_recent_exps
# from django.views.generic.detail import DetailView
from django.views.generic.edit import UpdateView

# Create your views here.

def is_active(user):
    return user.is_active

@login_required(login_url="/login")
@user_passes_test(is_active)
def home(request):
    projectsTable = get_user_projects(request, exc=["owner","id","expChecked"]) #takes in request
    libsTable = get_user_libraries(request, exc=[])
    recentExpsTable = get_user_recent_exps(request, exc=['owner','expChecked'])

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
    