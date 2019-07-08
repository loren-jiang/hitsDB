from django.db import models
from django.contrib.auth.models import User, Group
from django.utils import timezone
from datetime import date
import json

from itertools import compress
from orm_custom.custom_functions import bulk_add
from itertools import compress

# Create your models here.
class Compound(models.Model): #doesnt need to be unique?
    nameInternal = models.CharField(max_length=100, unique=True, null=True, blank=True)
    chemicalName = models.CharField(max_length=300,null=True, blank=True)
    commonName = models.CharField(max_length=100, default='')
    chemFormula = models.CharField(max_length=100, default='')
    # manufacturer = models.CharField(max_length=100, default='')
    # library = models.ForeignKey(Library, related_name='compounds', on_delete=models.CASCADE, null=True, blank=True)
    #not all smiles have unique zincID, or perhaps vice versa
    zinc_id = models.CharField(max_length=30, null=True, blank=True, unique=True)
    smiles = models.CharField(max_length=300,null=True, blank=True)
    zincURL = models.URLField(null=True, blank=True)
    molWeight = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    concentration = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    # chemName = models.CharField(max_length=1000, default='')
    active = models.BooleanField(default=True)
    def __str__(self):
        return self.zinc_id


class Library(models.Model):
    name = models.CharField(max_length=30, unique=True)
    # name = models.CharField(max_length=30, )
    description = models.CharField(max_length=300, default='')
    isCommerical = models.BooleanField(default=False)
    sourceURL = models.URLField(null=True, blank=True)
    groups = models.ManyToManyField(Group, related_name='libraries', blank=True)
    owner = models.ForeignKey(User, related_name='library', on_delete=models.CASCADE,null=True, blank=True)
    isTemplate = models.BooleanField(default=False)
    supplier = models.CharField(max_length=100, default='')
    # library can have many compounds; compound can have many libraries
    compounds = models.ManyToManyField(Compound, related_name='libraries', blank=True)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

        # import JSON of compounds and create new library from them
    def newLibraryFromJSON(self, f):
        from .serializers import CompoundJSONSerializer
        def insertCompoundsFromJSON(f):
            created = []
            existing = []
            for chunk in f.chunks():
                chunk_json = json.loads(chunk)
                compounds_created, compounds_existing = insertCompoundsFromChunk(chunk_json)
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

   

        relations = []
        created = []
        existed = []
        for chunk in f.chunks():
            chunk_json = json.loads(chunk)
            compounds_created, compounds_existing = insertCompoundsFromChunk(chunk_json)
            lib = self
            # below is sorta hacky "bulk add"
            LibCompoundRelation = Library.compounds.through
            # list of zinc codes for all compounds created and existing
            ZINC_lst = [c.zinc_id for c in compounds_created] +[c.zinc_id for c in compounds_existing]
            qs = Compound.objects.filter(zinc_id__in=ZINC_lst).prefetch_related("libraries")
            compound_pks = [c.pk for c in qs]
            # import pdb; pdb.set_trace()
            lib_pks = [lib.pk]
            rels = bulk_add(LibCompoundRelation, lib_pks, compound_pks,
                    "library_id","compound_id")
            relations.extend(rels)
            created.extend(compounds_created)
            existed.extend(compounds_existing)
        return relations, created, existed




    
