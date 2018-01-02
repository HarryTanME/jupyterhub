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
                        '<td> Description:</td>', '<td>{{config.description}}</td>',
                    '</tr>',
                    '<tr >',
                        '<td> Server Image:</td>', '<td>{{config.docker_image}}</td>',
                    '</tr>',
                    '<tr >',
                        '<td> Data Sources:</td>', '<td>{{config.data_sources}}</td>',
                    '</tr>',
                    '</table>'].join("\n");

                var html = Mustache.render(template, response);
                $("#proj_info").append(html);
        }
    });

/*
    api.get_project_sessions(user, proj_name, {
        success: function (response) {
            var data = JSON.parse(JSON.stringify(response));
            $('#proj_sessions').append(JSON.stringify(response));

                var template = ['<div>All Sessionss:</div>',
                    '<table>',
                   '{{#.}}',
                    '<tr class="user-row" >',
                        '<td > <span class ="session-choose btn-link" data-servername="{{name}}" > {{name if name != "" else "Default Session"}}',
                            '</span>',
                            '</td> ',
                        '<td> <a class ="btn-info btn-xs" href="{{ user.url}}{name}}" target="_blank" >Open Session</a>',
                            '</td>',
                        '<td> <span role="button" class="stop-server btn-xs btn-danger" data-servername="{{name}}">Stop</span></td>',
                    '</tr>',
                    '{{/.}}',
                    '</table>'].join("\n");

                var html = Mustache.render(template, response);
                $("#proj_sessions").empty().append(html);
        }
    });

   */
});
