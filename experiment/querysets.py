# common querysets that views will need
from .models import Project, Experiment, Soak
from import_ZINC.models import Library, Compound


#-------------------------------------------------Library querysets ---------------------------------------------------------

# libraries accessible to users; 
def accessible_libs(user):
    user_projects = user.projects.filter()
    user_collab_projects = user.collab_projects.filter()
    projs = user_projects.union(user_collab_projects)
    user_collab_libs = Library.objects.filter(
        experiments__in=Experiment.objects.filter(project_id__in=[p.id for p in projs]))
    user_libs = user.libraries.filter()
    return user_libs.union(user_collab_libs)

#-------------------------------------------------Experiment querysets ---------------------------------------------------------

#-------------------------------------------------Project querysets ---------------------------------------------------------
