# Copyright (C) 2014 Coders at Work
from habitat.dependency import *

import unittest


class DependencyTest(unittest.TestCase):
    def test_simple(self):
        dependencies = {
            "A": [],
            "B": []
        }
        self.assertEquals(dependencies.keys(), order_dependencies(dependencies))

    def test_simple_2(self):
        dependencies = {
            "A": [],
            "B": ["A"]
        }
        self.assertEquals(dependencies.keys(), order_dependencies(dependencies))

    def test_simple_3(self):
        dependencies = {
            "A": ["B"],
            "B": []
        }
        self.assertEquals(["B", "A"], order_dependencies(dependencies))
