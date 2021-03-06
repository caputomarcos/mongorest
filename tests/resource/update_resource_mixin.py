# -*- encoding: UTF-8 -*-
from __future__ import absolute_import, unicode_literals

from mongorest.collection import Collection
from mongorest.resource import UpdateResourceMixin
from mongorest.testcase import TestCase
from mongorest.wrappers import Response
from mongorest.utils import serialize
from mongorest.wsgi import WSGIDispatcher


class TestUpdateResourceMixin(TestCase):

    def setUp(self):
        class Test(Collection):
            schema = {'test': {'required': True, 'type': 'integer'}}

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
        errors = response.json
        errors['document'].pop('updated_at')

        self.assertEqual(
            errors,
            {
                'error_code': 21,
                'error_type': 'DocumentValidationError',
                'error_message': 'Validation of document from collection \'Test\' failed.',
                'errors': [
                    {
                        'error_code': 25,
                        'error_type': 'FieldTypeError',
                        'error_message': 'Field \'test\' on collection \'Test\' must be of type integer.',
                        'collection': 'Test',
                        'field': 'test',
                        'type': 'integer',
                    },
                ],
                'collection': 'Test',
                'schema': {'test': {'required': True, 'type': 'integer'}},
                'document': {'_id': 1, 'test': '1'},
            }
        )

    def test_update_mixin_returns_not_found_if_no_document_matches_id(self):
        response = self.update_client.put('/1/', data=serialize({}))

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json,
            {
                'error_code': 12,
                'error_type': 'DocumentNotFoundError',
                'error_message': '1 is not a valid _id for a document from collection \'Test\'.',
                'collection': 'Test',
                '_id': 1,
            }
        )

    def test_update_mixin_returns_updated_document_if_data_is_valid(self):
        self.db.test.insert_one({'_id': 1, 'test': 1})

        response = self.update_client.put(
            '/1/', data=serialize({'test': 2})
        )
        data = response.json
        data.pop('updated_at')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data, {'_id': 1, 'test': 2})
        self.assertEqual(self.db.test.find_one({'_id': 1})['test'], 2)
