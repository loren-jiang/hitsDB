// builds navigation path with url links
function buildNavPath() {
    let url_path = $('#url_path').text();
    let url_paths = [];
    let output='';
    let last;
    if (url_path) {
        let url_path_arr = url_path.split('/');
        last = url_path_arr.pop(); //pop off last element
        
        console.log(url_path_arr);
        let i;
        for (i = 0; i < url_path_arr.length; i++) { 
            url_paths.push(
            	url_path_arr.slice(0,i+1).join('/')
            );
        }
        let j;
        for (j = 0; j < url_paths.length; j++) { 
            output += '<a href="' + url_paths[j] + '">'+ url_path_arr[j] +'</a>' + '/';
        }
        
    }
    return output + last;
}

function userConfirm(btn) {
    if (confirm("Please confirm.")) {
        btn.click();
    }
}

// function ConfirmDialog(message) {
//   let bool = null;
//   $('<div></div>').appendTo('body')
//     .html('<div><h6>' + message + '?</h6></div>')
//     .dialog({
//       modal: true,
//       title: 'Delete message',
//       zIndex: 10000,
//       autoOpen: true,
//       width: 'auto',
//       resizable: false,
//       buttons: {
//         Yes: function() {
//           bool = true;
//           $(this).dialog("close");
          
//         },
//         No: function() {
//           bool = false;
//           $(this).dialog("close");
          
//         }
//       },
//       close: function(event, ui) {
//         bool = false;
//         $(this).remove();
//       }
//     });
//     return bool;
// };

$( document ).ready(function() {
    $('#url_path').html(buildNavPath());
    // $('.btn-danger').click( function(e) {
    //     e.preventDefault();
    //     userConfirm(this);
    // }
    // );
});
