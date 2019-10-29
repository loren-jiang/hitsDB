$(function() {
    const ArrSubtract = (arr1, arr2) => arr1.map((v, i) => arr1[i] - arr2[i]);

    //DATA which is needed by gui
    const DATA = window.guiData;

    const volumeToRadius = (x) => {
        const coeff = [
            6.1417074854930405e1,
            1.0073950737908067e1, -1.2531131468153611e-1,
            9.1304741996519126e-4, -3.2477314052641414e-6,
            4.4142610214669469e-9
        ];
        return coeff.reduce((sum, e, i) => sum + e * Math.pow(x, i));
    };

    const radiusToVolume = (x) => {
        const coeff = [-5.3743703571317667e-6,
            3.8296724440466813e-2,
            2.1381856713576437e-5,
            8.5669944196377545e-7, -5.7076472737908041e-16,
            2.5941761345047031e-19
        ];
        return coeff.reduce((sum, e, i) => sum + e * Math.pow(x, i));
    };

    //GLOBAL CONSTANTS 
    const PIX_TO_UM = 2.77; //conversion factor 2.77 µm/pixel at full size
    const UM_TO_PIX = 1 / PIX_TO_UM;
    const STROKE_WIDTH = 4; // pixels
    const IMG_SCALE = 1024 / $('#well-image').height();

    const SOAK_INPUTS = ['#id_soakOffsetX', '#id_soakOffsetY', '#id_soakVolume'];
    const WELL_INPUTS = ['#id_well_x', '#id_well_y', '#id_well_radius'];

    const IMG_PADDING = 100;
    const IMG_DIM = [$('#well-image').width(), $('#well-image').height()];
    // const IMG_CONTAINER_DIM = [$('#well-image-container').width(), $('#well-image-container').height()];
    const IMG_CONTAINER_DIM = IMG_DIM.map(x => x + 2 * IMG_PADDING);

    $('#well-image-container').width(IMG_CONTAINER_DIM[0]);
    $('#well-image-container').height(IMG_CONTAINER_DIM[1]);

    const roundNPlaces = (num, n) => Math.round(num * Math.pow(10, n)) / Math.pow(10, n);
    const convertPixToUm = (xyr) => xyr.map(e => roundNPlaces(e * IMG_SCALE * PIX_TO_UM, 2));
    const convertUmToPix = (xyr) => xyr.map(e => roundNPlaces(e * UM_TO_PIX / IMG_SCALE, 2));

    const getJQuery = (selectors) => selectors.map(s => $(s));

    const wCircData = {
        t_w_c: DATA.topWellCircle * UM_TO_PIX / IMG_SCALE + IMG_PADDING,
        l_w_c: DATA.leftWellCircle * UM_TO_PIX / IMG_SCALE + IMG_PADDING,
        s_w_c: DATA.sideWellCircle * UM_TO_PIX / IMG_SCALE,
        t_w_r: DATA.targetWellRadius * UM_TO_PIX / IMG_SCALE,
        r_w_c: DATA.radWellCircle_ * UM_TO_PIX / IMG_SCALE - STROKE_WIDTH,
    };

    const sCircData = {
        t_s_c: DATA.topSoakCircle * UM_TO_PIX / IMG_SCALE + IMG_PADDING,
        l_s_c: DATA.leftSoakCircle * UM_TO_PIX / IMG_SCALE + IMG_PADDING,
        s_s_c: DATA.sideSoakCircle * UM_TO_PIX / IMG_SCALE,
        t_s_r: DATA.radSoakCircle_ * UM_TO_PIX / IMG_SCALE,
        r_s_c: DATA.radSoakCircle_ * UM_TO_PIX / IMG_SCALE - STROKE_WIDTH,
    };

    $('#well-image-container').append(
        `
    <div id="well-circle" style="display: None; top: ${wCircData.t_w_c}px; left: ${wCircData.l_w_c}px">
      <svg class="svg-circle" width="${wCircData.s_w_c}" height="${wCircData.s_w_c}">
          <circle class="circle outer-circle" cx="${wCircData.t_w_r}" cy="${wCircData.t_w_r}" r="${wCircData.r_w_c}" stroke="${DATA.wellCircleColor}" stroke-width="${STROKE_WIDTH}" fill="" fill-opacity="0.0" />
          <circle class="circle inner-circle" cx="${wCircData.t_w_r}" cy="${wCircData.t_w_r}" r="1" stroke="${DATA.wellCircleColor}" stroke-width="${STROKE_WIDTH}" fill="${DATA.wellCircleColor}" fill-opacity="1.0" />
      </svg>
      
    </div>
    <div class="${DATA.use_soak ? '' : 'soak-hidden'}" id="soak-circle" style="display: None; top: ${sCircData.t_s_c}px; left: ${sCircData.l_s_c}px">
      <svg class="svg-circle" width="${sCircData.s_s_c}" height="${sCircData.s_s_c}">
          <circle class="circle outer-circle" cx="${sCircData.t_s_r}" cy="${sCircData.t_s_r}" r="${sCircData.r_s_c}" stroke="${DATA.soakCircleColor}" stroke-width="${STROKE_WIDTH}" fill="" fill-opacity="0.0" />
          <circle class="circle inner-circle" cx="${sCircData.t_s_r}" cy="${sCircData.t_s_r}" r="1" stroke="${DATA.soakCircleColor}" stroke-width="${STROKE_WIDTH}" fill="${DATA.soakCircleColor}" fill-opacity="1.0" />
      </svg>
    </div>

    <div id="scale-bar" style="top:${IMG_DIM[1] + IMG_PADDING + 10}px; left:${IMG_PADDING}px; ">
      <svg width="${1000*UM_TO_PIX/IMG_SCALE}" height="30" version="1.1">
        <style>
          .small { font: italic 20px sans-serif; }

        </style>

        <text x="${0.0*1000*UM_TO_PIX/IMG_SCALE}" y="25" class="small">1000  \u03BCm</text>

        <rect width="${1000*UM_TO_PIX/IMG_SCALE}" height="5" stroke="black" stroke-width="6" fill="black"/>
      </svg>
    </div>


    `
    );


    $('#soak-form').submit(function(event) {
        const input = $('#nextWellOnSave');
        const checked = input.is(':checked') ? input.is(':checked') : '';
        $("<input />").attr("type", "hidden")
            .attr("name", "nextWellOnSave")
            .attr("value", checked)
            .appendTo(this);
    });

    const getCircleXY = (w) => {
        //w -> width of svg
        return [roundNPlaces(w / 2, 2), roundNPlaces(w / 2, 2)];
    };

    const getCircleXYFromTopLeft = (l, t, w) => {
        //t -> top
        //l -> left
        //w -> width of svg
        return [roundNPlaces(l + w / 2, 2), roundNPlaces(t + w / 2, 2)];
    };

    const getStrokeCircleRadius = (w, str_w) => {
        //w -> width of svg
        //str_w -> stroke width
        return roundNPlaces(w / 2, 2) - str_w;
    };

    const getCircleRadius = (w) => {
        //w -> width of svg
        return roundNPlaces(w / 2, 2);
    };

    const circleWillBeOutsideContainer = (circle, container, delta) => {
        const w = circle.width();
        const pos = circle.position();
        const btm_corner = [pos.left + w + delta, pos.top + w + delta];
        const container_w = container.width();

        if (btm_corner[0] > container_w || btm_corner[1] > container_w) {
            return true;
        } else {
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


    const getSoakXYR = (soakData = getJQuery(SOAK_INPUTS)) => {
        return soakData.map(e => parseFloat(e.val()));
    };

    const getWellXYR = (wellData = getJQuery(WELL_INPUTS)) => {
        return wellData.map(e => parseFloat(e.val()));
    };

    const setSoakXYR = (XYR) => {
        /**
         * sets soak input fields
         * `XYR`, array of x-coord, y-coord, and radius in um to be set
         */
        let xyr = convertPixToUm(XYR);
        xyr[2] = XYR[2];
        // xyr[2] = Math.round( xyr[2] );
        setTargetValues(getJQuery(SOAK_INPUTS), xyr);
        return true;
    };

    const setWellXYR = (XYR) => {
        /**
         * sets well input fields
         * `XYR`, array of x-coord, y-coord, and radius in um to be set
         */
        setTargetValues(getJQuery(WELL_INPUTS), convertPixToUm(XYR));
        return true;
    };

    const setTargetValues = (targets, values) => {
        /**
         * returns True if values set, else if not
         * `targets`, array of jQiery objects; should be DOM input fields of the soak or well
         * `values`, array of values to be set 
         */
        try {
            targets[0].val(values[0]);
            targets[1].val(values[1]);
            targets[2].val(values[2]);
            return true;
        } catch (err) {
            return false;
        }
    };

    const setOffsetXY = (soakXY = getSoakXYR().slice(0, 2), wellXY = getWellXYR().slice(0, 2)) => {
        return ArrSubtract(soakXY, wellXY);
    };

    const getCircleParams = (circle, ui) => {
        const W = ui.size ? ui.size.width : circle.attr('width');
        const H = ui.size ? ui.size.height : circle.attr('height');
        const X_Y = getCircleXYFromTopLeft(ui.position.left, ui.position.top, W); //in pixels
        const R = getCircleRadius(W);
        const XYR = [X_Y[0] - IMG_PADDING, X_Y[1] - IMG_PADDING, R]; //in pixels

        return ({
            W: W,
            H: H,
            R: R,
            R_: getStrokeCircleRadius(W, STROKE_WIDTH),
            XYR: XYR,
            xyr: convertPixToUm(XYR),
        })
    }
    const onDragCircle = (circle, soakWellTargets, selector) => function(event, ui) {
        const targets = selector === '#soak-circle' ? soakWellTargets[0] : soakWellTargets[1];
        const circleParams = getCircleParams(circle, ui);
        const { W, H, R, R_, XYR, xyr } = circleParams;
        if (selector === '#soak-circle') {
            xyr[2] = targets[2].val();
        }

        setTargetValues(targets, xyr);
        setOffsetXY(getSoakXYR(soakWellTargets[0]), getWellXYR(soakWellTargets[1]));
    };

    const onResizeCircle = (circle, soakWellTargets, selector) => function(event, ui) {
        const targets = selector === '#soak-circle' ? soakWellTargets[0] : soakWellTargets[1];
        const circleParams = getCircleParams(circle, ui);
        const { W, H, R, R_, XYR, xyr } = circleParams;

        C_X_Y = getCircleXY(W);
        resizeCircleSVG(circle, [W, H], [C_X_Y[0], C_X_Y[1], R_]);
        if (selector === '#soak-circle') {
            xyr[2] = targets[2].val();
        }
        setTargetValues(targets, xyr);
        setOffsetXY(getSoakXYR(soakWellTargets[0]), getWellXYR(soakWellTargets[1]));
    };

    const onSliderTrigger = (slider, add_or_minus) => {
        slider.trigger('moveSlider', [add_or_minus]);
        const xyr = getSoakXYR(); //in um
        xyr[2] = volumeToRadius(xyr[2]);
        const XYR = convertUmToPix(xyr); //in pixels
        const circle = $(".svg-circle", $('#soak-circle'));
        const position = circle.parent('#soak-circle').position();
        const R1 = getCircleRadius(circle.attr("width"));
        const R2 = XYR[2];
        const delta = R2 - R1;
        setSoakXYR([XYR[0] + delta, XYR[1] + delta, slider.slider("value")]);
        resizeCircleSVG(circle, [XYR[2] * 2, XYR[2] * 2], [XYR[2], XYR[2], XYR[2] - STROKE_WIDTH]);
    };

    const hotKeyMap = {
        '77': { keyCode: 'm', desc: 'Next well', func: (slider) => $('#next-well')[0].click() },
        '78': { keyCode: 'n', desc: 'Previous well', func: (slider) => $('#prev-well')[0].click() },
        '83': { keyCode: 's', desc: 'Save', func: (slider) => $('#soak-form').find('#submit-id-submit').click() },
        '88': {
            keyCode: 'x',
            desc: 'Use Soak',
            func: (slider) => {
                const checkbox = $('#id_useSoak');
                checkbox.prop("checked", !checkbox.prop("checked")).change();
            }
        },
        '188': { keyCode: ',', desc: 'Decrease transfer vol', func: (slider) => onSliderTrigger(slider, '-') },
        '190': { keyCode: '.', desc: 'Increase transfer vol', func: (slider) => onSliderTrigger(slider, '+') },

    };

    function nav(e) {
        //http://gcctech.org/csc/javascript/javascript_keycodes.htm
        e = e || window.event;
        const slider = $('#soakVolume-slider');
        // perform nav function 
        if (hotKeyMap[e.keyCode]) {
            hotKeyMap[e.keyCode].func(slider);
        }

    }

    // submits soak coordinates form
    function saveCoordinates() {
        document.getElementById("soak-form").submit();
    }

    function goToWell(user_id, plate_id) {
        let well_name = $('#sel-well').val();
        window.location.replace("/image-gui/" + user_id + '/' + plate_id + '/' + well_name);
        return;
    }

    document.onkeydown = nav;

    $('#id_useSoak').change(function() {
        if ((this.checked)) {
            $('#use-soak-indicator').html("yes");
            $('#soak-circle').removeClass("soak-hidden");
        } else {
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
        const wellTargets = getJQuery(WELL_INPUTS);
        const soakTargets = getJQuery(SOAK_INPUTS);

        const soakWellTargets = [soakTargets, wellTargets];
        const myTargets = selector === '#well-circle' ? wellTargets : soakTargets;
        if (canDrag) {
            objdiv.draggable({
                containment: obj,
                drag: onDragCircle(circle, soakWellTargets, selector),
            });
        }

        if (canResize) {
            objdiv.resizable({
                aspectRatio: 1.0,
                containment: obj,
                minWidth: 40,
                minHeight: 40,
                // ghost: true,
                resize: onResizeCircle(circle, soakWellTargets, selector),
            });
        }

    }

    function makeSlider(sel, other_sel) {
        const step = 25;
        const min = 25;
        const max = 250;
        const num_steps = (max - min) / step;
        const slider = $(sel);
        slider.slider({
            step: step,
            min: min,
            max: max,
            disabled: true,
            value: $(other_sel).val() * step / 25,
            slide: function(event, ui) {
                const new_val = ui.value / step * 25;
                $(other_sel).val(new_val);
                const circle = $(".svg-circle", $('#soak-circle'));
                resizeCircleSVG(circle, [new_val * 2, new_val * 2], [new_val, new_val, new_val - STROKE_WIDTH]);
            },
        });

        slider.bind('moveSlider', function moveSlider(event, inc_or_dec) {
            const slider = $(this);
            const step = slider.slider("option", "step");
            const max = slider.slider("option", "max");
            const min = slider.slider("option", "min");
            const currVal = slider.slider("value");
            const newVal = inc_or_dec === '+' ? (currVal + step <= max ? currVal + step : max) : (currVal - step >= min ? currVal - step : min);
            const delta = inc_or_dec === '+' ? step : -step;
            if (!(circleWillBeOutsideContainer($('#soak-circle'), $('#well-image-container'), delta * 2))) {
                $(other_sel).val(newVal);
                slider.slider("value", newVal);
            }

        });
    }

    makeSlider("#soakVolume-slider", '#id_soakVolume');
    makeUICircle('#well-circle', $('#well-image-container'), true, true);
    makeUICircle('#soak-circle', $('#well-image-container'), true, false);

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