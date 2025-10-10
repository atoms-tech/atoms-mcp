"""Currying and partial application."""

from functools import partial as _partial
from functools import wraps
from typing import Callable


def curry(func: Callable, arity: int = None) -> Callable:
    """
    Curry a function.

    Example:
        def add(a, b, c):
            return a + b + c
        
        curried = curry(add)
        curried(1)(2)(3)  # 6
        curried(1, 2)(3)  # 6
    """
    if arity is None:
        arity = func.__code__.co_argcount

    @wraps(func)
    def curried(*args, **kwargs):
        if len(args) + len(kwargs) >= arity:
            return func(*args, **kwargs)
        return lambda *more_args, **more_kwargs: curried(
            *(args + more_args),
            **{**kwargs, **more_kwargs}
        )

    return curried


def partial(func: Callable, *args, **kwargs) -> Callable:
    """
    Partial function application.

    Example:
        add = lambda x, y: x + y
        add5 = partial(add, 5)
        add5(10)  # 15
    """
    return _partial(func, *args, **kwargs)
