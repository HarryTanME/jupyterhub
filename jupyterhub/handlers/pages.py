"""Basic html-rendering handlers."""

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

from http.client import responses

from jinja2 import TemplateNotFound
from tornado import web, gen
from tornado.httputil import url_concat
import json, datetime

from .. import orm
from ..utils import admin_only, url_path_join, unique_server_name, SimpleHtmlFilelistGenerator, slugify
from .base import BaseHandler
import os, binascii
import re

class RootHandler(BaseHandler):
    """Render the Hub root page.

    If next argument is passed by single-user server,
    redirect to base_url + single-user page.

    If logged in, redirects to:

    - single-user server if running
    - hub home, otherwise

    Otherwise, renders login page.
    """
    def get(self):
        next_url = self.get_argument('next', '')
        if next_url and not next_url.startswith('/'):
            self.log.warning("Disallowing redirect outside JupyterHub: %r", next_url)
            next_url = ''
        if next_url and next_url.startswith(url_path_join(self.base_url, 'user/')):
            # add /hub/ prefix, to ensure we redirect to the right user's server.
            # The next request will be handled by UserSpawnHandler,
            # ultimately redirecting to the logged-in user's server.
            without_prefix = next_url[len(self.base_url):]
            next_url = url_path_join(self.hub.base_url, without_prefix)
            self.log.warning("Redirecting %s to %s. For sharing public links, use /user-redirect/",
                self.request.uri, next_url,
            )
            self.redirect(next_url)
            return
        user = self.get_current_user()
        if user:
            url = 'home'
            #if user.running and not self.allow_named_servers: # when allow multi servers, do NOT redirect.
            #    url = user.url
            #    self.log.debug("User is running: %s", url)
            #    self.set_login_cookie(user) # set cookie
            #else:
            #    url = url_path_join(self.hub.base_url, 'home')
            #    self.log.debug("User is not running: %s", url)
        else:
            #url = self.settings['login_url']
            url = 'login'
        self.redirect(url)


class HomeHandler(BaseHandler):
    """Render the user's home page."""

    @web.authenticated
    @gen.coroutine
    def get(self):
        user = self.get_current_user()
        if user.running:
            # trigger poll_and_notify event in case of a server that died
            yield user.spawner.poll_and_notify()

        # send the user to /spawn if they aren't running or pending a spawn,
        # to establish that this is an explicit spawn request rather
        # than an implicit one, which can be caused by any link to `/user/:name`
        url = user.url if user.running or user.spawner.pending else url_path_join(self.hub.base_url, 'spawn')
        html = self.render_template('home.html',
            user=user,
            url=url,
            selected_session=user.running_spawners[0].name if len(user.running_spawners) > 0 else '',
        )
        self.finish(html)


class SpawnHandler(BaseHandler):
    """Handle spawning of single-user servers via form.

    GET renders the form, POST handles form submission.

    Only enabled when Spawner.options_form is defined.
    """
    def _render_form(self, message=''):
        user = self.get_current_user()
        return self.render_template('spawn.html',
            user=user,
            spawner_options_form=user.spawner.options_form,
            error_message=message,
            url=self.request.uri,
        )

    @web.authenticated
    def get(self):
        """GET renders form for spawning with user-specified options

        or triggers spawn via redirect if there is no form.
        """
        user = self.get_current_user()
        if not self.allow_named_servers and user.running:
            url = user.url
            self.log.debug("User is running: %s", url)
            self.redirect(url)
            return
        if user.spawner.options_form:
            self.finish(self._render_form())
        else:
            # Explicit spawn request: clear _spawn_future
            # which may have been saved to prevent implicit spawns
            # after a failure.
            if user.spawner._spawn_future and user.spawner._spawn_future.done():
                user.spawner._spawn_future = None
            # not running, no form. Trigger spawn by redirecting to /user/:name
            self.redirect(user.url)

    @web.authenticated
    @gen.coroutine
    def post(self):
        """POST spawns with user-specified options"""
        user = self.get_current_user()
        if not self.allow_named_servers and user.running:
            url = user.url
            self.log.warning("User is already running: %s", url)
            self.redirect(url)
            return
        if user.spawner.pending:
            raise web.HTTPError(
                400, "%s is pending %s" % (user.spawner._log_name, user.spawner.pending)
            )
        form_options = {}
        for key, byte_list in self.request.body_arguments.items():
            form_options[key] = [ bs.decode('utf8') for bs in byte_list ]
        for key, byte_list in self.request.files.items():
            form_options["%s_file"%key] = byte_list
        #server_name=binascii.hexlify(os.urandom(8)).decode('ascii')
        server_name = unique_server_name()
        
        try:
            options = user.spawner.options_from_form(form_options)
            print("~~~~~~~~"+str(options))
            yield self.spawn_single_user(user,server_name =server_name,  options=options)
        except Exception as e:
            self.log.error("Failed to spawn single-user server with form", exc_info=True)
            self.finish(self._render_form(str(e)))
            return
        self.set_login_cookie(user)
        url = user.url+server_name
        #next will have some issues.
        next_url = self.get_argument('next', '')
        
        if next_url and not next_url.startswith('/'):
            self.log.warning("Disallowing redirect outside JupyterHub: %r", next_url)
        elif next_url:
            url = next_url
        print("~~~spawn redirect url~~"+url)
        self.redirect(url)

class AdminHandler(BaseHandler):
    """Render the admin page."""

    @admin_only
    def get(self):
        available = {'name', 'admin', 'running', 'last_activity'}
        default_sort = ['admin', 'name']
        mapping = {
            'running': orm.Spawner.server_id,
        }
        for name in available:
            if name not in mapping:
                mapping[name] = getattr(orm.User, name)

        default_order = {
            'name': 'asc',
            'last_activity': 'desc',
            'admin': 'desc',
            'running': 'desc',
        }

        sorts = self.get_arguments('sort') or default_sort
        orders = self.get_arguments('order')

        for bad in set(sorts).difference(available):
            self.log.warning("ignoring invalid sort: %r", bad)
            sorts.remove(bad)
        for bad in set(orders).difference({'asc', 'desc'}):
            self.log.warning("ignoring invalid order: %r", bad)
            orders.remove(bad)

        # add default sort as secondary
        for s in default_sort:
            if s not in sorts:
                sorts.append(s)
        if len(orders) < len(sorts):
            for col in sorts[len(orders):]:
                orders.append(default_order[col])
        else:
            orders = orders[:len(sorts)]

        # this could be one incomprehensible nested list comprehension
        # get User columns
        cols = [ mapping[c] for c in sorts ]
        # get User.col.desc() order objects
        ordered = [ getattr(c, o)() for c, o in zip(cols, orders) ]

        users = self.db.query(orm.User).outerjoin(orm.Spawner).order_by(*ordered)
        users = [ self._user_from_orm(u) for u in users ]
        running = [ u for u in users if u.running ]

        html = self.render_template('admin.html',
            user=self.get_current_user(),
            admin_access=self.settings.get('admin_access', False),
            users=users,
            running=running,
            sort={s:o for s,o in zip(sorts, orders)},
        )
        self.finish(html)


class TokenPageHandler(BaseHandler):
    """Handler for page requesting new API tokens"""

    @web.authenticated
    def get(self):
        html = self.render_template('token.html')
        self.finish(html)
        
class TutorialsPageHandler(BaseHandler):
    """Handler for view list of courses."""

    #@web.authenticated
    def get(self):
        html = self.render_template('tutorials.html', courses=self.course_list, categories =self.course_categories, title="Tutorials | WodeAI")
        self.finish(html)

class ModelzooPageHandler(BaseHandler):
    """Handler for view list of pre-trained models."""

    #@web.authenticated
    def get(self):
        html = self.render_template('modelzoo.html', title="Model Zoo | WodeAI")
        self.finish(html)
        
class DatasetPageHandler(BaseHandler):
    """Handler for view list of datasets."""

    #@web.authenticated
    def get(self):
        html = self.render_template('datasets.html', title="Datasets | WodeAI")
        self.finish(html)

class ProxyErrorHandler(BaseHandler):
    """Handler for rendering proxy error pages"""

    def get(self, status_code_s):
        status_code = int(status_code_s)
        status_message = responses.get(status_code, 'Unknown HTTP Error')
        # build template namespace

        hub_home = url_path_join(self.hub.base_url, 'home')
        message_html = ''
        if status_code == 503:
            message_html = ' '.join([
                "Your server appears to be down.",
                "Try restarting it <a href='%s'>from the hub</a>" % hub_home
            ])
        ns = dict(
            status_code=status_code,
            status_message=status_message,
            message_html=message_html,
            logo_url=hub_home,
        )

        self.set_header('Content-Type', 'text/html')
        # render the template
        try:
            html = self.render_template('%s.html' % status_code, **ns)
        except TemplateNotFound:
            self.log.debug("No template for %d", status_code)
            html = self.render_template('error.html', **ns)

        self.write(html)

    
class CourseHandler(BaseHandler):
  
    def get(self):
        course_code=self.request.uri.split('/')[3]#there could be issues if more than folder name passed in.

        course = self.course_list[course_code]
        course_folder_name= course['FolderName']

        pth =os.path.join(self.settings['repo_path'],course_folder_name)
        path = os.path.expanduser(pth)
        
        gentr = SimpleHtmlFilelistGenerator(path, course_folder_name)
        ss = gentr.getTree()
        html = self.render_template('tutorial.html', course=course, tree=ss.encode('utf-8','ignore'), title = course['DisplayName'])
        self.write(html)

class ApiDocHandler(BaseHandler):
    
    def get(self):
        html=self.render_template("api_index.html", title = "API Document")
        self.write(html)
        
class ConstructionHandler(BaseHandler):
    
    def get(self):
        html=self.render_template("constuction.html")
        self.write(html)
        

def init_project(data):
    proj_name = slugify(form_options['name'])
    if not self._check_project_model(data):
        raise web.HTTPError(401, "A valid project config must have name, description, docker_image, workspace_software.")
    else :
        raise web.HTTPError(401, "Project config is empty.")

    new_proj= orm.Project(name=proj_name, user_id = user.id, config=json.dumps(form_options),
                      create_time = datetime.datetime.now(), last_update =  datetime.datetime.now())
    self.db.add(new_proj)
    self.db.commit()
    self.set_status(200)


        

class NewProjectHandler(BaseHandler):
    
    def _projectFolderPath(self, user,proj_name):
        return (os.path.join(user.user_data_path, proj_name))
    
    def _projectReadmePath(self, user, proj_name):
        if os.path.exists(os.path.join(self._projectFolderPath(user, proj_name),"README.md")):
            return os.path.join(self._projectFolderPath(user, proj_name),"README.md")
        elif os.path.exists(os.path.join(self._projectFolderPath(user, proj_name),"README.rst")):
            return os.path.join(self._projectFolderPath(user, proj_name),"README.md")
        else:
            return None
    
        
    def _options_form(self):
        return ''.join([
            """<option value="{image}">{name}</option>""".format(image=di, name= re.split('\W+', di)[1]) for di in self.settings['dockerimages']
        ])
    
    @web.authenticated
    def get(self):
        url = url_path_join(self.hub.base_url, 'new_project')
        options_form = self._options_form()
        print(options_form)
        html=self.render_template("new_project.html", title = "Create New Project", url=url, image_options= options_form)
        self.write(html)
    
    def _check_project_model(self, data):
        checks = [lambda x : x in data.keys() for x in ['name','description','docker_image','workspace_software']]
        if all(checks):
            return True
        return False
   

        
    @web.authenticated
    @gen.coroutine
    def post(self):    
        """POST create a new project."""
        user = self.get_current_user()
        
        form_options = {}
        for key, byte_list in self.request.body_arguments.items():
            form_options[key] =  (' ').join([bs.decode('utf8') for bs in byte_list ])
        #for key, byte_list in self.request.files.items():
        #   print("+++"+str(key))
        #    form_options["%s_file"%key] = byte_list
        #{'name': ['asdf'], 'description': ['df'], 'git_repo': ['dfs'], 'software': ['notebook'], 'data2mount':[''], 'pre-cmd': [''], 'cmd': [''], 'env': ['']}
        if len(form_options['data2mount']) > 0 :
            form_options['data_sources'] = [{'source':form_options['data2mount'][0],'target':"/home/wode-user/dataset","control":"ro"}]
        
        if len(form_options['cmd']) ==0 :
            form_options.pop('cmd',None)
    
        try:
            proj_name = slugify(form_options['name'])
            form_options['workspace'] =os.path.join(user.user_data_path,proj_name)
            if not self._check_project_model(form_options):
                raise web.HTTPError(401, "A valid project config must have name, description, docker_image, workspace_software.")
            
            new_proj= orm.Project(name=proj_name, user_id = user.id, config=json.dumps(form_options),
                              create_time = datetime.datetime.now(), last_update =  datetime.datetime.now())
            self.db.add(new_proj)
            
            realpath =self._projectFolderPath(user, proj_name)
            print(realpath)
            if os.path.exists(realpath):
                raise web.HTTPError(401, "There has been a project named '{}' existed in your workspace. Can you rename your project and try again?")
            else:
                os.mkdir(realpath)
            self.db.commit()
            self.set_status(200)
            self.redirect("/")
        except Exception as e:
            self.log.error("Failed to create new project", exc_info=True)
            self.redirect("/")
            return

class IndexHandler(BaseHandler):
    def get(self):
        html=self.render_template("index.html")
        self.write(html)
    
    
    
default_handlers = [
    (r'/?', RootHandler),
    (r'/home', HomeHandler),
    (r'/admin', AdminHandler),
    (r'/spawn', SpawnHandler),
    (r'/token', TokenPageHandler),
    (r'/tutorials', TutorialsPageHandler),
    (r'/tutorial/.*', CourseHandler),
    (r'/datasets', DatasetPageHandler),
    (r'/modelzoo', ModelzooPageHandler),
    (r'/api_doc', ApiDocHandler),
    (r'/new_project', NewProjectHandler),
    (r'/error/(\d+)', ProxyErrorHandler),
]
