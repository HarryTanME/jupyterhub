"""Tags handlers"""

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.


import json
import binascii
import os,datetime
from tornado import gen, web
import base64
from .. import orm
from ..utils import admin_only, token_authenticated
from .base import APIHandler
from .users import admin_or_self, UserAPIHandler

class TagsAPIHandler(UserAPIHandler):
    """Start and stop single-user servers"""
    
    def find_session_tag(self, session_name, tag):
        tag1 = orm.SessionTag.find_session_tag(self.db, session_name, tag)
        return tag1
        
    
    def find_session(self, session_name):
        spawner = orm.Spawner.find_by_name(self.db, session_name)
        return spawner
    
    @gen.coroutine
    @admin_or_self
    def post(self,name, session_name, tag):
        user = self.find_user(name)
        if user is None:
            raise web.HTTPError(400, "User [{}] doesn't exists.".format(name))
            
        session = self.find_session(session_name)
        
        if session is None:
            raise web.HTTPError(400, "Session [{}] doesn't exists.".format(session_name))

        new_tag= orm.SessionTag(session_name = session_name,user_id =user.id ,tag = tag, create_time =datetime.datetime.now())
        self.db.add(new_tag)
        self.db.commit()
        self.set_status(200)
        self.write({"status":200, "message":"Tag is posted."})
    
    
    @gen.coroutine
    @admin_or_self
    def delete(self,name, session_name, tag):
        session = self.find_session(session_name)   
        if session is None:
            raise web.HTTPError(400, "Session [{}] doesn't exists.".format(session_name))
            
        session_tag = self.find_session_tag(session_name, tag)

        #we purposely don't check the existence of a tag, just to smooth the experience.
        if session_tag is None:
            self.log.warn('Trying to delete a non-existing session tag.')
            self.write('{"status":"success", "message":"Tag is deleted."}')
            return
        #    raise web.HTTPError(400, "Session [{}] doesn't exists.".format(session_name))

        self.log.info("Deleting tag %s for session %s", tag, session_name)
        self.db.delete(session_tag)
        self.db.commit()
        self.set_status(200)
        self.write({"status":200, "message":"Tag is deleted."})

class ProjectTagListAPIHandler(UserAPIHandler):
    """ This API returns the list of tags of a project"""
    def find_tags_by_project(self, user,  proj_name):
        proj = orm.Project.find_one(self.db, user.id, proj_name)
        if proj is None:
            raise web.HTTPError(400, "Project [{}] doesn't exists.".format(proj_name))
        tags = orm.SessionTag.find_by_project(self.db, proj.id)#not tested.
        return tags
    
    @gen.coroutine
    @token_authenticated
    def get(self, name, project_name):
        user = self.find_user(name)
        if user is None:
            raise web.HTTPError(400, "User [{}] doesn't exists.".format(name))
        aa = []
        tags = self.find_tags_by_project(user=user, proj_name=project_name)
        for tag in tags:
            aa.append(tag.tag)
        self.set_status(200)
        self.write(json.dumps(aa))
    
default_handlers = [
    (r"/api/user/([^/]+)/session/([^/]+)/tag/([^/]+)", TagsAPIHandler),
    (r"/api/user/([^/]+)/project/([^/]*)/tags/?", ProjectTagListAPIHandler),
]


