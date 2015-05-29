# -*- encoding: UTF-8 -*-
from __future__ import absolute_import, unicode_literals

from werkzeug.exceptions import HTTPException, NotFound
from werkzeug.routing import Map
from werkzeug.wrappers import Request
from werkzeug.wsgi import DispatcherMiddleware

__all__ = [
    'WSGIWrapper',
    'WSGIDispatcher',
]


class WSGIWrapper(object):
    """
    Wrapper for WSGI Elements.
    This class is the base for Class Based Views.
    For example the ones created on resource.py
    It knows how to route its requests to the correct views using the url_map
    """
    endpoint = '/'
    rules = []
    url_map = Map()

    def __call__(self, environ, start_response):
        adapter = self.url_map.bind_to_environ(environ)

        try:
            endpoint, values = adapter.match()
            response = getattr(self, endpoint)(Request(environ), **values)
        except HTTPException as exc:
            response = exc.get_response(environ)

        return response(environ, start_response)


class WSGIDispatcher(DispatcherMiddleware):
    """
    Basic dispatcher class.
    This class should be created as your app for running on your WSGI Server.
    It defines the endpoints for each of the WSGIWrapper classes.
    """

    def __init__(self, resources):
        app = NotFound()
        mounts = {}

        from mongorest.settings import settings
        for resource in resources:
            key = '/{0}'.format(resource.endpoint.lstrip('/')).rstrip('/')
            resource_to_mount = resource()

            for middleware in settings.MIDDLEWARES:
                resource_to_mount = middleware(resource_to_mount)

            mounts[key] = resource_to_mount

        super(WSGIDispatcher, self).__init__(app, mounts)
