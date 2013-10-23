$(window).load(function(){
//On click any <dt> within the post-list
$('#post-list dt').click(function (e) {
    //Toggle open/close on the <div> after the <dt>, opening it if not open.
    $(e.target).next('dd').slideToggle('fast');
});
});


