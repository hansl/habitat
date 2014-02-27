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

    def __has_value(self, name, target, context):
        class __Nothing:
            pass

        if '.' in name:
            namelist = name.split('.')
            for n in namelist[:-1]:
                if isinstance(target, KeyValueStore):
                    target = self.__resolve_value(n, target, context, default)
                else:
                    target = target[n]
            name = namelist[-1]

        has = False
        if isinstance(target, dict):
            has = name in target
        elif isinstance(target, (list, tuple)):
            has = name in target
        else:
            has = hasattr(target, name)

        return (   has
                or (self.__kwargs and name in self.__kwargs)
                or (self.__parent and name in self.__parent))

    def __resolve_value(self, name, target, context,
                              default=__ShouldThrow):
        if '.' in name:
            namelist = name.split('.')
            for n in namelist[:-1]:
                if isinstance(target, KeyValueStore):
                    target = self.__resolve_value(n, target, context, default)
                else:
                    target = target[n]
            name = namelist[-1]

        if isinstance(target, dict):
            value = target.get(name, KeyValueStore.__Default)
        elif isinstance(target, (list, tuple)):
            value = target[name]
        else:
            value = getattr(target, name, KeyValueStore.__Default)

        if value == KeyValueStore.__Default:
            if name in self.__kwargs:
                return self.__format_value(self.__kwargs[name], target, context)
            elif self.__parent:
                return self.__parent.__resolve_value(name, self.__parent,
                                                     context, default)
            elif default is KeyValueStore.__ShouldThrow:
                raise Exception('Could not find value named "%s".' % name)
            else:
                return default

        else:
            if self.__parent and self.__parent.__has_value(name, self.__parent, context):
                parent_value = self.__parent.__resolve_value(name, self.__parent,
                                                             context, default)
                if parent_value:
                    return parent_value
            return self.__format_value(value, target, context)

    def __contains__(self, name):
        return self.__has_value(name, self, self)
    def __getitem__(self, name):
        return self.__resolve_value(name, self, self)

    @property
    def parent(self):
        return self.__parent
    @parent.setter
    def parent(self, value):
        self.__parent = value
