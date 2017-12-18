// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.

require(["jquery", "jhapi"], function ($, JHAPI) {
    "use strict";
    
    var base_url = window.jhdata.base_url;
    var user = window.jhdata.user;
    var api = new JHAPI(base_url);
    var proj_name = window.jhdata.proj_name;
    
            $('body').append("hellow");
    
            $('body').append(user);
    
            $('body').append(proj_name);
    
        api.get_project(user, proj_name, {
            success: function () {
            $('#proj_info').append(response);
            $('body').append("hellow");
            }
        });

});

