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

    @gen.coroutine
    @token_authenticated
    def post(self,name, session_name, tag):
        
        user = self.find_user(name)
        if user is None:
            raise web.HTTPError(400, "User [{}] doesn't exists.".format(name))
            
        session = user.find_session(session_name)
        
        if session is None:
            raise web.HTTPError(400, "Session [{}] doesn't exists.".format(session_name))

        new_tag= orm.Tag()#fixme
        self.db.add(new_tag)
        self.db.commit()
        self.set_status(200)
        self.write('{"status":"success", "message":"Tag is posted."}')
    
    @gen.coroutine
    @token_authenticated
    def get(self, user, project_name):
        self.write('{"status":"success", "message":"Content of the message."}')
        
        user = self.find_user(name)
        if user is None:
            raise web.HTTPError(400, "User [{}] doesn't exists.".format(name))
            
        aa = []
        tags = self.find_project_tags(user, project_name)#fixme
        for tag in tags:
            aa.append(tag)#fixme
        self.set_status(200)
        self.write(json.dumps(aa))
    
    @gen.coroutine
    @token_authenticated
    def delete(self,name, session_name, tag):
        session_tag = self.find_session_tag(session_name, tag)#fixme
        #if session_tag is None:
        #    raise web.HTTPError(400, "Session [{}] doesn't exists.".format(session_name))

        self.log.info("Deleting project %s for user %s", session_name, tag)
        self.db.delete(session_tag)
        self.db.commit()
        self.set_status(200)
        self.write('{"status":"success", "message":"Tag is deleted."}')

default_handlers = [
    (r"/api/user/([^/]+)/server/([^/]+)/tag/([^/]+)", TagsAPIHandler),
    (r"/api/user/([^/]+)/project/([^/]*)/tags/?", TagsAPIHandler),
]


