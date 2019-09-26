
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
