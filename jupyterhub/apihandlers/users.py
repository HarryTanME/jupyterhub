"""User handlers"""

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

import json
import binascii
import os
from tornado import gen, web
import base64
from .. import orm
from ..utils import admin_only
from .base import APIHandler


class SelfAPIHandler(APIHandler):
    """Return the authenticated user's model
    
    Based on the authentication info. Acts as a 'whoami' for auth tokens.
    """
    @web.authenticated
    def get(self):
        user = self.get_current_user()
        if user is None:
            # whoami can be accessed via oauth token
            user = self.get_current_user_oauth_token()
        if user is None:
            raise web.HTTPError(403)
        self.write(json.dumps(self.user_model(user)))


class UserListAPIHandler(APIHandler):
    @admin_only
    def get(self):
        users = [ self._user_from_orm(u) for u in self.db.query(orm.User) ]
        data = [ self.user_model(u) for u in users ]
        self.write(json.dumps(data))
    
    @admin_only
    @gen.coroutine
    def post(self):
        data = self.get_json_body()
        if not data or not isinstance(data, dict) or not data.get('usernames'):
            raise web.HTTPError(400, "Must specify at least one user to create")
        
        usernames = data.pop('usernames')
        self._check_user_model(data)
        # admin is set for all users
        # to create admin and non-admin users requires at least two API requests
        admin = data.get('admin', False)
        
        to_create = []
        invalid_names = []
        for name in usernames:
            name = self.authenticator.normalize_username(name)
            if not self.authenticator.validate_username(name):
                invalid_names.append(name)
                continue
            user = self.find_user(name)
            if user is not None:
                self.log.warning("User %s already exists" % name)
            else:
                to_create.append(name)
        
        if invalid_names:
            if len(invalid_names) == 1:
                msg = "Invalid username: %s" % invalid_names[0]
            else:
                msg = "Invalid usernames: %s" % ', '.join(invalid_names)
            raise web.HTTPError(400, msg)
        
        if not to_create:
            raise web.HTTPError(400, "All %i users already exist" % len(usernames))
        
        created = []
        for name in to_create:
            user = self.user_from_username(name)
            if admin:
                user.admin = True
                self.db.commit()
            try:
                yield gen.maybe_future(self.authenticator.add_user(user))
            except Exception as e:
                self.log.error("Failed to create user: %s" % name, exc_info=True)
                del self.users[user]
                raise web.HTTPError(400, "Failed to create user %s: %s" % (name, str(e)))
            else:
                created.append(user)
        
        self.write(json.dumps([ self.user_model(u) for u in created ]))
        self.set_status(201)


def admin_or_self(method):
    """Decorator for restricting access to either the target user or admin"""
    def m(self, name, *args, **kwargs):
        current = self.get_current_user()
        if current is None:
            raise web.HTTPError(403)
        if not (current.name == name or current.admin):
            self.log.debug("User doesn't match, {} {}".format(name, current.name))
            raise web.HTTPError(403)
        
        # raise 404 if not found
        if not self.find_user(name):
            self.log.debug("Can't find user {}".format(name))
            raise web.HTTPError(404)
        return method(self, name, *args, **kwargs)
    return m

def valid_user(method):
    """Decorator for restricting access to either the target user or admin"""
    def m(self, name, *args, **kwargs):
        current = self.get_current_user()
        if current is None:
            raise web.HTTPError(403)
        
        return method(self, name, *args, **kwargs)
    return m

class UserAPIHandler(APIHandler):
    
    def find_session(self, session_name):
        spawner = orm.Spawner.find_by_name(self.db, session_name)
        return spawner
    
    @admin_or_self
    def get(self, name):
        user = self.find_user(name)
        self.write(json.dumps(self.user_model(user)))

    @admin_only
    @gen.coroutine
    def post(self, name):
        data = self.get_json_body()
        user = self.find_user(name)
        if user is not None:
            raise web.HTTPError(400, "User %s already exists" % name)
        
        user = self.user_from_username(name)
        if data:
            self._check_user_model(data)
            if 'admin' in data:
                user.admin = data['admin']
                self.db.commit()
        
        try:
            yield gen.maybe_future(self.authenticator.add_user(user))
        except Exception:
            self.log.error("Failed to create user: %s" % name, exc_info=True)
            # remove from registry
            del self.users[user]
            raise web.HTTPError(400, "Failed to create user: %s" % name)
        
        self.write(json.dumps(self.user_model(user)))
        self.set_status(201)
    
    
    @admin_only
    @gen.coroutine
    def delete(self, name):
        user = self.find_user(name)
        if user is None:
            raise web.HTTPError(404)
        if user.name == self.get_current_user().name:
            raise web.HTTPError(400, "Cannot delete yourself!")
        if user.spawner._stop_pending:
            raise web.HTTPError(400, "%s's server is in the process of stopping, please wait." % name)
        if user.running:
            yield self.stop_single_user(user)
            if user.spawner._stop_pending:
                raise web.HTTPError(400, "%s's server is in the process of stopping, please wait." % name)
        
        yield gen.maybe_future(self.authenticator.delete_user(user))
        # remove from registry
        del self.users[user]

        self.set_status(204)

    @admin_only
    def patch(self, name):
        user = self.find_user(name)
        if user is None:
            raise web.HTTPError(404)
        data = self.get_json_body()
        self._check_user_model(data)
        if 'name' in data and data['name'] != name:
            # check if the new name is already taken inside db
            if self.find_user(data['name']):
                raise web.HTTPError(400, "User %s already exists, username must be unique" % data['name'])
        for key, value in data.items():
            setattr(user, key, value)
        self.db.commit()
        self.write(json.dumps(self.user_model(user)))

class UserAdminAccessAPIHandler(APIHandler):
    """Grant admins access to single-user servers
    
    This handler sets the necessary cookie for an admin to login to a single-user server.
    """
    @admin_only
    def post(self, name):
        self.log.warning("Deprecated in JupyterHub 0.8."
            " Admin access API is not needed now that we use OAuth.")
        current = self.get_current_user()
        self.log.warning("Admin user %s has requested access to %s's server",
            current.name, name,
        )
        if not self.settings.get('admin_access', False):
            raise web.HTTPError(403, "admin access to user servers disabled")
        user = self.find_user(name)
        if user is None:
            raise web.HTTPError(404)
default_handlers = [
    (r"/api/user/?", SelfAPIHandler),
    (r"/api/users/?", UserListAPIHandler),#admin only
    (r"/api/user/([^/]+)/?", UserAPIHandler),
#    (r"/api/users/([^/]+)/server", UserServerAPIHandler),
    (r"/api/user/([^/]+)/admin-access", UserAdminAccessAPIHandler),#admin only
]
