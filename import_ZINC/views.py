from django.http import HttpResponseRedirect
from django.shortcuts import render
from .forms import UploadCompoundsNewLib, UploadCompoundsFromJSON
from .models import Library, Compound
import json
from .serializers import CompoundJSONSerializer
from django.db import transaction, DatabaseError
from itertools import compress
from orm_custom.custom_functions import bulk_add

# Imaginary function to handle an uploaded file.
# from somewhere import handle_uploaded_file

def upload_file(request):
    if request.method == 'POST':
        form = UploadCompoundsNewLib(request.POST, request.FILES)
        if form.is_valid():
            lib_name = form.cleaned_data['name'] #assumes lib_name is unique
            new_lib = Library(name=lib_name, owner=request.user)
            new_lib.save()

            relations, created, existed = new_lib.newLibraryFromJSON(request.FILES['file'])

            data = {
                "createdCompounds":created,
                "exisitingCompounds":existed,
            }
            return render(request, 'upload_file.html', data)
            # return HttpResponseRedirect('')
    else:
        form = UploadCompoundsNewLib()
    return render(request, 'upload_file.html', {'form': form})
