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
        $.ajax({ 
            type: $(this).attr('method'), 
            url: this.action, 
            data: $(this).serialize(),
            context: this,
            dataType: 'json',
            success: function(data, status) {
                // $('#' + modalId).html(data);
                location.reload();
            },
            error: function(xhr, ajaxOptions, thrownError) { // on error..
                // console.log(xhr);
                console.log(JSON.parse(xhr.responseJSON.errors));
                // console.log(ajaxOptions);
            }
        });
        return false;
    });
    console.log(urlClass);
    $("." + urlClass).click(function(ev) { // for each edit modal url
        ev.preventDefault(); // prevent navigation
        var url = $(this).attr('href'); // get the project_edit form href
        $("#" + modalId).load(url, function() { // load the url into the modal
            $(this).modal('show'); // display the modal on url load
        });
        return false; // prevent the click propagation
    });
}
