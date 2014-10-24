$(function(){
    var mq = window.matchMedia( "(min-width: 768px)" );
    
    if(mq.matches) {
        $('#parallax1').parallax("50%", 0.3);
        $('#parallax2').parallax("50%", 0.3);
    }

    $('#ver-video a').magnificPopup({type:'iframe'});

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

    $("#android-notification-text-2").hide();
    $("#android-notification-form").submit(function( event ) {
        event.preventDefault();
        $.ajax({
            type: "POST",
            url: "/mobile-notification/",
            context: document.body,
            data: {
                email: $("#email-android-notification").val(),
                os: "Android",
                'csrfmiddlewaretoken': $('input[name="csrfmiddlewaretoken"]').val()
            }
        }).done(function() {
            $("#android-notification-text-1").hide();
            $("#android-notification-text-2").fadeIn();
        });
    });
    $("#ios-notification-text-2").hide();
    $("#ios-notification-form").submit(function( event ) {
        event.preventDefault();
        $.ajax({
            type: "POST",
            url: "/mobile-notification/",
            context: document.body,
            data: {
                email: $("#email-ios-notification").val(),
                os:"iOS",
                'csrfmiddlewaretoken': $('input[name="csrfmiddlewaretoken"]').val()
            }
        }).done(function() {
            $("#ios-notification-text-1").hide();
            $("#ios-notification-text-2").fadeIn();
        });
    });
});