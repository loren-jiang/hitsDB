from django.http import HttpResponseRedirect
from django.shortcuts import render
from .forms import UploadCompoundsNewLib, UploadCompoundsFromJSON
from .models import Library, Compound
import json
from django.db import transaction, DatabaseError
from itertools import compress
from orm_custom.custom_functions import bulk_add
from io import TextIOWrapper
from django.db import transaction
from django.core.exceptions import ValidationError

# upload file (.csv or .json), create new library, and import compounds 
def upload_file(request):
    if request.method == 'POST':
        form = UploadCompoundsNewLib(request.POST, request.FILES, request=request)
        if form.is_valid():
            f = TextIOWrapper(request.FILES['file'], encoding=request.encoding)
            lib_name = form.cleaned_data['name'] #assumes lib_name is unique
            new_lib = Library(name=lib_name, owner=request.user)
            context = {'form':form}
   
            try:
                with transaction.atomic():
                    new_lib.save()
                    relations, created, existed = new_lib.newCompoundsFromFile(f)
                    context.update({
                        "createdCompounds":created,
                        "exisitingCompounds":existed,
                    })
            except Exception as e:
                context['form']._errors['file'] = [repr(e)]
            return render(request, 'upload_file.html', context)
    else:
        form = UploadCompoundsNewLib()
    return render(request, 'upload_file.html', {'form': form})

# upload file (.csv or .json) and import compounds with existing library
# deletes library compounds and associates new compounds
def update_library(request):
    pass

