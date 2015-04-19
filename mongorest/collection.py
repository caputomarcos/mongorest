# -*- encoding: UTF-8 -*-

from inspect import getmembers

from .database import db
from .utils import serialize

__all__ = [
    'Collection',
]


class CollectionMeta(type):
    """
    MetaClass for the Collection Class.
    Prepares the member dict adding the correct collection based on the name,
    And adds the required_fields dict.
    """

    @classmethod
    def __prepare__(mcs, name, bases):
        """
        Returns the collection based on the name of the Class
        Also an empty required_fields dict to serve as a base
        """
        return {
            'collection': db[name.lower()],
            'required_fields': {},
        }


class Collection(object, metaclass=CollectionMeta):
    """
    Base class for Collections.
    Can Serialize and De-Serialize the data.
    """

    def __new__(cls, *args, **kwargs):
        """
        Instantiating a Collection will return a Document from that Collection
        """
        return Document(cls, *args, **kwargs)

    @classmethod
    def find_one(cls, filter=None, serialized=False):
        """
        Returns one document dict if at least one passes the filter
        Otherwise returns None
        Will return the serialized dict if serialized=True
        """
        document = cls.collection.find_one(filter)
        return serialize(document) if serialized else document

    @classmethod
    def find(cls, filter=None, serialized=False):
        """
        Returns all document dicts that pass the filter
        Will return the serialized dict if serialized=True
        """
        documents = list(cls.collection.find(filter))
        return serialize(documents) if serialized else documents

    @classmethod
    def aggregate(cls, pipeline, serialized=False):
        """
        Returns the list of document dicts returned from the Aggregate Pipeline
        Will return the serialized document dicts if serialized=True
        """
        documents = list(cls.collection.aggregate(pipeline))
        return serialize(documents) if serialized else documents

    @classmethod
    def insert_one(cls, document, serialized=False):
        """
        Inserts a document into the Collection
        Returns the inserted document's _id
        Will return the serialized _id if serialized=True
        """
        _id = cls.collection.insert_one(document).inserted_id
        return serialize(_id) if serialized else _id

    @classmethod
    def insert_many(cls, documents, ordered=True, serialized=False):
        """
        Inserts a list of documents into the Collection
        Returns the all the inserted documents' _ids
        Will return the serialized _ids if serialized=True
        """
        _ids = list(cls.collection.insert_many(documents, ordered).inserted_ids)
        return serialize(_ids) if serialized else _ids

    @classmethod
    def update_one(cls, filter, update, upsert=False, serialized=False):
        """
        Updates a document that passes the filter
        Returns the updated document's dict
        Will return the serialized document dict if serialized=True
        """
        updated = cls.collection.udpate_one(filter, update, upsert).raw_result
        return serialize(updated) if serialized else updated

    @classmethod
    def update_many(cls, filter, update, upsert=False, serialized=False):
        """
        Updates all the documents that pass the filter
        Returns the updated documents' dicts
        Will return the serialized document dicts if serialized=True
        """
        updated = list(cls.collection.udpate_many(filter, update, upsert).raw_result)
        return serialize(updated) if serialized else updated

    @classmethod
    def delete_one(cls, filter, serialized=False):
        """
        Deletes a document that passes the filter
        Returns the deleted document's dict
        Will return the serialized document dict if serialized=True
        """
        deleted = cls.collection.delete_one(filter).raw_result
        return serialize(deleted) if serialized else deleted

    @classmethod
    def delete_many(cls, filter, serialized=False):
        """
        Deletes all the documents that pass the filter
        Returns the deleted documents' dicts
        Will return the serialized document dicts if serialized=True
        """
        deleted = list(cls.collection.delete_many(filter).raw_result)
        return serialize(deleted) if serialized else deleted

    @classmethod
    def count(cls, filter=None):
        """
        Returns the number of documents that pass the filter
        """
        return len(cls.find(filter))

    @classmethod
    def get(cls, filter=None):
        """
        Returns a Document Object if any document passes the filter
        Returns None otherwise
        """
        document = Document(cls, cls.find_one(filter), processed=True)
        return document if document.pk() else None


class Document(object):
    """
    Document Class
    It will know how to validate its fields
    Will use the required_fields of the Collection to do so.
    """

    def __init__(self, cls, fields=None, processed=False):
        """
        Initializes the Document Object with the given attributes
        Then validates the fields based on the Collection
        """
        super(Document, self).__init__()

        self._cls = cls
        self._fields = fields or {}
        self._errors = {}

        self._validate()

        if not processed:
            self._process()

    def __getattr__(self, attr):
        if attr in ('_cls', '_fields', '_errors'):
            return object.__getattribute__(self, attr)
        elif attr in self._fields:
            return self._fields[attr]
        elif hasattr(self._cls, attr):
            return getattr(self._cls, attr)
        else:
            return object.__getattribute__(self, attr)

    def __setattr__(self, attr, value):
        if attr in ('_cls', '_fields', '_errors'):
            object.__setattr__(self, attr, value)
        else:
            self._fields[attr] = value

    def _validate(self):
        """
        Validates if the required fields are present on the Document
        Validates if the required fields are of the correct types
        If one of these two validations fail, add an error to self._errors
        """
        for (field, type_or_tuple) in self.required_fields.items():
            if field in self._fields:
                if not isinstance(self._fields[field], type_or_tuple):
                    types = type_or_tuple

                    if hasattr(type_or_tuple, '__iter__'):
                        types = ' or '.join([t.__name__ for t in type_or_tuple])

                    self.errors[field] = 'Field \'{}\' must be of type(s): {}.'.format(
                        field, types
                    )
            else:
                self.errors[field] = 'Field \'{}\' is required.'.format(field)

    def _process(self):
        """
        Calls every collection method that starts with process.
        Does this in order to process the values on the fields
        So they will be ready to be saved on the Database
        """
        for (name, member) in getmembers(self.cls):
            if name.lower().startswith('process'):
                member()

    def save(self, serialized=False):
        """
        Saves the Document to the database if it is valid.
        Returns the error dict otherwise.
        If the Document does not contain an _id it will insert a new Document
        If the Document contains an _id it will be updated instead of inserted
        """
        if self.is_valid() and self.pk():
            self.update_one({'_id': self.pk()}, self._fields)

            return serialize(self._fields) if serialized else self._fields
        elif self.is_valid:
            self._fields['_id'] = self.insert_one(self._fields).inserted_id

            return self.pk(serialized)
        else:
            return self._errors

    def is_valid(self):
        """
        Returns True if no errors have been found, False otherwise.
        """
        return len(self._errors) == 0

    def pk(self, serialized=False):
        """
        Returns the non-serialized PK
        """
        _id = self._fields.get('_id')
        return serialize(_id) if serialized else _id
