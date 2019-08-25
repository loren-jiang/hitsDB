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

$(document).ready(function() {
    
    $('#delete-exp').on('click', function(e) {
        r = confirm("Are you sure?");
        console.log(r);
        if (r==true) {

        } else {
            e.preventDefault();
        }
    });
});