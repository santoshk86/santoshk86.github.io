$(".header").click(function () {

    const $header = $(this);
    // getting the next element
    const $content = $header.next();
    // open up the content needed - toggle the slide- if visible, slide up, if not slide down.
    $content.slideToggle(500, function () {
        // execute this after slideToggle is done
        // change text of header based on visibility of content div
        $header.text(function () {
            // change text based on condition
            return $content.is(":visible") ? "Collapse" : "Expand";
        });
    });

});
