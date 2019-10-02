import logging

import os
import numpy as np

from abcd.frontends.commandline.decorators import init_db, init_config, check_readonly

logger = logging.getLogger(__name__)


@init_config
def login(*, config, name, url, **kwargs):
    logger.info('login args: \nconfig:{}, name:{}, url:{}, kwargs:{}'.format(config, name, url, kwargs))
    from abcd import ABCD
    from abcd.errors import URLError, AuthenticationError

    try:
        db = ABCD.from_url(url=url)
        info = db.info()

        config['url'] = url
        config.save()

        print('Successfully connected to the database!')
        print(" type:       {type}\n"
              " hostname:   {host}\n"
              " port:       {port}\n"
              " database:   {db}\n"
              " # of confs: {number of confs}".format(**info))

    except URLError:
        print('Wrong connection: Please check the parameters of th url!')
        exit(1)
    except AuthenticationError:
        print('Authentication failed!')
        exit(1)


@init_config
@init_db
def download(*, db, query, filename, **kwargs):
    logger.info('download\n kwargs: {}'.format(kwargs))

    from ase.io import write
    write(filename, list(db.get_atoms(query=query)))


@init_config
@init_db
@check_readonly
def delete(*, db, query, yes, **kwargs):
    logger.info('delete\n kwargs: {}'.format(kwargs))

    if not yes:
        print('Please use --yes for deleting {} configurations'.format(db.count(query=query)))
        exit(1)

    count = db.delete(query=query)
    print('{} configuration has been deleted'.format(count))


@init_config
@init_db
@check_readonly
def upload(*, db, path, extra_infos, ignore_calc_results, **kwargs):
    from pathlib import Path

    calculator = not ignore_calc_results

    path = Path(path)

    if path.is_file():
        db.upload(path, extra_infos, calculator=calculator)

    elif path.is_dir():
        for file in path.glob('.xyz'):
            logger.info('Uploaded file: {}'.format(file))
            db.upload(file, extra_infos, calculator=calculator)
        else:
            logger.info('No file found: {}'.format(path))
            raise FileNotFoundError()

    else:
        raise FileNotFoundError()


@init_config
@init_db
def summary(*, db, query, print_all, bins, truncate, props, **kwargs):
    logger.info('summary\n kwargs: {}'.format(kwargs))
    logger.info('query: {}'.format(query))

    if print_all:
        bins, truncate = None, None

    if props is None:
        props_list = None
    else:
        import re

        props_list = []
        for prop in props:
            # TODO: Check that is this the right place?
            props_list.extend(re.split(r';\s*|,\s*|\s+', prop))

        if '*' in props_list:
            props_list = '*'

        logging.info('property list: {}'.format(props_list))

    f = Formater()
    if props_list is None:

        total = db.count(query)
        props = db.count_properties(query=query)

        print('Total number of configurations: {}'.format(total))

        if props['arrays']:
            f.title('Arrays (per atom properties)')

            labels, counts = [], []
            for k in sorted(props['arrays'], key=str.lower):
                labels.append(k)
                counts.append(props['arrays'][k]['count'])

            f.hist_labels(counts, labels)

        if props['info']:
            f.title('Infos (properties of the whole configuration)')

            labels, counts = [], []
            for k in sorted(props['info'], key=str.lower):
                labels.append(k)
                counts.append(props['info'][k]['count'])

            f.hist_labels(counts, labels)

        if props['derived']:
            f.title('Derived')

            labels, counts = [], []
            for k in sorted(props['derived'], key=str.lower):
                labels.append(k)
                counts.append(props['derived'][k]['count'])

            f.hist_labels(counts, labels)

    elif props_list == '*':
        props = db.properties(query=query)

        for p in props['arrays']:
            data = db.hist(p, query=query, bins=bins, truncate=truncate)

            if data:
                f.describe(data)
                f.hist(data)

        for p in props['info']:
            data = db.hist(p, query=query, bins=bins, truncate=truncate)

            if data:
                f.describe(data)
                f.hist(data)

    else:
        for p in props_list:
            data = db.hist(p, query=query, bins=bins, truncate=truncate)

            if data:
                f.describe(data)
                f.hist(data)


@init_config
@init_db
def show(*, db, query, print_all, props, **kwargs):
    logger.info('show\n kwargs: {}'.format(kwargs))
    logger.info('query: {}'.format(query))

    limit = None if print_all else 10

    from itertools import islice

    for dct in islice(db.get_items(query), 0, limit):
        if props:
            for prop in props:
                print(dct.get(prop, None))
            continue

        print(dct)

    logging.info('property list: {}'.format(props))


@check_readonly
@init_config
@init_db
def key_add(*, db, query, keys, **kwargs):
    from abcd.parsers.extras import parser

    keys = ' '.join(keys)
    data = parser.parse(keys)

    if query:
        test = ('AND', query, ("OR", *(('NAME', key) for key in data.keys())))
    else:
        test = ("OR", *(('NAME', key) for key in data.keys()))

    if db.count(query=test):
        print('The new key already exist for the given query! '
              'Please make sure that the target key name don\'t exist')
        exit(1)

    db.add_property(data, query=query)


@check_readonly
@init_config
@init_db
def key_rename(*, db, query, old_keys, new_keys, **kwargs):
    if db.count(query=query + [old_keys, new_keys]):
        print('The new key already exist for the given query! '
              'Please make sure that the target key name don\'t exist')
        exit(1)

    db.rename_property(old_keys, new_keys, query=query)


@check_readonly
@init_config
@init_db
def key_delete(*, db, query, yes, keys, **kwargs):
    print(keys)
    print(query)

    query += keys

    if not yes:
        print('Please use --yes for deleting keys from {} configurations'.format(db.count(query=query)))
        exit(1)

    for k in keys:
        db.delete_property(k, query=query)


@check_readonly
@init_config
@init_db
def execute(*, db, query, yes, python_code, **kwargs):
    if not yes:
        print('Please use --yes for executing code on {} configurations'.format(db.count(query=query)))
        exit(1)

    db.exec(python_code, query)


class Formater(object):
    partialBlocks = ["▏", "▎", "▍", "▌", "▋", "▊", "▉", "█"]  # char=pb

    def title(self, title):
        print('', title, '=' * len(title), sep=os.linesep)

    def describe(self, data):
        if data['type'] == 'hist_float':
            print('{}  count: {} '.format(data["name"], sum(data["counts"])),
                  'min: {:.8g} med: {:.8g} max: {:.8g}  '.format(data["min"], data["median"], data["max"]),
                  'std: {:.8g} var:{:.8g}'.format(data["std"], data["var"])
                  )

        elif data['type'] == 'hist_int':
            print('{}  count: {} '.format(data["name"], sum(data["counts"])),
                  'min: {:d} med: {:d} max: {:d}  '.format(int(data["min"]), int(data["median"]), int(data["max"]))
                  )

        elif data['type'] == 'hist_str':
            print('{} count: {} unique: {}'.format(data["name"], data["total"], data["unique"]))

        else:
            pass

    def hist_float(self, bin_edges, counts, width_hist=40):
        ratio = width_hist / max(counts)
        width_count = len(str(max(counts)))

        for count, lower, upper in zip(counts, bin_edges[:-1], bin_edges[1:]):
            scale = int(ratio * count)
            self.print('{:<{}} {:>{}d} [{:.4e}, {:.4e})'.format(
                "▉" * scale, width_hist,
                count, width_count,
                lower, upper))

    def hist_int(self, bin_edges, counts, width_hist=40):

        ratio = width_hist / max(counts)
        width_count = len(str(max(counts)))

        for count, lower, upper in zip(counts, bin_edges[:-1], bin_edges[1:]):
            scale = int(ratio * count)
            self.print('{:<{}} {:>{}d} [{:d}, {:d})'.format(
                "▉" * scale, width_hist,
                count, width_count,
                np.ceil(lower).astype(int), np.floor(upper).astype(int)))

    def hist_str(self, total, counts, labels, width_hist=40):
        remain = total - sum(counts)
        if remain > 0:
            counts = (*counts, remain)
            labels = (*labels, '...')

        width_count = len(str(max(counts)))
        ratio = width_hist / max(counts)
        for label, count in zip(labels, counts):
            scale = int(ratio * count)
            self.print('{:<{}} {:>{}d} {}'.format("▉" * scale, width_hist, count, width_count, label))

    def hist_labels(self, counts, labels, width_hist=40):

        width_count = len(str(max(counts)))
        ratio = width_hist / max(counts)
        for label, count in zip(labels, counts):
            scale = int(ratio * count)
            self.print('{:<{}} {:>{}d} {}'.format("▉" * scale, width_hist, count, width_count, label))

    def hist(self, data: dict, width_hist=40):
        if data['type'] == 'hist_float':
            self.hist_float(data['edges'], data['counts'])
        elif data['type'] == 'hist_int':
            self.hist_int(data['edges'], data['counts'])
        elif data['type'] == 'hist_str':
            self.hist_str(data['total'], data['counts'], data['labels'])
        elif data['type'] == 'hist_labels':
            self.hist_labels(data['counts'], data['labels'])
        else:
            pass

    @staticmethod
    def print(*args, **kwargs):
        print(*args, **kwargs)

    def _trunc(self, text, width=80):
        return text if len(text) < width else text[:width - 3] + '...'