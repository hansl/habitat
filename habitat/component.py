# Copyright (C) 2014 Coders at Work
from dictionary import Dictionary

import os
import sys

class ComponentBase(Dictionary):
    __habitat = None

    @property
    def habitat(self):
        return self._habitat
    @habitat.setter
    def habitat(self, value):
        self.parent = value
        self._habitat = value
