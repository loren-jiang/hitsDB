#turns list into sublists of size n using generator
def chunks(l, n):
    """Yield successive n-sized chunks from l."""
    for i in range(0, len(l), n):
        yield l[i:i + n]


#turns list into sublists of size n using list comprehension
def chunk_list(l,n):
    return [l[i * n:(i + 1) * n] for i in range((len(l) + n - 1) // n )] 