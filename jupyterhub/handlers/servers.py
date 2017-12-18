"""Basic html-rendering handlers."""

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

from http.client import responses

from jinja2 import TemplateNotFound
from tornado import web, gen
from tornado.httputil import url_concat

from .. import orm
from ..utils import admin_only, url_path_join, unique_server_name
from .base import BaseHandler
import os, binascii

class ProjectHandler(BaseHandler):
    @web.authenticated
    def get(self, username, proj_name):
        
        user = self.get_current_user()
        
        html = self.render_template('project.html',
            user=user,
            proj_name=proj_name,
        )
        self.finish(html)

class ServerInfoHandler(BaseHandler):
    @web.authenticated
    def get(self, username, server_name):
        self.write(username+"  "+server_name)


default_handlers = [
    (r'/user/([^/]+)/project/([^/]+)/?', ProjectHandler),
    (r'/user/([^/]+)/session/([^/]+)/info', ServerInfoHandler),
    
]

