# Copyright (C) 2014 Coders at Work
from habitat.keyvalue import *

import unittest


class KeyValueStoreTest(unittest.TestCase):
    def test_simple(self):
        class Simple(KeyValueStore):
            value = 'abc'
            value2 = 'abc%(value)s'
        d = Simple()
        self.assertEquals(d['value'], 'abc')
        self.assertEquals(d['value2'], 'abcabc')

    def test_inherit(self):
        class Base(KeyValueStore):
            value = 'abc'
        class Sub(Base):
            value2 = 'abc%(value)s'

        d = Sub()
        self.assertEquals(d['value'], 'abc')
        self.assertEquals(d['value2'], 'abcabc')

    def test_parent(self):
        class Parent(KeyValueStore):
            value = 'abc'
        class Test(KeyValueStore):
            def __init__(self):
                super(Test, self).__init__(Parent())
            value2 = 'abc%(value)s'

        d = Test()
        self.assertEquals(d['value'], 'abc')
        self.assertEquals(d['value2'], 'abcabc')

    def test_parent_2(self):
        class Parent(KeyValueStore):
            value2 = 'abc%(value)s'
        class Test(KeyValueStore):
            def __init__(self):
                super(Test, self).__init__(Parent())
            value = 'abc'

        d = Test()
        self.assertEquals(d['value'], 'abc')
        self.assertEquals(d['value2'], 'abcabc')

    def test_parent_3(self):
        class Parent(KeyValueStore):
            value = 'abc%(value3)s'
        class Test(KeyValueStore):
            def __init__(self):
                super(Test, self).__init__(Parent())
            value2 = 'abc%(value)s'
            value3 = 'abc'

        d = Test()
        self.assertEquals(d['value'], 'abcabc')
        self.assertEquals(d['value2'], 'abcabcabc')

    def test_parent_4(self):
        class Base(KeyValueStore):
            value = 'abc%(value2)s'
        class Parent(Base):
            value2 = 'abc%(value3)s'
        class Test(Base):
            def __init__(self):
                super(Test, self).__init__(Parent())
            value3 = 'abc'

        d = Test()
        self.assertEquals(d['value'], 'abcabcabc')

    def test_parent_5(self):
        class Base(KeyValueStore):
            value = 'abc%(value2)s'
        class Parent(Base):
            value2 = 'abc%(value3)s'
            value3 = '123'
        class Test(Base):
            def __init__(self):
                super(Test, self).__init__(Parent())
            value3 = 'abc'

        d = Test()
        self.assertEquals(d['value'], 'abcabcabc')

    def test_parent_6(self):
        class Base(KeyValueStore):
            value = 'abc%(value2)s'
            value3 = '123'
        class Parent(Base):
            value2 = 'abc%(value3)s'
            value3 = 'abc'
        class Test(Base):
            def __init__(self):
                super(Test, self).__init__(Parent())

        d = Test()
        self.assertEquals(d['value'], 'abcabc123')

    def test_parent_7(self):
        class Base(KeyValueStore):
            value = 'abc%(value2)s'
            class KeyValueDefault:
                value3 = '123'
        class Parent(Base):
            value2 = 'abc%(value3)s'
            class KeyValueDefault:
                value3 = '456'
        class Test(Base):
            def __init__(self):
                super(Test, self).__init__(Parent())

        d = Test()
        self.assertEquals(d['value'], 'abcabc456')

    def test_parent_8(self):
        class Base(KeyValueStore):
            value = 'abc%(value2)s'
            value3 = '123'
        class Parent(Base):
            value2 = 'abc%(value3)s'
            value3 = '456'
        class Test(Base):
            def __init__(self):
                super(Test, self).__init__(Parent())

        d = Test()
        self.assertEquals(d['value'], 'abcabc123')

    def test_parent_9(self):
        class Base(KeyValueStore):
            value = 'abc%(value2)s'
            class KeyValueDefault:
                value3 = '123'
        class Parent(Base):
            value2 = 'abc%(value3)s'
        class Test(Base):
            def __init__(self):
                super(Test, self).__init__(Parent())

        d = Test()
        self.assertEquals(d['value'], 'abcabc123')

    def test_set_1(self):
        class Simple(KeyValueStore):
            value = 'abc'
        d = Simple()
        self.assertEquals(d['value'], 'abc')
        d['value'] = 'def'
        self.assertEquals(d['value'], 'def')

        d['value2'] = 'def'
        d['value'] = 'abc%(value2)s'
        self.assertEquals(d['value'], 'abcdef')


