from functools import reduce 
from operator import mul

def reshape(lst, shape):
    if len(shape) == 1:
        return lst
    n = reduce(mul, shape[1:])
    return [reshape(lst[i*n:(i+1)*n], shape[1:]) for i in range(len(lst)//n)]

def polynomial(coeff):
    def apply(coeff, x):
        ret = 0
        for i, c in enumerate(coeff):
            ret += c * x**i
        return ret 
    return lambda x: apply(coeff, x)

def RadiusToVolume(x):
    coeff = [
        -5.3743703571317667e-6,
        3.8296724440466813e-2,
        2.1381856713576437e-5,
        8.5669944196377545e-7,
        -5.7076472737908041e-16,
        2.5941761345047031e-19
    ]
    return polynomial(coeff)(float(x))

def VolumeToRadius(x):
    coeff = [     
        6.1417074854930405e1,
        1.0073950737908067e1,
        -1.2531131468153611e-1,
        9.1304741996519126e-4,
        -3.2477314052641414e-6,
        4.4142610214669469e-9
    ]
    return polynomial(coeff)(float(x))

### GLOBAL CONSTANTS 
PIX_TO_UM = 2.77; #conversion factor 2.77 µm/pixel at full size
UM_TO_PIX = 1/PIX_TO_UM
STROKE_WIDTH = 4; # pixels
IMG_SCALE = 2.45; #1024 px / 418 px 


def mapUmToPix(lst):
    return list(map(lambda x: float(x)*UM_TO_PIX, lst))

def mapPixToUm(lst):
    return list(map(lambda x: float(x)*PIX_TO_UM, lst))

#turns list into sublists of size n using generator
def chunks(l, n):
    """Yield successive n-sized chunks from l."""
    for i in range(0, len(l), n):
        yield l[i:i + n]


#turns list into sublists of size n using list comprehension
def chunk_list(l,n):
    return [l[i * n:(i + 1) * n] for i in range((len(l) + n - 1) // n )] 

#get items at positions specified by idxs 
#max(idxs) < chunk_size
#len(lst) must be divisible by chunk_size
def items_at(lst, chunk_size, idxs):
    assert max(idxs) < chunk_size
    assert len(lst) % chunk_size == 0
    chunked = chunk_list(lst, chunk_size)
    num_elems = len(idxs)*len(chunked)
    out = [None] * num_elems
    i = 0
    for c in chunked:
        for k in idxs:
            out[i] = c[k]
            i += 1
    return out


def ceiling_div(x,y):
    return -(-x // y)

def gen_circ_list(lst, num_el):
    if lst:
        ret_lst = lst.copy()
        length = len(lst)
        num_extra_lsts = ceiling_div(num_el, length) - 1
        extra_lsts = []

        for j in range(num_extra_lsts):
            extra_lsts.extend(map(lambda x: x * (j+2), lst))

        ret_lst.extend(extra_lsts)
        ret_lst = ret_lst[0:num_el]
        return ret_lst
