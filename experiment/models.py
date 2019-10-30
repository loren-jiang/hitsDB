from django.db import models
from django.contrib.auth.models import User, Group
from django.utils import timezone
from import_ZINC.models import Library, Compound
from .exp_view_process import formatSoaks, split_list, getWellIdx, getSubwellIdx
from django.db.models.signals import post_save, post_init, pre_save
from django.dispatch import receiver
from django.utils.functional import cached_property 
from my_utils.orm_functions import bulk_add, bulk_one_to_one_add
from django.contrib.postgres.fields import ArrayField, JSONField
from django.core.validators import MaxValueValidator, MinValueValidator, RegexValidator
from django.db.models import Count, F, Value
from my_utils.utility_functions import chunk_list, items_at, ceiling_div, gen_circ_list, \
    PIX_TO_UM, UM_TO_PIX, IMG_SCALE, VolumeToRadius, RadiusToVolume, \
        mapUmToPix, mapPixToUm
import string
from datetime import datetime
from django.utils.timezone import make_aware
from s3.s3utils import PrivateMediaStorage
from s3.models import PrivateFile, PrivateFileJSON
import json 
import csv 
from django.db import transaction, IntegrityError


# Create your models here.
class Project(models.Model):
    name = models.CharField(max_length=30)
    owner = models.ForeignKey(User, related_name='projects',on_delete=models.CASCADE)
    dateTime = models.DateTimeField(auto_now_add=True, verbose_name='Created')
    description = models.CharField(max_length=300, blank=True, null=True)
    collaborators = models.ManyToManyField(User, related_name='collab_projects',blank=True) 
    
    # takes in exc list of column names to exclude
    def getExperimentsTable(self, exc=[]):
        from .tables import ExperimentsTable
        # might want to implement try catch
        return ExperimentsTable(self.experiments.all(), exclude=exc)

    def getCollaboratorsTable(self,exc=[]):
        from .tables import CollaboratorsTable
        # might want to implement try catch
        return CollaboratorsTable(self.collaborators.all(), exclude=exc)

    #get list of libraries used in project's experiments
    def getLibrariesTable(self, exc=[]):
        from .tables import LibrariesTable
        qs = Library.objects.filter(experiments__in=self.experiments.all()).union(
            Library.objects.filter(isTemplate=True))
        return LibrariesTable(qs)

    class Meta:
        get_latest_by = "dateTime"

    def get_absolute_url(self):
        return "/projects/%i/" % self.id

    def __str__(self):
        return self.name

def defaultSubwellLocations():
    return list([1])


def exp_init_upload_path(instance, filename):
    return str(instance.owner.id)+ '/init_data_files/' + str(instance.id) 

class Experiment(models.Model):
    name = models.CharField(max_length=30)
    library = models.ForeignKey(Library, related_name='experiments',
        on_delete=models.CASCADE)
    prev_library_id = None #prev library to check if library has changed
    project = models.ForeignKey(Project, null=True, blank=True, on_delete=models.CASCADE, related_name='experiments')
    description = models.CharField(max_length=300, blank=True, null=True)
    dateTime = models.DateTimeField(auto_now_add=True)
    protein = models.CharField(max_length=100)
    owner = models.ForeignKey(User, related_name='experiments',on_delete=models.CASCADE)
    srcPlateType = models.ForeignKey('PlateType', null=True, blank=True, on_delete=models.CASCADE, related_name='experiments_src') #only one src plate type per experiment
    destPlateType = models.ForeignKey('PlateType', null=True, blank=True, on_delete=models.CASCADE, related_name='experiments_dest') #noly one dest plate type per experiment
    subwell_locations = ArrayField(
        models.PositiveSmallIntegerField(blank=True, null=True, validators=[MaxValueValidator(3), MinValueValidator(1)]),
        size=3, default=defaultSubwellLocations
        )
    initDataJSON = JSONField(default=dict)
    init_data_file = models.FileField(upload_to=exp_init_upload_path,storage=PrivateMediaStorage(), blank=True, null=True)
    initData = models.OneToOneField(PrivateFileJSON, null=True, blank=True, on_delete=models.CASCADE, related_name='experiment')
    prev_initData_id = None #prev library to check if initData file has changed
    
    class Meta:
        get_latest_by="dateTime"
        # ordering = ['-dateTime']

    @property
    def initDataValid(self):
        """
        Return True if self.initData exists and has all the right initialization data
        """
        if bool(self.initData):
            return True
        reutrn False

    @property
    def getCurrentStep(self):
        """
        Gets the current step of the experiment; used for rendering main experiment view
        """
        cond0 = bool(self)
        cond1 = self.libraryValid and self.initDataValid
        cond2 = self.destPlatesValid
        cond3 = self.srcPlatesValid
        # cond3 = self.soaksValid
        conds = [cond0, cond1, cond2, cond3] # cond1 corresponds to step 1
        if all(conds[0:4]): #might want to more robust check (e.g. # soaks = # compounds in library)
            return 4
        if all(conds[0:3]):
            return 3
        if all(conds[0:2]):
            return 2
        if all(conds[0:1]):
            return 1
        return 0

    @property
    def getTransferPlatePairs(self):
        """
        TODO: add doc string
        """
        pairs = []
        qs = self.soaks.select_related('src__plate','dest__parentWell__plate'
            ).annotate(src_plate_id=F('src__plate_id')
            ).annotate(dest_plate_id=F('dest__parentWell__plate_id'))
        for s in qs:
            s.__dict__
            pair = (s.src_plate_id, s.dest_plate_id)
            if pair not in pairs:
                pairs.append(pair)
        return pairs

    @property
    def soaksValid(self):
        """
        Returns True if experiment soaks exist and if each soak's dest subwell and source well exist and is in plate,
        else returns False
        """
        if not(self.soaks.count()):
            return False
        for s in self.soaks.select_related('src__plate', 'dest__parentWell__plate'):
            if not(s.src_id and s.dest_id):
                return False
            if not(s.src.plate.id==self.id and s.dest.parentWell.plate.id==self.id):
                return False
        return True

    @property
    def libraryValid(self):
        """
        Returns True if experiment library has compounds, else False
        """
        return bool(self.library.compounds.count())

    @property
    def srcPlatesValid(self):
        return bool(self.plates.filter(isSource=True).count())
    
    @property
    def destPlatesValid(self):
        """
        Returns True if all dest plates have drop images, else False
        """
        dest_plates = self.plates.filter(isSource=False).prefetch_related('drop_images')
        for p in dest_plates:
            if not(p.drop_images.count()):
                return False
        return True
    @property
    def platesValid(self):
        """
        Returns True if dest plates and source plates are valid, else False
        """
        return self.destPlatesValid and self.srcPlatesValid

    @property
    def libCompounds(self):
        """
        Returns compounds in experiment library ordered by id
        """
        if self.library.compounds.first():
            return self.library.compounds.order_by('id')
        else:
            return Compound.objects.none() #empty queryset

    @property
    def numSrcPlates(self):
        """
        Returns number of source plates
        """
        return self.plates.filter(isSource=True).count()
    
    @property
    def numDestPlates(self):
        """
        Returns number of dest plates
        """
        return self.plates.filter(isSource=False).count()

    def expNumSrcPlates(self):
        """
        Returns expected number of source plates based on number of compounds in library
        """
        src_plate_type = self.srcPlateType
        num_src_wells = src_plate_type.numCols * src_plate_type.numRows
        return ceiling_div(self.libCompounds.count(), num_src_wells)
  
    def expNumDestPlates(self):
        """
        Returns expected number of dest plates based on number of compounds in library
        """
        num_subwells  = len(self.subwell_locations)
        dest_plate_type = self.destPlateType
        num_dest_wells = dest_plate_type.numCols * dest_plate_type.numRows
        return ceiling_div(self.libCompounds.count(),num_dest_wells * num_subwells)


    @property
    def usedSoaks(self):
        """
        Returns the experiment's ordered used soaks
        """
        return self.soaks.filter(useSoak=True).order_by('dest__parentWell__plate__plateIdxExp','dest__idx')

    @property
    def destSubwells(self):
        """
        Returns ordered subwells in the experiment's destination plates
        """
        return SubWell.objects.filter(parentWell__plate__isSource=False).order_by('parentWell__plate__plateIdxExp', 'idx')

    @property
    def srcWells(self):
        """
        Returns ordered wells in the experiment's source plates
        """
        return Well.objects.filter(plate__isSource=True).filter().order_by('plate__plateIdxExp', 'name')
    
    @property
    def srcWellsWithCompounds(self):
        """
        Returns the wells in the experiment's source plates with compounds
        """
        return self.srcWells.exclude(compounds__isnull=True)

    def createSrcPlatesFromLibFile(self, numPlates=0, file=''):
        """
        Creates source plates from CSV file (https://docs.google.com/spreadsheets/d/1FRBm6wVNSpwg4d3zGCYKLQkEZjf4BP9JL0YkEJzSojw/edit?usp=sharing)
        Then update wells with the appropriate compounds specified from csv file

        Parameters:
        numPlates (int): number of empty plates to make
        file (uploaded file): CSV file to update wells with appropriate compounds (see example file above)
        """
        exp = self
        file_reader = csv.reader(file, delimiter=',')
        headers = next(file_reader)
        zinc_id_idx = headers.index('zinc_id')
        plate_idx_idx = headers.index('plate_idx')
        well_idx = headers.index('well')
        try:
            with transaction.atomic():
                platesMade = exp.makeSrcPlates(numPlates)
                plateIdxRange = range(1, numPlates+1)

                compound_dict = {}
                for row in file_reader:
                    compound_dict[row[zinc_id_idx]] = {
                        'plate_idx': row[plate_idx_idx],
                        'well_name':row[well_idx],
                    }
                #retrieve existing compounds 
                existing_compounds_qs = Compound.objects.filter(zinc_id__in=compound_dict.keys())
                existing_compounds_dict = {}
                for c in existing_compounds_qs:
                    key_ = compound_dict[c.zinc_id]['plate_idx'] + '_' + compound_dict[c.zinc_id]['well_name']
                    existing_compounds_dict[key_] = c
                existing_compounds_ids = [existing_compounds_dict[k_].id for k_ in existing_compounds_dict.keys()]
                
                #retrieve and update existing wells with appropriate compound
                wells_qs = Well.objects.filter(plate__in=platesMade
                    ).select_related('plate'
                    ).prefetch_related('compounds'
                    ).annotate(plate_idx=F('plate__plateIdxExp'))
                wells_dict = {}
                for w in wells_qs:
                    wells_dict[str(w.plate_idx) + '_' + w.name] = w

                wells_with_compounds_ids = [wells_dict[k_].id for k_ in existing_compounds_dict.keys()]
                throughRel = Well.compounds.through
                bulk_one_to_one_add(throughRel, wells_with_compounds_ids, existing_compounds_ids, 'well_id', 'compound_id')
        except IntegrityError as e:
            print(e)
        except KeyError as e:
            print(e)

    def matchSrcWellsToSoaks(self, src_wells=[], soaks=[]):
        """
        Match soaks to source wells by looping through one-by-one
        
        Parameters:
        src_wells (list): List of an experiment's source wells with compounds
        soaks (list): List of an experiment's used soaks 

        Returns:
        None
        """
        if not(soaks):
            soaks = [s for s in self.usedSoaks]
        if not(src_wells):
            src_wells = [w for w in self.srcWellsWithCompounds]

        assert len(soaks) <= len(src_wells)
        try:
            with transaction.atomic():
                for i in range(len(soaks)):
                    soaks[i].src = None
                Soak.objects.bulk_update(soaks, ['src'])
                for i in range(len(soaks)):
                    soaks[i].src = src_wells[i]
                Soak.objects.bulk_update(soaks, ['src'])
        except Exception as e: 
            print(e)
            pass
    
    def generateSoaks(self, transferVol=25, soakOffsetX=0, soakOffsetY=0):
        self.soaks.all().delete() #start from fresh
        ct = 0
        cmpds = self.libCompounds
        list_soaks = [None]*cmpds.count()
        list_src_wells = [w for w in self.srcWells.order_by('id')]
        list_dest_subwells = [w for w in self.destSubwells.order_by('id')]
        # a = chunk_list(list_dest_subwells, 3)
        s_w_idxs = list(map(lambda x: x-1, self.subwell_locations))
        
        list_dest_subwells = items_at(lst=list_dest_subwells, 
            chunk_size=self.destPlateType.numSubwells, idxs=s_w_idxs)
        for c in cmpds:
            src_well = list_src_wells[ct]
            dest_subwell = list_dest_subwells[ct]
            dest_subwell.hasCrystal = True
            soak = Soak(experiment_id=self.id,src=src_well,dest=dest_subwell, transferCompound=c, 
                soakOffsetX=soakOffsetX, soakOffsetY=soakOffsetY, transferVol=transferVol)
            list_soaks[ct] = soak
            ct += 1
        Soak.objects.bulk_create(list_soaks)

        cmpds_pks = [c.pk for c in cmpds]
        src_wells_pks = [w.pk for w in list_src_wells]
        dest_subwells_pks = [s_w.pk for s_w in list_dest_subwells]
        WellCompoundRelation = Well.compounds.through
        SubWellCompoundRelation = SubWell.compounds.through
        bulk_one_to_one_add(WellCompoundRelation, src_wells_pks, cmpds_pks,
            "well_id","compound_id")
        bulk_one_to_one_add(SubWellCompoundRelation, dest_subwells_pks, cmpds_pks,
            "subwell_id","compound_id")
        return
    
    def groupSoaks(self):
        src_plate_ids = [p.id for p in self.plates.filter(isSource=True)]
        chunk_size = self.srcPlateType.numResWells * len(self.subwellLocations)
        grouped_soaks = []
        for id in src_plate_ids:
            grouped_soaks.append(
                chunk_list(self.soaks.filter(src__plate_id=id), chunk_size)
            )
        return grouped_soaks

    #create the source plate and dest plates given the library size
    # num_subwells should be lte to dest_plate_type.numSubwells
    def generateSrcDestPlates(self):
        try:
            # exp_compounds = self.library.compounds.order_by('id')
            self.plates.all().delete() #start from fresh 
            src_plate_type = self.srcPlateType
            dest_plate_type = self.destPlateType
            num_compounds = self.libCompounds.count()
            num_subwells = len(self.subwell_locations)
            num_src_wells = src_plate_type.numCols * src_plate_type.numRows
            num_dest_wells = dest_plate_type.numCols * dest_plate_type.numRows
            num_src_plates = ceiling_div(num_compounds,num_src_wells)
            num_dest_plates = ceiling_div(num_compounds,num_dest_wells * num_subwells)
            src_plates_to_create = [None]*num_src_plates
            dest_plates_to_create = [None]*num_dest_plates
            # loop through and create the appropriate number of plates 
            for i in range(num_src_plates):
                src_plates_to_create[i] = Plate(name='src_'+str(i+1),plateType=src_plate_type, 
                    experiment_id=self.id, isSource=True, plateIdxExp=i+1)
                # src_plates_to_create[i].save()
            for i in range(num_dest_plates):
                dest_plates_to_create[i] = Plate(name='dest_'+str(i+1),plateType=dest_plate_type, 
                    experiment_id=self.id,isSource=False, plateIdxExp=i+1)
                # dest_plates_to_create[i].save()
            plates = Plate.objects.bulk_create(src_plates_to_create + dest_plates_to_create) #bulk create Plate objects
            for p in plates:
                p.createPlateWells() # bulk_create doesn't send signals so need to call explicitly
            return True
        except Exception as e:
            #print(e)
            return False
    
    def makeSrcPlates(self, num_plates):
        self.plates.filter(isSource=True).delete()
        if (self.srcPlateType):
            return self.makePlates(num_plates, self.srcPlateType)
        else:
            return []

    def makeDestPlates(self, num_plates):
        self.plates.filter(isSource=False).delete()
        if (self.destPlateType):
            return self.makePlates(num_plates, self.destPlateType)
        else:
            return []

    def makePlates(self, num_plates, plate_type, plates_init_data=None):
        try:
            assert num_plates > 0
            plates_to_create = [None] * num_plates
            name_prefix = 'src_' if plate_type.isSource else 'dest_'
            if plates_init_data:
                pass
            else:
                for i in range(num_plates):
                    plates_to_create[i] = Plate(name=name_prefix+str(i+1),plateType=plate_type, 
                        experiment_id=self.id,isSource=plate_type.isSource, plateIdxExp=i+1)
                plates = Plate.objects.bulk_create(plates_to_create)
                
                for p in plates:
                    p.createPlateWells()
                return plates
        except Exception as e:
            return []

    def createPlatesSoaksFromInitDataJSON(self):
        exp = self
        dest_plates = exp.plates.filter(isSource=False)
        if dest_plates.exists():
            dest_plates.delete()
        init_data_plates = exp.initDataJSON.items()
        lst_plates = exp.makePlates(len(init_data_plates), self.destPlateType)
        soaks = []
        for i, (plate_id, plate_data) in enumerate(init_data_plates):
            id = plate_data.pop("plate_id", None) 
            date_time = plate_data.pop("date_time", None)
            plate = lst_plates[i]
            plate.rockMakerId = plate_id
            plate.dateTime = make_aware(datetime.strptime(date_time, '%Y-%m-%d %H:%M:%S.%f'))
            plate.save()

            # loop through well keys and create soaks w/ appropriate data
            for j, (well_key, well_data) in enumerate(plate_data.items()):
                well_name, s_w_idx = well_key.split('_')
                well = plate.wells.filter(name=well_name)[0]
                s_w = well.subwells.get(idx=s_w_idx) 
                soaks.append(Soak(
                    experiment_id = exp.id,
                    dest_id = s_w.id, 
                    drop_x = well_data['drop_x'] * PIX_TO_UM, 
                    drop_y = well_data['drop_y'] * PIX_TO_UM,
                    drop_radius = well_data['drop_radius'] * PIX_TO_UM,
                    well_x =  well_data['well_x'] * PIX_TO_UM, 
                    well_y =  well_data['well_y'] * PIX_TO_UM,
                    well_radius =  well_data['well_radius'] * PIX_TO_UM,
                    soakOffsetX =  well_data['well_x'] * PIX_TO_UM,
                    soakOffsetY = well_data['well_y'] * PIX_TO_UM,
                    # soakVolume = ,
                    useSoak= True
                ))    
        soaks = Soak.objects.bulk_create(soaks)  
        return soaks

    def formattedSoaks(self, qs_soaks,
                    s_num_rows=16, s_num_cols = 24, 
                    d_num_rows=8, d_num_cols=12, d_num_subwells=3):
        num_src_plates = self.numSrcPlates
        num_dest_plates = self.numDestPlates
            
        s_num_wells = s_num_rows * s_num_cols
        d_num_wells = d_num_rows * d_num_cols
        # qs_soaks = self.soaks.select_related('dest__parentWell__plate','src__plate',
        #     ).prefetch_related('transferCompound',).order_by('id')

        soaks_lst = [soak for soak in qs_soaks]
        src_wells = [0]*num_src_plates*s_num_wells
        dest_subwells = [0]*num_dest_plates*d_num_wells*d_num_subwells

        for j in range(len(soaks_lst)):
            s = soaks_lst[j]
            src = s.src # source Well
            src_well_idx = src.wellIdx
            src_plate_idx = src.plate.plateIdxExp
            s_w_idx = getWellIdx(src_plate_idx,src_well_idx, s_num_wells)
            dest = s.dest
            dest_subwell_idx = dest.idx
            dest_parentwell_idx = dest.parentWell.wellIdx
            dest_plate_idx = dest.parentWell.plate.plateIdxExp
            d_sw_idx = getSubwellIdx(dest_plate_idx,dest_parentwell_idx,
                dest_subwell_idx, d_num_wells,d_num_subwells) 
            compound = s.transferCompound
            src_wells[s_w_idx] = {
                                'well_id':src.id, 
                                'well_name':src.name, 
                                'compound':compound.nameInternal,
                                'dest_subwell_id':dest.id,
                                'soak_id':s.id
                                }

            dest_subwells[d_sw_idx] = {
                                'src_well_id': src.id,
                                'parentWell_id': dest.parentWell.id,
                                'parentWell_name': dest.parentWell.name,
                                'subwell_id':dest.id,
                                'subwell_idx':dest.idx,
                                'compound':compound.nameInternal,
                                }

        src_wells = chunk_list(src_wells,s_num_cols)
        dest_subwells = chunk_list(dest_subwells,d_num_subwells) #group subwells 1-3 into well
        dest_subwells = chunk_list(dest_subwells,d_num_cols) #group columns into row

        return {'src_plates':split_list(src_wells,num_src_plates), 
                'dest_plates':split_list(dest_subwells,num_dest_plates),
                }

    # takes in exc list of column names to exclude
    def getSoaksTable(self, exc=[]):
        from .tables import SoaksTable
        qs = self.soaks.select_related('dest__parentWell__plate','src__plate',
            ).prefetch_related('transferCompound',).order_by('id')
        return SoaksTable(qs, exclude=exc)

    def getDestPlatesGUITable(self, exc=[]):
        from .tables import DestPlatesForGUITable
        return DestPlatesForGUITable(self.plates.filter(isSource=False), exclude=exc)
    # takes in exc list of column names to exclude
    def getSrcPlatesTable(self, exc=[]):
        from .tables import PlatesTable
        # might want to implement try catch
        return PlatesTable(self.plates.filter(isSource=True), exclude=exc)

    def getDestPlatesTable(self, exc=[]):
        from .tables import PlatesTable
        # might want to implement try catch
        return PlatesTable(self.plates.filter(isSource=False), exclude=exc)

    def get_absolute_url(self):
        return "/exp/%i/" % self.id

    def __str__(self):
        return self.name

class Ingredient(models.Model):
    name = models.CharField(max_length=100,)
    manufacturer = models.CharField(max_length=100, default='')
    date_dispensed = models.DateField(default=timezone.now, blank=True)

    def __str__(self):
        return self.name

class Plate(models.Model):
    name = models.CharField(max_length=20)
    plateType = models.ForeignKey('PlateType', related_name='plates', on_delete=models.SET_NULL, null=True)
    experiment = models.ForeignKey(Experiment, related_name='plates', on_delete=models.CASCADE)
    isSource = models.BooleanField(default=False) #is it a source plate? if not, it's a dest plate
    plateIdxExp = models.PositiveIntegerField(default=1,null=True, blank=True)
    dataSheetURL = models.URLField(max_length=200, null=True, blank=True)
    echoCompatible = models.BooleanField(default=False)
    rockMakerId = models.PositiveIntegerField(unique=True, null=True, blank=True)
    dateTime = models.DateTimeField(null=True, blank=True)

    def get_absolute_url(self):
        return "/plate/%i/" % self.id
    
    @property
    def subwells(self):
        return SubWell.objects.filter(parentWell__in=self.wells.filter())
    @property
    def numCols(self):
        return self.plateType.numCols
    @property
    def numRows(self):
        return self.plateType.numRows
    @property
    def numSubwells(self):
        return self.plateType.numSubwells
    # returns number of reservoir wells
    @property 
    def numResWells(self):
        if self.plateType:
            return self.plateType.numCols * self.plateType.numRows

    class Meta:
        ordering = ('id',)
        constraints = [
            models.UniqueConstraint(fields=['plateIdxExp', 'isSource', 'experiment'], name='unique_src_dest_plate_idx')
        ]
        # unique_together = ('plateIdxExp', 'isSource', 'experiment')

    # creates appropriate wells for plate instance
    def createPlateWells(self):
        wells = None
        plateType = self.plateType
        wellDict = plateType.wellDict
        well_lst = [None]*len(wellDict)
        if plateType:
            for key, val in wellDict.items():
                well_props = val
                wellIdx = well_props['wellIdx']
                wellRowIdx = well_props['wellRowIdx']
                wellColIdx = well_props['wellColIdx']

                well_lst[wellIdx] = Well(name=key, wellIdx=wellIdx, wellRowIdx=wellRowIdx, wellColIdx=wellColIdx,
                    maxResVol=130, minResVol=10, plate_id=self.pk)

            Well.objects.bulk_create(well_lst)
            wells = self.wells.all()
            numSubwells = plateType.numSubwells
            if numSubwells:
                for w in wells:
                    subwells_lst = [None]*numSubwells
                    for i in range(numSubwells):
                        subwells_lst[i] = SubWell(idx=i+1,xPos= 0,yPos=0, parentWell_id=w.pk)
                    SubWell.objects.bulk_create(subwells_lst)
        return wells

@receiver(post_save, sender=Plate)
def createPlateWells(sender, instance, created, **kwargs):
    if created: # we only want to create wells and subwells once for plates on model creation
        instance.createPlateWells()
    return 

class PlateType(models.Model):
    name = models.CharField(max_length=30, default="",unique=True) 
    numCols = models.PositiveIntegerField(default=12, 
        validators=[
            MaxValueValidator(99),
            MinValueValidator(12)
        ])
    numRows = models.PositiveIntegerField(default=8, 
        validators=[
            MaxValueValidator(99),
            MinValueValidator(8)
        ])
    isSource = models.BooleanField(default=False) #is it a source plate? if not, it's a dest plate
    numSubwells = models.PositiveIntegerField(default=0) # num subwells per well
    # x and y synonmous with row and col respectively
    xPitch = models.DecimalField(max_digits=10, decimal_places=3) # pitch in x direction of wells [mm]
    yPitch = models.DecimalField(max_digits=10, decimal_places=3) # pitch in y direction of wells [mm]
    plateHeight = models.DecimalField(max_digits=10, decimal_places=3) # height of plate
    plateWidth = models.DecimalField(max_digits=10, decimal_places=3) #width of plate
    plateLength = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    wellDepth = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    xOffsetA1 = models.DecimalField(max_digits=10, decimal_places=3) #x postion of center of well A1 relative to top left corner of plate
    yOffsetA1 = models.DecimalField(max_digits=10, decimal_places=3) #y postion of center of well A1 relative to top left corner of plate
    dataSheetURL = models.URLField(max_length=200, null=True, blank=True)
    echoCompatible = models.BooleanField(default=False, null=True, blank=True)
    isSBS = models.BooleanField(default=True)

    maxResVol = models.DecimalField(max_digits=10, decimal_places=0, default=1000) #in uL
    minResVol = models.DecimalField(max_digits=10, decimal_places=0, default=50) #in uL

    maxDropVol = models.DecimalField(max_digits=10, decimal_places=0,default=5.0) #in uL
    minDropVol = models.DecimalField(max_digits=10, decimal_places=0, default=0.5) #in uL

    # returns number of reservoir wells
    @property 
    def numResWells(self):
        return self.numCols * self.numRows
    
    @property
    def numSubwellsTotal(self):
        return self.numResWells * self.numSubwells

    @property
    def wellDict(self):
        return createWellDict(self.numRows, self.numCols)

    def __str__(self):
        return self.name

    @classmethod
    def createEchoSourcePlate(cls):
        try: 
            instance = cls(
                name="Echo 384-well source plate",
                numRows=16,
                numCols=24,
                xPitch = 4.5,
                yPitch = 4.5,
                plateLength = 127.76,
                plateWidth = 85.48,
                plateHeight = 10.48,
                xOffsetA1 = 12.13,
                yOffsetA1 = 8.99,
                echoCompatible=True,
                isSource=True,
                dataSheetURL=''
            )
            instance.save()
        except:
            pass
        return instance

    @classmethod
    def create96MRC3DestPlate(cls):
        try:
            instance = cls(
                name="Swiss MRC-3 96 well microplate",
                numRows=8,
                numCols=12,
                numSubwells = 3,
                xPitch = 9,
                yPitch = 9,
                plateLength = 127.5,
                plateWidth = 85.3,
                plateHeight = 11.7,
                xOffsetA1 = 16.1,
                yOffsetA1 = 8.9,
                echoCompatible=True,
                isSource=False,
                dataSheetURL=''
            )
            instance.save()
        except:
            pass
        return instance

class Well(models.Model):
    validWellName = RegexValidator(regex=r'^[A-Z]\d{2}$', message='Enter valid well name')
    name = models.CharField(max_length=3, 
        validators=[validWellName]
        ) #format should be A01, X10, etc.
    compounds = models.ManyToManyField(Compound, related_name='wells', blank=True) #can a well have more than one compound???
    maxResVol = models.DecimalField(max_digits=10, decimal_places=0)
    minResVol = models.DecimalField(max_digits=10, decimal_places=0)
    plate = models.ForeignKey(Plate, on_delete=models.CASCADE, related_name='wells',null=True, blank=True)
    screen_ingredients = models.ManyToManyField(Ingredient, related_name='wells', blank=True)
    wellIdx = models.PositiveIntegerField(default=0)
    wellRowIdx = models.PositiveIntegerField(default=0)
    wellColIdx = models.PositiveIntegerField(default=0)

    @property
    def numSubwells(self):
        return self.subwells.count()

    def __str__(self):
        return str(self.plate.plateIdxExp) + '_' + self.name

    class Meta:
        ordering = ('wellRowIdx','wellColIdx')
        constraints = [
            models.UniqueConstraint(fields=['plate_id', 'name'], name='unique_well_name_in_plate')
        ]
        # unique_together = ('plate', 'name',) #ensure that each plate has unique well names

class SubWell(models.Model):
    validSubwellName = RegexValidator(regex=r'^[A-Z]\d{2}$', message='Enter valid well name')
    name = models.CharField(max_length=3, 
        validators=[validSubwellName]
        )
    idx = models.PositiveIntegerField(default=1) #CHANGE TO 0-indexed?
    xPos = models.DecimalField(max_digits=10, decimal_places=2,default=0) # relative to center of well
    yPos = models.DecimalField(max_digits=10, decimal_places=2,default=0)
    maxDropVol = models.DecimalField(max_digits=10, decimal_places=0,default=5.0) #in uL
    minDropVol = models.DecimalField(max_digits=10, decimal_places=0, default=0.5) #in uL
    parentWell = models.ForeignKey(Well,on_delete=models.CASCADE, related_name='subwells',null=True, blank=True)
    compounds = models.ManyToManyField(Compound, related_name='subwells', blank=True)
    protein = models.CharField(max_length=100, default="")
    hasCrystal = models.BooleanField(default=True)
    useSoak = models.BooleanField(default=False)

    
    def __str__(self):
        return repr(self.parentWell) + "_" + str(self.idx)

    class Meta:
        # ordering = ('idx',)
        constraints = [
            models.UniqueConstraint(fields=['parentWell_id', 'idx'], name='unique_subwell_in_well')
        ]
        # unique_together = ('parentWell', 'idx',) 

class Soak(models.Model):
    experiment = models.ForeignKey(Experiment,on_delete=models.CASCADE,null=True, blank=True, related_name='soaks',)
    
    dest = models.OneToOneField(SubWell, on_delete=models.CASCADE,null=True, blank=True, related_name='soak',)
    src = models.OneToOneField(Well, on_delete=models.CASCADE,null=True, blank=True, related_name='soak',)
    transferCompound = models.ForeignKey(Compound, on_delete=models.CASCADE,null=True, blank=True, related_name='soaks',)
    
    soakOffsetX = models.DecimalField(max_digits=10, decimal_places=2,default=0, validators=[MinValueValidator(0.0)])
    soakOffsetY = models.DecimalField(max_digits=10, decimal_places=2,default=0, validators=[MinValueValidator(0.0)])
    soakVolume = models.DecimalField(max_digits=10, decimal_places=2, default=25, validators=[MinValueValidator(0.0)]) # in nL

    drop_x = models.DecimalField(max_digits=6, decimal_places=2,default=0, validators=[MinValueValidator(0.0)]) #in um
    drop_y = models.DecimalField(max_digits=6, decimal_places=2,default=0, validators=[MinValueValidator(0.0)]) #in um
    drop_radius = models.DecimalField(max_digits=6, decimal_places=2,default=0, validators=[MinValueValidator(0.0)]) #in um

    well_x = models.DecimalField(max_digits=6, decimal_places=2,default=0, validators=[MinValueValidator(0.0)]) #in um
    well_y = models.DecimalField(max_digits=6, decimal_places=2,default=0, validators=[MinValueValidator(0.0)]) #in um
    well_radius = models.DecimalField(max_digits=6, decimal_places=2,default=0, validators=[MinValueValidator(0.0)]) #in um

    useSoak = models.BooleanField(default=False)
    saveCount = models.PositiveIntegerField(default=0)

    @property
    def transferVol(self):
        return RadiusToVolume(float(self.drop_radius) * UM_TO_PIX) #arg should be in pixels, return should be in uL

    @property 
    def offset_XY_um(self):
        """Retuns the computed offset of the target soak relative to the target well"""
        drop_xyr = self.drop_XYR_um
        well_xyr = self.well_XYR_um
        return [drop_xyr[0] - well_xyr[0], drop_xyr[1] - well_xyr[1]]

    @property
    def soak_XYR_um(self):
        """"""
        return list(map(lambda x: float(x), [self.soakOffsetX, self.soakOffsetY, VolumeToRadius(self.soakVolume)]))

    @property
    def well_XYR_um(self):
        """Returns the target well x, y, and radius in pixels"""
        return list(map(lambda x: float(x), [self.well_x, self.well_y, self.well_radius]))

    @property
    def well_XYR_pix(self):
        """Returns the target well x, y, and radius in pixels"""
        return mapUmToPix([self.well_x, self.well_y, self.well_radius])
    
    @property
    def drop_XYR_um(self):
        """Returns the target drop x, y, and radius in pixels"""
        return list(map(lambda x: float(x), [self.drop_x, self.drop_y, self.drop_radius]))

    @property
    def drop_XYR_pix(self):
        """Returns the target drop x, y, and radius in pixels"""
        return mapUmToPix([self.drop_x, self.drop_y, self.drop_radius])

    def __str__(self):
        return self.experiment.name + "_soak_" + str(self.id)


# HELPER FUNCTIONS -----------------------------------------------------

def createWellDict(numRows, numCols):
    numWells = numRows * numCols
    letters = gen_circ_list(list(string.ascii_uppercase), numWells)
    wellNames = [None] *  numWells
    wellProps = [None] * numWells
    wellIdx = 0
    for rowIdx in range(numRows):
        for colIdx in range(numCols):
            let = letters[rowIdx]
            num = str(colIdx + 1)
            if (len(num)==1):
                num = "0" + num
            s = let + num
            wellNames[wellIdx] = s
            wellProps[wellIdx] = {
                'wellIdx':wellIdx,
                'wellRowIdx':rowIdx,
                'wellColIdx':colIdx,
            }
            wellIdx += 1
    return dict(zip(wellNames, wellProps))


# SIGNALS -----------------------------------------------------
@receiver(post_save, sender=Experiment)
def delete_plates_soaks_on_library_change(sender, instance, created, **kwargs):
    """
    Delete experiment plates and soaks on library change
    """
    if instance.prev_library_id != instance.library_id and not(created):
        instance.plates.all().delete()
        instance.soaks.all().delete()
        reset = {'srcPlateType':None, 'destPlateType':None, 'subwell_locations':[]}
        Experiment.objects.filter(id=instance.id).update(**reset) # does not call save() so not signals emitted
        # set state of current library
        instance.prev_library_id = instance.library_id

@receiver(post_save, sender=Experiment)
def create_plates_and_soaks_init_data(sender, instance, created, **kwargs):
    """
    If initData PrivateFile exists, try to create plates and soaks from it
    """
    # #print('in create_plates_and_soaks_init_data: ')
    #print(bool(instance.initData_id) and (instance.prev_initData_id != instance.initData_id or created))
    if instance.initData_id and (instance.prev_initData_id != instance.initData_id or created):
        # try:
            # read file and save to JSON field initDataJSON
        post_save.disconnect(create_plates_and_soaks_init_data, sender=Experiment)
        data_json = str(instance.initData.local_upload.read(), encoding='utf-8').replace("'", "\"") #needs double quotes to parse correctly
        instance.initDataJSON = json.loads(data_json)
        instance.save()

        # set state of current initData
        instance.prev_initData_id = instance.initData_id

        post_save.connect(create_plates_and_soaks_init_data, sender=Experiment)
        instance.createPlatesSoaksFromInitDataJSON()
        # except Exception as e:
            # #print(e)

@receiver(post_init, sender=Experiment) #TODO should this be pre_save signal?
def remember_experiment_state(sender, instance, **kwargs):
    # if instance.library_id:
    instance.prev_library_id = instance.library_id
    # if instance.initData_id:
    instance.prev_initData_id = instance.initData_id

@receiver(pre_save, sender=Soak)
def increment_save_count(sender, instance, **kwargs):
    # #print(instance.saveCount)
    instance.saveCount += 1
