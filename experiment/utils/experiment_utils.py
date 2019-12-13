from django.apps import apps
from django.db import transaction, IntegrityError
from my_utils.orm_functions import bulk_add, bulk_one_to_one_add
from my_utils.utility_functions import lists_diff, lists_equal
from django.db.models import F
from my_utils.utility_functions import chunk_list, items_at, ceiling_div, gen_circ_list, \
    PIX_TO_UM, UM_TO_PIX, IMG_SCALE, VolumeToRadius, RadiusToVolume, \
        mapUmToPix, mapPixToUm, group_objs_lists_by, interleave, priority_interleave
from django.utils.timezone import make_aware
from datetime import datetime
from ..querysets import plate_soaks

import json 
import csv 

Soak = apps.get_model('experiment', 'Soak')
Library = apps.get_model('lib', 'Library')
Compound = apps.get_model('lib', 'Compound')
Plate = apps.get_model('experiment', 'Plate')
Well = apps.get_model('experiment', 'Well')
SubWell = apps.get_model('experiment', 'SubWell')
Experiment = apps.get_model('experiment', 'Experiment')


def importTemplateSourcePlates(self, templateSrcPlates):
    """
    Makes new source plates from template source plates, usually with compounds

    Parameters:
    templateSrcPlates (list): list of plates that are template and source
    """
    plates = self.makeSrcPlates(len(templateSrcPlates))
    for p1, p2 in zip(plates, templateSrcPlates):
        p1.copyCompoundsFromOtherPlate(p2)

def createSrcPlatesFromLibFile(self, numPlates=0, file=None, file_reader=None):
    """
    Creates source plates from CSV file (https://docs.google.com/spreadsheets/d/1FRBm6wVNSpwg4d3zGCYKLQkEZjf4BP9JL0YkEJzSojw/edit?usp=sharing)
    Then update wells with the appropriate compounds specified from csv file

    Parameters:
    numPlates (int): number of empty plates to make
    file (uploaded file): CSV file to update wells with appropriate compounds (see example file above)
    """
    exp = self
    if not(file_reader):
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
                
                if int(row[plate_idx_idx]) not in plateIdxRange:
                    raise IntegrityError

                compound_dict[row[zinc_id_idx]] = {
                    'plate_idx': row[plate_idx_idx],
                    'well_name':row[well_idx],
                }
            grouped_compound_dict_by_plate  = {}
            for k, v in compound_dict.items():
                plate = grouped_compound_dict_by_plate.get(v['plate_idx'], None)
                if not(plate):
                    grouped_compound_dict_by_plate[v['plate_idx']] = {v['well_name']:k}
                else:
                    plate.update({v['well_name']:k})
                    
                # grouped_compound_dict.setdefault(v['plate_idx'], []).append(key)
            #retrieve existing compounds 
            compounds_existed = [c for c in Compound.objects.filter(zinc_id__in=compound_dict.keys())]
            zincs_existed = [c.zinc_id for c in compounds_existed]

            zincs_created = lists_diff(compound_dict.keys(), zincs_existed)

            compounds = [Compound(zinc_id=z) for z in zincs_created]
            compounds_created = Compound.objects.bulk_create(compounds)
            
            compounds_all = []
            compounds_all.extend(compounds_created)
            compounds_all.extend(compounds_existed)
            well_compounds_dict = {}
            for c in compounds_all:
                key_ = compound_dict[c.zinc_id]['plate_idx'] + '_' + compound_dict[c.zinc_id]['well_name']
                well_compounds_dict[key_] = c
            well_compounds_ids = [well_compounds_dict[k_].id for k_ in well_compounds_dict.keys()]
            
            #retrieve and update existing wells with appropriate compound
            wells_qs = Well.objects.filter(plate__in=platesMade
                ).select_related('plate'
                ).prefetch_related('compounds'
                ).annotate(plate_idx=F('plate__plateIdxExp'))
            wells_dict = {}
            
            for w in wells_qs:
                wells_dict[str(w.plate_idx) + '_' + w.name] = w

            for k in well_compounds_dict.keys():
                wells_dict[k].compound_id = well_compounds_dict[k].id

            Well.objects.bulk_update([v for k, v in wells_dict.items()], ['compound_id'], batch_size=500)
            
    except IntegrityError as e:
        print(e)
    except KeyError as e:
        print(e)

def priorityInterleaveSrcWellsToSoaks(self, src_wells=[], soaks=[]):
    """
    Match soaks to source wells interleaved by priority and plate id

    Parameters:
    src_wells (list): List of an experiment's source wells with compounds
    soaks (list): List of an experiment's used soaks 

    Returns:
    None
    """
    src_wells = self.srcWellsWithCompounds.select_related('plate')
    wells_grouped_by_plate_id = group_objs_lists_by([w for w in src_wells], ['plate_id']).values()
    wells_interleaved = priority_interleave(wells_grouped_by_plate_id, Well.getPriorityRange())
    return matchSrcWellsToSoaks(self, wells_interleaved, soaks)

def interleaveSrcWellsToSoaks(self, src_wells=[], soaks=[]):
    """
    Match soaks to source wells interleaved by plate id

    Parameters:
    src_wells (list): List of an experiment's source wells with compounds
    soaks (list): List of an experiment's used soaks 

    Returns:
    None
    """
    src_wells = self.srcWellsWithCompounds.select_related('plate')
    wells_grouped_by_plate_id = group_objs_lists_by([w for w in src_wells], ['plate_id']).values()
    wells_interleaved = interleave(wells_grouped_by_plate_id)
    # wells_interleaved.sort(key=lambda x: x.plate.plateIdxExp)
    return matchSrcWellsToSoaks(self, wells_interleaved, soaks)

def matchSrcWellsToSoaks(self, src_wells=[], soaks=[]):
    """
    Match soaks to source wells by looping through one-by-one
    
    Parameters:
    src_wells (list): List of an experiment's source wells with compounds
    soaks (list): List of an experiment's used soaks 

    Returns:
    None
    """
    self.soak_export_date = None
    self.save()
    if not(soaks):
        soaks = [s for s in self.usedSoaks]
    if not(src_wells):
        src_wells = [w for w in self.srcWellsWithCompounds]

    min_len = min(len(soaks), len(src_wells))
    soaks_sliced = soaks[:min_len]
    src_wells_sliced = src_wells[:min_len]

    src_wells_sliced.sort(key=lambda x: x.plate.plateIdxExp)
    try:
        with transaction.atomic():
            # clear existing source wells of soaks
            for i in range(len(soaks)):
                soaks[i].src = None
            Soak.objects.bulk_update(soaks, ['src'])

            # update soaks with source wells
            for i in range(min_len):
                soaks_sliced[i].src = src_wells_sliced[i]
            Soak.objects.bulk_update(soaks_sliced, ['src'])
    except Exception as e: 
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
    src_plate_qs = self.plates.filter(isSource=True)
    for p in src_plate_qs:
        if p.isTemplate:
            self.plates.remove(p, bulk=False)
        else:
            p.delete()
    # self.plates.filter(isSource=True).delete()
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

def revertToStep(exp, step):
    def revertToStepOne(exp):
        """
        """
        # Delete dest plates in experiment 
        dest_plates = exp.plates.filter(isSource=False) 
        dest_plates.delete()
          
        # Remove soaks
        exp.soaks.remove()

    def revertToStepTwo(exp):
        """
        Delete 
        """
        # Delete src plates in experiment except ones that are templates; in that case, remove
        src_plates = exp.plates.filter(isSource=True)
        for p in src_plates:
            if p.isTemplate:
                exp.plates.remove(p)
            else:
                p.delete()  

    def revertToStepThree(exp):
        """
        Removes relationship between plates and their drop_images
        """
        dest_plates = exp.plates.filter(isSource=False).prefetch_related('drop_images')
        for p in dest_plates:
            p.removeDropImages()
            # p.drop_images.remove(*[img for img in p.drop_images.all()])

    def revertToStepFour(exp):
        """
        Remove source well from soaks
        """
        soaks = [s for s in exp.soaks.all()]
        for s in soaks:
            s.src = None
        Soak.objects.bulk_update(soaks, fields=['src'])

    def revertToStepFive(exp):
        # Remove picklist file if it exists
        exp.picklist = None
        exp.save()
    
    fxn_array = [
        revertToStepOne,
        revertToStepTwo,
        revertToStepThree,
        revertToStepFour,
        revertToStepFive,
    ]

    def apply(fxn_array, exp, step):
        for i in range(step-1, len(fxn_array)):
            print(fxn_array[i])
            fxn_array[i](exp)

    apply(fxn_array, exp, step)


def createPlatesSoaksFromInitDataJSON(self):
    exp = self
    # revertToStep(exp, 1)
    init_data_plates = exp.initDataJSON.items()
    lst_plates = exp.makePlates(len(init_data_plates), self.destPlateType)
    soaks = []
    try:
        for i, (plate_id, plate_data) in enumerate(init_data_plates):
            id = plate_data.pop("plate_id", None) 
            date_time = plate_data.pop("date_time", None)
            temp = plate_data.pop("temperature", None)
            subwells = plate_data.pop("subwells", {})
            plate = lst_plates[i]
            plate.rockMakerId = plate_id
            plate.created_date = make_aware(datetime.strptime(date_time, '%Y-%m-%d %H:%M:%S.%f'))
            plate.save()

            if subwells:
                # loop through well keys and create soaks w/ appropriate data
                for j, (subwell_key, subwell_data) in enumerate(subwells.items()):
                    well_name, s_w_idx = subwell_key.split('_')
                    well = plate.wells.filter(name=well_name)[0]
                    s_w = well.subwells.get(idx=s_w_idx) 
                    soaks.append(Soak(
                        experiment_id = exp.id,
                        dest_id = s_w.id, 
                        drop_x_initial = subwell_data['drop_x'] * PIX_TO_UM, 
                        drop_y_initial = subwell_data['drop_y'] * PIX_TO_UM,
                        drop_radius_initial = subwell_data['drop_radius'] * PIX_TO_UM,
                        well_x_initial  =  subwell_data['well_x'] * PIX_TO_UM, 
                        well_y_initial  =  subwell_data['well_y'] * PIX_TO_UM,
                        well_radius_initial  =  subwell_data['well_radius'] * PIX_TO_UM,
                        drop_x = subwell_data['drop_x'] * PIX_TO_UM, 
                        drop_y = subwell_data['drop_y'] * PIX_TO_UM,
                        drop_radius = subwell_data['drop_radius'] * PIX_TO_UM,
                        well_x =  subwell_data['well_x'] * PIX_TO_UM, 
                        well_y =  subwell_data['well_y'] * PIX_TO_UM,
                        well_radius =  subwell_data['well_radius'] * PIX_TO_UM,
                        soakOffsetX =  subwell_data['well_x'] * PIX_TO_UM, #defaults to well center
                        soakOffsetY = subwell_data['well_y'] * PIX_TO_UM,
                        # soakVolume = ,
                        useSoak= True
                    ))    
    except Exception as e:
        print(e)
    soaks = Soak.objects.bulk_create(soaks)  
    return soaks

def processPicklist(exp, f):
    """
    Takes picklist file and processes the data, updating soaks in destination plates as appropriate
    """
    from my_utils.constants import reverse_subwell_map, subwell_map
    from io import TextIOWrapper

    file_reader = csv.reader(TextIOWrapper(f), delimiter=',')
    soaks_qs = exp.soaks.select_related('dest__parentWell__plate')
    soaks_map = {}
    for soak in soaks_qs:
        soak_key = "_".join([soak.dest.parentWell.plate.rockMakerId, 
            soak.dest.parentWell.name, 
            subwell_map[soak.dest.idx]])
        soaks_map[soak_key] = soak
    from collections import OrderedDict
    rows_dict = {}
    for row in file_reader: 
        data = OrderedDict([
            ('plate_type',''),
            ('plate_id',''),
            ('location', ''),
            ('plate_row', ''),
            ('plate_column', ''),
            ('plate_subwell', ''),
            ('comment', ''),
            ('crystal_id', ''),
            ('arrival_time', ''),
            ('departure_time', ''),
            ('duration', ''),
            ('destination_name', ''),
            ('destination_location', ''),
            ('barcode', ''),
            ('external_comment', ''),
        ])
        data_keys = list(data.keys())
        for i, col in enumerate(row):
            data[data_keys[i]] = col
        tweaked_col = data['plate_column'] if len(data['plate_column'])==2 else '0' + data['plate_column']
        rows_dict["_".join([data['plate_id'],data['plate_row']+tweaked_col,data['plate_subwell']])] = data
    for k,v in rows_dict.items():
        soak = soaks_map.get(k)
        if soak:
            soak.isMounted = True
            soak.storage_position = int(v['destination_location']) if v['destination_location'] else None
            soak.shifterComment = v['comment']
            soak.shifterCrystalID = v['crystal_id']
            soak.shifterArrivalTime = make_aware(datetime.strptime(v['arrival_time'], '%Y-%m-%d %H:%M:%S.%f')) if v['arrival_time'] else None
            soak.shifterDepartureTime = make_aware(datetime.strptime(v['departure_time'], '%Y-%m-%d %H:%M:%S.%f')) if v['departure_time'] else None
            soak.barcode = v['barcode']
            soak.shifterExternalComment = v['external_comment']
    Soak.objects.bulk_update([v for k,v in soaks_map.items()], fields=['storage_position',
        'shifterComment','shifterCrystalID','shifterArrivalTime', 'shifterDepartureTime', 'barcode','shifterExternalComment'])