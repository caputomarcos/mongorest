# -*- encoding: UTF-8 -*-
from __future__ import absolute_import, unicode_literals

from werkzeug.contrib.sessions import SessionStore

from mongorest.collection import Collection
from mongorest.settings import settings
from mongorest.utils import deserialize

__all__ = [
    'AuthenticationMiddleware',
    'CORSMiddleware',
]


class AuthenticationMiddleware(object):

    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        session_store = settings.SESSION_STORE
        auth_collection = settings.AUTH_COLLECTION

        if not session_store or not issubclass(session_store, SessionStore):
            raise ValueError(
                'SESSION_STORE must be a sub class of \'SessionStore\''
            )

        session_store = session_store()

        if not auth_collection or not issubclass(auth_collection, Collection):
            raise ValueError(
                'AUTH_COLLECTION must be a sub class of \'Collection\''
            )

        auth_collection_name = auth_collection.__name__.lower()

        sid = environ.get('HTTP_AUTHORIZATION', '')
        if len(sid.split('Token ')) == 2:
            session = session_store.get(sid.split('Token ')[1])
        else:
            session = session_store.new()

        environ['session'] = session
        environ[auth_collection_name] = auth_collection.get({
            '_id': deserialize(session.get(auth_collection_name, '""'))
        })

        def authentication(status, headers, exc_info=None):
            headers.extend([
                ('HTTP_AUTHORIZATION', 'Token {0}'.format(session.sid)),
            ])

            return start_response(status, headers, exc_info)

        response = self.app(environ, authentication)

        if session.should_save:
            session_store.save(session)

        return response


class CORSMiddleware(object):

    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        def cors(status, headers, exc_info=None):
            headers.extend([
                (
                    'Access-Control-Allow-Origin',
                    settings.CORS['Access-Control-Allow-Origin']
                ),
                (
                    'Access-Control-Allow-Methods',
                    settings.CORS['Access-Control-Allow-Methods']
                ),
                (
                    'Access-Control-Allow-Headers',
                    settings.CORS['Access-Control-Allow-Headers']
                ),
                (
                    'Access-Control-Allow-Credentials',
                    settings.CORS['Access-Control-Allow-Credentials']
                )
            ])

            return start_response(status, headers, exc_info)

        if environ.get('REQUEST_METHOD') == 'OPTIONS':
            cors('200 OK', [('Content-Type', 'text/plain')])
            return ['200 OK']

        return self.app(environ, cors)
