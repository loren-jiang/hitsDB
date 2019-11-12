from .models import Library, Compound
from my_utils.utility_functions import lists_diff

def bulk_get_or_create_compounds(model_instances_to_add, model_pk='zinc_id', model_class=Compound):
    filt_kwargs = {
        '{0}__in'.format(model_pk): [getattr(t, model_pk) for t in model_instances_to_add],
    }
    existing = model_class.objects.filter(**filt_kwargs)
    pks_existing = [getattr(t, model_pk) for t in existing]

    bulk = model_class.objects.bulk_create(model_instances_to_add, ignore_conflicts=True)
    pks_bulk = [getattr(t, model_pk) for t in bulk]
    pks_added = lists_diff(pks_bulk, pks_existing)
    return pks_added, pks_existing

def bulk_get_or_create_compounds_to_library(model_instances_to_add, library=None, model_pk='zinc_id', model_class=Compound):
    [pks_added, pks_existing] = bulk_get_or_create_compounds(model_instances_to_add, model_pk, model_class)
    pks_to_add = pks_added + pks_existing
    filt_kwargs = {
            '{0}__in'.format(model_pk): pks_to_add,
        }
    compounds_to_add = [c for c in model_class.objects.filter(**filt_kwargs)]
    if library:
        existing = library.compounds.filter(**filt_kwargs)
        pks_existing_in_lib = [getattr(c, model_pk) for c in existing]
        library.compounds.add(*compounds_to_add)
        pks_to_add_to_lib = [getattr(c, model_pk) for c in compounds_to_add]
        pks_added_to_lib = lists_diff(pks_to_add_to_lib, pks_existing_in_lib)

        return pks_added_to_lib, pks_existing_in_lib