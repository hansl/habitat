# Copyright (C) 2014 Coders at Work


class CyclicalDependencyListError(Exception):
    @property
    def deps(self):
        return self._deps
    def __init__(self, deps):
        self._deps = deps
        super(CyclicalDependencyListError, self).__init__(
            u'A list of components has a dependency cycle: %r.' % deps)


class InvalidDependencyError(Exception):
    pass


def order_dependencies(deps, implicit_deps=True):
    """Order a list of components by their dependencies. This ensure that
    the caller could iterate through the returned list without having
    considerations for dependencies, as they are already ordered.

    Will throw:
        CyclicalDependencyListError: if a cycle is discovered.
        InvalidDependencyError: If a dependency is not part of the list.

    Example:
        order_dependencies({'A': ['A', 'B']}) == ['B', 'A']
        order_dependencies({'A': ['A', 'B'], False}) will throw.
        order_dependencies({'A': ['A', 'B'], 'B': [], False}) == ['B', 'A']

        Please note the second example output is slightly different
        because of the order of the input, but the assumptions aren't
        broken.

    Optional dependencies are supported by this.
    """
    ret_list = list()
    ordered_set = set(deps.keys())

    while len(ordered_set):
        to_add = []

        for c in ordered_set:
            should_add = True
            for d in deps[c]:
                if d not in ret_list:
                    if d not in ordered_set:
                        if not implicit_deps:
                            raise InvalidDependencyError(d)
                        else:
                            to_add.append(d)
                    else:
                        should_add = False
                        break

            if should_add:
                to_add.append(c)

        for c in to_add:
            ret_list.append(c)
            ordered_set.remove(c)

        if not to_add and not to_remove and ordered_set:
            raise CyclicalDependencyListError(ordered_set)

    return ret_list
