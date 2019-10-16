
$(function () {
const DATA = window.guiData;
console.log(DATA);  
const pix_to_um = 2.77; //conversion factor 2.77 µm/pixel at full size
const um_to_pix = 1/pix_to_um;

const scaling_factor = 2.45; //1024 px / 418 px 

const convertPixToUm = (xyr) => xyr.map(e => (e*scaling_factor*pix_to_um).toFixed(2));
const convertUmToPix = (xyr) => xyr.map(e => (e*um_to_pix/scaling_factor).toFixed(2));

const wCircData = {
  t_w_c: DATA.topWellCircle*um_to_pix/scaling_factor,
  l_w_c: DATA.leftWellCircle*um_to_pix/scaling_factor,
  s_w_c: DATA.sideWellCircle*um_to_pix/scaling_factor,
  t_w_r: DATA.targetWellRadius*um_to_pix/scaling_factor,
  r_w_c: DATA.radWellCircle_*um_to_pix/scaling_factor,
};

const sCircData = {
  t_s_c: DATA.topSoakCircle*um_to_pix/scaling_factor,
  l_s_c: DATA.leftSoakCircle*um_to_pix/scaling_factor,
  s_s_c: DATA.sideSoakCircle*um_to_pix/scaling_factor,
  t_s_r: DATA.transferVol*um_to_pix/scaling_factor,
  r_s_c: DATA.radSoakCircle_*um_to_pix/scaling_factor,
};

  $('#well-image-container').append(
    `                    <div id="well-circle" style="display: None; top: ${wCircData.t_w_c}px; left: ${wCircData.l_w_c}px">
    <svg class="svg-circle" width="${wCircData.s_w_c}" height="${wCircData.s_w_c}">
        <circle class="circle outer-circle" cx="${wCircData.t_w_r}" cy="${wCircData.t_w_r}" r="${wCircData.r_w_c}" stroke="green" stroke-width="4" fill="" fill-opacity="0.0" />
        <circle class="circle inner-circle" cx="${wCircData.t_w_r}" cy="${wCircData.t_w_r}" r="1" stroke="green" stroke-width="4" fill="green" fill-opacity="1.0" />
    </svg>
    
 </div>
 <div class="${DATA.use_soak ? '' : 'soak-hidden'}" id="soak-circle" style="display: None; top: ${sCircData.t_s_c}px; left: ${sCircData.l_s_c}px">
    <svg class="svg-circle" width="${sCircData.s_s_c}" height="${sCircData.s_s_c}">
        <circle class="circle outer-circle" cx="${sCircData.t_s_r}" cy="${sCircData.t_s_r}" r="${sCircData.r_s_c}" stroke="red" stroke-width="4" fill="" fill-opacity="0.0" />
        <circle class="circle inner-circle" cx="${sCircData.t_s_r}" cy="${sCircData.t_s_r}" r="1" stroke="red" stroke-width="4" fill="red" fill-opacity="1.0" />
    </svg>
    
 </div>`
  );


  $('#soak-form').submit(function(event)  {
    const input = $('#nextWellOnSave');
    const checked = input.is(':checked') ? input.is(':checked') : '';
    $("<input />").attr("type", "hidden")
          .attr("name", "nextWellOnSave")
          .attr("value", checked)
          .appendTo(this);
  }
  );

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

    if (btm_corner[0] > container_w || btm_corner[1] > container_w) {
      return true;
    }
    else {
      return false;
    }
  };

  const resizeCircleSVG = (circle, w_h, cx_cy_r) => {
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
    let xyr = convertPixToUm(XYR);
    xyr[2] = Math.round( xyr[2] );
    const targets = [$('#id_soakOffsetX'), $('#id_soakOffsetY'), $('#id_transferVol')];
    setTargetValues(targets, xyr);
    // $('#id_soakOffsetX').val(xyr[0]);
    // $('#id_soakOffsetY').val(xyr[1]);
    // $('#id_transferVol').val(xyr[2]);
    return true;
  };
  
  const setWellXYR = (XYR) => {
    const xyr = convertPixToUm(XYR);
    const targets = [$('#id_targetWellX'), $('#id_targetWellY'), $('#id_targetWellRadius')];
    setTargetValues(targets, xyr);
    return true;
  };

  const setTargetValues = (targets, values) => {
    targets[0].val(values[0]);
    targets[1].val(values[1]);
    targets[2].val(values[2]);
    return true;
  };

  const resizeCircle = (circle, tar) => function(event, ui) {
    var outer_circle = $(".outer-circle", circle);
    var inner_circle = $(".inner-circle", circle);
    const w = ui.size.width;
    const h = ui.size.height;

    const c_x_y = getCircleXY(w);
    const r_ = getStrokeCircleRadius(w, 4);
    const r = getCircleRadius(w);

    resizeCircleSVG(circle, [w,h], [c_x_y[0], c_x_y[1], r_]);

    const x_y = getCircleXYFromTopLeft(ui.position.left, ui.position.top, w);
    const XYR = [x_y[0], x_y[1], r]; // in pixels
    const xyr = convertPixToUm(XYR);
    console.log(xyr);
    // const xyr = [ui.position.left + r, ui.position.top + r, r].map( (el)=> Math.round(el));
    // tar[0].val(xyr[0]);
    // tar[1].val(xyr[1]);
    // tar[2].val(xyr[2]);
    setTargetValues(tar, xyr);
  };
  
  const hotKeyMap = {
    '77': {keyCode:'m', desc:'Next well', func: (slider)=>$('#prev-well')[0].click()},
    '78': {keyCode:'n', desc:'Previous well', func: (slider)=>$('#next-well')[0].click()},
    '83': {keyCode:'s', desc:'Save', func: (slider)=>$('#soak-form').find('#submit-id-submit').click()},
    '88': {keyCode:'x', desc:'Use Soak', func: (slider)=>{
        const checkbox = $('#id_useSoak');
        checkbox.prop("checked", !checkbox.prop("checked")).change(); }},

    '188':{keyCode:',', desc:'Decrease transfer vol', func: (slider)=>{      
          slider.trigger('moveSlider',['-']);
          const xyr = getSoakXYR().map(e=>parseInt(e)); //in um
          const XYR = convertUmToPix(xyr); //in pixels

          const circle = $(".svg-circle", $('#soak-circle'));
          const position = circle.parent('#soak-circle').position();
          const r1 = getCircleRadius( circle.attr("width") );
          const r2 = XYR[2];
          const delta = r2 - r1;

          const new_xyr = convertPixToUm([XYR[0] + delta, XYR[1] + delta, r2]);
          setSoakXYR(new_xyr);

          resizeCircleSVG(circle, [XYR[2]*2, XYR[2]*2], [XYR[2], XYR[2], XYR[2]-4] );
        }},
    '190': {keyCode:'.', desc:'Increase transfer vol', func: (slider)=>{
          slider.trigger('moveSlider',['+']);
          const xyr = getSoakXYR().map(e=>parseInt(e)); //in um
          const XYR = convertUmToPix(xyr); //in pixels

          const circle = $(".svg-circle", $('#soak-circle'));
          const position = circle.parent('#soak-circle').position();
          const r1 = getCircleRadius( circle.attr("width") );
          const r2 = XYR[2];
          const delta = r2 - r1;

          const new_xyr = convertPixToUm([XYR[0] + delta, XYR[1] + delta, r2]);
          setSoakXYR(new_xyr);
          
          resizeCircleSVG(circle, [XYR[2]*2, XYR[2]*2], [XYR[2], XYR[2], XYR[2]-4] );
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

  $('#sel-well').change(function() {
    const curr_url = window.location.href;
    let split_url = curr_url.split('/');
    split_url[split_url.length - 2] = this.value;
    let joined_url = split_url.join('/');
    window.location.href = joined_url;
  });

  // https://stackoverflow.com/questions/53811350/how-to-make-svg-tag-image-resizable-using-jquery-ui
  function makeUICircle(selector, obj, canDrag, canResize) {
      var objdiv = $(selector);
      var circle = $(".svg-circle", objdiv);
      objdiv.show();
      const tarX = $(selector==='#well-circle' ? '#id_targetWellX': '#id_soakOffsetX');
      const tarY = $(selector==='#well-circle' ? '#id_targetWellY': '#id_soakOffsetY');
      const tarR = $(selector==='#well-circle' ? '#id_targetWellRadius' : '#id_transferVol');
      if (canDrag) {
        objdiv.draggable({
        containment: obj,
        drag: function(event, ui) {
          w = circle.attr('width');
          r = getCircleRadius(w);
          x_y = getCircleXYFromTopLeft(ui.position.left, ui.position.top, w);
          XYR = [x_y[0], x_y[1], r]; //in pixels
          xyr = convertPixToUm(XYR);
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
      disabled:true, 
      value: $(other_sel).val() * step / 25,
      slide: function( event, ui ) {
        const new_val =ui.value / step * 25;
        $(other_sel).val(new_val);
        const circle = $(".svg-circle", $('#soak-circle'));
        resizeCircleSVG(circle, [new_val*2, new_val*2] , [new_val,new_val, new_val-4] );
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
      if (!(circleWillBeOutsideContainer($('#soak-circle'), $('#well-image-container'), delta*2))) {
        $(other_sel).val(newVal / step * 25);
        slider.slider("value", newVal);
      }
      
    });
  }

  makeSlider("#transferVol-slider",'#id_transferVol');
  makeUICircle('#well-circle', $('#well-image-container'), true, true);
  makeUICircle('#soak-circle', $('#well-image-container'), true, false);
  // makeUICircle('#well-circle_', $('#well-image-container'), true, true);
  // makeUICircle('#soak-circle_', $('#well-image-container'), true, false);

  var hotkey_tbody = $('#hotKey-map');
  var tbody_html = '';
  for (var i = 0; i < Object.keys(hotKeyMap).length; i++) {
      var tr = "<tr>";
      var key = Object.keys(hotKeyMap)[i];

      tr += "<td>" + hotKeyMap[key].keyCode + "</td>" + "<td>" + hotKeyMap[key].desc + "</td></tr>";

      /* We add the table row to the table body */
      tbody_html += tr;
  };

  hotkey_tbody.html(
    tbody_html
  );

});