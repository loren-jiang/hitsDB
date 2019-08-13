// Javascript module used to get selected options from Django table (django-tables-2)
// and delete them
function getSelected() {
  var selected = [];
            $.each($("td input[type='checkbox']:checked"), function(){
                var exp = $(this).val();     
                if (exp.length > 0)  {selected.push(exp);}   
            });
  return selected;
}

function deleteSelected(selected, base_url) {
  // let url = base_url + '/' + selected.join("_");
  let url = base_url + selected.join("_");
  console.log(url);
  if (selected.length > 0) {
    if (confirm("Are you sure you want to delete?")) {
      // $("#delete-exps").prop("href", url);
      window.location.href = url;
    } 
  } 
}



// $(document).ready(function() {
     


//   $("#delete-projs").click(function(){
    
//     selected = getSelected();
//     var newurl = '/projects/delete_projs/' + selected.join("/");
//     if (selected.length > 0) {
//       if (confirm("Are you sure you want to delete these projects?")) {
//         $("#delete-projs").attr("href", newurl);
//       } 
//       else {
//         $("#delete-projs").attr("href", '/projects/');
//       }
//     } 
    
//   });
          
// });

