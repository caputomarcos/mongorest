# -*- encoding: UTF-8 -*-
from __future__ import absolute_import, unicode_literals

from mock import Mock
from os import environ
from werkzeug.wrappers import Response

from mongorest.decorators import login_required, serializable
from mongorest.testcase import TestCase


class TestLoginRequired(TestCase):

    def setUp(self):
        environ['MONGOREST_SETTINGS_MODULE'] = 'tests.fixtures.login_required_test_settings'

        @login_required
        @serializable
        def test(self, request, **kwargs):
            return Response()

        self.func = test

    def test_login_required_appends_to_the_list_of_decorators(self):
        @login_required
        def test(self, request, **kwargs):
            return Response()

        self.assertIn('login_required', test.decorators)

    def test_login_required_returns_401_if_auth_collection_not_present(self):
        request = Mock(environ={})

        self.assertEqual(self.func(None, request).status_code, 401)

    def test_login_required_returns_401_if_auth_collection_is_none(self):
        request = Mock(environ={'account': None})

        self.assertEqual(self.func(None, request).status_code, 401)

    def test_login_required_returns_401_if_auth_collection_not_authorized_and_method_not_authorized(self):
        account = Mock(is_authorized=False, authorized_methods=[])
        request = Mock(environ={'account': account}, method='GET')

        self.assertEqual(self.func(None, request).status_code, 401)

    def test_login_required_returns_function_if_auth_collection_is_authorized(self):
        account = Mock(is_authorized=True, authorized_methods=[])
        request = Mock(environ={'account': account}, method='GET')

        self.assertEqual(self.func(None, request).status_code, 200)

    def test_login_required_returns_function_if_auth_collection_not_authorized_but_method_authorized(self):
        account = Mock(is_authorized=False, authorized_methods=['GET'])
        request = Mock(environ={'account': account}, method='GET')

        self.assertEqual(self.func(None, request).status_code, 200)
