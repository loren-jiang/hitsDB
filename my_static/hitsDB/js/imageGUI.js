$(document).ready(function(){ 

    $('#well-image').click(function (ev) {
        $('.marker').remove();
        let color = 'red';
        let size = 6;
        mouseX = ev.pageX - $(this).offset().left;
        mouseY = ev.pageY - $(this).offset().top;
        // $('#soak-coordinates').html(mouseX + "," + mouseY);
        coordX = mouseX/$(this).width()
        coordY = mouseY/$(this).height()
        $('#well-image-container').append(
            $('<div class="marker"></div>')
                .css('position', 'absolute')
                .css('top', mouseY - size/2 + 'px')
                .css('left', mouseX - size/2 + 'px')
                .css('width', size + 'px')
                .css('height', size + 'px')
                .css('background-color', color)
        );
        $('#soak-x').val(coordX)
        $('#soak-y').val(coordY)
        console.log(coordX);
        console.log(coordY);
    });
 });

// submits soak coordinates form
function saveCoordinates() {
    document.getElementById("soak-form").submit();
}

function goToWell(user_id, plate_id) {
    // $( "#sel-well option:selected" ).text();
    let well_name = $('#sel-well').val();
    // let url = window.location
    console.log(well_name);
    window.location.replace("/image-gui/"+user_id+'/'+plate_id+'/'+well_name);
    return;
}