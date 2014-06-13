# Copyright (C) 2014 Coders at Work
import types

class KeyValueStore(object):
    """A dictionary-like object which resolves internal values.

    This is the core of the variable referencing system of Habitat. Both Habitat
    and Components implement this mixin to allow people to use variables between
    the different components and use each other to resolve internal references.

    For example:
        class AnotherDictionary(Dictionary):
            value1 = '456'
        class MyCustomDictionary(Dictionary):
            value2 = '123%(value1)s789'

            def __init__(self):
                MyCustomDictionary.__init__(self, AnotherDictionary)

        assert(MyCustomDictionary()['value1'] == '456')
        assert(MyCustomDictionary()['value2'] == '123456789')

    There are more complex cases as well. Look for the unit tests to get ideas.

    The order of resolution is really important here:
        1. If the key is a direct attribute of the object, return that.
        2. If the key is a direct attribute of the kwargs, return that.
        3. If the parent contains the key, return that.
        4. If the KeyValueDefault class is defined in the class, fetch that
           value.
        5. Finally, returns the default value (or throw).

    WARNING: Case 3 and 4 interacts in a non-intuitive way: if the key is in the
    parent's KeyValueDefault object, then it will be used instead of the class's
    default.

    Setting items results in either the kwargs object being modified, or the
    attribute being set. The value returned is the same as the value set.
    """

    def __init__(self, parent=None, **kwargs):
        self.__parent = parent
        self.__kwargs = kwargs

    class __ShouldThrow:
        pass

    class __Default:
        pass

    def __format_value(self, value, target, context):
        if isinstance(value, basestring):
            return value % context
        elif isinstance(value, (list, tuple)):
            return map(lambda x: self.__format_value(x, target, context), value)
        elif isinstance(value, dict):
            return {
                self.__format_value(key, target, context):
                        self.__format_value(value, target, context)
                for key, value in value.iteritems()
            }
        elif isinstance(value, (
                types.FunctionType,
                types.BuiltinFunctionType,
                types.MethodType,
                types.BuiltinMethodType,
                types.UnboundMethodType)):
            return self.__format_value(value(), target, context)
        else:
            return value

    def __has_value(self, key, target, context):
        class __Nothing:
            pass

        if '.' in key:
            keylist = key.split('.')
            for n in keylist[:-1]:
                if isinstance(target, KeyValueStore):
                    target = self.__resolve_value(n, target, context, default)
                else:
                    target = target[n]
            key = keylist[-1]

        has = False
        if isinstance(target, dict):
            has = key in target
        elif isinstance(target, (list, tuple)):
            has = key in target
        else:
            has = hasattr(target, key)

        return (   has
                or (self.__kwargs and key in self.__kwargs)
                or (hasattr(self, 'KeyValueDefault') and hasattr(self.KeyValueDefault, key))
                or (self.__parent and key in self.__parent))

    def __resolve_value(self, key, target, context,
                              default=__ShouldThrow):
        if '.' in key:
            keylist = key.split('.')
            for n in keylist[:-1]:
                if isinstance(target, KeyValueStore):
                    target = self.__resolve_value(n, target, context, default)
                else:
                    target = target[n]
            key = keylist[-1]

        # The order of resolution is really important here:
        #     1. If the key is a direct attribute of the object, return that.
        #     2. If the key is a direct attribute of the kwargs, return that.
        #     3. If the parent contains the key, return that.
        #     4. If the KeyValueDefault class is defined in the class, fetch that value.
        #     5. Finally, returns the default value (or throw).
        # Covering case 1 for dictionaries, lists and tuples, and attributes on self.
        if isinstance(target, dict) and key in target:
            return self.__format_value(target[key], target, context)
        elif isinstance(target, (list, tuple)):
            return self.__format_value(target[int(key)], target, context)
        elif hasattr(target, key):
            return self.__format_value(getattr(target, key), target, context)

        # Case 2.
        elif key in self.__kwargs:
            return self.__format_value(self.__kwargs[key], target, context)
        # Case 3.
        elif target.__parent and key in target.__parent:
            return self.__resolve_value(key, self.__parent, context, default)

        # Case 4.
        elif (    hasattr(target.__class__, 'KeyValueDefault')
              and hasattr(target.__class__.KeyValueDefault, key)):
            return self.__format_value(getattr(target.__class__.KeyValueDefault, key),
                                       target, context)

        # Case 5.
        elif default is KeyValueStore.__ShouldThrow:
            raise Exception('Could not find value keyd "%s".' % key)
        else:
            return self.__format_value(default, target, context)

    def __contains__(self, key):
        return self.__has_value(key, self, self)
    def __getitem__(self, key):
        return self.__resolve_value(key, self, self)
    def __setitem__(self, key, value):
        if hasattr(self, key):
            setattr(self, key, value)
        else:
            self.__kwargs[key] = value
        return value

    def get(self, key, default_value=None):
        return self.__resolve_value(key, self, self, default_value)
    def format(self, str):
        return self.__format_value(str, self, self)

    @property
    def parent(self):
        return self.__parent
    @parent.setter
    def parent(self, value):
        self.__parent = value
