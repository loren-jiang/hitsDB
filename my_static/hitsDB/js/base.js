// builds navigation path with url links
function buildNavPath(check_responses=false) {
    let url_path = $('#url_path').text().trim();
    let url_paths = [];
    let output='';
    let last;
    if (url_path) {
        let url_path_arr = url_path.split('/');
        url_path_arr = url_path_arr.filter((el, idx)=> el.length!=0 || idx==0 );
        let last;
        for (let i = 0; i < url_path_arr.length; i++) { 
            url_paths.push(
            	url_path_arr.slice(0,i+1).join('/')
            );
        }
        if (check_responses) {
            if (url_paths.map((el, idx)=> testURL(el)).every((el)=>el)) {
                for (let j = 0; j < url_paths.length; j++) { 
                    output += '<a href="' + url_paths[j] + '">'+ url_path_arr[j] +'</a>' + '/';
                }
            }
        }
        else {
            for (let j = 0; j < url_paths.length; j++) { 
                output += '<a href="' + url_paths[j] + '">'+ url_path_arr[j] +'</a>' + '/';
            }
        }
        
        
    }
    return output;
}

function testURL(url) {
    let bool;
    $.ajax({
        type: 'HEAD',
        url: url,
        async: false,
        success: function() {
                // page exists
            bool = true;
        },
        error: function() {
                // page does not exist
            bool = false;
        }
    });
    return bool;
}

function toggleMessages(show_dur, hide_dur, init_delay_dur, delay_inc, cascade_dur) {
    const messages = $('#messages-container').find('.message').not('.permanent');
    let delay = init_delay_dur;
    if (messages) {
        messages.each((idx, el) =>
            {
                delay = delay + delay_inc;
                $(el).delay(delay).show(show_dur);
                $(el).delay(delay+cascade_dur).hide(hide_dur);
            }
        );
    }
    
}

function userConfirm(btn) {
    if (confirm("Please confirm.")) {
        btn.click();
    }
}

$( document ).ready(function() {
    $('#url_path').html(buildNavPath());
    toggleMessages(500, 500, 0, 200, 1000);
});
