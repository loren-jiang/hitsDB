function confirmLibraryChange(lib_pk) {
    $('select#id_library').on('focus', function () {
        // Store the current value on focus and on change
        previous = this.value;
    }).on("change", function() {
        $val = $(this).val();
        if ($val!=lib_pk) {
            r = confirm("Changing the library will delete experiment plates and soaks. Do you want to continue?");
            if (r==false) {
                $(this).val(previous);
            } 
        }
    });
}

function getCurrentStep(step) {
    return $(`#exp-tab a:nth-child(${parseInt(step)})`);
}

function initCurrentStep(step) {

    let exp_step = `#exp-tab a:nth-child(${parseInt(step)})`;
    const hash = window.location.hash;
    const selector = hash ? hash + '-tab': exp_step;
    $(selector).tab('show');
}

$(document).ready(function() {
    $('#delete-exp').on('click', function(e) {
        r = confirm("Are you sure?");
        if (r==true) {
        } else {
            e.preventDefault();
        }
    });

    // $('.form-option-title:first').click();
    $('.form-option .collapse-btn').on('click', function() {
        $form_option = $(this).parent('.form-option');
        $collapse = $form_option.find('collapse');
        $('.form-option .collapse').not($collapse).collapse('hide');
    });
});