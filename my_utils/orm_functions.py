### ORM (object-relational mapping layer) functions to interact with DB
def update_instance(instance, cleaned_data, fields=[]):
    if not(fields):
        fields = [key for key in cleaned_data]
    for field in fields:
        new_field_data = cleaned_data[field]
        old_field_data = getattr(instance, field)
        
        if old_field_data.__class__.__name__ == 'ManyRelatedManager':
            old_field_data.set([el for el in new_field_data], clear=True)
        else:
            if (new_field_data != old_field_data):
                setattr(instance, field, new_field_data)
    instance.save()
    # instance.save(update_fields=fields)

def bulk_create_get(model_class, objs):
    """
    Like built-in bulk_create (https://docs.djangoproject.com/en/2.2/ref/models/querysets/#bulk-create)
    but returns objects created and objects not created (existing)
    """
    # existing_qs = model_class.objects.filter(zinc_id__in=compound_dict.keys())
    pass

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

def make_instance_from_dict(instance_model_a_as_dict, model_a):
    """
    Makes Model instance (unsaved) from dict of fields; fields must be valid to be saved later

    Parameters:
    instance_model_a_as_dict (dictionary): dictionary of Model fields to be created with instance
    model_a (Model instance): instance of Model to be created

    Returns (Model instance)
    """
    try:
        del instance_model_a_as_dict['id']
    except KeyError:
        pass
    return model_a(**instance_model_a_as_dict)

def copy_instance(instance_a, instance_b):
    """
    Copies Model instance a to Model instance b; both instances should be of the same Model

    Parameters:
    instance_a (Model instance): instance of Model from which to copy fields
    instance_b (Model instance): instance of Model to which to copy fields

    Returns (Model instance) instance_b
    """
    for field in instance_a._meta.fields:
        if field.primary_key == True:
            continue  # don't want to clone the PK
        setattr(instance_b, field.name, getattr(instance_a, field.name))
    return instance_b