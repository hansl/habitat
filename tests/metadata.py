# Copyright (C) 2014 Coders at Work
from habitat.metadata import *

import tempfile
import unittest


class MetaDataStorageTest(unittest.TestCase):
    def test_raise(self):
        st = MetaDataStorage(__file__, False)
        self.assertRaises(NotImplementedError, st.load)
        self.assertRaises(NotImplementedError, st.save)

    def test_base(self):
        class TempStorage(MetaDataStorage):
            calls = 0
            dictionary = {'hello': 'world'}

            def _load(self, data):
                self.calls += 1
                return self.dictionary
            def _save(self, data):
                self.calls += 1
                return None

        st = TempStorage(__file__)
        self.assertEquals('world', st['hello'])
        st.save()

    def test_python_comment(self):
        # @TestValue = 123
        path = __file__
        if path.endswith('.pyc'):
            path = path[0:-1]
        st = PythonCommentStorage(path)
        self.assertEquals('123', st['TestValue'])

        path = tempfile.mktemp()
        st.save(path)

        st2 = PythonCommentStorage(path)
        st2['hello'] = 'world'
        self.assertEquals('123', st2['TestValue'])

    def test_text(self):
        path = tempfile.mktemp()
        st = TextFileStorage(path)
        st['hello'] = 'world'
        st.save()

        st2 = TextFileStorage(path)
        self.assertEquals('world', st2['hello'])

    def test_pickle(self):
        path = tempfile.mktemp()
        st = PickleStorage(path)
        st['hello'] = 'world'
        st.save()

        st2 = PickleStorage(path)
        self.assertEquals('world', st2['hello'])


class MetaDataFileTest(unittest.TestCase):
    def test_base(self):
        key = 'hello'
        value = ['world']
        path = tempfile.mktemp()
        md = MetaDataFile(path)
        md[key] = value
        md2 = MetaDataFile(path)
        self.assertEquals(value, md2[key])
