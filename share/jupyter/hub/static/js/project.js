// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.

require(["jquery", "jhapi","handlebars"], function ($, JHAPI) {
    "use strict";
    
    var base_url = window.jhdata.base_url;
    var user = window.jhdata.user;
    var api = new JHAPI(base_url);
    var proj_name = window.jhdata.proj_name;

    
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
                //    '<span role="button" class="delete-project btn btn-xs btn-danger" data-projname="{{proj.name}}">Delete</span> ',
                    ].join("\n");

                var html = Mustache.render(template, response);
                $("#proj_info").append(html);
        }
    });


    api.get_project_sessions(user, proj_name, {
        success: function (response) {
            var data = JSON.parse(JSON.stringify(response));
            //$('#proj_sessions').append(JSON.stringify(response));

                var template = ['<div>All Sessionss:</div>',
                    '<div>',
                   '{{#.}}',
                        '<span role="button" class ="session-choose btn-link" data-servername="{{name}}" > {{name}}',
                            '</span>',
                        '<div>Status:{{status}} ',
                        '   End Time:{{end_time}}',
                        '<span role="button" class="delete-session btn-xs btn-danger" data-servername="{{name}}">X</span></div>',
                    '{{/.}}',
                    '</div>'].join("\n");

                var html = Mustache.render(template, response);
                $("#proj_sessions").empty().append(html);
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
    
    $(".delete-session").click(function (e) {        
        var session_name = $(this).data('servername');
        window.alert('Are you sure?');
        api.delete_seassion(user, session_name, {
            success: function (response) {
                window.location.reload(true);
            }
        });
    });
    
    
});
