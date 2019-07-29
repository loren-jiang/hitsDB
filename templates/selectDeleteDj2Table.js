// Javascript module used to get selected options from Django table (django-tables-2)
// and delete them

$(document).ready(function() {
     
  function getSelected() {
    var selected = [];
              $.each($("td input[type='checkbox']:checked"), function(){
                  var exp = $(this).val();     
                  if (exp.length > 0)  {selected.push(exp);}   
              });
    return selected;
  }

  $("#delete-projs").click(function(){
    
    selected = getSelected();
    var newurl = '/projects/delete_projs/' + selected.join("/");
    if (selected.length > 0) {
      if (confirm("Are you sure you want to delete these projects?")) {
        $("#delete-projs").attr("href", newurl);
      } 
      else {
        $("#delete-projs").attr("href", '/projects/');
      }
    } 
    
  });
          
});

