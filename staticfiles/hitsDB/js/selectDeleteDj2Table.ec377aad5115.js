// Javascript module used to get selected options from Django table (django-tables-2)
// and delete them
// $(document).ready(function() {

// get selected checkboxes and return as array
function getSelected(selector) {
  var selected = [];
            $.each($(selector), function(){
                var a = $(this).val();     
                if (a.length > 0)  {selected.push(a);}   
            });
  return selected;
}

function deleteSelected(selected, base_url, delimiter) {
  let url = base_url + selected.join(delimiter);
  let msg = "Are you sure? \n"; //+ selected.join(", ")
  if (selected.length > 0) {

    if (confirm(msg)) {
      window.location.href = url;
    } 
  } 
}

// checks elements toBeSelected depending of status
$.fn.checkIfChecked = function(toBeSelected) {
  this.click( function(evt) {
    let status = this.checked;
    toBeSelected.prop('checked', status);
  });
  
};

//https://gist.github.com/AndrewRayCode/3784055
// Usage: $form.find('input[type="checkbox"]').shiftSelectable();
// replace input[type="checkbox"] with the selector to match your list of checkboxes
$.fn.shiftSelectable = function() {
  var lastChecked,
      $chkboxes = this;

  $chkboxes.click(function(evt) {
      if(!lastChecked) {
          lastChecked = this;
          return;
      }

      if (evt.shiftKey) {
        var start = $chkboxes.index(this);
        var end = $chkboxes.index(lastChecked);

        $chkboxes.slice(Math.min(start,end), Math.max(start,end)+ 1).prop('checked', lastChecked.checked);
      }

      lastChecked = this;
  });
};
// });
function getFormInputData(form_id) {
  return $('#'+form_id).find('td input:checked');
}
$(document).ready(function() {
  $('.select-table').each((i, el) => {
    // let $table = $(el).find(".table");
    let $table = $(el);
    let $th_checkbox = $table.find('th input[type="checkbox"]');
    let $td_checkboxes = $table.find('td input[type="checkbox"]');
    $th_checkbox.checkIfChecked($td_checkboxes);
    $td_checkboxes.shiftSelectable(); 
  });
          
});

