// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.

require(["jquery", "jhapi"], function ($, JHAPI) {
    "use strict";
    
    var base_url = window.jhdata.base_url;
    var user = window.jhdata.user;
    var api = new JHAPI(base_url);
    
    /*
    var proj_name = proj.jhdata.proj_name;
    

    $('.project-name').click(function () {
        var url = $(this).data('url');
        $.get(url, function ( response) {
            $('body').append(response);
        });
    });*/

     
    $(".stop-server").click(function () {
        var server_name = $(this).data('server_name');
            var server_name = $(this).data('servername');
        
        api.stop_server(user, server_name, {
            success: function () {
                //$(_this).parents('li').remove();
                window.location.reload(true);
            }
        });
    });
    
    
});
