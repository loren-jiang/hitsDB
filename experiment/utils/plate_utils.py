from django.apps import apps
from django.db import transaction, IntegrityError

Plate = apps.get_model('experiment', 'Plate')
Well = apps.get_model('experiment', 'Well')
SubWell = apps.get_model('experiment', 'SubWell')


def createPlateWells(self):
    """
    TODO: write DOCSTRING
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

def updateCompounds(self, compounds, compound_dict={}):
    if compounds:
        my_wells = [w for w in self.wells.all().order_by('name')]
        num_my_wells = len(my_wells)
        num_compounds = len(compounds)
        assert num_compounds >= num_my_wells
        
        if compound_dict:
            pass
        else: #no compound_dict provided so update one-by-one in order
            for i in range(num_my_wells):
                my_wells[i].compound = compounds[i] 
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