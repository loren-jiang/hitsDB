$(document).ready(function(){ 

    // $('#well-image').click(function (ev) {
    //     let color;
    //     let size;
    //     let marker_class;
    //     let mouseX = ev.pageX - $(this).offset().left;
    //     let mouseY = ev.pageY - $(this).offset().top;
    //     if (!($('#soak-or-well')[0].checked)){
    //         $('.marker.soak-marker').remove();
    //         color = 'red';
    //         size = 6;
    //         marker_class = 'marker soak-marker';
    //         coordX = mouseX/$(this).width();
    //         coordY = mouseY/$(this).height();
    //         $('#soak-x').val(coordX.toFixed(2));
    //         $('#soak-y').val(coordY.toFixed(2));
    //     }
    //     else {
    //         $('.marker.well-marker').remove();
    //         color = 'blue';
    //         size = 6;
    //         marker_class = 'marker well-marker';
    //         coordX = mouseX/$(this).width();
    //         coordY = mouseY/$(this).height();
    //         $('#well-x').val(coordX.toFixed(2));
    //         $('#well-y').val(coordY.toFixed(2));
    //     }

    //     $('#well-image-container').append(
    //         $('<div class="' + marker_class + '"></div>')
    //             .css('position', 'absolute')
    //             .css('top', mouseY - size/2 + 'px')
    //             .css('left', mouseX - size/2 + 'px')
    //             .css('width', size + 'px')
    //             .css('height', size + 'px')
    //             .css('background-color', color)
    //     );


    // });

    document.onkeydown = navigateWells;

    $('#soak-or-well').change(function(){
        if(!(this.checked)) {
            $('#which-pick').html("soak");
        }
        else {
            $('#which-pick').html("well");
        }
    });

    // https://stackoverflow.com/questions/53811350/how-to-make-svg-tag-image-resizable-using-jquery-ui
    function makeDragableCircle(selector, obj) {
        var height = obj.height();
        var width = obj.width();
        var objdiv = $(selector);
        var circle = $(".svg-circle", objdiv);
        console.log(circle);
        $(selector).draggable({
          containment: obj,
          drag: function(event, ui) {
            var cleft = ui.position.left * 100 / width;
            var top = ui.position.top * 100 / height;
            $(event.target).attr('data-offsetx', cleft);
            $(event.target).attr('data-offsety', top);
          }
        }).resizable({
          aspectRatio: 1.0,
          containment: obj,
          minWidth: 40,
          minHeight: 40,
          resize: function(e, ui) {
            circle.attr({
              width: ui.size.width,
              height: ui.size.height
            });
            $("circle", circle).attr({
              cx: Math.round(ui.size.width / 2) - 2,
              cy: Math.round(ui.size.height / 2) - 2,
              r: Math.round(ui.size.width / 2) - 4
            });
          }
        });
      }
    
      makeDragableCircle('#well-circle', $('#well-image-container'));
      makeDragableCircle('#soak-circle', $('#well-image-container'));

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