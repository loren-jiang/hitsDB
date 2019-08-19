from django.http import HttpResponseRedirect
from django.shortcuts import render
from .forms import UploadCompoundsNewLib, UploadCompoundsFromJSON
from .models import Library, Compound
import json
from django.db import transaction, DatabaseError
from itertools import compress
from orm_custom.custom_functions import bulk_add
from io import TextIOWrapper

# upload file (.csv or .json), create new library, and import compounds 
def upload_file(request):
    if request.method == 'POST':
        form = UploadCompoundsNewLib(request.POST, request.FILES, request=request)
        if form.is_valid():
            f = TextIOWrapper(request.FILES['file'], encoding=request.encoding)
            lib_name = form.cleaned_data['name'] #assumes lib_name is unique
            new_lib = Library(name=lib_name, owner=request.user)
            new_lib.save()

            relations, created, existed = new_lib.newCompoundsFromFile(f)

            data = {
                "createdCompounds":created,
                "exisitingCompounds":existed,
            }
            return render(request, 'upload_file.html', data)
            # return HttpResponseRedirect('')
    else:
        form = UploadCompoundsNewLib()
    return render(request, 'upload_file.html', {'form': form})

# upload file (.csv or .json) and import compounds with existing library
# deletes library compounds and associates new compounds
def update_library(request):
    pass

