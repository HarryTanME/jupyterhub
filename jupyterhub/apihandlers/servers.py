"""Users/Server handlers"""

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.


import json
import binascii
import os
from tornado import gen, web
import base64,datetime
from .. import orm
from ..utils import admin_only, unique_server_name, token_authenticated
from .base import APIHandler
from .projects import _ProjectAPIHandler, admin_or_self
from .users import UserAPIHandler

def session_model(session):
        ss= {"name":session.name, "project":session.project_id, "option":session.option}
        ss['status'] ='active' if session.end_time is None else 'stopped'
        ss["end_time"] = session.end_time.isoformat() if session.end_time is not None else None
        return ss
    
class UserServerAPIHandler(APIHandler):
    """Start and stop single-user servers"""

    @gen.coroutine
    @admin_or_self
    def post(self, name, server_name=''):
        # force every server has its owner name.
        server_name = unique_server_name(server_name)
        self.log.debug("server name: "+str(server_name))
        user = self.find_user(name)
        if server_name and not self.allow_named_servers:
            raise web.HTTPError(400, "Named servers are not enabled.")
        spawner = user.spawners[server_name]
        pending = spawner.pending
        if pending == 'spawn':
            self.set_header('Content-Type', 'text/plain')
            self.set_status(202)
            return
        elif pending:
            raise web.HTTPError(400, "%s is pending %s" % (spawner._log_name, pending))

        if spawner.ready:
            # include notify, so that a server that died is noticed immediately
            # set _spawn_pending flag to prevent races while we wait
            spawner._spawn_pending = True
            try:
                state = yield spawner.poll_and_notify()
            finally:
                spawner._spawn_pending = False
            if state is None:
                raise web.HTTPError(400, "%s is already running" % spawner._log_name)
            
        options = self.get_json_body()
        if "workspace" not in options:# this is hackable, meaning users can overwrite workspace to mount their own path.
            #self.volumes[user_home] = "/home/wode-user/work/"
            options["workspace"] = self.current_user.user_data_path
            
        yield self.spawn_single_user(user, server_name, options=options)
        status = 202 if spawner.pending == 'spawn' else 201
        self.set_header('Content-Type', 'text/plain')
        self.set_status(status)
        self.write(json.dumps({"session_name":"{}".format(server_name),"url":str(user.url+server_name)}))
    
    def _getActiveSpawners(self, user):
        spawners = orm.Spawner.find_all_active_sessions(self.db, user.id)
        return spawners
    
    def _getAllSpawners(self, user):
        spawners = orm.Spawner.find_by_userid(self.db, user.id)
        return spawners
    
    
        
    @gen.coroutine
    @admin_or_self
    def get(self, name):
        tag = self.get_argument("tag", None, False) #just a placeholder, not implemented.
        sess_stats = self.get_argument("status", None, False)         
        user = self.find_user(name)
        if user is None:
            status=400
            error_json ={"error":status, "message":"User {} doesn't exists".format(name)}
            self.set_status(status)
            self.write(json.dumps(error_json))
        elif sess_stats is not None and sess_stats != "" :
            if sess_stats not in ['active']:
                raise  web.HTTPError(403, 'Status can only be "active" (for now).')
            orm_spawners = self._getActiveSpawners(user)
            data =[]
            for s in orm_spawners:
                data.append(session_model(s))
            status = 200
            self.set_status(status)
            self.write(json.dumps(data))
        else:
            orm_spawners = self._getAllSpawners(user)
            status = 200
            self.set_status(status)
            data =[]
            for s in orm_spawners:
                data.append(session_model(s))
            self.write(json.dumps(data))
            
    @gen.coroutine
    @admin_or_self
    def delete(self, name, server_name=''):
        user = self.find_user(name)
        if server_name:
            if not self.allow_named_servers:
                raise web.HTTPError(400, "Named servers are not enabled.")
            if server_name not in user.spawners:
                raise web.HTTPError(404, "%s has no server named '%s'" % (name, server_name))

        spawner = user.spawners[server_name]
        if spawner.pending == 'stop':
            self.log.debug("%s already stopping", spawner._log_name)
            self.set_header('Content-Type', 'text/plain')
            self.set_status(202)
            return

        if not spawner.ready:
            raise web.HTTPError(
                400, "%s is not running %s" %
                (spawner._log_name, '(pending: %s)' % spawner.pending if spawner.pending else '')
            )
        # include notify, so that a server that died is noticed immediately
        status = yield spawner.poll_and_notify()
        if status is not None:
            raise web.HTTPError(400, "%s is not running" % spawner._log_name)
        yield self.stop_single_user(user, server_name)
        status = 202 if spawner._stop_pending else 204
        self.set_status(status)

class ServerStatusAPIHandler(APIHandler):
    @gen.coroutine
    def _getData(self, user, server_name=""):
        spawner = user.spawners[server_name]
#        c= yield spawner.get_container()
#        for a in c['State']:
#            print(a)
        data=yield spawner._status()
        print(data)
        return data["status"]

    @gen.coroutine
    @admin_or_self
    def get(self, name, server_name=''):
        user = self.find_user(name)
        if user is None:
            status=400
            error_json ={"error":status, "message":"User {} doesn't exists".format(name)}
            self.set_status(status)
            self.write(json.dumps(error_json))
        else:
            data = yield self._getData(user, server_name)
            status = 200
            self.set_status(status)
            self.write(data)
            
class ServerLogsAPIHandler(UserServerAPIHandler):
    @gen.coroutine
    def _getData(self, user, server_name=""):
        spawner = user.spawners[server_name]
        log= yield spawner._logs_container()
        return log
    
    @gen.coroutine
    @admin_or_self
    def get(self, name, server_name=''):
        user = self.find_user(name)
        if user is None:
            status=400
            error_json ={"error":status, "message":"User {} doesn't exists".format(name)}
            self.set_status(status)
            self.write(json.dumps(error_json))
        else:
            data = yield self._getData(user, server_name)
            status = 200
            self.set_status(status)
            self.write(data)
        
class ServerStatsAPIHandler(UserServerAPIHandler):
    @gen.coroutine
    def _getData(self, user, server_name=""):
        spawner = user.spawners[server_name]
        hist= spawner.stats_history
#        print(str(hist))
        return hist
    
    @gen.coroutine
    @admin_or_self
    def get(self, name, server_name=''):
        user = self.find_user(name)
        if user is None:
            status=400
            error_json ={"error":status, "message":"User {} doesn't exists".format(name)}
            self.set_status(status)
            self.write(json.dumps(error_json))
        else:
            data = yield self._getData(user, server_name)
            status = 200
            self.set_status(status)
            self.write(json.dumps(data))
            
class ServerOutputsAPIHandler(UserServerAPIHandler):
    @gen.coroutine
    def _getData(self, user, server_name=""):
        return {"data":"Output"}
    
    @gen.coroutine
    @admin_or_self
    def get(self, name, server_name=''):
        user = self.find_user(name)
        if user is None:
            status=400
            error_json ={"error":status, "message":"User {} doesn't exists".format(name)}
            self.set_status(status)
            self.write(json.dumps(error_json))
        else:
            data = yield self._getData(user, server_name)
            status = 200
            self.set_status(status)
            self.write(data)  


class ProjectServerAPIHandler(_ProjectAPIHandler):
    
    @gen.coroutine
    @admin_or_self
    def post(self, name, proj_name, server_name=''):
        # force every server has its owner name.
        timestamp= datetime.datetime.now().strftime('%y%m%d%H%M%S%f')
        if server_name == "":
            server_name = "DefaultServer"
        server_name +=timestamp
        user = self.find_user(name)
        project = self.find_user_project(user, proj_name)
        
        if server_name and not self.allow_named_servers:
            raise web.HTTPError(400, "Named servers are not enabled.")
        spawner = user.spawners[server_name]
        pending = spawner.pending
        if pending == 'spawn':
            self.set_header('Content-Type', 'text/plain')
            self.set_status(202)
            return
        elif pending:
            raise web.HTTPError(400, "%s is pending %s" % (spawner._log_name, pending))

        if spawner.ready:
            # include notify, so that a server that died is noticed immediately
            # set _spawn_pending flag to prevent races while we wait
            spawner._spawn_pending = True
            try:
                state = yield spawner.poll_and_notify()
            finally:
                spawner._spawn_pending = False
            if state is None:
                raise web.HTTPError(400, "%s is already running" % spawner._log_name)
        
        options = json.loads(project.config)
        options.update(self.get_json_body() or {})
        options['project_name'] = proj_name #inject projectname so that the program will save the spawner with project name.
        print("~~~~options~~~~~"+str(options))  
        
        yield self.spawn_single_user(user, server_name, options=options)
        status = 202 if spawner.pending == 'spawn' else 201
        self.set_header('Content-Type', 'text/plain')
        self.set_status(status)
        self.write(json.dumps({"session_name":"{}".format(server_name),"url":str(user.url+server_name)}))
    

class ServerTagsAPIHandler(UserAPIHandler):
    """API returns the list of tags for a given session/server."""
    def find_tags_by_session(self, session_name):
        tags = orm.SessionTag.find_by_session(self.db, session_name)
        return tags
    
    #find by tags
    def find_session_tags(self, tag):
        sessions = orm.SessionTag.find_by_tag(tag)
        return sessions
    
    @gen.coroutine
    @admin_or_self
    def get(self, name, session_name): 
        session = self.find_session(session_name)                            
        if session is None:
            raise web.HTTPError(400, "Session [{}] doesn't exists.".format(session_name))
            
        aa = []
        tags = self.find_tags_by_session(session_name)
        for tag in tags:
            aa.append(tag.tag)
        self.set_status(200)
        self.write(json.dumps(aa))
    

class SesseionListAPIHandler(UserAPIHandler):
    """ This API returns the list of sessions in a project by a given tag."""
    def find_by_project(self, proj_name, tag):
        sessions = orm.SessionTag.find_sessions_by_project_tag(self.db, proj_name, tag)
        return sessions
    
    
    def all_sesssions(self, user, proj_name):
        sessions = orm.Spawner.find_all_sessions(self.db, user.id, proj_name)
        return sessions

    @gen.coroutine
    @admin_or_self
    def get(self, user, project_name):
        user = self.find_user(user)
        if user is None:
            status=400
            error_json ={"error":status, "message":"User {} doesn't exists".format(name)}
            self.set_status(status)
            self.write(json.dumps(error_json))
            return
        tag = self.get_argument("tag", None, False)
        if tag is not None and tag != "":
            aa = []
            sessions = self.find_by_project(project_name, tag)
            for s in sessions:
                aa.append(session_model(s))
            self.set_status(200)
            self.write(json.dumps(aa))
        else :
            sessions =  self.all_sesssions(user, project_name)
            print(str(sessions))
            aa = []
            for s in sessions:
                aa.append(session_model(s))
            self.set_status(200)
            self.write(json.dumps(aa))

default_handlers =[
    (r"/api/user/([^/]+)/sessions/?", UserServerAPIHandler),
    (r"/api/user/([^/]+)/project/([^/]+)/session/([^/]*)", ProjectServerAPIHandler),
    (r"/api/user/([^/]+)/project/([^/]*)/sessions/?", SesseionListAPIHandler),
    (r"/api/user/([^/]+)/session/([^/]*)", UserServerAPIHandler),
    (r"/api/user/([^/]+)/session/([^/]*)/status/?", ServerStatusAPIHandler),
    (r"/api/user/([^/]+)/session/([^/]*)/stats/?", ServerStatsAPIHandler),
    (r"/api/user/([^/]+)/session/([^/]*)/logs/?", ServerLogsAPIHandler),
    (r"/api/user/([^/]+)/session/([^/]*)/outputs/?", ServerOutputsAPIHandler),
    (r"/api/user/([^/]+)/session/([^/]*)/tags/?", ServerTagsAPIHandler),
]