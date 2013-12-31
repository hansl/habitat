# Copyright (C) 2013 Coders at Work
import base64
import pickle
import re
import os


class MetaDataStorage(object):
    def __init__(self, path, should_load=True):
        self.path = path
        if should_load:
            self.load()
        else:
            self._dict = None

    def load(self):
        if os.path.exists(self.path):
            with open(self.path, 'r') as fin:
                data = fin.read()
            self._dict = self._load(data)
        else:
            self._dict = {}

    def save(self, to=None):
        if to is None:
            to = self.path
        data = self._save(self._dict)
        if data is not None:
            with open(to, 'w') as fout:
                fout.write(data)

    def _load(self, data):
        raise NotImplementedError()
    def _save(self, dict):
        raise NotImplementedError()

    def __contains__(self, name):
        return name in self._dict
    def __getitem__(self, name):
        return self._dict[name]
    def __setitem__(self, name, value):
        self._dict[name] = value
        self.save()

    def __str__(self):
        return str(self._dict)
    def __unicode__(self):
        return unicode(self._dict)
    def get(self, name, default=None):
        return self._dict.get(name, default)


class PickleStorage(MetaDataStorage):
    def _load(self, data):
        return pickle.loads(data)
    def _save(self, dict):
        return pickle.dumps(dict)


class TextFileStorage(MetaDataStorage):
    RE = r'^([a-zA-Z_][0-9a-zA-Z_-]*)\s*=\s*(.*)\s*\n'
    VALUE_RE = r'^\s*%(name)s\s*=.*\n'
    VALUE = '%(name)s = %(value)s\n'

    def __init__(self, path):
        self.RE = re.compile(self.RE, re.MULTILINE)
        super(TextFileStorage, self).__init__(path)

    def _load(self, data):
        self.data = data  # Save data for later.
        return {g.groups()[0]: g.groups()[1] for g in self.RE.finditer(data)}

    def _save(self, dict):
        if os.path.exists(self.path):
            with open(self.path, 'r') as fin:
                data = fin.read()
        else:
            data = ''

        for n, v in dict.iteritems():
            d = {'name': n, 'value': v}
            regex = re.compile(self.VALUE_RE % d)
            result = regex.sub(data, self.VALUE % d)
            if result == data:
                if len(data) and data[-1] != '\n':
                    data += '\n'
                data += self.VALUE % d
            else:
                data = result
        return data


class PythonCommentStorage(TextFileStorage):
    RE = r'^\s*#\s*@([a-zA-Z_][0-9a-zA-Z_-]*)\s*=\s*(.*)\s*\n'
    VALUE_RE = r'#\s*@%(name)s\s*=.*\n'
    VALUE = '# @%(name)s = %(value)s\n'


class MetaDataFile(object):
    def __init__(self, path, storage = PickleStorage):
        self.storage = storage(path)

    def __contains__(self, name):
        return name in self.storage

    def __getitem__(self, name):
        return self.storage.get(name, None)

    def __setitem__(self, name, value):
        self.storage[name] = value
