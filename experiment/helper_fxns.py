from django.contrib.auth.models import User, Group
from django.http import HttpResponse 
from django.shortcuts import render, redirect, get_object_or_404
from .models import Experiment, Library, Compound, Plate, Well, SubWell, Soak
from django.core.serializers.json import DjangoJSONEncoder
from django.core.serializers import serialize

def ceiling_div(x,y):
    return -(-x // y)

#takes a one-dimensional coordinates and converts it two 2-dimensional coordinates
def twoD_idx(idx, width):
    x = idx // width
    y = idx % width
    return x, y

#turns list into sublists of size n
def chunk_list(oneD_lst,n):
    return [oneD_lst[i * n:(i + 1) * n] for i in range((len(oneD_lst) + n - 1) // n )] 

#splits list into the number of wanted_parts
def split_list(alist, wanted_parts=1):
    length = len(alist)
    return [ alist[i*length // wanted_parts: (i+1)*length // wanted_parts] 
             for i in range(wanted_parts) ]

def parsePlate(p):
    qs = p.wells.select_related('plate','crystal_screen').prefetch_related('compounds',
            'dest_subwells__parentWell',)

    wells = [w for w in qs]
    data = [[None]*p.numCols for _ in range(p.numRows)]
    idx = 0
    for j in range(len(data)):
        for k in range(len(data[j])):
            data[j][k] = wells[idx]
            idx += 1
    return data

def getWellIdx(plateIdx, wellIdx, numWells=384):
    if wellIdx > numWells:
        wellIdx = numWells
    well_index = (plateIdx-1)*numWells + (wellIdx-1)
    return well_index

def getSubwellIdx(plateIdx, wellIdx, subwellIdx=0, numWells=96, numSubwells=3):
    if wellIdx > numWells:
        wellIdx = numWells
    if subwellIdx > numSubwells:
        subwellIdx = numSubwells

    well_index = ((plateIdx-1)*numWells + wellIdx-1)
    return  well_index*numSubwells + (subwellIdx - 1)

def formatSoaks(soaks,num_src_plates, num_dest_plates):
    soaks_lst = [soak for soak in soaks]
    # first_dest_well = Well.objects.get(soaks_lst[0].dest.parentWell.id)
    # soaks_json = serialize('json',soaks,cls=DjangoJSONEncoder)
    # src_iter = iter(srcs)
    # dest_iter = iter(dests)
    # compound_iter = iter(compounds)

    src_wells = [0]*num_src_plates*384
    dest_subwells = [0]*num_dest_plates*96*3
    subwells = [0]*3 #three subwells locations
    for j in range(len(soaks_lst)):
        # try:
        s = soaks_lst[j]
        src = s.src
        src_well_idx = src.wellIdx
        src_plate_idx = src.plate.plateIdxExp
        s_w_idx = getWellIdx(src_plate_idx,src_well_idx,384)

        dest = s.dest
        dest_subwell_idx = dest.idx
        dest_parentwell_idx = dest.parentWell.wellIdx
        dest_plate_idx = dest.parentWell.plate.plateIdxExp
        d_sw_idx = getSubwellIdx(dest_plate_idx,dest_parentwell_idx,
            dest_subwell_idx,96,3)
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
        # except:
        #     break

    src_wells = chunk_list(src_wells,24)
    dest_subwells = chunk_list(dest_subwells,3) #group subwells 1-3 into well
    dest_subwells = chunk_list(dest_subwells,12) #group columns into row

    return {'src_plates':split_list(src_wells,num_src_plates), 
            'dest_plates':split_list(dest_subwells,num_dest_plates),
            }