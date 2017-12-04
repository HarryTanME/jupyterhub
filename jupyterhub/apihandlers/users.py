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
            raise web.HTTPError(403)
        
        # raise 404 if not found
        if not self.find_user(name):
            raise web.HTTPError(404)
        return method(self, name, *args, **kwargs)
    return m

class UserAPIHandler(APIHandler):
    
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

class UserServerAPIHandler(APIHandler):
    """Start and stop single-user servers"""

    @gen.coroutine
    @admin_or_self
    def post(self, name, server_name=''):
        # force every server has its owner name.
        if server_name == '':
            server_name=binascii.hexlify(os.urandom(8)).decode('ascii')
            
        user = self.find_user(name)
        print("~~~~list spawner~~~~~"+str(user.spawners))
        if server_name and not self.allow_named_servers:
            raise web.HTTPError(400, "Named servers are not enabled.")
        spawner = user.spawners[server_name]
        pending = spawner.pending
        if pending == 'spawn':
            self.set_header('Content-Type', 'text/plain')
            self.set_status(202)
            return
        elif pending:
            raise web.HTTPError(400, "%s is pending %s" % (spawner._log_name, pending))

        if spawner.ready:
            # include notify, so that a server that died is noticed immediately
            # set _spawn_pending flag to prevent races while we wait
            spawner._spawn_pending = True
            try:
                state = yield spawner.poll_and_notify()
            finally:
                spawner._spawn_pending = False
            if state is None:
                raise web.HTTPError(400, "%s is already running" % spawner._log_name)
            
        options = self.get_json_body()
        print("~~~~options~~~~~"+str(options))  
        
        yield self.spawn_single_user(user, server_name, options=options)
        status = 202 if spawner.pending == 'spawn' else 201
        self.set_header('Content-Type', 'text/plain')
        self.set_status(status)
        self.write(json.dumps({"session_name":"{}".format(server_name)}))
    
    def _getData(self, user, server_name=''):

        model = self.user_model(self.users[user])
        if self.allow_named_servers :
            servers = model['servers'] 
        elif model['server'] is not None:
            servers = {"":model['server']}
        else:
            servers = {}
        return servers
    
    @gen.coroutine
    @admin_or_self
    def get(self, name, server_name=''):
        user = self.find_user(name)
        if user is None:
            status=400
            error_json ={"error":status, "message":"User {} doesn't exists".format(name)}
            self.set_status(status)
            self.write(json.dumps(error_json))
        else:
            data = self._getData(user, server_name)
            status = 200
            self.set_status(status)
            self.write(json.dumps(data))
            
    @gen.coroutine
    @admin_or_self
    def delete(self, name, server_name=''):
        user = self.find_user(name)
        if server_name:
            if not self.allow_named_servers:
                raise web.HTTPError(400, "Named servers are not enabled.")
            if server_name not in user.spawners:
                raise web.HTTPError(404, "%s has no server named '%s'" % (name, server_name))

        spawner = user.spawners[server_name]
        if spawner.pending == 'stop':
            self.log.debug("%s already stopping", spawner._log_name)
            self.set_header('Content-Type', 'text/plain')
            self.set_status(202)
            return

        if not spawner.ready:
            raise web.HTTPError(
                400, "%s is not running %s" %
                (spawner._log_name, '(pending: %s)' % spawner.pending if spawner.pending else '')
            )
        # include notify, so that a server that died is noticed immediately
        status = yield spawner.poll_and_notify()
        if status is not None:
            raise web.HTTPError(400, "%s is not running" % spawner._log_name)
        yield self.stop_single_user(user, server_name)
        status = 202 if spawner._stop_pending else 204
        self.set_header('Content-Type', 'text/plain')
        self.set_status(status)

class ServerStatusAPIHandler(UserServerAPIHandler):
    def _getData(self, user, server_name=""):
        spawner = user.spawners[server_name]
#        c= yield spawner.get_container()
#        for a in c['State']:
#            print(a)
        data=yield spawner._status()
    
        return {"spawner":data}#list(*c['State'])

class ServerLogsAPIHandler(UserServerAPIHandler):
    def _getData(self, user, server_name=""):
        return {"data":"Logs"}
        
class ServerOutputsAPIHandler(UserServerAPIHandler):

    def _getData(self, user, server_name=""):
        return {"data":"Output"}
        
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
    (r"/api/user/([^/]+)/servers/?", UserServerAPIHandler),
    (r"/api/user/([^/]+)/servers/([^/]*)", UserServerAPIHandler),
    (r"/api/user/([^/]+)/servers/([^/]*)/status", ServerStatusAPIHandler),
    (r"/api/user/([^/]+)/servers/([^/]*)/logs", ServerLogsAPIHandler),
    (r"/api/user/([^/]+)/servers/([^/]*)/outputs", ServerOutputsAPIHandler),
    (r"/api/user/([^/]+)/admin-access", UserAdminAccessAPIHandler),#admin only
]
