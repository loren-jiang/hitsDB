
# takes through relation model a and b
# bulk adds instances of model b to instances of model a
# designed for m2m relations
def bulk_add(throughRel, a_pks, b_pks, a_col_name, b_col_name): 
    relations = []

    for b in b_pks:
        relations.extend([throughRel(**{a_col_name: a, b_col_name: b}) 
            for a in a_pks])

    rels = throughRel.objects.bulk_create(relations, ignore_conflicts=True)
    return rels

