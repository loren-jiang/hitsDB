
def bulk_add(throughRel, a_pks, b_pks, a_col_name, b_col_name): 
    """
    Takes through relation Model a and b and bulk adds instances of Model b to instances of Model a;
    designed for m2m relations

    Parameters:
    throughRel (ManyToManyField.through): see https://docs.djangoproject.com/en/2.2/ref/models/fields/#django.db.models.ManyToManyField.through
    a_pks (list): list of Model a primary keys
    b_pks (list): list of Model b primary keys
    a_col_name (string): string of Model a SQL table column identifier (usually '[model_name]_id')
    b_col_name (string): string of Model b SQL table column identifier (usually '[model_name]_id')

    Returns (list) of created relations
    """
    relations = []
    for b in b_pks:
        relations.extend([throughRel(**{a_col_name: a, b_col_name: b}) 
            for a in a_pks])
    rels = throughRel.objects.bulk_create(relations, ignore_conflicts=True)
    return rels

def bulk_one_to_one_add(throughRel, a_pks, b_pks, a_col_name, b_col_name): 
    """
    Takes through relation Model a and b and bulk adds instances of Model b to instances of Model a strictly row-wise;
    Designed for m2m relations and number of a instances == number of b instances

    Parameters:
    throughRel (ManyToManyField.through): see https://docs.djangoproject.com/en/2.2/ref/models/fields/#django.db.models.ManyToManyField.through
    a_pks (list): list of Model a primary keys
    b_pks (list): list of Model b primary keys
    a_col_name (string): string of Model a SQL table column identifier (usually '[model_name]_id')
    b_col_name (string): string of Model b SQL table column identifier (usually '[model_name]_id')

    Returns (list) of created relations
    """
    relations = []
    num_a = len(a_pks)
    num_b = len(b_pks)
    assert num_a == num_b #must be same length
    for i in range(num_b):
        relations.append(throughRel(**{a_col_name: a_pks[i], b_col_name: b_pks[i]}))
    rels = throughRel.objects.bulk_create(relations, ignore_conflicts=True)
    return rels 

def make_instance_from_dict(instance_model_a_as_dict,model_a):
    try:
        del instance_model_a_as_dict['id']
    except KeyError:
        pass
    return model_a(**instance_model_a_as_dict)

def copy_instance(instance_of_model_a,instance_of_model_b):
    for field in instance_of_model_a._meta.fields:
        if field.primary_key == True:
            continue  # don't want to clone the PK
        setattr(instance_of_model_b, field.name, getattr(instance_of_model_a, field.name))
    return instance_of_model_b