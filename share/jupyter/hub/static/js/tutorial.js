
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
        
        if(image == 'dl'){
            image = "wodeai/deeplearning:hubdev"
        }else if(image == 'nlp'){
            image = "wodeai/nlp:hubdev"
        } else if(image == 'r'){
            image = "wodeai/r-notebook:hubdev"
        }else{
            image = "wodeai/datascience:hubdev"
        }
        var datastr='{"docker_image": "'.concat(image).concat('", "pre-cmd":"git clone ').concat(github).concat('; "}')
        
        api.start_named_session(user, session_name, {
            success: function (response) {
                var data = JSON.parse(response);
                //window.location.replace(data.url);
                window.open(data.url);
            },
            data: datastr
        });
    });
});    