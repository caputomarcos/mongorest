# -*- encoding: UTF-8 -*-
from __future__ import absolute_import, unicode_literals

from bson.objectid import ObjectId
from collections import Mapping
from cerberus import Validator as CerberusValidator

from .errors import *

__all__ = [
    'Validator',
]


class Validator(CerberusValidator):

    def __init__(self, schema=None, allow_unknown=True, **kwargs):
        super(Validator, self).__init__(
            schema=schema or {}, allow_unknown=allow_unknown, **kwargs
        )

    def _validate_type_objectid(self, field, value):
        if not isinstance(value, ObjectId):
            self._error(field, 'must be of ObjectId type')

    def validate_document(self, document):
        errors = {}

        collection = document.collection
        collection_name = collection.__name__

        self.validate(document.fields)
        for key, _error in self.flattened_errors.items():
            field = key
            field_schema = self.get_field_schema(field)

            if _error == 'required field':
                error = RequiredFieldError(collection_name, field)
            elif _error.startswith('must be of') and _error.endswith('type'):
                error = FieldTypeError(
                    collection_name, field, field_schema['type']
                )
            else:
                error = SchemaValidationError()

            if error and isinstance(error, SchemaValidationError):
                if 'error_code' in errors:
                    errors['errors'].append(error)
                else:
                    errors = DocumentValidationError(
                        collection_name, self.schema, document.fields, [error]
                    )

        document._errors = errors
        return not bool(document.errors)

    @property
    def flattened_errors(self):
        return self.flatten(self._errors, '', '.')

    def flatten(self, mapping, parent='', separator='.'):
        items = []

        for key, value in mapping.items():
            flat_key = separator.join([parent, key]).strip(separator)

            if isinstance(value, Mapping):
                items.extend(self.flatten(value, flat_key, separator).items())
            else:
                items.append((flat_key, value))

        return dict(items)

    def get_field_schema(self, field):
        schema, fields = self.schema, field.split('.')

        for field in fields:
            schema = schema.get(field) or schema.get('schema').get(field)

        return schema
