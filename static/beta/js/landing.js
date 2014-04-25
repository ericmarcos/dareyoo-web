$(function(){
    $('#parallax1').parallax("50%", 0.3);
    $('#parallax2').parallax("50%", 0.3);

    $('.video-btn a').magnificPopup({type:'iframe'});

    // From http://css-tricks.com/snippets/jquery/smooth-scrolling
    $('a[href*=#]:not([href=#])').click(
        function() {
            if(location.pathname.replace(/^\//, '') == this.pathname.replace(/^\//, '') && location.hostname == this.hostname) {
                var target = $(this.hash);
                target = target.length ? target : $('[name=' + this.hash.slice(1) + ']');
                if(target.length) {
                    $('html, body').animate({
                        scrollTop: target.offset().top
                    }, "slow");
                    return false;
                }
            }
        }
    );
});