import json 

def build_modal_form_context(*args, **kwargs):
    """
    Function to help build the context for the 'modals/modal_form.html' template
    """

    return {
        'modal_title': getattr(kwargs, 'modal_title',  ''), 
        'form_class': getattr(kwargs, 'form_class',  ''), 
        'action': getattr(kwargs, 'action',  ''), 
        'use_ajax': getattr(kwargs, 'use_ajax',  False), 
        'form': getattr(kwargs, 'form',  ''), 
    }


def build_filter_table_context(filt, table, modals, buttons):
    """
    Function to help build the context for the 'filter_table.html' template
    """
    # buttons = [
    #     {'id': 'delete', 'text': 'Delete Selected','class': 'btn-danger btn-confirm'},
    #     {'id': 'lib_new','text': 'New Library','class': 'btn-primary ' + 'new_lib_url', 
    #         'href':reverse('upload_file', kwargs={'form_class':"new_lib_form"})},
    #     ]

    # modals = [
    #     {'url_class': url_class, 'modal_id': modal_id, 'form_class': "lib_edit_idform"},
    #     {'url_class': 'new_lib_url', 'modal_id': 'new_lib_modal', 'form_class': "new_lib_form"},
    #     ]

    context = {
        'filter': {
            'filter': filt, 
            'form':filt.form,
            'filter_id': filt.filter_id,
            'filter_form_id': filt.form_id,
            },
        'table': {
            'table': table,
            'table_id': table.table_id,
            'table_form_id': table.form_id,
            'form_action_url': table.form_action,
            },
        'modals': {
            'modals': modals,
            'json': json.dumps(modals),
            },
        'buttons': {
            'buttons': buttons,
            'json': json.dumps(buttons)
            },
    }
    return context