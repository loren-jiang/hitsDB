from experiment.models import Experiment 
from .models import Library
#-------------------------------------------------Library querysets --------------------------------------------------------------

# libraries accessible to users; 
def user_accessible_libs(user):
    user_collab_projects = user.collab_projects.filter()
    collab_exps = Experiment.objects.filter(project_id__in=[p.id for p in user_collab_projects])
    collab_libs = Library.objects.filter(experiments__in=collab_exps)
    user_libs = user.libraries
    libs = Library.objects.filter(id__in=[lib.id for lib in user_libs.union(collab_libs)])
    return libs

