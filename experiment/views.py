from django.contrib.auth.models import User, Group
from django.shortcuts import render, redirect, get_object_or_404
from .forms import NewExperimentForm
from .models import Experiment, Library
from django.contrib.auth.decorators import login_required
from django.core.serializers.json import DjangoJSONEncoder
from django.core.serializers import serialize


# Create your views here.
@login_required(login_url="login/")
def experiment(request, pk):
    experiment = get_object_or_404(Experiment, pk=pk)
    data = {
        'pkUser': request.user.id,
        'experiment': experiment,
        'pkOwner': experiment.owner_id,
    }
    return render(request,'experiment.html', data)

@login_required(login_url="login/")
def experiments(request):
    data = {
        'experiments':request.user.experiments.all(),
    }
    return render(request,'experiments.html',data)#,{'experiments':})

@login_required(login_url="login/")
def new_experiment(request): 
    user = request.user # TODO: get the currently logged in user
    if request.method == 'POST':
        form = NewExperimentForm(request.POST)
        if form.is_valid():
            experiment = form.save(commit=False)
            experiment.owner = user
            # experiment.dateTime = 
            experiment.save()
     
            return redirect('exp', pk=experiment.id) 
    else:
        form = NewExperimentForm()
    lstLibraries = []
    lstLibCompounds = []
    for group in user.groups.all():
        for lib in group.libraries.all():
            if not(lib in lstLibraries):
                lstLibraries.append(lib)
                lstLibCompounds.append(serialize('json',
                    lib.compounds.all(), cls=DjangoJSONEncoder))

    data = {'form': form,
            'Libraries': zip(lstLibraries,lstLibCompounds),
            }
    return render(request, 'new_experiment.html', data)
