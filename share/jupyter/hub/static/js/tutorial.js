
require(["jquery", "jhapi"], function ($, JHAPI) {
    "use strict";
    
    var base_url = window.jhdata.base_url;
    var user = window.jhdata.user;
    var api = new JHAPI(base_url);
    
    $(".start-project").click(function (e) {
        var btn = $(e.target);
        btn.attr("disabled", "disabled");
        
        
        var github = $(this).data('github');
        var image = $(this).data('image');
        var session_name =$(this).data('name');
        var default_notebook = $(this).data('path');
        
        if(image == 'dl'){
            image = "wodeai/deeplearning:hubdev";
        }else if(image == 'nlp'){
            image = "wodeai/nlp:hubdev";
        } else if(image == 'r'){
            image = "wodeai/r-notebook:hubdev";
        }else{
            image = "wodeai/datascience:hubdev";
        }
        if (typeof default_notebook == 'undefined'){
            var datastr='{"docker_image": "'.concat(image).concat('", "pre-cmd":"git clone ').concat(github).concat(';" }');
        }else{
            var datastr='{"docker_image": "'.concat(image).concat('", "pre-cmd":"git clone ').concat(github).concat('; ", ').concat(' "argv":["--NotebookApp.default_url=').concat(default_notebook).concat('"] }');
        }
        api.start_named_session(user, session_name, {
            success: function (response) {
                btn.removeAttr('disabled');
                var data = JSON.parse(response);
                //window.location.replace(data.url);
                window.open(data.url);
            },
            data: datastr
        });
    });
});    