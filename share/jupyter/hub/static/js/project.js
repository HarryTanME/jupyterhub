// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.

require(["jquery", "jhapi","handlebars"], function ($, JHAPI) {
    "use strict";
    
    var base_url = window.jhdata.base_url;
    var user = window.jhdata.user;
    var api = new JHAPI(base_url);
    var proj_name = window.jhdata.proj_name;
    var user_url = window.jhdata.user_url;
    var readme =  window.jhdata.readme;
    var file_tree =  window.jhdata.file_tree;
    
    $(document).on("click", ".start-project", function (e) {
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
    
    $(document).on("click", ".delete-session", function (e) {  

        var session_name = $(this).data('servername');
        window.alert('Are you sure?');
        api.delete_seassion(user, session_name, {
            success: function (response) {
                window.location.reload(true);
            }
        });
    });
    
    $(document).on("click", ".delete-project", function (e) {       
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
    
    api.get_project(user, proj_name, {

        success: function (response) {
            var data = JSON.parse(JSON.stringify(response));
                       
                var template = [
                    '<table>',
                    '<tr >',
                        '<td> Project Name:</td>', '<td> <b>{{config.name}}</b> </td>',
                    '</tr>',
                    '<trc>',
                        '<td >Project Owner:</td> ', '<td>  {{owner}} </td> ',
                    '</tr>',
                    '<tr>',
                        '<td> Create Time:</td>','<td>{{create_time}}</td>',
                    '</tr>',
                    '<tr >',
                        '<td> Last Update:</td>','<td>{{last_update}}</td>',
                    '</tr>',
                    '<tr >',
                        '<td> Git Repo:</td>', '<td>{{config.git_repo}}</td>',
                    '</tr>',
                    '<tr >',
                    '<tr >',
                        '<td> Server Image:</td>', '<td>{{config.docker_image}}</td>',
                    '</tr>',
                    '<tr >',
                        '<td> Data Sources:</td>', '<td>{{config.data_sources}}</td>',
                    '</tr>',
                    '<tr>',
                        '<td> Description:</td>', '<td>{{config.description}}</td>',
                    '</tr>',
                    '</table>',
                    ' <span role="button" class="start-project btn btn-sm btn-success" data-projname="{{name}}">Start Project Session </span> ',
                    '<span role="button" class="show-all-files btn-link btn-sm" data-projname="{{name}}">Show Files</span> ',
                    '<span role="button" class="show-all-tags btn-link btn-sm" data-projname="{{name}}">Show Tags</span> ',
                    '<span role="button" class="show-all-sessions btn-link btn-sm" data-projname="{{name}}">Show Sessions</span> ',
                    '<span role="button" class="show-all-comments btn-link btn-sm" data-projname="{{name}}">Show Comments</span> ',
                    '<span role="button" class="delete-project btn btn-xs" data-projname="{{name}}">Delete Project</span> ',
                    ].join("\n");

                var html = Mustache.render(template, response);
                $("#proj_info").append(html);
        }
    });

    function reloadSessions(data){
        //$('#proj_sessions').append(JSON.stringify([data[0]]));
            var actives = [];
            var stops = [];
            
            for (var i= 0; i<data.length; i++){
                if(data[i].status == 'stopped'){
                    stops.push(data[i]);
                }else{
                    actives.push(data[i]);
                }
            } 
            
            var active_temp = ['{{#.}}','<span role="button" class ="session-choose btn-link" data-servername="{{name}}" > {{name}}</span>',
                                '<div><a class ="btn-info btn-xs" href="'.concat(user_url).concat('{{name}}" target="_blank" >Open Session</a>'),
                                '<span role="button" class="stop-server btn-xs btn-danger" data-servername="{{name}}">Stop</span></div>',
                              '{{/.}}'].join("\n");

            var stopped_temp =['{{#.}}',
                        '<span role="button" class ="session-choose btn-link" data-servername="{{name}}" > {{name}}',
                            '</span>',
                        '<div>{{status}}   at {{end_time}}',
                        '<span role="button" class="delete-session btn-xs btn-danger" data-servername="{{name}}">X</span></div>',
                        '{{/.}}'].join("\n");
            
            
            var active_html =  Mustache.render(active_temp, actives);
            var stopped_html=  Mustache.render(stopped_temp, stops);

            
                var html = ['<div>All Sessionss:</div>',
                    '<div>',
                    active_html,
                    stopped_html,
                    '</div>'].join("\n");

                $("#proj_sessions").empty().append(html);
    }
    
    
    
    
    function reloadComments(response){
        //$("#proj_sessions").empty().append(JSON.stringify([data[0]]));
        var len = response.length;
                var item = null;
                for(var i = 0; i < len; i++) {
                    item = response[i];
                    response[i].body = '<p>' + response[i].body.replace(/\n/g, "</p>\n<p>") + '</p>';
                }

                var template = [
                    '{{#.}}',
                    '<div>',
                        '<div class="CommentMeta">{{comment_by}} wrote at {{create_time}}:',
                        '<span role="button" class="delete-project-comment btn btn-link" data-commentId="{{id}}"  >DELETE</span>',
                        '</div>',
                        '<div class="CommentBody">{{{body}}}</div>',
                        '<br/>',
                    '</div>',
                    '{{/.}}',
                    
                '<div class="comment-form">',
                    '<div><textarea class="form-textarea" id="comment_body_id" placeholder=" Share your thoughts here." rows="4" cols="90"></textarea></div>',
                    '<button class="add-project-comment" >Add Comment</button> ',
                '</div>',
                ].join("\n");
                /*FIXME the {{body}} is not formated, no way to return to new lines. */
                var html = Mustache.render(template, response);
                
                $("#proj_sessions").empty().append(html);
    }
    
    $(document).on("click", ".show-all-files", function (e) {  
         console.log(unescape(file_tree));
        $("#proj_sessions").empty().append(unescape(file_tree));
    });
    
                   
    $(document).on("click", ".add-project-comment", function (e) {  
        var project_name = proj_name;
        var comment= document.getElementById("comment_body_id").value;
        if (comment == null | comment == ""){
            window.alert("Commment is empty.");
        }else if (comment.length > 2250){
            
            window.alert("Your comments is longer than the system limit of 2250 characters.\n Can you break it down to several comments?");
        }
        else{
        api.add_project_comment(user, project_name,comment, {
            success: function (response) {
                
                api.get_project_comments(user, proj_name, {
                    success: function (response) {
                        var data = JSON.parse(JSON.stringify(response));
                        reloadComments(data);
                    }
                });
                var box = document.getElementById("comment_body_id");
                box.value = "";
            }
        });
        }
    });
    
    $(document).on("click", ".delete-project-comment", function (e) {  
        var project_name = proj_name; 
        var comment_id = $(this).data('commentid');

        api.delete_project_comment(user, project_name,comment_id, {
                success: function (response) {
                    
                api.get_project_comments(user, proj_name, {
                    success: function (response) {
                        var data = JSON.parse(JSON.stringify(response));
                        reloadComments(data);
                    }
                });
                }
            });
    });
    
    
    
    $(document).on("click", ".show-all-sessions", function (e) {  
        var btn = $(e.target);
        btn.attr("disabled", "disabled");
        
        api.get_project_sessions(user, proj_name, {
            success: function (response) {
                var data = JSON.parse(JSON.stringify(response));
                reloadSessions(data);
            }
        });
        btn.removeAttr('disabled');
    });
    
    
    $(document).on("click", ".show-all-comments", function (e) {  
        var btn = $(e.target);
        btn.attr("disabled", "disabled");
        
        api.get_project_comments(user, proj_name, {
            success: function (response) {
                var data = JSON.parse(JSON.stringify(response));
                reloadComments(data);
            }
        });
        btn.removeAttr('disabled');
    });
    
    $(document).on("click", ".stop-server", function (e) {  
        var btn = $(e.target);
        btn.attr("disabled", "disabled");
        
        var server_name = $(this).data('servername');
        if (confirm("Are you sure to stop the running server?") == true) {
            api.stop_server(user, server_name, {
                success: function () {
                    window.location.reload(true);
                }
            });
        }else{
            btn.removeAttr('disabled');
        }
    });

    $(document).on("click", ".show-all-tags", function (e) {  
        api.get_project_tags(user, proj_name, {
            success: function (response) {
                var data = JSON.parse(JSON.stringify(response));
                //$('#proj_sessions').append(JSON.stringify(response));

                    var template = ['<div>All Tag:</div>',
                        '<div>',
                       '{{#.}}',
                            '<span role="button" class ="get-sessions-by-tag btn-link" data-tag="{{tag}}" >{{tag}}({{count}})  </span>',
                        '{{/.}}',
                        '</div>'].join("\n");

                    var html = Mustache.render(template, response);
                    $("#proj_sessions").empty().append(html);
            }
        });
    });
    
    $(document).on("click", ".get-sessions-by-tag", function (e) {     

        var tag = $(this).data('tag');
        api.get_project_sessions_by_tags(user, proj_name, tag,{
        success: function (response) {
            var data = JSON.parse(JSON.stringify(response));
            //$('#proj_sessions').append(JSON.stringify(response));
            reloadSessions(data);
            }
        });
        
    });
});
