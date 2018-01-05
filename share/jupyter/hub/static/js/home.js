// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.

require(["jquery", "jhapi", "Mustache"], function ($, JHAPI) {
    "use strict";
    
    var base_url = window.jhdata.base_url;
    var user = window.jhdata.user;
    var api = new JHAPI(base_url);
    var selected_session = window.jhdata.selected_session;
    
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
        if (val != null){
            api.add_session_comment(user, session_name,comment, {
                success: function (response) {
                    reloadCommentTab(selected_session);
                }
            });
        }
    });
     $(".add-session-comment2").click(function (e) {
      
        var session_name = selected_session;
        var comment= document.getElementById("comment_body_id").value;
        if (comment == null | comment == ""){
            window.alert("Commment is empty.");
        }else if (comment.length > 2250){
            
            window.alert("Your comments is longer than the system limit of 2250 characters.\n Can you break it down to several comments?");
        }
        else{
        api.add_session_comment(user, session_name,comment, {
            success: function (response) {
                reloadCommentTab(selected_session);
                var box = document.getElementById("comment_body_id");
                box.value = "";
            }
        });
        }
    });
    
    $(".delete-session-comment").click(function (e) {   
         window.alert("  adsfad "); 
           // window.alert(session_name+"   "+comment_id); 
        var session_name = $(this).data('sessionName'); 
        var comment_id = $(this).data('commentId');
        api.delete_session_comment(user, session_name,comment_id, {
                success: function (response) {
                    reloadCommentTab(session_name);
                }
            });
    });
    
    
    $(".session-logs").click(function (e) {        
        var session_name = $(this).data('servername');

        reloadLogTab(session_name);
    });
    
    $("#log_tablink").click(function (e) { 
        $('#logs_tab').empty();
        reloadLogTab(selected_session);
    });
    
    function reloadLogTab (session_name) {        
       api.get_session_logs(user, session_name, {
            success: function (response) {
                $('#logs_tab').empty().append(response.replace(/(\r\n|\n|\r)/gm, "<br>"));
            }
        });
    }
    
    $(".session-stats").click(function (e) {        
        var session_name = $(this).data('servername');
        reloadStatsTab(session_name);
    });

    $("#stats_tablink").click(function (e) {  
        reloadStatsTab(selected_session);
    });

    function reloadStatsTab(session_name){
        
        api.get_session_stats(user, session_name, {
            success: function (response) {
                //$('#session_info').empty().append(response)
                
              
              google.charts.load('current', {'packages':['corechart']});
              google.charts.setOnLoadCallback(drawChart);

              function drawChart() {
                // 5. Create a new DataTable (Charts expects data in this format)
                var cpudata = new google.visualization.DataTable();
                var ramdata = new google.visualization.DataTable();


                // 6. Add two columns to the DataTable
                cpudata.addColumn('datetime', 'Timestamp');
                cpudata.addColumn('number',   'CPU');
                
                ramdata.addColumn('datetime', 'Timestamp');
                ramdata.addColumn('number',   'Memory');

                // 7. Cycle through the records, adding one row per record
                var records = response;
                var max_ram = 0.5;
                for (var i = 0; i < records.length; i++){
                    var record = records[i];
                    cpudata.addRow([
                      (new Date(record.timestamp)),
                      parseFloat(record.cpu_usage)
                    ]);
                    ramdata.addRow([
                      (new Date(record.timestamp)),
                      parseFloat(record.ram_usage)
                    ]);
                    if (record.ram_usage>max_ram)
                    {
                        max_ram = record.ram_usage;
                    }
                }
                  max_ram=max_ram*2;//make the chart look better
                var cpuoptions = {
                  title: 'CPU Usage (%)',
                  //curveType: 'function',
                  legend: { position: 'right' },
                  vAxis: {
                    viewWindowMode:'explicit',
                    viewWindow: {
                      max:100,
                      min:0
                    }
                  },
                };
                var ramoptions = {
                  title: 'Memory Usage (GB)',
                  //curveType: 'function',
                  legend: { position: 'right' },
                  vAxis: {
                    viewWindowMode:'explicit',
                    viewWindow: {
                      max:max_ram,
                      min:0
                    }
                  },
                };
                var cpuchart = new google.visualization.LineChart(document.getElementById('cpu_chart'));
                var ramchart = new google.visualization.LineChart(document.getElementById('memory_chart'));

                cpuchart.draw(cpudata, cpuoptions);
                ramchart.draw(ramdata, ramoptions);
              }
            }
        
        });
    }
    
    $(".session-status").click(function (e) {        
        var session_name = $(this).data('servername');
        reloadStatusTab(session_name);
    });
    
    
    $("#status_tablink").click(function (e) {        
        reloadStatusTab(selected_session);
    });
    
    function reloadStatusTab(session_name){
        api.get_session_status(user, session_name, {
            success: function (response) {
                //$('#Status_tab').append(JSON.stringify(response));
                
                google.charts.load('current', {'packages':['table']});
                  google.charts.setOnLoadCallback(drawTable);

                  function drawTable() {
                    var statusdata= response;
                    var data = new google.visualization.DataTable();
                    data.addColumn('string', 'KeyName');
                    data.addColumn('string', 'Value');
                      
                      for (var key in statusdata){
                            data.addRow([key, JSON.stringify(statusdata[key])]);
                      }
                    var table = new google.visualization.Table(document.getElementById('status_table'));
                    
                    table.draw(data, {showRowNumber: false, width: '300', height: '100%'});
                    }
            }
        });
    }
    
    $(".session-comments").click(function (e) {        
        var session_name = $(this).data('servername');
        reloadCommentTab(session_name);
    });
    $("#comment_tablink").click(function (e) {        
        reloadCommentTab(selected_session);
    });
          
    function reloadCommentTab(session_name) {        
        api.get_session_comments(user, session_name, {
            success: function (response) {
                
                var template = [
                    '{{#.}}',
                    '<div>',
                        '<div class="CommentMeta">{{comment_by}} wrote at {{create_time}}:',
                        '<span role="button" class="delete-session-comment btn btn-link" data-commentId="{{id}}" data-sessionName="{{session_name}}" >DELETE</span>',
                        '</div>',
                        '<div class="CommentBody">{{body}}</div>',
                        '<br/>',
                    '</div>',
                    '{{/.}}'
                ].join("\n");
                /*FIXME the {{body}} is not formated, no way to return to new lines. */
                var html = Mustache.render(template, response);
                
                $("#comments_tab").empty().append(html);
            }
        });
    }
    
    function reloadTagTab(session_name){
        
        api.get_session_tags(user, session_name, {
            success: function (response) {
                $('#tags_tab').empty().append(response)
            }
        });
    }
    $(".session-tags").click(function (e) {        
        var session_name = $(this).data('servername');
        reloadTagTab(session_name);
    });
    
    $("#tag_tablink").click(function (e) {        
        
        reloadTagTab(selected_session);
    });
    
    $('.tablink-container .tablink').click(function(e) {
        var id = $(this).data('contenttabid');        
        if(id !== '') {
            $('.tabcontent-container .tabcontent.active').removeClass('active');
            $('.tabcontent-container ' + '#' + id).addClass('active');
        }
    });   
    
    $('.session-choose').click(function (e){
        var session_name = $(this).data('servername');
        selected_session = session_name;
        $('.tabcontent-container .tabcontent.active').removeClass('active');
        $('.tabcontent-container ' + '#Status_tab' ).addClass('active');
        //$('.tabcontent-container .tabcontent.active' ).click();
        

    });
    function loadSessionList(e){
        api.get_active_sessions(user, {
            success: function (response) {
                $('#tags_tab').empty().append(response);
                
                var template = ['<div>Running Servers:</div>',
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

                $("#session_list").empty().append(html);
            }
        });
        
    }
    //loadSessionList();
    
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
    evt.currentTarget.className += " active";
    */


    
    