"""Comments handlers"""

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
from .users import admin_or_self, UserAPIHandler, valid_user



class SessionCommenListtsAPIHandler(APIHandler):
    """Handle comments on a session/server"""
    
    def _comment_model(self, comment):
        """Produce the model for an docker comment."""
        return {
            'id':comment.id,
            'session_name':comment.session_name,
            'comment_by': comment.user_id, #FIXME: we need name here.
            'body':comment.body,
            'create_time':str(comment.create_time),
            'last_update':str(comment.last_update)
        }
    
    def find_session_comments(self, session_name):
        comments = orm.SessionComment.find_by_session(self.db, session_name)
        return comments

    @gen.coroutine
    @valid_user
    def get(self, session_name):
        comments = self.find_session_comments(session_name)
        aa = []
        for c in comments:
            aa.append(self._comment_model(c))
        self.set_status(200)
        self.write(json.dumps(aa))


class SessionCommentsAPIHandler(UserAPIHandler):
    """Handle comments on a session/server"""

    def _check_comment_model(self, data):
        return True
        checks = [lambda x : x in data.keys() for x in ['body']]
        if all(checks):
            return True
        return False
    
    def _comment_model(self, comment):
        """Produce the model for an docker comment."""
        return {
            'id':comment.id,
            'session_name':comment.session_name,
            'comment_by': comment.user_id, #FIXME: we need name here.
            'body':comment.body,
            'create_time':str(comment.create_time),
            'last_update':str(comment.last_update)
        }
        
    
    def find_by_comment_id(self, comment_id):
        comment = orm.SessionComment.find_by_comment_id(self.db, comment_id)
        return comment
    
    @gen.coroutine
    @valid_user
    def post(self, session_name):
        user= self.get_current_user()
        spawner = self.find_session(session_name)

        self.log.info(str(spawner))
        if spawner is None:
            raise web.HTTPError(400, "Session [{}] doesn't exists.".format(session_name))

        data = self.get_json_body()
        if data:
            if not self._check_comment_model(data):
                raise web.HTTPError(401, "A valid image config must have name, description, docker_image, workspace_software.")
        else :
            raise web.HTTPError(401, "The body is empty.")
            
        comment_id = server_name=binascii.hexlify(os.urandom(16)).decode('ascii')
        print((data['body']))
        new_comment= orm.SessionComment(id=comment_id ,user_id = user.id, session_name=spawner.name, body=data['body'],
                          create_time = datetime.datetime.now(), last_update =  datetime.datetime.now())
        self.db.add(new_comment)
        self.db.commit()
        self.set_status(200)
        self.write({"status":200, "message":"Comment is posted.", "comment_id": comment_id})
    
    
    @gen.coroutine
    @valid_user
    def get(self, session_name, comment_id):
        comment = self.find_by_comment_id(comment_id)
        if comment is None:
            raise web.HTTPError(400, "Comment [{}] doesn't exists.".format(comment_id))
            
        self.write(json.dumps(self._comment_model( comment)))
    
    @gen.coroutine
    @valid_user
    def delete(self, session_name, comment_id):
        comment = self.find_by_comment_id(comment_id)
        if comment is None:
            raise web.HTTPError(400, "Comment [{}] doesn't exists.".format(comment_id))
        user= self.get_current_user()
        if user.id != comment.user_id:
            raise web.HTTPError(403, "Comment can only be deleted by the original commentor.")
        
        self.db.delete(comment)
        self.db.commit()
        
        status = 200
        self.set_status(status)
        self.write({"status":200, "message":"Comment is deleted."})
        
    @gen.coroutine
    @valid_user
    def put(self, session_name, comment_id):
        comment = self.find_by_comment_id(comment_id)
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
        
class ProjectCommenListtsAPIHandler(APIHandler):
    """Handler a list of comments on a project."""
    
    def _comment_model(self, proj_name, comment):
        """Produce the model for an docker comment."""
        return {
            'id':comment.id,
            'project_id':proj_name,
            'comment_by': comment.user_id,
            'body':comment.body,
            'create_time':str(comment.create_time),
            'last_update':str(comment.last_update)
        }
    
    def find_project_comments(self, project):
        comments = orm.ProjectComment.find_by_project(self.db, project.id)
        return comments
    
    
    @gen.coroutine
    @valid_user
    def get(self, name, proj_name):
        user = self.find_user(name)
        project = self.find_project(user, proj_name)
        if project is None:
            raise web.HTTPError(400, "Project [{}] doesn't exists.".format(proj_name))
        
        comments = self.find_project_comments(project)
        if comment is None:
            raise web.HTTPError(400, "Comment [{}] doesn't exists.".format(comment_id))
            
        aa = []
        for c in comments:
            aa.append(self._comment_model(proj_name, c))
        self.set_status(200)
        self.write(json.dumps(aa))
        
class ProjectCommentsAPIHandler(APIHandler):
    """Handler comments on a project."""

    def _check_comment_model(self, data):
        return True
        checks = [lambda x : x in data.keys() for x in ['body']]
        if all(checks):
            return True
        return False
    
    def _comment_model(self, user, proj_id, comment):
        """Produce the model for an docker comment."""
        return {
            'id':comment.id,
            'project_id':proj_id,
            'comment_by': user.id,
            'body':comment.body,
            'create_time':str(comment.create_time),
            'last_update':str(comment.last_update)
        }
    
    def find_project(self, user, proj_name):
        proj = orm.Project.find_one(self.db,user.id, proj_name)
        return proj
    
    
    def find_project_comment(self, project, comment_id):
        comment = orm.ProjectComment.find_by_comment_id(self.db, comment_id)
        return comment

    @gen.coroutine
    @valid_user
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
        new_comment= orm.ProjectComment(id=comment_id ,user_id = user.id, proejct_id=project.id, body=data['body'],
                          create_time = datetime.datetime.now(), last_update =  datetime.datetime.now())
        self.db.add(new_comment)
        self.db.commit()
        self.set_status(200)
        
        self.write({"status":200, "message":"Comment is posted.", "comment_id": comment_id})
    
    
    @gen.coroutine
    @valid_user
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
    (r"/api/session/([^/]+)/comment/([^/]+)", SessionCommentsAPIHandler),
    (r"/api/session/([^/]+)/comment/?", SessionCommentsAPIHandler),
    (r"/api/session/([^/]+)/comments/?", SessionCommenListtsAPIHandler),
    (r"/api/user/([^/]+)/project/([^/]+)/comment/([^/]+)", ProjectCommentsAPIHandler),
    (r"/api/user/([^/]+)/project/([^/]+)/comment/?", ProjectCommentsAPIHandler),
    (r"/api/user/([^/]+)/project/([^/]+)/comments/?", ProjectCommenListtsAPIHandler),
]