"""User Projects handlers"""

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

import json,datetime
import binascii
import os
from tornado import gen, web
import base64
from .. import orm
from ..utils import admin_only
from .base import APIHandler
from .users import admin_or_self, UserAPIHandler

class _ProjectAPIHandler(UserAPIHandler):
    
    def _check_project_model(self, data):
        checks = [lambda x : x in data.keys() for x in ['name','description','docker_image','workspace_software']]
        if all(checks):
            return True
        return False
    
    def _project_model(self, user, project):
        """Produce the model for a project."""
        return {
            'owner': user.name,
            'create_time':str(project.create_time),
            'last_update':str(project.last_update),
            'config':project.config
        }
    
    def find_user_projects(self, user):
        projects = orm.Project.find_all(self.db, user.id)
        return projects
    
    def find_user_project(self, user, proj_name):
        project = orm.Project.find_one(self.db, user.id, proj_name)
        return project

class UserProjectListAPIHandler(_ProjectAPIHandler):
    
    @admin_or_self
    def get(self, name):
        user = self.find_user(name)
        if user is None:
            raise web.HTTPError(400, "User [{}] doesn't exists.".format(name))
            
        aa = []
        projects = self.find_user_projects(user)
        for project in projects:
            aa.append(self._project_model(user, project))
        self.set_status(200)
        self.write(json.dumps(aa))
        
class UserProjectAPIHandler(_ProjectAPIHandler):
    
    
    @admin_or_self
    @gen.coroutine
    def post(self, name, proj_name):
        user = self.find_user(name)
        if user is None:
            raise web.HTTPError(400, "User [{}] doesn't exists.".format(name))
        project = self.find_user_proj(user, proj_name)
        if project is not None:
            raise web.HTTPError(401, "Project name [{}] already exists.".format(proj_name))
        
        data = self.get_json_body()

        if data:
            if not self._check_project_model(data):
                raise web.HTTPError(401, "A valid project config must have name, description, docker_image, workspace_software.")
        else :
            raise web.HTTPError(401, "Project config is empty.")
            
        new_proj= orm.Project(name=proj_name, user_id = user.id, config=json.dumps(data),
                          create_time = datetime.datetime.now(), last_update =  datetime.datetime.now())
        self.db.add(new_proj)
        self.db.commit()
        self.set_status(200)
        
    @admin_or_self
    def get(self, name, proj_name):
        user = self.find_user(name)
        if user is None:
            raise web.HTTPError(400, "User [{}] doesn't exists.".format(name))
        if proj_name is None or proj_name == "":
            raise web.HTTPError(400, "Project Id cannot be null or empty.")
        
        project = self.find_user_project(user, proj_name)
        self.write(json.dumps(self._project_model(user, project)))

    
    @admin_or_self
    @gen.coroutine
    def delete(self, name, proj_name):
        user = self.find_user(name)
        if user is None:
            raise web.HTTPError(400, "User [{}] doesn't exists.".format(name))
        if proj_name is None or proj_name == "":
            raise web.HTTPError(400, "Project Id cannot be null or empty.")
        
        project = self.find_user_project(user, proj_name)
        if project is None:
            raise web.HTTPError(400, "Project [{}] doesn't exist.".format(proj_name))
        
        self.log.info("Deleting project %s for user %s", proj_name, name)
        self.db.delete(project)
        self.db.commit()
        self.set_status(204)

    @admin_or_self
    def patch(self, name, proj_name):
        user = self.find_user(name)
        if user is None:
            raise web.HTTPError(400, "User [{}] doesn't exists.".format(name))
        
        if proj_name is None or proj_name == "":
            raise web.HTTPError(400, "Project Id cannot be null or empty.")
        
        project = self.find_user_project(user, proj_name)
        if project is None:
            raise web.HTTPError(400, "Failed to find the project []" % proj_name)
        
        data = self.get_json_body()
        if self._check_project_model(data):
            project.config = json.dumps(data)
            project.last_update = datetime.datetime.now()
        self.db.commit()
        
        
        

default_handlers = [
    (r"/api/user/([^/]+)/projects/?", UserProjectListAPIHandler),
    (r"/api/user/([^/]+)/project/([^/]*)/?", UserProjectAPIHandler),
]


