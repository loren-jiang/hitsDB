from . import factories

def make_n_compounds(n):
    """
    Makes n number of compounds and returns them
    """
    return factories.CompoundFactory.create_batch(size=n)
