from django.db import models
from django.contrib.auth.models import User, Group
from django.utils import timezone
from django.core.validators import MaxValueValidator, MinValueValidator
from datetime import date
import json
import csv

from itertools import compress
from orm_custom.custom_functions import bulk_add
from itertools import compress
from utility_functions import chunks
from .validators import validate_prefix
# from django.core.exceptions import ValidationError

# Create your models here.
class Compound(models.Model): #doesnt need to be unique?
    chemicalName = models.CharField(max_length=300,null=True, blank=True)
    chemicalFormula = models.CharField(max_length=100, default='')
    # library = models.ForeignKey(Library, related_name='compounds', on_delete=models.CASCADE, null=True, blank=True)
    #not all smiles have unique zincID, or perhaps vice versa
    wellLocation = models.CharField(max_length=4, null=True, blank=True) # e.g. A01, AB02
    zinc_id = models.CharField(max_length=30, unique=True)#, validators=[validate_prefix("zinc")])
    smiles = models.CharField(max_length=300,null=True, blank=True)
    zincURL = models.URLField(null=True, blank=True)
    molWeight = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    concentration = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    purity = models.PositiveSmallIntegerField(default=100, validators=[MaxValueValidator(100), MinValueValidator(0)])
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.zinc_id


class Library(models.Model):
    name = models.CharField(max_length=30, unique=True)
    # name = models.CharField(max_length=30, )
    description = models.CharField(max_length=300, default='')
    isCommerical = models.BooleanField(default=False)
    sourceURL = models.URLField(null=True, blank=True)
    groups = models.ManyToManyField(Group, related_name='group_libraries', blank=True)
    owner = models.ForeignKey(User, related_name='libraries', on_delete=models.CASCADE,null=True, blank=True)
    isTemplate = models.BooleanField(default=False)
    supplier = models.CharField(max_length=100, default='')
    # library can have many compounds; compound can have many libraries
    compounds = models.ManyToManyField(Compound, related_name='libraries', blank=True)
    active = models.BooleanField(default=True)

    def get_absolute_url(self):
        return "/libraries/%i/" % self.id
    def __str__(self):
        return self.name
    
    @property
    def numCompounds(self):
        return self.compounds.all().count()

    def insertCompoundsFromChunk(self, serialized_data):
        from .serializers import NoSaveCompoundSerializer
        num = len(serialized_data)
        obj_lst = [None for k in range(num)]
    
        for i in range(num):
            data = serialized_data[i]
            fields = NoSaveCompoundSerializer.__dict__['_declared_fields']
            data = { k: data[k] for k in fields }
            serialize = NoSaveCompoundSerializer(data=data)
            if serialize.is_valid(raise_exception=True):
                obj_lst[i]=serialize.save()

        compounds_lst = [c for c in obj_lst if c is not None] #filter out None elems just in case
        
        # Greedy solution, but will not support updating compounds in the future
        # compounds_created = Compound.bulk_create(compounds_lst, ignore_conflicts=True)
        
        # check zinc_ids to see if they exist already in database
        # filter to find compounds not in db
        filt = [Compound.objects.filter(zinc_id=c.zinc_id).exists() for c in compounds_lst] 

        compounds_to_be_created = list(compress(compounds_lst, [not i for i in filt]))
        compounds_existing = list(compress(compounds_lst, filt))
        compounds_created = Compound.objects.bulk_create(compounds_to_be_created, ignore_conflicts=True)

        # optionally, we can bulk update here I think...
        return [c for c in compounds_created], [c for c in compounds_existing]

    # import file (.json or .csv) of compounds
    def newCompoundsFromFile(self, f):
        chunk_size = 1000
        file_name = f.name
        relations = []
        created = []
        existed = []
        rows = []
        is_csv = file_name.endswith(".csv")
        if is_csv:
            reader = csv.DictReader(f)
            rows = chunks(list(reader), chunk_size)
        else: # if file is .json
            rows = f.chunks(chunk_size)

        for chunk in rows:
            if is_csv:
                chunk_serialized = chunk
            else:
                chunk_serialized = json.loads(chunk)
            compounds_to_create, compounds_existing = self.insertCompoundsFromChunk(chunk_serialized)
            lib = self
            LibCompoundRelation = Library.compounds.through
            # list of zinc codes for all compounds created and existing
            ZINC_lst = [c.zinc_id for c in compounds_to_create] + [c.zinc_id for c in compounds_existing]
            qs = Compound.objects.filter(zinc_id__in=ZINC_lst).prefetch_related("libraries")
            compound_pks = [c.pk for c in qs]
            lib_pks = [lib.pk]
            rels = bulk_add(LibCompoundRelation, lib_pks, compound_pks,
                    "library_id","compound_id")
            relations.extend(rels)
            created.extend(compounds_to_create)
            existed.extend(compounds_existing)
        return relations, created, existed
