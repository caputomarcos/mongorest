# -*- encoding: UTF-8 -*-
from __future__ import absolute_import, unicode_literals

from os import environ
from werkzeug.wrappers import Response

from mongorest.resource import ListResourceMixin
from mongorest.settings import settings
from mongorest.testcase import TestCase
from mongorest.wsgi import WSGIDispatcher


class TestAuthenticationMiddleware(TestCase):

    def test_raises_value_error_if_session_store_is_not_sub_class_of_session_store(self):
        environ['MONGOREST_SETTINGS_MODULE'] = 'tests.test_middlewares.fixtures.session_store_error_settings'

        self.test_client = self.client(
            WSGIDispatcher([ListResourceMixin]), Response
        )

        with self.assertRaises(ValueError):
            self.test_client.get('/')

        environ.pop('MONGOREST_SETTINGS_MODULE')

    def test_raises_value_error_if_auth_collection_is_not_sub_class_of_collection(self):
        environ['MONGOREST_SETTINGS_MODULE'] = 'tests.test_middlewares.fixtures.auth_collection_error_settings'

        self.test_client = self.client(
            WSGIDispatcher([ListResourceMixin]), Response
        )

        with self.assertRaises(ValueError):
            self.test_client.get('/')

        environ.pop('MONGOREST_SETTINGS_MODULE')

    def test_adds_authorization_header_to_response_without_token(self):
        environ['MONGOREST_SETTINGS_MODULE'] = 'tests.test_middlewares.fixtures.authentication_settings'

        self.test_client = self.client(
            WSGIDispatcher([ListResourceMixin]), Response
        )

        response = self.test_client.get('/')

        self.assertIn('HTTP_AUTHORIZATION', response.headers)
        self.assertIn('Token ', response.headers.get('HTTP_AUTHORIZATION'))

        environ.pop('MONGOREST_SETTINGS_MODULE')

    def test_adds_authorization_header_to_response_with_token(self):
        environ['MONGOREST_SETTINGS_MODULE'] = 'tests.test_middlewares.fixtures.authentication_settings'

        self.test_client = self.client(
            WSGIDispatcher([ListResourceMixin]), Response
        )

        session_store = settings.SESSION_STORE()
        session = session_store.new()
        session_store.save(session)

        response = self.test_client.get(
            '/', headers=[('Authorization', 'Token {0}'.format(session.sid))]
        )

        self.assertIn('HTTP_AUTHORIZATION', response.headers)
        self.assertEqual(
            response.headers.get('HTTP_AUTHORIZATION'), 'Token {0}'.format(session.sid)
        )

        environ.pop('MONGOREST_SETTINGS_MODULE')