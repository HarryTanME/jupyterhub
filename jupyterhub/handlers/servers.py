"""Basic html-rendering handlers."""

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

from http.client import responses

from jinja2 import TemplateNotFound
from tornado import web, gen
from tornado.httputil import url_concat

from .. import orm
from ..utils import admin_only, url_path_join, unique_server_name, convertMarkdown, SimpleHtmlFilelistGenerator
from .base import BaseHandler
import os, binascii

class ProjectHandler(BaseHandler):
    
    
    def _projectFolderPath(self, user,proj_name):
        return (os.path.join(user.user_data_path, proj_name))
    
    def _projectReadmePath(self, user, proj_name):
        if os.path.exists(os.path.join(self._projectFolderPath(user, proj_name),"README.md")):
            return os.path.join(self._projectFolderPath(user, proj_name),"README.md")
        elif os.path.exists(os.path.join(self._projectFolderPath(user, proj_name),"README.rst")):
            return os.path.join(self._projectFolderPath(user, proj_name),"README.md")
        else:
            return None
    
        
    @web.authenticated
    def get(self, username, proj_name):
        user = self.get_current_user()
        owner = self.find_user(username)
        readme_path = self._projectReadmePath(user, proj_name)
        if readme_path:
            readme= convertMarkdown(readme_path)
        else:
            readme= None
            
        path =self._projectFolderPath(user, proj_name)
        
        gentr = SimpleHtmlFilelistGenerator(path, proj_name)
        file_tree = gentr.getTree()    
        
        html = self.render_template('project.html',
            user_url=user.url,
            proj_name=proj_name,
            title=proj_name,
            is_self =  (user.id == owner.id),
            readme = readme,
            file_tree =file_tree,
        )
        self.finish(html)

default_handlers = [
    (r'/user/([^/]+)/project/([^/]+)/?', ProjectHandler),    
]

