from django.db import models
from django.contrib.auth.models import User, Group
from django.utils import timezone
from import_ZINC.models import Library, Compound
from .exp_view_process import formatSoaks, split_list, getWellIdx, getSubwellIdx
from django.db.models.signals import post_save, post_init
from django.dispatch import receiver
from django.utils.functional import cached_property 
from orm_custom.custom_functions import bulk_add, bulk_one_to_one_add
from django.contrib.postgres.fields import ArrayField, JSONField
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db.models import Count, F, Value
from utility_functions import chunk_list, items_at, ceiling_div, gen_circ_list
import string 


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
    destPlateType = models.ForeignKey('PlateType', null=True, blank=True, on_delete=models.CASCADE,related_name='experiments_dest') #noly one dest plate type per experiment
    subwell_locations = ArrayField(
        models.PositiveSmallIntegerField(blank=True, null=True, validators=[MaxValueValidator(3), MinValueValidator(1)]),
        size=3, default=defaultSubwellLocations
        )

    class Meta:
        get_latest_by="dateTime"
        # ordering = ['-dateTime']

    @property
    def getCurrentStep(self):
        if self.soaks_valid: #might want to more robust check (e.g. # soaks = # compounds in library)
            return 4
        if self.plates_valid:
            return 3
        if self.library_valid:
            return 2
        return 1

    @property
    def getTransferPlatePairs(self):
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
    def soaks_valid(self):
        return self.soaks.count() > 0

    @property 
    def library_valid(self):
        return bool(self.library)

    @property
    def plates_valid(self):
        try:
            return self.plates.count() > 0 \
                and self.numSrcPlates == self.expNumSrcPlates() \
                    and self.numDestPlates >= self.expNumDestPlates()
        except AttributeError:
            return False

    @property
    def libCompounds(self):
        try:
            compounds = self.library.compounds.all()
            return compounds
        except AttributeError:
            return None

    @property
    def numSrcPlates(self):
        return len(self.plates.filter(isSource=True))
    
    @property
    def numDestPlates(self):
        return len(self.plates.filter(isSource=False))

    #expected number of source plates based on number of compounds in library
    def expNumSrcPlates(self):
        src_plate_type = self.srcPlateType
        num_src_wells = src_plate_type.numCols * src_plate_type.numRows
        return ceiling_div(self.libCompounds.count(), num_src_wells)
  

    #expected number of dest plates based on number of compounds in library
    def expNumDestPlates(self):
        num_subwells  = len(self.subwell_locations)
        dest_plate_type = self.destPlateType
        num_dest_wells = dest_plate_type.numCols * dest_plate_type.numRows
        return ceiling_div(self.libCompounds.count(),num_dest_wells * num_subwells)

    #get queryset of destination subwells
    @property
    def getDestSubwells(self):
        return SubWell.objects.filter(parentWell_id__in=Well.objects.filter(plate_id__in= self.plates.filter(isSource=False)))

    #get queryset of source wells
    @property
    def getSrcWells(self):
        return Well.objects.filter(plate_id__in=self.plates.filter(isSource=True))
    
    def generateSoaks(self, transferVol=25, soakOffsetX=0, soakOffsetY=0):
        self.soaks.all().delete() #start from fresh
        ct = 0
        cmpds = self.libCompounds
        list_soaks = [None]*cmpds.count()
        list_src_wells = [w for w in self.getSrcWells.order_by('id')]
        list_dest_subwells = [w for w in self.getDestSubwells.order_by('id')]
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
            p.createPlateWells()
        return 

    def formattedSoaks(self, qs_soaks,
                    s_num_rows=16, s_num_cols = 24, 
                    d_num_rows=8, d_num_cols=12, d_num_subwells=3):
        num_src_plates = self.numSrcPlates
        num_dest_plates = self.numDestPlates
        # if (num_src_plates != 0 and num_dest_plates!= 0):
        #     src_plate = src_plates[0]
        #     dest_plate = dest_plates[0]
        #     s_num_rows = src_plate.numRows 
        #     s_num_cols = src_plate.numCols
        #     d_num_rows = dest_plate.numRows
        #     d_num_cols = dest_plate.numCols
        #     d_
            
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

class CrystalScreen(models.Model):
    name = models.CharField(max_length=100,)
    manufacturer = models.CharField(max_length=100, default='')
    date_dispensed = models.DateField(default=timezone.now, blank=True)

    def __str__(self):
        return self.name

class Plate(models.Model):
    name = models.CharField(max_length=30, default="plate_name") #do I need unique?
    # formatType = models.CharField(max_length=100, null=True, blank=True)
    plateType = models.ForeignKey('PlateType', related_name='plates', on_delete=models.SET_NULL, null=True, blank=True)
    # numCols = models.PositiveIntegerField(default=12)
    # numRows = models.PositiveIntegerField(default=8)
    # numSubwells = models.PositiveIntegerField(default=0) 
    # x and y synonmous with row and col respectively
    # xPitch = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True) # pitch in x direction of wells [mm]
    # yPitch = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True) # pitch in y direction of wells [mm]
    # plateHeight = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True) # height of plate
    # plateWidth = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True) #width of plate
    # plateLength = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    # wellDepth = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    # xOffsetA1 = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True) #x postion of center of well A1 relative to top left corner of plate
    # yOffsetA1 = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True) #y postion of center of well A1 relative to top left corner of plate
    # experiments can have multiple plates, but plates can only have one experiment
    experiment = models.ForeignKey(Experiment, related_name='plates', on_delete=models.CASCADE, null=True, blank=True)
    isSource = models.BooleanField(default=False) #is it a source plate? if not, it's a dest plate
    # isTemplate = models.BooleanField(default=False,null=True, blank=True) #is it a template we want build plates from?
    # isCustom = models.BooleanField(default=False, null=True, blank=True) #is it a custom plate that the user modified (e.g. custom well offsets)
    # index of plate in certain experiment (needed for echo instruction generation)
    plateIdxExp = models.PositiveIntegerField(default=1,null=True, blank=True)
    dataSheetURL = models.URLField(max_length=200, null=True, blank=True)
    echoCompatible = models.BooleanField(default=False, null=True, blank=True)
    
    def get_absolute_url(self):
        return "/plate/%i/" % self.id
        
    @property
    def numCols(self):
        return self.plateType.numCols
    @property
    def numRows(self):
        return self.plateType.numRows
            
    # returns number of reservoir wells
    @property 
    def numResWells(self):
        if self.plateType:
            return self.numCols * self.numRows

    @property
    def wellDict(self):
        numWells = self.numResWells
        # letters = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 
        #     'L', 'M', 'N','O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X']
        letters = gen_circ_list(list(string.ascii_uppercase), numWells)
        wellNames = [None] *  numWells
        wellIdx = 0
        for rowIdx in range(self.numRows):
          for colIdx in range(self.numCols):
            let = letters[rowIdx]
            num = str(colIdx + 1)
            if (len(num)==1):
                num = "0" + num
            s = let + num
            wellNames[wellIdx] = s
            wellIdx += 1
        return dict(zip(wellNames, range(numWells))) 

    def __str__(self):
        return self.name

    class Meta:
        ordering = ('id',)
    
    def createPlateWells(self):
        # creates appropriate wells for plate instance
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

                # self.wells.create(name=key, maxResVol=130, minResVol=10)
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
    numCols = models.PositiveIntegerField(default=12)
    numRows = models.PositiveIntegerField(default=8)
    isSource = models.BooleanField(default=False) #is it a source plate? if not, it's a dest plate
    numSubwells = models.PositiveIntegerField(default=0) 
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
    def wellDict(self):
        numWells = self.numResWells
        # letters = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 
        #     'L', 'M', 'N','O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X']
        letters = gen_circ_list(list(string.ascii_uppercase), numWells)
        wellNames = [None] *  numWells
        wellProps = [None] * numWells
        wellIdx = 0
        for rowIdx in range(self.numRows):
          for colIdx in range(self.numCols):
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

    def __str__(self):
        return self.name

    @classmethod
    def createEchoSourcePlate(cls):
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
        return instance

    @classmethod
    def create96MRC3DestPlate(cls):
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
        return instance

class Well(models.Model):
    name = models.CharField(max_length=4) #format should be A01, X10, etc.
    compounds = models.ManyToManyField(Compound, related_name='wells', blank=True) #can a well have more than one compound???
    maxResVol = models.DecimalField(max_digits=10, decimal_places=0)
    minResVol = models.DecimalField(max_digits=10, decimal_places=0)
    plate = models.ForeignKey(Plate, on_delete=models.CASCADE, related_name='wells',null=True, blank=True)
    crystal_screen = models.ForeignKey(CrystalScreen, on_delete=models.CASCADE,related_name='wells',null=True, blank=True)
    wellIdx = models.PositiveIntegerField(default=0)
    wellRowIdx = models.PositiveIntegerField(default=0)
    wellColIdx = models.PositiveIntegerField(default=0)

    @property
    def numSubwells(self):
        return len(self.subwells)

    def __str__(self):
        return "plate_" + str(self.plate.id) + "_" + self.name

    class Meta:
        ordering = ('wellIdx',)

class SubWell(models.Model):
    #relative to A1 well center
    idx = models.PositiveIntegerField(default=1) #CHANGE TO 0-indexed?
    xPos = models.DecimalField(max_digits=10, decimal_places=2,default=0) # relative to center of well
    yPos = models.DecimalField(max_digits=10, decimal_places=2,default=0)
    maxDropVol = models.DecimalField(max_digits=10, decimal_places=0,default=5.0) #in uL
    minDropVol = models.DecimalField(max_digits=10, decimal_places=0, default=0.5) #in uL
    parentWell = models.ForeignKey(Well,on_delete=models.CASCADE, related_name='subwells',null=True, blank=True)
    compounds = models.ManyToManyField(Compound, related_name='subwells', blank=True)
    protein = models.CharField(max_length=100, default="")
    hasCrystal = models.BooleanField(default=False)

    def __str__(self):
        return repr(self.parentWell) + "Subwell_" + str(self.idx)

    class Meta:
        ordering = ('idx',)

class Soak(models.Model):
    experiment = models.ForeignKey(Experiment,on_delete=models.CASCADE,null=True, blank=True, related_name='soaks',)
    
    dest = models.OneToOneField(SubWell, on_delete=models.CASCADE,null=True, blank=True, related_name='soak',)
    src = models.OneToOneField(Well, on_delete=models.CASCADE,null=True, blank=True, related_name='soak',)
    transferCompound = models.ForeignKey(Compound, on_delete=models.CASCADE,null=True, blank=True, related_name='soaks',)
    transferVol = models.PositiveIntegerField(default=25) # in nL
    #relative to center of subwell
    soakOffsetX = models.DecimalField(max_digits=10, decimal_places=2,default=0)
    soakOffsetY = models.DecimalField(max_digits=10, decimal_places=2,default=0)
    targetWellX = models.DecimalField(max_digits=10, decimal_places=2,default=0)
    targetWellY = models.DecimalField(max_digits=10, decimal_places=2,default=0)
    targetWellRadius = models.DecimalField(max_digits=10, decimal_places=2,default=0)

    useSoak = models.BooleanField(default=False)
    
    @property
    def soakRadius(self):
        # returns radius of soak based on some calibration curve of soak volume to radius
        return self.transferVol

    def __str__(self):
        return "soak_" + str(self.id)

def createWellDict(numCol, numRow):
    numWells = numRow * numCol
    letters = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 
        'L', 'M', 'N','O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X']

    wellNames = [None] *  numWells

    wellIdx = 0
    for colIdx in range(numCol):
      for rowIdx in range(numRow):
        s = letters[rowIdx] + str(colIdx + 1)
        wellNames[wellIdx] = s
        wellIdx += 1

    return dict(zip(wellNames, range(numWells)))

def enum_well_location(s):
    # format needs to be [letter][0-9][0-9]
    letters = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N',
                'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X']
    lettersRange = range(len(letters))
    dic = dict(zip(letters, lettersRange))
    l, d = s[0], s[0:2]

    if len(s) != 3:
        return 
    else:
        return dic[l] + int(d)

# SIGNALS -----------------------------------------------------
#delete experiment plates and soaks on library change
@receiver(post_save, sender=Experiment)
def delete_plates_soaks_on_library_change(sender, instance, created, **kwargs):
    if instance.prev_library_id != instance.library.id or created:
        instance.plates.all().delete()
        instance.soaks.all().delete()
        reset = {'srcPlateType':None, 'destPlateType':None, 'subwell_locations':[]}
        Experiment.objects.filter(id=instance.id).update(**reset)

@receiver(post_init, sender=Experiment)
def remember_library(sender, instance, **kwargs):
    try:
        if instance.library.id:
            instance.prev_library_id = instance.library.id
    except Library.DoesNotExist: # added to fix case where experiment has no library when first creating experiment
        pass