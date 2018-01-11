# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

import os
#from ..utils import convert_markdown
from tornado.web import StaticFileHandler
from .base import BaseHandler
import markdown
from nbconvert import HTMLExporter
from ..utils import convertMarkdown



class CacheControlStaticFilesHandler(StaticFileHandler):
    """StaticFileHandler subclass that sets Cache-Control: no-cache without `?v=`
    
    rather than relying on default browser cache behavior.
    """
    def compute_etag(self):
        return None
    
    def set_extra_headers(self, path):
        if "v" not in self.request.arguments:
            self.add_header("Cache-Control", "no-cache")

class LogoHandler(StaticFileHandler):
    """A singular handler for serving the logo."""
    def get(self):
        return super().get('')

    @classmethod
    def get_absolute_path(cls, root, path):
        """We only serve one file, ignore relative path"""
        return os.path.abspath(root)

class ReadmeHandler(StaticFileHandler):
    
    def parse_url_path(self, url_path):
        if not url_path or url_path.endswith('/'):
            url_path = url_path + 'README.html'
        return url_path

    def obs_write_error(self, status_code, *args, **kwargs):
        # custom 404 page
        if status_code in [403]:
            self.render("templates/error-403.html",
                status_code=status_code,
                status_message="Permission denied",
                message="You don't have permission to view this file or folder."
                )
        if status_code in [404]:
            self.render("templates/error-404.html",
                status_code=status_code,
                status_message="Not Found",
                message="Unable to find the resource."
                )
        else:
            super().write_error(status_code, *args, **kwargs)

            
class MarkdownHandler(BaseHandler):
    
    def get(self, url_path):
        filenameext= self.request.uri.split('.')[-1]
        
        filepath = self.settings['repo_path']+url_path+'.'+filenameext
        filenamebase = url_path.split('/')[-1]
        
        content = convertMarkdown(filepath)
        
        html = self.render_template('static.html',
            html_content = content,
            title=filenamebase,
        )
        self.finish(html)


class NBViewerHandler(BaseHandler):

    #fixme we need authentication check here.
    def get(self, url_path):
        filenameext= self.request.uri.split('.')[-1]
        filepath = self.settings['repo_path']+url_path+'.'+filenameext
        filenamebase = url_path.split('/')[-1]
        
                # 2. Instantiate the exporter. We use the `basic` template for now; we'll get into more details
                # later about how to customize the exporter further.
        html_exporter = HTMLExporter()
        html_exporter.template_file = 'full'

                # 3. Process the notebook we loaded earlier
        (content, resources) = html_exporter.from_file(filepath)
        
        html = self.render_template('static.html',
            html_content = content,
            title=filenamebase,
        )
        self.finish(html)
        
default_handlers = [
        (r'/repo/(.*).md', MarkdownHandler),
        (r'/repo/(.*).rst', MarkdownHandler),
        (r'/repo/(.*).ipynb', NBViewerHandler),
        (r'/repo/(.*)', ReadmeHandler, {'path': '/data/repos/'}),
]

