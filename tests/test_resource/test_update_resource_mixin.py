# -*- encoding: UTF-8 -*-
from __future__ import absolute_import, unicode_literals

import six

from werkzeug.wrappers import Response

from mongorest.collection import Collection
from mongorest.resource import UpdateResourceMixin
from mongorest.testcase import TestCase
from mongorest.wsgi import WSGIDispatcher
from mongorest.utils import deserialize, serialize


class TestUpdateResourceMixin(TestCase):

    def setUp(self):
        class Test(Collection):
            meta = {'required': {'test': six.integer_types}}

        class TestCollectionUpdate(UpdateResourceMixin):
            collection = Test

        self.update_client = self.client(
            WSGIDispatcher(resources=[TestCollectionUpdate]),
            Response
        )

    def test_update_mixin_rule(self):
        rules = UpdateResourceMixin.rules

        self.assertEqual(len(rules), 1)
        self.assertEqual(rules[0].rule, '/<_id>/')
        self.assertEqual(rules[0].methods, set(['PUT']))
        self.assertEqual(rules[0].endpoint, 'update')

    def test_update_mixin_url_map(self):
        urls = list(UpdateResourceMixin.url_map.iter_rules())

        self.assertEqual(len(urls), 1)
        self.assertEqual(urls[0].rule, '/<_id>/')
        self.assertEqual(urls[0].methods, set(['PUT']))
        self.assertEqual(urls[0].endpoint, 'update')

    def test_update_mixin_returns_errors_if_data_is_not_valid(self):
        self.db.test.insert_one({'_id': 1, 'test': 1})

        response = self.update_client.put(
            '/1/', data=serialize({'test': '1'})
        )

        self.assertEqual(response.status_code, 400)
        errors = deserialize(response.get_data(as_text=True))
        errors['document'].pop('updated_at')

        self.assertEqual(
            errors,
            {
                'code': 1,
                'type': 'ValidationError',
                'message': 'Document validation failed.',
                'errors': [
                    {
                        'code': 2,
                        'type': 'FieldTypeError',
                        'message': 'Field \'test\' must be of type(s): {0}.'.format(
                            ' or '.join(t.__name__ for t in list(six.integer_types))
                        ),
                        'field': 'test',
                    },
                ],
                'document': {'_id': 1, 'test': '1'},
            }
        )

    def test_udpate_mixin_returns_not_found_if_no_document_matches_id(self):
        response = self.update_client.put('/1/', data=serialize({}))

        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            deserialize(response.get_data(as_text=True)),
            {
                'code': 4,
                'type': 'DocumentNotFound',
                'message': '{0} is not a valid {1} document _id.'.format(
                    repr(1), 'Test'
                ),
                '_id': 1,
                'collection': 'Test',
            }
        )

    def test_update_mixin_returns_updated_document_if_data_is_valid(self):
        self.db.test.insert_one({'_id': 1, 'test': 1})

        response = self.update_client.put(
            '/1/', data=serialize({'test': 2})
        )
        data = deserialize(response.get_data(as_text=True))
        data.pop('updated_at')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data, {'_id': 1, 'test': 2})
        self.assertEqual(self.db.test.find_one({'_id': 1})['test'], 2)
