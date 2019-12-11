from functools import reduce 
from operator import mul
from collections import defaultdict

def reverse_dict(dic, prop=''):
    if prop:
        return dict([(v.get(prop),k) for k,v in dic.items()])    
    return dict([(v,k) for k,v in dic.items()])

def insert_every_nth(lst, nth, item, offset=0):
    """
    Inserts item at every nth position in list

    Parameters:
    lst (list): a list to insert into
    nth (nth): one-indexed integer position to insert at
    item (obj): item to insert
    """
    new_list = []
    for start_index in range(offset, len(lst), nth):
        new_list.extend(lst[start_index:start_index+nth])
        new_list.append(item)
    new_list.pop()
    return new_list

def group_list_by(lst, attrs, separator='_'):
    if lst:
        if type(lst[0]) is dict:
            return group_dicts_list_by(lst, attrs, separator)
        else:
            return group_objs_lists_by(lst, attrs, separator)
    else:
        return lst

def group_dicts_list_by(lst, attrs, separator='_'):
    groups = defaultdict(list)
    for obj in lst:
        keys = [str(obj.get(attr, '')) for attr in attrs]
        cleaned_key  = separator.join(keys)
        groups[cleaned_key].append(obj)
    return groups

def group_objs_lists_by(lst, attrs, separator='_'):
    groups = defaultdict(list)
    for obj in lst:
        keys = [str(getattr(obj, attr, '')) for attr in attrs]
        cleaned_key  = separator.join(keys)
        groups[cleaned_key].append(obj)
    return groups

def get_max_len(lsts):
    return max(list(map(lambda lst: len(lst), lsts)))

def interleave(lsts):
    """
    Takes n lists and interleaves them. If one list is longer, then the remainder of that list is appended
    """
    max_len = get_max_len(lsts)

    lsts = list(map(lambda x: none_pad(x, max_len), lsts))
    ret = []
    for k in range(max_len):
        temp = list(map(lambda x: x[k], lsts))
        ret.extend(temp)
    return remove_falsey_values(ret)

def priority_interleave(lsts, priority_range=None, is_lst_of_dicts=False):
    if priority_range:
        ret = []
        for p in [str(k) for k in priority_range]:
            sublist = []
            for el in list(map( lambda x: group_list_by(x, ['priority']), lsts)):
                x = el.get(p, None)
                if x: 
                    sublist.append(x)
            if sublist:
                ret.extend(interleave(sublist))
        return ret
    else:
        return(interleave(lsts))

def remove_falsey_values(lst):
    """
    Remove values that evaluate to false from lst
    """
    return list(filter(lambda x: x, lst))

def none_pad(lst, k):
    """
    'None' pad list to desired length k
    """
    diff = k - len(lst)
    assert diff >= 0
    lst += [None] * (diff)
    return lst


def shuffleDict(d):
    """
    Shuffles key, value pairs of dictionary, maintaining uniqueness
    """
    import random
    d_ = d.copy()
    items = list([ [k,v] for k,v in d_.items() ])
    random.shuffle(items)
    i = 0
    for k in d_.keys():
      items[i][0] = k
      i += 1
    return dict(items)

def lists_equal(L1, L2):
    """
    Checks if two lists are equal
    """
    return len(L1) == len(L2) and sorted(L1) == sorted(L2)

def lists_diff(list1, list2):
    """
    Returns the difference of two lists 
    """
    return list(set(list1).symmetric_difference(set(list2)))  # or return list(set(list1) ^ set(list2))

def missing_list_elems(list1, list2):
    """
    Returns the missing elements of list1 in list2; list1 is a list of required elements
    """
    missing = []
    for el in list1:
        if el not in list2:
            missing.append(el)
    return missing

def tests_wrapper(tests):
    """
    Wrapper which returns a function that returns True if all tests pass

    Parameters: 
    tests(list): list of tests

    Returns (function) which takes user argument
    """
    return lambda user: all(list(map(lambda test: test(user), tests)))

def checkValidWellName(s):
    pass

def reshape(lst, shape):
    """
    Reshape list to desired shaped 2d, 3d, etc. similar numpy.reshape

    Parameters:
    lst (list): list to reshape
    shape (tuple): desired shape e.g. (2,3,4) or (1,10)

    Returns (list) 

    """
    if len(shape) == 1:
        return lst
    n = reduce(mul, shape[1:])
    return [reshape(lst[i*n:(i+1)*n], shape[1:]) for i in range(len(lst)//n)]

def polynomial(coeff):
    """
    Returns polynomial function with given coefficients

    Parameters:
    coeff (list): list of coefficients for each ascending powered term; e.g. coeff[0]*x^0 + coeff[1]*x^1 

    Returns (function)
    """
    def apply(coeff, x):
        ret = 0
        for i, c in enumerate(coeff):
            ret += c * x**i
        return ret 
    return lambda x: apply(coeff, x)

def RadiusToVolume(x):
    """
    Converts radius (pix) to volume (uL); coefficients are based off fitted polynomial with pixels values from original drop
    image size

    Parameters:
    x (float, int, str): value to convert

    Returns (float)
    """
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
    """
    Back-calculation of RadiusToVolume(x)

    Parameters:
    x (float, int, str): value to convert

    Returns (float)
    """
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
