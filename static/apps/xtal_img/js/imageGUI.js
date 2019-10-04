// $(document).ready(function(){ 

//     // $('#well-image').click(function (ev) {
//     //     let color;
//     //     let size;
//     //     let marker_class;
//     //     let mouseX = ev.pageX - $(this).offset().left;
//     //     let mouseY = ev.pageY - $(this).offset().top;
//     //     if (!($('#soak-or-well')[0].checked)){
//     //         $('.marker.soak-marker').remove();
//     //         color = 'red';
//     //         size = 6;
//     //         marker_class = 'marker soak-marker';
//     //         coordX = mouseX/$(this).width();
//     //         coordY = mouseY/$(this).height();
//     //         $('#soak-x').val(coordX.toFixed(2));
//     //         $('#soak-y').val(coordY.toFixed(2));
//     //     }
//     //     else {
//     //         $('.marker.well-marker').remove();
//     //         color = 'blue';
//     //         size = 6;
//     //         marker_class = 'marker well-marker';
//     //         coordX = mouseX/$(this).width();
//     //         coordY = mouseY/$(this).height();
//     //         $('#well-x').val(coordX.toFixed(2));
//     //         $('#well-y').val(coordY.toFixed(2));
//     //     }

//     //     $('#well-image-container').append(
//     //         $('<div class="' + marker_class + '"></div>')
//     //             .css('position', 'absolute')
//     //             .css('top', mouseY - size/2 + 'px')
//     //             .css('left', mouseX - size/2 + 'px')
//     //             .css('width', size + 'px')
//     //             .css('height', size + 'px')
//     //             .css('background-color', color)
//     //     );


//     // });

//  });

$(function () {

    document.onkeydown = nav;

    $('#id_useSoak').change(function(){
        if((this.checked)) {
            $('#use-soak-indicator').html("yes");
            $('#soak-circle').removeClass("soak-hidden");

        }
        else {
            $('#use-soak-indicator').html("no");
            $('#soak-circle').addClass("soak-hidden");
        }
    });

    function drawCircle(selector, obj) {
        var objdiv = $(selector);
        objdiv.css('top', "200px");
        objdiv.css('left', "200px");


    }

    // https://stackoverflow.com/questions/53811350/how-to-make-svg-tag-image-resizable-using-jquery-ui
    function makeDragableCircle(selector, obj) {
        var height = obj.height();
        var width = obj.width();
        // console.log(height);console.log(width);
        // console.log(obj.css("height")); console.log(obj.css("width"));
        var objdiv = $(selector);
        var circle = $(".svg-circle", objdiv);
        const tarX = selector==='#well-circle' ? '#id_targetWellX': '#id_soakOffsetX';
        const tarY = selector==='#well-circle' ? '#id_targetWellY': '#id_soakOffsetY';
        const tarR = selector==='#well-circle' ? '#id_targetWellRadius' : '#id_transferVol';
        objdiv.draggable({
          containment: obj,
          drag: function(event, ui) {
            cleft = ui.position.left * 100 / width;
            top = ui.position.top * 100 / height;
            // console.log(ui.position);
            $(event.target).attr('data-offsetx', cleft);
            $(event.target).attr('data-offsety', top);
            r = Math.round($(".svg-circle" , $(event.target)).attr('height') / 2)- 4;
            const xyr = [ui.position.left + r, ui.position.top + r, r].map( (el)=> Math.round(el));
            $(tarX).val(xyr[0]);
            $(tarY).val(xyr[1]);
            $(tarR).val(xyr[2]);
          }
        }).resizable({
          aspectRatio: 1.0,
          containment: obj,
          minWidth: 40,
          minHeight: 40,
          resize: function(event, ui) {
            var outer_circle = $(".outer-circle", circle);
            var inner_circle = $(".inner-circle", circle);
            const w = ui.size.width;
            const h = ui.size.height;
            const cx = Math.round(w / 2) - 2;
            const cy = Math.round(h / 2) - 2;
            const r = Math.round(w / 2) - 4;
            circle.attr({
              width: w,
              height: h,
            });
       
            outer_circle.attr({
              cx: cx,
              cy: cy,
              r: r,
            });
            inner_circle.attr({
              cx: cx,
              cy: cy,
            });
            const xyr = [ui.position.left + r, ui.position.top + r, r].map( (el)=> Math.round(el));
            $(tarX).val(xyr[0]);
            $(tarY).val(xyr[1]);
            $(tarR).val(xyr[2]);
          }

        });
    }
    

    makeDragableCircle('#well-circle', $('#well-image-container'));
    makeDragableCircle('#soak-circle', $('#well-image-container'));

    // drawCircle('#well-circle', $('#well-image-container'));
});

function nav(e) {

    e = e || window.event;
    console.log(e);
    if (e.keyCode == '37') {
       // left arrow
        $('#prev-well')[0].click();
    }
    if (e.keyCode == '39') {
       // right arrow
       $('#next-well')[0].click();
    }
    if (e.keyCode =='83') { 
      //'s'
      $('#soak-form').submit();
    }
    if (e.keyCode =='88') {
      //'x'
      const checkbox = $('#id_useSoak');
      checkbox.prop("checked", !checkbox.prop("checked")).change();
      // console.log(checkbox.prop('checked'));
    }

}


// submits soak coordinates form
function saveCoordinates() {
    document.getElementById("soak-form").submit();
}

function goToWell(user_id, plate_id) {
    let well_name = $('#sel-well').val();
    window.location.replace("/image-gui/"+user_id+'/'+plate_id+'/'+well_name);
    return;
}