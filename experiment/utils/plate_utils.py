from django.apps import apps
from django.db import transaction, IntegrityError
import string
from my_utils.utility_functions import gen_circ_list, ceiling_div

Plate = apps.get_model('experiment', 'Plate')
Well = apps.get_model('experiment', 'Well')
SubWell = apps.get_model('experiment', 'SubWell')


def createPlateWells(self):
    """
    Assuming self.plateType exists, this function populates the plate with the appropriate wells and/or subwells
    """
    wells = None
    plateType = self.plateType
    
    if plateType:
        wellDict = plateType.wellDict
        well_lst = [None]*len(wellDict)
        for key, val in wellDict.items():
            well_props = val
            wellIdx = well_props['wellIdx']
            wellRowIdx = well_props['wellRowIdx']
            wellColIdx = well_props['wellColIdx']

            well_lst[wellIdx] = Well(name=key, wellIdx=wellIdx, wellRowIdx=wellRowIdx, wellColIdx=wellColIdx,
                maxResVol=130, minResVol=10, plate=self)

        Well.objects.bulk_create(well_lst)
        wells = self.wells.all()
        numSubwells = plateType.numSubwells
        if numSubwells:
            for w in wells:
                subwells_lst = [None]*numSubwells
                for i in range(numSubwells):
                    subwells_lst[i] = SubWell(name=w.name+'_'+str(i+1), idx=i+1,xPos= 0,yPos=0, parentWell=w)
                SubWell.objects.bulk_create(subwells_lst)
    return wells

def updateCompounds(plate, compounds, compounds_dict={}):
    """
    Update plate with list of compounds; number of compounds should be less than or equal to number of plate's wells

    Parameters:
    plate (Plate): instance of Plate model
    compounds (list): list of compounds
    compounds_dict (dictionary): dictionary of compounds that maps a compound to certain well; key is zinc_id and val is well name
    """
    if compounds:
        my_wells = [w for w in plate.wells.all().order_by('name')]
        num_my_wells = len(my_wells)
        num_compounds = len(compounds)
        assert num_compounds <= num_my_wells
        ordered_compounds = compounds
        if compounds_dict:
            my_wells_map = dict([(w.name, idx) for idx, w in enumerate(my_wells)])
            temp = [None]*num_compounds
            for c in compounds:
                idx = my_wells_map[compounds_dict[c.zinc_id]]
                temp[idx] = c
            ordered_compounds = temp
        for i in range(num_compounds):
            my_wells[i].compound = ordered_compounds[i] 
        Well.objects.bulk_update(my_wells, fields=['compound'])

def copyCompoundsFromOtherPlate(self, plate):
    """
    Takes other plate (isTemplate must be True) and copy its compounds in the appropriate well locations
    """
    assert plate.isTemplate #only template plates can be copied from 
    compounds_to_copy = [c for c in plate.compounds.all()]
    if compounds_to_copy:
        my_wells = [w for w in self.wells.all().order_by('name')]
        num_my_wells = len(my_wells)
        num_compounds = len(compounds_to_copy)
        assert num_compounds >= num_my_wells

        for i in range(num_my_wells):
            my_wells[i].compound = compounds_to_copy[i] 
        Well.objects.bulk_update(my_wells, fields=['compound'])

def getRowIdxFromWellLetter(c):
    letters = [c for c in string.ascii_lowercase]
    num_letters = len(letters)
    letters = dict([(tup[1], tup[0]) for tup in enumerate(letters)])
    c = c.lower()
    num_chars = len(c)
    return num_letters*(num_chars-1) + (letters.get(c[num_chars-1]) + 1) 

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