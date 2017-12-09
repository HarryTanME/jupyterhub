from .base import *
from . import auth, hub, proxy, users, groups, services, projects, servers, tags, comments, images

default_handlers = []
for mod in (auth, hub, proxy, users, groups, services, projects, servers, tags, comments, images):
    default_handlers.extend(mod.default_handlers)
