# From http://stackoverflow.com/a/23257774/1986995

import inspect


class BadSignatureException(Exception):
    pass


class SignatureCheckerMeta(type):
    def __new__(mcs, name, base_classes, d):
        # For each method in d, check to see if any base class already
        # defined a method with that name. If so, make sure the
        # signatures are the same.
        for method_name, func in d.items():
            for base_class in base_classes:
                base_func = getattr(base_class, method_name)
                if not callable(base_func):
                    continue

                inspect_func = inspect.signature(func)
                inspect_base_func = inspect.signature(base_func)
                if not inspect_func == inspect_base_func:
                    raise BadSignatureException("{func} expected to take {args}".format(
                        func=func.__qualname__, args=inspect_base_func))

        return type(name, base_classes, d)
