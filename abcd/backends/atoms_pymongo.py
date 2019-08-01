import types
import logging
import numpy as np

from typing import Union, Iterable
from os import linesep
from operator import itemgetter
from collections import Counter

from ase import Atoms
from ase.io import iread

from abcd import ABCD
from abcd.model import AtomsModel
from abcd.parsers.queries import QueryParser
from abcd.parsers.arguments import key_val_str_to_dict

from pymongo import MongoClient

logger = logging.getLogger(__name__)


# TODO: derived properties when save ()
#     def pre_save_post_validation(cls, sender, document, **kwargs):
#
#         document.info['username'] = getpass.getuser()
#
#         natoms = len(document.arrays['numbers'])
#         elements = Counter(str(element) for element in document.arrays['numbers'])
#
#         arrays_keys = list(document.arrays.keys())
#         info_keys = list(document.info.keys())
#         derived_keys = ['natoms', 'elements', 'username', 'uploaded', 'modified']
#
#         cell = document.info.get('cell')
#         if cell:
#             derived_keys.append('volume')
#             virial = document.info.get('virial')
#             if virial:
#                 derived_keys.append('pressure')
#
#         document.derived = DerivedModel(
#             natoms=natoms,
#             elements=elements,
#             arrays_keys=arrays_keys,
#             info_keys=info_keys,
#             derived_keys=derived_keys,
#             username=getpass.getuser()
#         )
#
#         cell = document.info.get('cell')
#         if cell:
#             volume = abs(np.linalg.det(cell))  # atoms.get_volume()
#             document.derived['volume'] = volume
#
#             virial = document.info.get('virial')
#             if virial:
#                 # pressure P = -1/3 Tr(stress) = -1/3 Tr(virials/volume)
#                 document.derived['pressure'] = -1 / 3 * np.trace(virial / volume)
#
#         if not document.uploaded:
#             document.uploaded = datetime.datetime.utcnow()
#
#         document.modified = datetime.datetime.utcnow()
#
#         logger.debug("Pre Save: %s" % document)
#
#     @classmethod
#     def post_save(cls, sender, document, **kwargs):
#
#         logger.debug("Post Save: %s" % document)
#
#         if 'created' in kwargs:
#             if kwargs['created']:
#                 logger.debug("Created")
#             else:
#                 logger.debug("Updated")
#
#     @classmethod
#     def pre_bulk_insert(cls, sender, documents, **kwargs):
#         for document in documents:
#             cls.pre_save_post_validation(sender, document, **kwargs)
#
#
# signals.pre_save_post_validation.connect(AtomsModel.pre_save_post_validation, sender=AtomsModel)
# signals.pre_bulk_insert.connect(AtomsModel.pre_bulk_insert, sender=AtomsModel)
#
# signals.post_save.connect(AtomsModel.post_save, sender=AtomsModel)


# def query_to_dict(query):
#     if query is None:
#         query = {}
#     elif isinstance(query, str):
#         with MongoQuery() as parser:
#             query = parser(query)
#     elif isinstance(query, list):
#         with MongoQuery() as parser:
#             query = parser(' and '.join(query))
#
#     return query


class MongoQuery(object):

    def __init__(self):
        self.parser = QueryParser()

    def visit(self, syntax_tree):
        op, *args = syntax_tree
        try:
            fun = self.__getattribute__('visit_' + op.lower())
            return fun(*args)
        except:
            pass

    def visit_name(self, fields):
        # return {fields: {'$exists': True}}
        return {
            '$or': [
                {fields: {'$exists': True}},
                {'info.' + fields: {'$exists': True}},
                {'arrays.' + fields: {'$exists': True}},
                {'derived.' + fields: {'$exists': True}},
            ]
        }

    def visit_and(self, *args):
        return {'$and': [self.visit(arg) for arg in args]}
        # TODO recursively combining all the and statements
        # out = {}
        # for arg in args:
        #     a = self.visit(arg)
        #
        #     out.update(**a)
        # return out

    def visit_or(self, *args):
        return {'$or': [self.visit(arg) for arg in args]}

    def visit_eq(self, field, value):
        # return {field[1]: value[1]}
        return {
            '$or': [
                {'info.' + field[1]: value[1]},
                {'arrays.' + field[1]: value[1]},
                {'derived.' + field[1]: value[1]},
            ]
        }

    def visit_re(self, field, value):
        # return {field[1]: {'$regex': value[1]}}
        return {
            '$or': [
                {'info.' + field[1]: {'$regex': value[1]}},
                {'arrays.' + field[1]: {'$regex': value[1]}},
                {'derived.' + field[1]: {'$regex': value[1]}},
            ]
        }

    def visit_gt(self, field, value):
        # return {field[1]: {'$gt': value[1]}}
        return {
            '$or': [
                {'info.' + field[1]: {'$gt': value[1]}},
                {'arrays.' + field[1]: {'$gt': value[1]}},
                {'derived.' + field[1]: {'$gt': value[1]}},
            ]
        }

    def visit_gte(self, field, value):
        # return {field[1]: {'$gte': value[1]}}
        return {
            '$or': [
                {'info.' + field[1]: {'$gte': value[1]}},
                {'arrays.' + field[1]: {'$gte': value[1]}},
                {'derived.' + field[1]: {'$gte': value[1]}},
            ]
        }

    def visit_lt(self, field, value):
        # return {field[1]: {'$lt': value[1]}}
        return {
            '$or': [
                {'info.' + field[1]: {'$lt': value[1]}},
                {'arrays.' + field[1]: {'$lt': value[1]}},
                {'derived.' + field[1]: {'$lt': value[1]}},
            ]
        }

    def visit_lte(self, field, value):
        # return {field[1]: {'$lte': value[1]}}
        return {
            '$or': [
                {'info.' + field[1]: {'$lte': value[1]}},
                {'arrays.' + field[1]: {'$lte': value[1]}},
                {'derived.' + field[1]: {'$lte': value[1]}},
            ]
        }

    def visit_in(self, field, *values):
        # return {field[1]: {'$in': [value[1] for value in values]}}
        return {
            '$or': [
                {'info.' + field[1]: {'$in': [value[1] for value in values]}},
                {'arrays.' + field[1]: {'$in': [value[1] for value in values]}},
                {'derived.' + field[1]: {'$in': [value[1] for value in values]}},
            ]
        }

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def __call__(self, string):
        ast = self.parser.parse(string)
        logger.info('parsed ast: {}'.format(ast))
        return self.visit(ast) if ast is not None else {}


parser = MongoQuery()


def parse_query(func):
    def wrapper(*args, query=None, **kwargs):
        print(func)
        print((args, query, kwargs))
        query = parser(query)

        func(*args, **kwargs, query=query)

    return wrapper


class MongoDatabase(ABCD):
    """Wrapper to make database operations easy"""

    def __init__(self, host='localhost', port=27017,
                 db_name='abcd', collection_name='atoms',
                 username=None, password=None, authSource='admin', **kwargs):
        super().__init__()

        logger.info((host, port, db_name, collection_name, username, password, authSource, kwargs))

        self.client = MongoClient(
            host=host, port=port, username=username, password=password,
            authSource=authSource)

        self.db = self.client[db_name]
        self.collection = self.db[collection_name]

    def info(self):
        host, port = self.client.address

        return {
            'host': host,
            'port': port,
            'db': self.db.name,
            'collection': self.collection.name,
            'number of confs': self.collection.count(),
            'type': 'mongodb'
        }

    def delete(self, query=None):
        query = parser(query)
        return self.collection.delete_many(query)

    def destroy(self):
        self.collection.drop()

    def push(self, atoms: Union[Atoms, Iterable], extra_info=None):

        if extra_info and isinstance(extra_info, str):
            extra_info = key_val_str_to_dict(extra_info)

        if isinstance(atoms, Atoms):
            data = AtomsModel.from_atoms(atoms, extra_info)
            self.collection.insert_one(data)

        if isinstance(atoms, types.GeneratorType) or isinstance(atoms, list):
            self.collection.insert_many(AtomsModel.from_atoms(at, extra_info) for at in atoms)

    def upload(self, file, extra_info=None):

        if extra_info:
            extra_info = key_val_str_to_dict(' '.join(extra_info))
        else:
            extra_info = {}

        extra_info['filename'] = str(file)

        data = iread(str(file))
        self.push(data, extra_info)

    def get_atoms(self, query=None):
        query = parser(query)
        for dct in self.db.atoms.find(query):
            yield AtomsModel(dct).to_atoms()

    def count(self, query=None):
        query = parser(query)
        logger.info('query; {}'.format(query))

        if not query:
            return self.collection.count()

        return self.db.atoms.count_documents(query)

    def property(self, name, query=None):
        query = parser(query)

        pipeline = [
            {'$match': query},
            {'$match': {'{}'.format(name): {"$exists": True}}},
            {'$project': {'_id': False, 'data': '${}'.format(name)}}
        ]

        return [val['data'] for val in self.db.atoms.aggregate(pipeline)]

    def properties(self, query=None):
        query = parser(query)
        properties = {}

        pipeline = [
            {'$match': query},
            {'$unwind': '$derived.info_keys'},
            {'$group': {'_id': '$derived.info_keys'}}
        ]
        properties['info'] = [value['_id'] for value in self.db.atoms.aggregate(pipeline)]

        pipeline = [
            {'$match': query},
            {'$unwind': '$derived.arrays_keys'},
            {'$group': {'_id': '$derived.arrays_keys'}}
        ]
        properties['arrays'] = [value['_id'] for value in self.db.atoms.aggregate(pipeline)]

        return properties

    def count_properties(self, query=None):
        query = parser(query)

        properties = {
            'info': {},
            'arrays': {},
            'derived': {}
        }

        pipeline = [
            {'$match': query},
            {'$unwind': '$derived.info_keys'},
            {'$group': {'_id': '$derived.info_keys', 'count': {'$sum': 1}}}
        ]

        info_keys = self.db.atoms.aggregate(pipeline)
        for val in info_keys:
            properties['info'][val['_id']] = {'count': val['count']}

        pipeline = [
            {'$match': query},
            {'$unwind': '$derived.arrays_keys'},
            {'$group': {'_id': '$derived.arrays_keys', 'count': {'$sum': 1}}}
        ]
        arrays_keys = list(self.db.atoms.aggregate(pipeline))
        for val in arrays_keys:
            properties['arrays'][val['_id']] = {'count': val['count']}

        pipeline = [
            {'$match': query},
            {'$unwind': '$derived.derived_keys'},
            {'$group': {'_id': '$derived.derived_keys', 'count': {'$sum': 1}}}
        ]
        arrays_keys = list(self.db.atoms.aggregate(pipeline))
        for val in arrays_keys:
            properties['derived'][val['_id']] = {'count': val['count']}

        return properties

    def add_property(self, data, query=None):
        logger.info('add: data={}, query={}'.format(data, query))

        info_data = {'info.' + key: value for key, value in data.items()}

        self.collection.update_many(
            parser(query),
            {'$push': {'derived.info_keys': {'$each': list(data.keys())}},
             '$set': info_data})

    def rename_property(self, name, new_name, query=None):
        logger.info('rename: query={}, old={}, new={}'.format(query, name, new_name))

        self.collection.update_many(
            parser(query + ['info.{}'.format(name)]),
            {'$push': {'derived.info_keys': new_name}})

        self.collection.update_many(
            parser(query + ['info.{}'.format(name)]),
            {
                '$pull': {'derived.info_keys': name},
                '$rename': {'info.{}'.format(name): 'info.{}'.format(new_name)}})

        self.collection.update_many(
            parser(query + ['arrays.{}'.format(name)]),
            {'$push': {'derived.arrays_keys': new_name}})

        self.collection.update_many(
            parser(query + ['arrays.{}'.format(name)]),
            {'$pull': {'derived.arrays_keys': name},
             '$rename': {'arrays.{}'.format(name): 'arrays.{}'.format(new_name)}})

    def delete_property(self, name, query=None):
        logger.info('delete: query={}, porperty={}'.format(name, query))

        self.collection.update_many(
            parser(query + ['info.{}'.format(name)]),
            {'$pull': {'derived.info_keys': name},
             '$unset': {'info.{}'.format(name): ''}})

        self.collection.update_many(
            parser(query + ['arrays.{}'.format(name)]),
            {'$pull': {'derived.arrays_keys': name},
             '$unset': {'arrays.{}'.format(name): ''}})

    def hist(self, name, query=None, **kwargs):

        data = self.property(name, query)
        return histogram(name, data, **kwargs)

    def exec(self, code, query=None):
        for item in self.db.atoms.find(query):
            # TODO: map all of the available variables
            exec(code)

    def __repr__(self):
        host, port = self.client.address

        return '{}('.format(self.__class__.__name__) + \
               'url={}:{}, '.format(host, port) + \
               'db={}, '.format(self.db.name) + \
               'collection={})'.format(self.collection.name)

    def _repr_html_(self):
        """Jupyter notebook representation"""
        return '<b>ABCD MongoDB database</b>'

    def print_info(self):
        """shows basic information about the connected database"""

        out = linesep.join(['{:=^50}'.format(' ABCD MongoDB '),
                            '{:>10}: {}'.format('type', 'mongodb'),
                            linesep.join('{:>10}: {}'.format(k, v) for k, v in self.info().items())])

        print(out)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


def histogram(name, data, **kwargs):
    if not data:
        return None

    elif data and isinstance(data, list):
        if isinstance(data[0], float):
            bins = kwargs.get('bins', 10)
            return _hist_float(name, data, bins)

        elif isinstance(data[0], int):
            bins = kwargs.get('bins', 10)
            return _hist_int(name, data, bins)

        elif isinstance(data[0], str):
            return _hist_str(name, data, **kwargs)

        else:
            print('{}: Histogram for list of {} types are not supported!'.format(name, type(data)))
            logger.info('{}: Histogram for list of {} types are not supported!'.format(name, type(data)))

    else:
        logger.info('{}: Histogram for {} types are not supported!'.format(name, type(data)))
        return None


def _hist_float(name, data, bins=10):
    data = np.array(data)
    hist, bin_edges = np.histogram(data, bins=bins)

    return {
        'type': 'hist_float',
        'name': name,
        'bins': bins,
        'edges': bin_edges,
        'counts': hist,
        'min': data.min(),
        'max': data.max(),
        'median': data.mean(),
        'std': data.std(),
        'var': data.var()
    }


def _hist_int(name, data, bins=10):
    data = np.array(data)
    delta = max(data) - min(data) + 1

    if bins > delta:
        bins = delta

    hist, bin_edges = np.histogram(data, bins=bins)

    return {
        'type': 'hist_int',
        'name': name,
        'bins': bins,
        'edges': bin_edges,
        'counts': hist,
        'min': data.min(),
        'max': data.max(),
        'median': data.mean(),
        'std': data.std(),
        'var': data.var()
    }


def _hist_str(name, data, bins=10, truncate=20):
    n_unique = len(set(data))

    if truncate:
        # data = (item[:truncate] for item in data)
        data = (item[:truncate] + '...' if len(item) > truncate else item for item in data)

    data = Counter(data)

    if bins:
        labels, counts = zip(*sorted(data.items(), key=itemgetter(1, 0), reverse=True))
    else:
        labels, counts = zip(*data.items())

    return {
        'type': 'hist_str',
        'name': name,
        'total': sum(data.values()),
        'unique': n_unique,
        'labels': labels[:bins],
        'counts': counts[:bins]
    }


if __name__ == '__main__':
    # import json
    # from ase.io import iread
    # from pprint import pprint
    # from server.styles.myjson import JSONEncoderOld, JSONDecoderOld, JSONEncoder

    print('hello')
    db = MongoDatabase(username='mongoadmin', password='secret')
    print(db.info())
    print(db.count())

    # for atoms in iread('../../tutorials/data/bcc_bulk_54_expanded_2_high.xyz', index=slice(None)):
    #     # print(at)
    #     atoms.calc.results['forces'] = atoms.arrays['force']
    #     # at.arrays['force'] = None
    #
    #     json_data = json.dumps(atoms, cls=JSONEncoderOld)
    #     print(json_data)
    #
    #     atom_dict = json.loads(json_data, cls=JSONDecoderOld)
    #     print(atom_dict)
    #
    #     print(atoms == atom_dict)
    #
    # with JSONEncoder() as encoder:
    #     data = encoder.encode(atoms)
    #
    # print(data)
    #
    # with DictEncoder() as encoder:
    #     data = encoder.encode(atoms)
    #
    # pprint(data)
    #
    # db.collection.insert_one(DictEncoder().encode(atoms))
