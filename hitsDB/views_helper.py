import json 

def filter_table_context_builder(filt, table, modals, buttons):
    """
    Function help build the context for the 'filter_table.html' template
    """
    # buttons = [
    #     {'id': 'delete', 'text': 'Delete Selected','class': 'btn-danger btn-confirm'},
    #     {'id': 'new_lib','text': 'New Library','class': 'btn-primary ' + 'new_lib_url', 
    #         'href':reverse('upload_file', kwargs={'form_class':"new_lib_form"})},
    #     ]

    # modals = [
    #     {'url_class': url_class, 'modal_id': modal_id, 'form_class': "lib_edit_form"},
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
        'btn': {
            'buttons': buttons,
            'json': json.dumps(buttons)
            },
    }
    return context