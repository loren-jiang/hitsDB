function setUpModalForm(urlClass, modalId, formClass) {
    $("." + urlClass).click(function(ev) { // for each edit contact url
        ev.preventDefault(); // prevent navigation
        var url = $(this).attr('href'); // get the project_edit form href
        $("#" + modalId).load(url, function() { // load the url into the modal
            $(this).modal('show'); // display the modal on url load
        });

        return false; // prevent the click propagation
    });

    $('.' + formClass).on('submit', function() {
        $.ajax({ 
            type: $(this).attr('method'), 
            url: this.action, 
            data: $(this).serialize(),
            context: this,
            success: function(data, status) {
                $('#' + modalId).html(data);
            }
        });
        return false;
    });
}
