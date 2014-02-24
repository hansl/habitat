# Copyright (C) 2014 Coders at Work
import types

class Dictionary(object):
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
    def _format_value(self, value, context):
        if isinstance(value, basestring):
            return value % context
        elif isinstance(value, (list, tuple)):
            return map(lambda x: x % context, value)
        elif isinstance(value, dict):
            return {
                key % context: self._format_value(value, context)
                for key, value in value.iteritems()
            }
        elif isinstance(value, (
                types.FunctionType,
                types.BuiltinFunctionType,
                types.MethodType,
                types.BuiltinMethodType,
                types.UnboundMethodType)):
            return self._format_value(value(), context)
        else:
            return value

    def _resolve_value(self, name, target=None, context=None,
                            default=__ShouldThrow):
        if target is None:
            target = self
        if context is None:
            context = self
        if '.' in name:
            namelist = name.split('.')
            for n in namelist[:-1]:
                if isinstance(target, Dictionary):
                    target = self._resolve_value(n, target, context, default)
                else:
                    target = target[n]
            name = namelist[-1]

        class __Default:
            pass

        if isinstance(target, dict):
            value = target.get(name, __Default)
        elif isinstance(target, (list, tuple)):
            value = target[name]
        else:
            value = getattr(target, name, __Default)

        if value == __Default:
            if value in self.__kwargs:
                return self._format_value(self.__kwargs[value], context)
            elif self.__parent:
                return self.__parent._resolve_value(name, self.__parent,
                                                    context, default)
            elif default is Dictionary.__ShouldThrow:
                raise Exception('Could not find value named "%s".' % name)
            else:
                return default

        else:
            if self.__parent and name in self.__parent:
                return self.__parent._resolve_value(name, self.__parent,
                                                    context, default)
            return self._format_value(value, context)

    def __contains__(self, name):
        class __Nothing:
            pass
        return self._resolve_value(name, default=__Nothing) is not __Nothing
    def __getitem__(self, name):
        return self._resolve_value(name)

    @property
    def parent(self):
        return self.__parent
    @parent.setter
    def parent(self, value):
        self.__parent = value
