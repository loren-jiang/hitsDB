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
            rels = newLibraryFromJSON(request.FILES['file'], new_lib)

            # createdCompounds, exisitingCompounds = insertCompoundsFromJSON(request.FILES['file'])
            # data = {
            #     "createdCompounds":createdCompounds,
            #     "exisitingCompounds":exisitingCompounds
            # }
            # return render(request, 'upload_file.html', data)
            return HttpResponseRedirect('')
    else:
        form = UploadCompoundsNewLib()
    return render(request, 'upload_file.html', {'form': form})

def insertCompoundsFromJSON(f):
    created = []
    existing = []
    for chunk in f.chunks():
        chunk_json = json.loads(chunk)
        compounds_created, compounds_existing,  = insertCompoundsFromChunk(chunk_json)
        created.extend(compounds_created)
        existing.extend(compounds_existing)
    return created, existing

def insertCompoundsFromChunk(chunk_json):
    num = len(chunk_json)
    obj_lst = [None for k in range(num)]

    for i in range(num):
        data = chunk_json[i]
        serialize = CompoundJSONSerializer(data=data)
        if serialize.is_valid():
            obj_lst[i]=serialize.save()

    compounds_lst = [c for c in obj_lst if c is not None] #filter out None elems just in case
    
    # Greedy solution, but will not support updating compounds in the future
    # compounds_created = Compound.bulk_create(compounds_lst, ignore_conflicts=True)
    
    # check zinc_ids to see if they exist already in database
    # filter to find compounds not in db
    filt = [Compound.objects.filter(zinc_id=c.zinc_id).exists() 
            for c in compounds_lst] 

    compounds_to_be_created = list(compress(compounds_lst, [not i for i in filt]))
    compounds_existing = list(compress(compounds_lst, filt))
    compounds_created = Compound.objects.bulk_create(compounds_to_be_created)

    # optionally, we can bulk update here I think...
    return [c for c in compounds_created], [c for c in compounds_existing]

#zinc_ids is a list of ZINC codes
def queryCompoundsByZINC(zinc_ids):
    return Compound.objects.filter(zinc_id__in=zinc_ids).prefetch_related("libraries")

# def modifyLibrary(lib):

# import JSON of compounds and create new library from them
def newLibraryFromJSON(f, lib):
    relations = []
    for chunk in f.chunks():
        chunk_json = json.loads(chunk)
        compounds_created, compounds_existing = insertCompoundsFromChunk(chunk_json)
        lib.save()
        # below is sorta hacky "bulk add"
        LibCompoundRelation = Library.compounds.through
        # list of zinc codes for all compounds created and existing
        ZINC_lst = [c.zinc_id for c in compounds_created] +[c.zinc_id for c in compounds_existing]
        qs = queryCompoundsByZINC(ZINC_lst)
        compound_pks = [c.pk for c in qs]
        import pdb; pdb.set_trace()
        lib_pks = [lib.pk]
        rels = bulk_add(LibCompoundRelation, lib_pks, compound_pks,
                "library_id","compound_id")
        relations.extend(rels)
    return relations
        # relations = []
        # for c in compounds_created:
        #     relations.extend([LibCompoundRelation(
        #         library_id=lib.id,
        #         compound_id=c.id)])
        # LibCompoundRelation.objects.bulk_create(relations)

        #update library since compounds can have more than 1 library
        # lib.compounds.add(*compounds_existing)
        
        # import pdb; pdb.set_trace()
