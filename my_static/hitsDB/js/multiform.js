// collects all other form data inside <div class="multiform"></div> 
//and sends as one form 
function collectFormsData() {
    $(".multiform form").submit( function(eventObj) {
        $otherforms = $("form").not(this);
        $form = $(this);
        $otherforms.each(function() {
            data = $(this).find('input[type=text], input[type=number], select');
            cloned_data = data.clone()
            cloned_data.hide()
            $form.append(cloned_data)        
        });
        return true;
    });
};

$( document ).ready(function() {
    // collectFormsData();
});