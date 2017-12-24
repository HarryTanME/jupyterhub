// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.

require(["jquery", "jhapi"], function ($, JHAPI) {
    "use strict";
    
    var base_url = window.jhdata.base_url;
    var user = window.jhdata.user;
    var api = new JHAPI(base_url);
    
     
    $(".stop-server").click(function (e) {
        var btn = $(e.target);
        btn.attr("disabled", "disabled");
        
        var server_name = $(this).data('servername');
        if (confirm("Are you sure?") == true) {
            api.stop_server(user, server_name, {
                success: function () {
                    window.location.reload(true);
                }
            });
        }else{
            btn.removeAttr('disabled');
        }
    });
    
    $(".start-project").click(function (e) {
        var btn = $(e.target);
        btn.attr("disabled", "disabled");
        var proj_name = $(this).data('projname');
        api.start_project(user, proj_name, {
            success: function (response) {
                window.location.reload(true);
                //var data = JSON.parse(response);
                //window.location.replace(data.url);
                //window.open(data.url);
            }
        });
    });
    
    $(".delete-project").click(function (e) {
        var btn = $(e.target);
        btn.attr("disabled", "disabled");
        
        var proj_name = $(this).data('projname');
        if (confirm("Deleted project can't be recovered. Are you sure?") == true) {
            api.delete_project(user, proj_name, {
                success: function (response) {
                }
            });
        } else {
            btn.removeAttr('disabled');
        }

    });
    
    $(".session-more").click(function (e) {
        var x = document.getElementById("sessionCommands");
        
        if (x.style.display === "none") {
            x.style.display = "block";
        } else {
            x.style.display = "none";
        }
        
    });
    
    $(".add-session-tag").click(function (e) {
      
        var session_name = $(this).data('servername');
        var tag= window.prompt("Enter your tag..."); 
        api.add_session_tag(user, session_name, tag,{
            success: function (response) {
            }
        });
        
    });
    
    $(".add-session-comment").click(function (e) {
      
        var session_name = $(this).data('servername');
        var comment= window.prompt("Enter your comments..."); 
        
        api.add_session_comment(user, session_name,comment, {
            success: function (response) {
            }
        });
        
    });
    
    $(".session-logs").click(function (e) {        
        var session_name = $(this).data('servername');
        
        api.get_session_logs(user, session_name, {
            success: function (response) {
                $('#session_info').empty().append(response)
            }
        });
    });
    $(".session-stats").click(function (e) {        
        var session_name = $(this).data('servername');
        
        api.get_session_stats(user, session_name, {
            success: function (response) {
                $('#session_info').empty().append(response)
            }
        });
    });
    $(".session-status").click(function (e) {        
        var session_name = $(this).data('servername');
        
        api.get_session_status(user, session_name, {
            success: function (response) {
                $('#session_info').empty().append(response)
            }
        });
    });
    $(".session-comments").click(function (e) {        
        var session_name = $(this).data('servername');
        
        api.get_session_comments(user, session_name, {
            success: function (response) {
                $('#session_info').empty().append(response)
            }
        });
    });
    $(".session-tags").click(function (e) {        
        var session_name = $(this).data('servername');
        
        api.get_session_tags(user, session_name, {
            success: function (response) {
                $('#session_info').empty().append(response)
            }
        });
    });
    
    
    
    
});


    /*
    function openSessionTabs(evt, cityName) {
        // Declare all variables
        var i, tabcontent, tablinks;

        // Get all elements with class="tabcontent" and hide them
        tabcontent = document.getElementsByClassName("tabcontent");
        for (i = 0; i < tabcontent.length; i++) {
            tabcontent[i].style.display = "none";
        }

        // Get all elements with class="tablinks" and remove the class "active"
        tablinks = document.getElementsByClassName("tablinks");
        for (i = 0; i < tablinks.length; i++) {
            tablinks[i].className = tablinks[i].className.replace(" active", "");
    }

    // Show the current tab, and add an "active" class to the button that opened the tab
    document.getElementById(cityName).style.display = "block";
    evt.currentTarget.className += " active";*/