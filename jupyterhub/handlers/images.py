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

class ImageListHandler(BaseHandler):
    @web.authenticated
    def get(self, username):
        self.write("here are all your images.")

class ImageHandler(BaseHandler):
    @web.authenticated
    def get(self, username, image_name):
        self.write(username+"  "+image_name)


default_handlers = [
    (r'/user/([^/]+)/images/?', ImageListHandler),
    (r'/user/([^/]+)/image/([^/]+)/?', ImageHandler),
    
]


