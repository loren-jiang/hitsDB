function setUpModalForm(urlClass, modalId, formClass) {
    function getCookie(name) {
        var cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            var cookies = document.cookie.split(';');
            for (var i = 0; i < cookies.length; i++) {
                var cookie = cookies[i].trim();
                // Does this cookie string begin with the name we want?
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    var csrftoken = getCookie('csrftoken');
    function csrfSafeMethod(method) {
        // these HTTP methods do not require CSRF protection
        return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
    }
    $.ajaxSetup({
        beforeSend: function(xhr, settings) {
            if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
                xhr.setRequestHeader("X-CSRFToken", csrftoken);
            }
        }
    });
    $(document).on('submit','.' + formClass + '.ajax_form', function(ev) {
        ev.preventDefault();
        let data_ = new FormData($(this)[0]);
        $.ajax({ 
            type: $(this).attr('method'), 
            url: this.action, 
            data: data_,
            context: this,
            dataType: 'json',
            processData: false,
            contentType: false,
            success: function(data, status) {
                // $('#' + modalId).html(data);
                location.reload();
            },
            error: function(data, xhr, ajaxOptions, thrownError) {
                const errors = JSON.parse(data.responseJSON.errors);
                const keys = Object.keys(errors);
                var i;
                for (i = 0; i < keys.length; i++) {
                    const selector = '#div_id_' + keys[i];
                    $(selector).find('input').addClass('form-control is-invalid');
                    errors[keys[i]].forEach((err)=> {
                        $(selector).append('<p class="invalid-feedback" style="display:flex;"><strong>' + err.message + '</strong></p>');
                    });
                    
                  }
            }
            // error: function(xhr, ajaxOptions, thrownError) { // on error..
            //     console.log(JSON.parse(xhr.responseJSON.errors));
            // }
        });
        return false;
    });

    $("." + urlClass).click(function(ev) { // for each edit modal url
        ev.preventDefault(); // prevent navigation
        var url = $(this).attr('href'); // get the project_edit form href
        $("#" + modalId).load(url, function() { // load the url into the modal
            $(this).modal('show'); // display the modal on url load
        });
        return false; // prevent the click propagation
    });
}
