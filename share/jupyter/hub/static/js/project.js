// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.

require(["jquery", "jhapi", "project","handlebars"], function ($, JHAPI) {
    "use strict";
    
    var base_url = window.jhdata.base_url;
    var user = window.jhdata.user;
    var api = new JHAPI(base_url);
    var proj_name = window.jhdata.proj_name;

    
    api.get_project(user, proj_name, {

        success: function (response) {
            var data = JSON.parse(JSON.stringify(response));
            $('#proj_info').append(data.owner);
            $('#proj_info').append(data.create_time);
            $('#proj_info').append(data.last_update);
            $('#proj_info').append(data.config);
        }
    });


    api.get_project_sessions(user, proj_name, {

        success: function (response) {
            var data = JSON.parse(JSON.stringify(response));
            $('#all_sessions').append(JSON.stringify(response));
            /*$('#proj_info').append(data.create_time);
            $('#proj_info').append(data.last_update);
            $('#proj_info').append(data.config);*/
        }
    });

    
  // Grab the template script
  var theTemplateScript = $("#address-template").html();

  // Compile the template
  var theTemplate = Handlebars.compile(theTemplateScript);

  // Define our data object
  var context={
    "city": "London",
    "street": "Baker Street",
    "number": "221B"
  };

  // Pass our data to the template
  var theCompiledHtml = theTemplate(context);

  // Add the compiled html to the page
  $('.content-placeholder').html(theCompiledHtml);
});
