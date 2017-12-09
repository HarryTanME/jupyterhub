"""User Images handlers"""

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

class _ImageAPIHandler(UserAPIHandler):

    def _check_image_model(self, data):
        return True
        checks = [lambda x : x in data.keys() for x in ['image_name','version_tag','description','Dockerfile']]
        if all(checks):
            return True
        return False
    
    def _image_model(self, user, image):
        """Produce the model for an docker image."""
        return {
            'owner': user.name,
            'status':image.status,
            'create_time':str(image.create_time),
            'last_update':str(image.last_update),
            'config':image.config
        }
    
    def find_user_images(self, user):
        images = orm.Image.find_all(self.db, user.id)
        return images
    
    def find_user_image(self, user, image_name):
        image = orm.Image.find_one(self.db, user.id, image_name)
        return image
    
class UserImageListAPIHandler(_ImageAPIHandler):    
    
    @admin_or_self
    def get(self, name):    
        user = self.find_user(name)
        if user is None:
            raise web.HTTPError(400, "User [{}] doesn't exists.".format(name))
            
        aa = []
        images = self.find_user_images(user)
        for image in images:
            aa.append(self._image_model(user, image))
        self.set_status(200)
        self.write(json.dumps(aa))
        
class UserImageAPIHandler(_ImageAPIHandler):
    
    @admin_or_self
    @gen.coroutine
    def post(self, name, image_name):
        user = self.find_user(name)
        if user is None:
            raise web.HTTPError(400, "User [{}] doesn't exists.".format(name))
        image = self.find_user_image(user, image_name)
        if image is not None:
            raise web.HTTPError(401, "Image name [{}] already exists.".format(image_name))
        
        data = self.get_json_body()

        if data:
            if not self._check_image_model(data):
                raise web.HTTPError(401, "A valid image config must have name, description, docker_image, workspace_software.")
        else :
            raise web.HTTPError(401, "Image config is empty.")
            
        new_image= orm.Image(name=image_name, user_id = user.id, config=json.dumps(data),status="pending",
                          create_time = datetime.datetime.now(), last_update =  datetime.datetime.now())
        self.db.add(new_image)
        self.db.commit()
        self.set_status(200)
        
        ###build it in docker image.
        ####
        #### fix me.
        
    @admin_or_self
    def get(self, name, image_name):
        user = self.find_user(name)
        if user is None:
            raise web.HTTPError(400, "User [{}] doesn't exists.".format(name))
        if image_name is None or image_name == "":
            raise web.HTTPError(400, "Image name cannot be null or empty.")
        
        image = self.find_user_image(user, image_name)
        self.write(json.dumps(self._image_model(user, image)))

    
    @admin_or_self
    @gen.coroutine
    def delete(self, name, image_name):
        user = self.find_user(name)
        if user is None:
            raise web.HTTPError(400, "User [{}] doesn't exists.".format(name))
        if image_name is None or image_name == "":
            raise web.HTTPError(400, "Image name cannot be null or empty.")
            
        image = self.find_user_image(user, image_name)
        if image is None:
            raise web.HTTPError(400, "image [{}] doesn't exist.".format(image_name))
        ###Delete in docker image.
        ####
        #### fix me.
        
        self.log.info("Deleting image %s for user %s", image_name, name)
        self.db.delete(image)
        self.db.commit()
        self.set_status(204)


default_handlers = [
    (r"/api/user/([^/]+)/images/?", UserImageListAPIHandler),
    (r"/api/user/([^/]+)/image/([^/]*)/?", UserImageAPIHandler),
]


