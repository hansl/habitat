# Copyright (C) 2014 Coders at Work
from habitat.dictionary import *

import unittest


class DictionaryTest(unittest.TestCase):
    def test_simple(self):
        class Simple(Dictionary):
            value = 'abc'
            value2 = 'abc%(value)s'
        d = Simple()
        self.assertEquals(d['value'], 'abc')
        self.assertEquals(d['value2'], 'abcabc')

    def test_inherit(self):
        class Base(Dictionary):
            value = 'abc'
        class Sub(Base):
            value2 = 'abc%(value)s'

        d = Sub()
        self.assertEquals(d['value'], 'abc')
        self.assertEquals(d['value2'], 'abcabc')

    def test_parent(self):
        class Parent(Dictionary):
            value = 'abc'
        class Test(Dictionary):
            def __init__(self):
                super(Test, self).__init__(Parent())
            value2 = 'abc%(value)s'

        d = Test()
        self.assertEquals(d['value'], 'abc')
        self.assertEquals(d['value2'], 'abcabc')

    def test_parent_2(self):
        class Parent(Dictionary):
            value2 = 'abc%(value)s'
        class Test(Dictionary):
            def __init__(self):
                super(Test, self).__init__(Parent())
            value = 'abc'

        d = Test()
        self.assertEquals(d['value'], 'abc')
        self.assertEquals(d['value2'], 'abcabc')

    def test_parent_3(self):
        class Parent(Dictionary):
            value = 'abc%(value3)s'
        class Test(Dictionary):
            def __init__(self):
                super(Test, self).__init__(Parent())
            value2 = 'abc%(value)s'
            value3 = 'abc'

        d = Test()
        self.assertEquals(d['value'], 'abcabc')
        self.assertEquals(d['value2'], 'abcabcabc')

    def test_parent_4(self):
        class Base(Dictionary):
            value = 'abc%(value2)s'
        class Parent(Base):
            value2 = 'abc%(value3)s'
        class Test(Base):
            def __init__(self):
                super(Test, self).__init__(Parent())
            value3 = 'abc'

        d = Test()
        self.assertEquals(d['value'], 'abcabcabc')

