$(document).ready(function() {
    $('.soak').hover(function() {
      $this = $(this);
      $this.toggleClass( "active" );
      pair_id = $this.attr('pair_id');
      $pair = $("#"+pair_id);
      $pair.toggleClass( "active" );
    });
  });