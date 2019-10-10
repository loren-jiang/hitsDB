
$(function () {
  const getCircleXY = (w) => {
    //t -> top
    //l -> left
    //w -> width of svg
    return [Math.round(w/2), Math.round(w/2)];
  };

  const getCircleXYFromTopLeft = (l,t, w) => {
    //t -> top
    //l -> left
    //w -> width of svg
    return [Math.round(l + w/2), Math.round(t + w/2)];
  };

  const getStrokeCircleRadius = (w, str_w) => {
    //w -> width of svg
    //str_w -> stroke width
    return Math.round(w/2)-str_w;
  };

  const getCircleRadius = (w) => {
    //w -> width of svg
    return Math.round(w/2);
  };

  const circleWillBeOutsideContainer = (circle, container, delta) => {
    const w = circle.width();
    const pos = circle.position();
    const btm_corner = [pos.left + w + delta, pos.top + w + delta];
    const container_w = container.width(); 
    console.log(pos);
    console.log(w);
    console.log(delta);
    console.log(btm_corner);
    console.log(container_w);
    if (btm_corner[0] > container_w || btm_corner[1] > container_w) {
      return true;
    }
    else {
      return false;
    }
  };

  const drawCircleSVG = (circle, w_h, cx_cy_r) => {
    const outer_circle = $(".outer-circle", circle);
    const inner_circle = $(".inner-circle", circle);
    circle.attr({
      width: w_h[0],
      height: w_h[1],
    });

    outer_circle.attr({
      cx: cx_cy_r[0],
      cy: cx_cy_r[1],
      r: cx_cy_r[2],
    });
    inner_circle.attr({
      cx: cx_cy_r[0],
      cy: cx_cy_r[1],
    });
  };

  const getSoakXYR = () => ( [$('#id_soakOffsetX').val(), $('#id_soakOffsetY').val(), $('#id_transferVol').val()] );
  
  const setSoakXYR = (XYR) => {
    $('#id_soakOffsetX').val(XYR[0]);
    $('#id_soakOffsetY').val(XYR[1]);
    $('#id_transferVol').val(XYR[2]);
    return true;
  };
  
  const resizeCircle = (circle, tar) => function(event, ui) {
    var outer_circle = $(".outer-circle", circle);
    var inner_circle = $(".inner-circle", circle);
    const w = ui.size.width;
    const h = ui.size.height;
    // console.log("Comparing w and h");
    // console.log(w); console.log(h);
    // console.log(circle.attr('width'));
    // console.log(circle.attr('height'));

    // const cx = Math.round(w / 2) - 2;
    // const cy = Math.round(h / 2) - 2;
    // const r = Math.round(w / 2) - 4;
    const c_x_y = getCircleXY(w);
    const r_ = getStrokeCircleRadius(w, 4);
    const r = getCircleRadius(w);

    drawCircleSVG(circle, [w,h], [c_x_y[0], c_x_y[1], r_]);

    const x_y = getCircleXYFromTopLeft(ui.position.left, ui.position.top, w);
    const xyr = [x_y[0], x_y[1], r];

    // const xyr = [ui.position.left + r, ui.position.top + r, r].map( (el)=> Math.round(el));
    tar[0].val(xyr[0]);
    tar[1].val(xyr[1]);
    tar[2].val(xyr[2]);
  };
  const hotKeyMap = {
    '77': {key:'m', desc:'Previous well', func: (slider)=>$('#prev-well')[0].click()},
    '78': {keyCode:'n', desc:'Next well', func: (slider)=>$('#next-well')[0].click()},
    '83': {keyCode:'s', desc:'Save', func: (slider)=>$('#soak-form').submit()},
    '88': {keyCode:'x', desc:'Use Soak', func: (slider)=>{
        const checkbox = $('#id_useSoak');
        checkbox.prop("checked", !checkbox.prop("checked")).change(); }},

    '188':{keyCode:',', desc:'Decrease transfer vol', func: (slider)=>{      
          slider.trigger('moveSlider',['-']);
          const XYR = getSoakXYR().map(e=>parseInt(e));
          const circle = $(".svg-circle", $('#soak-circle'));
          const position = circle.parent('#soak-circle').position();
          const r1 = getCircleRadius( circle.attr("width") );
          const r2 = XYR[2];
          const delta = r2 - r1;
          // console.log(XYR);
          // console.log(delta);
          setSoakXYR([XYR[0] + delta, XYR[1] + delta, r2]);
          drawCircleSVG(circle, [XYR[2]*2, XYR[2]*2], [XYR[2], XYR[2], XYR[2]-4] );

          // drawCircleSVG(circle, [w, w], [x_y[0], x_y[1], r] );
        }},
    '190': {keyCode:'.', desc:'Increase transfer vol', func: (slider)=>{
          slider.trigger('moveSlider',['+']);
          const XYR = getSoakXYR().map(e=>parseInt(e));
          const circle = $(".svg-circle", $('#soak-circle'));
          const position = circle.parent('#soak-circle').position();
          const r1 = getCircleRadius( circle.attr("width") );
          const r2 = XYR[2];
          const delta = r2 - r1;
          // console.log(XYR);
          // console.log(delta);
          setSoakXYR([XYR[0] + delta, XYR[1] + delta, r2]);
          drawCircleSVG(circle, [XYR[2]*2, XYR[2]*2], [XYR[2], XYR[2], XYR[2]-4] );

          // drawCircleSVG(circle, [w, w], [x_y[0], x_y[1], r] );
          }},

  };

  function nav(e) {
    //http://gcctech.org/csc/javascript/javascript_keycodes.htm
    e = e || window.event;
    const slider = $('#transferVol-slider');

    

    // perform nav function 
    hotKeyMap[e.keyCode].func(slider);

  
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
  function makeUICircle(selector, obj, canDrag, canResize) {
      var height = obj.height();
      var width = obj.width();
      var objdiv = $(selector);
      var circle = $(".svg-circle", objdiv);
      const tarX = $(selector==='#well-circle' ? '#id_targetWellX': '#id_soakOffsetX');
      const tarY = $(selector==='#well-circle' ? '#id_targetWellY': '#id_soakOffsetY');
      const tarR = $(selector==='#well-circle' ? '#id_targetWellRadius' : '#id_transferVol');
      if (canDrag) {
        objdiv.draggable({
        containment: obj,
        drag: function(event, ui) {
          // cleft = ui.position.left * 100 / width;
          // top = ui.position.top * 100 / height;
          // console.log(ui.position);
          // $(event.target).attr('data-offsetx', cleft);
          // $(event.target).attr('data-offsety', top);
          // const circle = $(".svg-circle" , $(event.target));
          w = circle.attr('width');
          r = getCircleRadius(w);
          
          // r = Math.round(circle.attr('width') / 2)- 4;
          x_y = getCircleXYFromTopLeft(ui.position.left, ui.position.top, w);
          // console.log(x_y);
          xyr = [x_y[0], x_y[1], r];
          tarX.val(xyr[0]);
          tarY.val(xyr[1]);
          tarR.val(xyr[2]);
        }
      });
    }
    
    if (canResize) {
      objdiv.resizable({
        aspectRatio: 1.0,
        containment: obj,
        minWidth: 40,
        minHeight: 40,
        // ghost: true,
        resize: resizeCircle(circle, [tarX, tarY, tarR]),
      });
    }
      
  }
  function makeSlider(sel, other_sel) { 
    const step = 10;
    const min = 10;
    const max = 100;
    const num_steps = (max-min)/step;
    const slider = $(sel);
    slider.slider({
      step: step,
      min: min,
      max: max,
      value: $(other_sel).val() * step / 25,
      slide: function( event, ui ) {
        const new_val =ui.value / step * 25;
        $(other_sel).val(new_val);

        const circle = $(".svg-circle", $('#soak-circle'));
        // console.log(circleOutsideContainer($('#soak-circle'), $('#well-image-container')));
        drawCircleSVG(circle, [new_val*2, new_val*2] , [new_val,new_val, new_val-4] );
      },  
    });
    
    slider.bind('moveSlider', function moveSlider(event, inc_or_dec) {
      const slider = $(this);
      const step = slider.slider("option", "step");
      const max = slider.slider("option", "max");
      const min = slider.slider("option", "min");
      const currVal = slider.slider("value");      
      const newVal = inc_or_dec==='+' ?  (currVal + step <= max ? currVal + step: max) : (currVal - step >= min ? currVal - step: min);
      const delta = inc_or_dec==='+' ? 25 : -25;
      if (circleWillBeOutsideContainer($('#soak-circle'), $('#well-image-container'), delta*2)) {

      } else{
        $(other_sel).val(newVal / step * 25);
        slider.slider("value", newVal);
      }
      
    });
  }

  makeSlider("#transferVol-slider",'#id_transferVol');
  
  makeUICircle('#well-circle', $('#well-image-container'), true, true);
  makeUICircle('#soak-circle', $('#well-image-container'), true, false);

  $('#hotKey-map').text(
    "m -> next well \n n -> prev well \n s -> save \n x -> use soak \n . -> inc soak vol \n  -> dec soak vol"
  );

  // $('#well-image').click(()=>{
  //   console.log("clcked");
  // })
});



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
