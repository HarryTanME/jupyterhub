// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.

define(['jquery', 'utils'], function ($, utils) {
    "use strict";

    var JHAPI = function (base_url) {
        this.base_url = base_url;
    };
    
    var default_options = {
        type: 'GET',
        contentType: "application/json",
        cache: false,
        dataType : "json",
        processData: false,
        success: null,
        error: utils.ajax_error_dialog,
    };
    
    var update = function (d1, d2) {
        $.map(d2, function (i, key) {
            d1[key] = d2[key];
        });
        return d1;
    };
    
    var ajax_defaults = function (options) {
        var d = {};
        update(d, default_options);
        update(d, options);
        return d;
    };
    
    JHAPI.prototype.api_request = function (path, options) {
        options = options || {};
        options = ajax_defaults(options || {});
        var url = utils.url_path_join(
            this.base_url,
            'api',
            utils.encode_uri_components(path)
        );
        $.ajax(url, options);
    };
    
    
    
    JHAPI.prototype.get_project = function (user, proj_name, options) {
        options = options || {};
        options = update(options, {type: 'GET', dataType: null});

        this.api_request(utils.url_path_join('user', user, 'project',proj_name), options);
    };
    
    
    JHAPI.prototype.get_sessions = function (user, options) {
        options = options || {};
        options = update(options, {type: 'GET', dataType: null});

        this.api_request(utils.url_path_join('user', user, 'sessions'), options);
    };
    
    JHAPI.prototype.get_active_sessions = function (user, options) {
        options = options || {};
        options = update(options, {type: 'GET', dataType: null});
        //FIXME: This is too ugly.
        this.api_request(utils.url_path_join('user', user, 'sessions?status=active'), options);
    };
    
    JHAPI.prototype.get_project_sessions = function (user, proj_name, options) {
        options = options || {};
        options = update(options, {type: 'GET', dataType: null});

        this.api_request(utils.url_path_join('user', user, 'project',proj_name, 'sessions'), options);
    };
    
    JHAPI.prototype.get_project_tags = function (user, proj_name, options) {
        options = options || {};
        options = update(options, {type: 'GET', dataType: null});

        this.api_request(utils.url_path_join('user', user, 'project',proj_name, 'tags'), options);
    };
    //FIXME
    JHAPI.prototype.get_project_sessions_by_tags = function (user, proj_name, tag, options) {
        options = options || {};
        options = update(options, {type: 'GET',data:"tag=".concat(tag), dataType: null});

        this.api_request(utils.url_path_join('user', user, 'project',proj_name, 'sessions'), options);
    };
    JHAPI.prototype.get_session_logs = function (user, session_name, options) {
        options = options || {};
        options = update(options, {type: 'GET', dataType: "text"});

        this.api_request(utils.url_path_join('user', user,  'session',session_name,'logs'), options);
    };
    
    JHAPI.prototype.get_session_status = function (user, session_name, options) {
        options = options || {};
        options = update(options, {type: 'GET', dataType: null});

        this.api_request(utils.url_path_join('user', user,  'session',session_name,'status'), options);
    };
    
    JHAPI.prototype.get_session_stats = function (user, session_name, options) {
        options = options || {};
        options = update(options, {type: 'GET', dataType: null});

        this.api_request(utils.url_path_join('user', user,  'session',session_name,'stats'), options);
    };
    
    JHAPI.prototype.get_session_tags = function (user, session_name, options) {
        options = options || {};
        options = update(options, {type: 'GET', dataType: null});

        this.api_request(utils.url_path_join('user', user,  'session',session_name,'tags'), options);
    };
    
    JHAPI.prototype.get_session_comments = function (user, session_name, options) {
        options = options || {};
        options = update(options, {type: 'GET', dataType: null});

        this.api_request(utils.url_path_join('session',session_name,'comments'), options);
    };
    
    JHAPI.prototype.get_project_comments = function (user, proj_name, options) {
        options = options || {};
        options = update(options, {type: 'GET', dataType: null});

        this.api_request(utils.url_path_join('user',user,'project', proj_name,'comments'), options);
    };
    
    JHAPI.prototype.start_server = function (user, options) {
        options = options || {};
        options = update(options, {type: 'POST', dataType: null});
        this.api_request(
            utils.url_path_join('user', user, 'session'),
            options
        );
    };
    JHAPI.prototype.delete_seassion = function (user, session_name, options) {
        options = options || {};
        options = update(options, {type: 'GET', dataType: null});
        this.api_request(
            utils.url_path_join('user', user, 'session',session_name,'archive'),
            options
        );
    };
    JHAPI.prototype.start_project = function (user, proj_name, options) {
        options = options || {};
        options = update(options, {type: 'POST', dataType: null});
        this.api_request(
            utils.url_path_join('user', user, 'project', proj_name,'session',proj_name),
            options
        );
    };
    
    JHAPI.prototype.add_session_tag = function (user, session_name, tag, options) {
        options = options || {};
        options = update(options, {type: 'POST', dataType: null});
        this.api_request(
            utils.url_path_join('user', user, 'session', session_name,'tag',tag),
            options
        );
    };
    
    JHAPI.prototype.add_session_comment = function (user, session_name, comment, options) {
        options = options || {};
        var comment_data ={"body":comment};
        options = update(options, {type: 'POST',data:JSON.stringify(comment_data), dataType: null});
        this.api_request(
            utils.url_path_join('session', session_name,'comment'),
            options
        );
    };
    
    JHAPI.prototype.add_project_comment = function (user, project_name, comment, options) {
        options = options || {};
        var comment_data ={"body":comment};
        options = update(options, {type: 'POST',data:JSON.stringify(comment_data), dataType: null});
        this.api_request(
            utils.url_path_join('user',user,'project', project_name,'comment'),
            options
        );
    };
    
    
    JHAPI.prototype.delete_session_comment =function (user, session_name, comment_id, options) {
        options = options || {};
        options = update(options, {type: 'DELETE', dataType: null});
        this.api_request(
            utils.url_path_join('session', session_name,'comment', comment_id),
            options
        );
    };
    
    JHAPI.prototype.delete_project_comment =function (user, project_name, comment_id, options) {
        options = options || {};
        options = update(options, {type: 'DELETE', dataType: null});
        this.api_request(
            utils.url_path_join('user',user,'project', project_name,'comment', comment_id),
            options
        );
    };
    
    JHAPI.prototype.start_named_session = function (user, session_name, options) {
        options = options || {};
        options = update(options, {type: 'POST', dataType: null});
        this.api_request(
            utils.url_path_join('user', user, 'session', session_name),
            options
        );
    };
    
    
    JHAPI.prototype.delete_project = function (user, proj_name, options) {
        options = options || {};
        options = update(options, {type: 'DELETE', dataType: null});
        this.api_request(
            utils.url_path_join('user', user, 'project', proj_name),
            options
        );
    };
    
    
    JHAPI.prototype.delete_session = function (user, session_name, options) {
        options = options || {};
        options = update(options, {type: 'DELETE', dataType: null});
        this.api_request(
            utils.url_path_join('user', user, 'session', session_name),
            options
        );
    };
    
    JHAPI.prototype.stop_server = function (user, server_name, options) {
        options = options || {};
        options = update(options, {type: 'DELETE', dataType: null});
        this.api_request(
            utils.url_path_join('user', user, 'session', server_name),
            options
        );
    };
    
    JHAPI.prototype.list_users = function (options) {
        this.api_request('users', options);
    };
    
    JHAPI.prototype.get_user = function (user, options) {
        this.api_request(
            utils.url_path_join('users', user),
            options
        );
    };
    
    JHAPI.prototype.add_users = function (usernames, userinfo, options) {
        options = options || {};
        var data = update(userinfo, {usernames: usernames});
        options = update(options, {
            type: 'POST',
            dataType: null,
            data: JSON.stringify(data)
        });
        
        this.api_request('users', options);
    };
    
    JHAPI.prototype.edit_user = function (user, userinfo, options) {
        options = options || {};
        options = update(options, {
            type: 'PATCH',
            dataType: null,
            data: JSON.stringify(userinfo)
        });
        
        this.api_request(
            utils.url_path_join('user', user),
            options
        );
    };
    
    JHAPI.prototype.admin_access = function (user, options) {
        options = options || {};
        options = update(options, {
            type: 'POST',
            dataType: null,
        });
        
        this.api_request(
            utils.url_path_join('user', user, 'admin-access'),
            options
        );
    };
    
    JHAPI.prototype.delete_user = function (user, options) {
        options = options || {};
        options = update(options, {type: 'DELETE', dataType: null});
        this.api_request(
            utils.url_path_join('user', user),
            options
        );
    };

    JHAPI.prototype.request_token = function (options) {
        options = options || {};
        options = update(options, {type: 'POST'});
        this.api_request('authorizations/token', options);
    };

    JHAPI.prototype.shutdown_hub = function (data, options) {
        options = options || {};
        options = update(options, {type: 'POST'});
        if (data) {
            options.data = JSON.stringify(data);
        }
        this.api_request('shutdown', options);
    };
    
    return JHAPI;
});