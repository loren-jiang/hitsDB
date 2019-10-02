$(document).ready(function(){ 

    $('#well-image').click(function (ev) {
        
        console.log(($('#soak-or-well')));
        if (!($('#soak-or-well')[0].checked)){
            $('.marker.soak-marker').remove();
            let color = 'red';
            let size = 6;
            mouseX = ev.pageX - $(this).offset().left;
            mouseY = ev.pageY - $(this).offset().top;
            // $('#soak-coordinates').html(mouseX + "," + mouseY);
            coordX = mouseX/$(this).width();
            coordY = mouseY/$(this).height();
            $('#well-image-container').append(
                $('<div class="marker soak-marker"></div>')
                    .css('position', 'absolute')
                    .css('top', mouseY - size/2 + 'px')
                    .css('left', mouseX - size/2 + 'px')
                    .css('width', size + 'px')
                    .css('height', size + 'px')
                    .css('background-color', color)
            );
            $('#soak-x').val(coordX);
            $('#soak-y').val(coordY);
            console.log(coordX);
            console.log(coordY);
        }
        else {
            $('.marker.well-marker').remove();
            let color = 'blue';
            let size = 6;
            mouseX = ev.pageX - $(this).offset().left;
            mouseY = ev.pageY - $(this).offset().top;
            // $('#soak-coordinates').html(mouseX + "," + mouseY);
            coordX = mouseX/$(this).width();
            coordY = mouseY/$(this).height();
            $('#well-image-container').append(
                $('<div class="marker well-marker"></div>')
                    .css('position', 'absolute')
                    .css('top', mouseY - size/2 + 'px')
                    .css('left', mouseX - size/2 + 'px')
                    .css('width', size + 'px')
                    .css('height', size + 'px')
                    .css('background-color', color)
            );
            $('#well-x').val(coordX);
            $('#well-y').val(coordY);
            console.log(coordX);
            console.log(coordY);
        }

        


    });

    document.onkeydown = navigateWells;

    $('#soak-or-well').change(function(){
        if(this.checked) {
            console.log("this");
        }
        else {
            console.log("that");
        }
    });
 });

 function navigateWells(e) {

    e = e || window.event;

    if (e.keyCode == '37') {
       // left arrow
        $('#prev-well')[0].click();
    }
    if (e.keyCode == '39') {
       // right arrow
       $('#next-well')[0].click();
    }

}

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