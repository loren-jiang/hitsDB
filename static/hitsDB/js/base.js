// builds navigation path with url links
function buildNavPath() {
    let url_path = $('#url_path').text();
    let url_paths = [];
    let output='';
    let last;
    if (url_path) {
        let url_path_arr = url_path.split('/');
        last = url_path_arr.pop(); //pop off last element        
        // console.log(url_path_arr);
        for (let i = 0; i < url_path_arr.length; i++) { 
            url_paths.push(
            	url_path_arr.slice(0,i+1).join('/')
            );
        }
        for (let j = 0; j < url_paths.length; j++) { 
            output += '<a href="' + url_paths[j] + '">'+ url_path_arr[j] +'</a>' + '/';
        }
        
    }
    return output + last;
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
