from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
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
from django.urls import reverse, reverse_lazy
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required


# upload file (.csv or .json), create new library, and import compounds 
def upload_file(request):
    if request.method == 'POST':
        form = UploadCompoundsNewLib(request.POST, request.FILES,request=request)
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

# upload file (.csv or .json), create new library, and import compounds 
@login_required(login_url="/login")
def new_lib_from_file(request, form_class="new_lib_form"):
    context = {
        "form":UploadCompoundsNewLib(),
        "modal_title":"New Library",
        "action":reverse('upload_file', kwargs={'form_class':form_class}), #should be view w/o arg
        "form_class":form_class,
        "use_ajax":True, 
    }
    if request.method == 'POST':# and request.is_ajax():
        form = UploadCompoundsNewLib(request.POST, request.FILES, request=request)
        if form.is_valid():
            cd = form.cleaned_data
            fi = cd.pop('file')
            cd.update({'owner':request.user})
            new_lib = Library(**cd)
            if fi: #if file is not None
                f = TextIOWrapper(fi, encoding=request.encoding)
                try:
                    print("IN TRY!!!!!!!")
                    with transaction.atomic():
                        new_lib.save()
                        relations, created, existed = new_lib.newCompoundsFromFile(f)
                        context.update({
                            "createdCompounds":created,
                            "exisitingCompounds":existed,
                        })
                except Exception as e:
                    context['form']._errors['file'] = [str(e.detail.serializer._errors)]
                    return render(request, 'modals/modal_form.html', context)
            else:
                new_lib.save()            
            data = {'result':'success'}
            return JsonResponse(data, status=200)

        else:
            data = {'result':'success'}
            data.update({'errors':form.errors.as_json()})
            # return HttpResponse(response, status=400)
            return JsonResponse(data, status=400)
        context.update({'form':form})
    if request.method == 'GET':
        # return JsonResponse(context)
        return render(request, 'modals/modal_form.html', context)
        # return render(request, 'upload_file.html', context)

# upload file (.csv or .json) and import compounds with existing library
# deletes library compounds and associates new compounds
def update_library(request):
    pass