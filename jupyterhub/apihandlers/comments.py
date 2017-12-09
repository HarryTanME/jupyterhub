"""Comments handlers"""

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.


import json
import binascii
import os,datetime
from tornado import gen, web
import base64
from .. import orm
from ..utils import admin_only
from .base import APIHandler
from .users import admin_or_self

class SessionCommentsAPIHandler(APIHandler):
    """Start and stop single-user servers"""

    @gen.coroutine
    @admin_or_self
    def post(self, name, session_id):
        name
        session = self.find_session(session_id)#fixme
        if session is None:
            raise web.HTTPError(400, "Session [{}] doesn't exists.".format(session_id))

        new_tag= orm.Tag()#fixme
        self.db.add(new_tag)
        self.db.commit()
        self.set_status(200)
        self.write('{"status":"success", "message":"Tag is posted."}')
    
    
    @gen.coroutine
    @admin_or_self
    def get(self, name, session_id, comment_id):
        self.write('{"status":"success", "message":"Content of the message."}')
        
    
    @gen.coroutine
    @admin_or_self
    def delete(self, name, session_id, comment_id):
        self.write('{"status":"success", "message":"Comment is deleted."}')
    
    @gen.coroutine
    @admin_or_self
    def put(self, name, session_id, comment_id):
        self.write('{"status":"success", "message":"Comment is updated."}')
        

class ProjectCommentsAPIHandler(APIHandler):
    """Start and stop single-user servers"""

    def _check_comment_model(self, data):
        return True
        checks = [lambda x : x in data.keys() for x in ['body']]
        if all(checks):
            return True
        return False
    
    def _comment_model(self, user, proj_id, comment):
        """Produce the model for an docker comment."""
        return {
            'project_id':proj_id,
            'comment_by': user.id,
            'body':comment.body,
            'create_time':str(comment.create_time),
            'last_update':str(comment.last_update)
        }
    
    def find_project(self, user, proj_name):
        proj = orm.Project.find_one(self.db,user.id, proj_name)
        return proj
    
    def find_project_comments(self, project):
        comments = orm.ProjectComments.find_by_project(self.db, project.id)
        return comments
    
    def find_project_comment(self, project, comment_id):
        comment = orm.ProjectComments.find_by_comment_id(self.db, comment_id)
        return comment

    @gen.coroutine
    @admin_or_self
    def post(self, name, proj_name):
        user = self.find_user(name)
        project = self.find_project(user, proj_name)
        
        if project is None:
            raise web.HTTPError(400, "Project [{}] doesn't exists.".format(proj_name))
            
        data = self.get_json_body()

        if data:
            if not self._check_comment_model(data):
                raise web.HTTPError(401, "A valid image config must have name, description, docker_image, workspace_software.")
        else :
            raise web.HTTPError(401, "The body is empty.")
            
        comment_id = server_name=binascii.hexlify(os.urandom(16)).decode('ascii')
        print(len(comment_id))
        new_comment= orm.ProjectComments(id=comment_id ,user_id = user.id, proejct_id=project.id, body=data['body'],
                          create_time = datetime.datetime.now(), last_update =  datetime.datetime.now())
        self.db.add(new_comment)
        self.db.commit()
        self.set_status(200)
        
        self.write({"status":200, "message":"Comment is posted.", "comment_id": comment_id})
    
    
    @gen.coroutine
    @admin_or_self
    def get(self,  name, proj_name, comment_id):
        user = self.find_user(name)
        project = self.find_project(user, proj_name)
        if project is None:
            raise web.HTTPError(400, "Project [{}] doesn't exists.".format(proj_name))
        
        comment = self.find_project_comment(project, comment_id)
        if comment is None:
            raise web.HTTPError(400, "Comment [{}] doesn't exists.".format(comment_id))
            
        self.write(json.dumps(self._comment_model(user, project.id, comment)))
    
    @gen.coroutine
    @admin_or_self
    def delete(self,  name, proj_name, comment_id):
        user = self.find_user(name)
        project = self.find_project(user, proj_name)
        if project is None:
            raise web.HTTPError(400, "Project [{}] doesn't exists.".format(proj_name))
        
        comment = self.find_project_comment(project, comment_id)
        if comment is None:
            raise web.HTTPError(400, "Comment [{}] doesn't exists.".format(comment_id))
        self.db.delete(comment)
        self.db.commit()
        
        status = 200
        self.set_status(status)
        self.write({"status":200, "message":"Comment is deleted."})
    
    @gen.coroutine
    @admin_or_self
    def put(self,  name, proj_name, comment_id):
        user = self.find_user(name)
        project = self.find_project(user, proj_name)
        if project is None:
            raise web.HTTPError(400, "Project [{}] doesn't exists.".format(proj_name))
        
        comment = self.find_project_comment(project, comment_id)
        if comment is None:
            raise web.HTTPError(400, "Comment [{}] doesn't exists.".format(comment_id))
        
        data = self.get_json_body()

        if data:
            if not self._check_comment_model(data):
                raise web.HTTPError(401, "A valid image config must have name, description, docker_image, workspace_software.")
        else :
            raise web.HTTPError(401, "The body is empty.")
            
        comment.last_update=datetime.datetime.now()
        comment.body = data['body']
        self.db.commit()
        self.write({"status":200, "message":"Comment is updated."})
        
        
default_handlers = [
    (r"/api/server/([^/]+)/comment/([^/]+)", SessionCommentsAPIHandler),
    (r"/api/server/([^/]+)/comment/?", SessionCommentsAPIHandler),
    (r"/api/user/([^/]+)/project/([^/]+)/comment/([^/]+)", ProjectCommentsAPIHandler),
    (r"/api/user/([^/]+)/project/([^/]+)/comment/?", ProjectCommentsAPIHandler),
]