# -*- coding: utf-8 -*-
"""
======
stopit
======

Raise asynchronous exceptions in other thread, control the timeout of blocks
or callables with a context manager or a decorator.
"""

import ctypes
import functools
import threading

__all__ = ('async_raise', 'TimeoutException', 'Timeout', 'timeoutable')


def async_raise(target_tid, exception):
    """Raises an asynchronous exception in another thread.
    Read http://docs.python.org/c-api/init.html#PyThreadState_SetAsyncExc
    for further enlightenments.

    :param target_tid: target thread identifier
    :param exception: Exception class to be raised in that thread
    """
    # Ensuring and releasing GIL are useless since we're not in C
    # gil_state = ctypes.pythonapi.PyGILState_Ensure()
    ret = ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(target_tid),
                                                     ctypes.py_object(exception))
    # ctypes.pythonapi.PyGILState_Release(gil_state)
    if ret == 0:
        raise ValueError("Invalid thread ID {}".format(target_tid))
    elif ret > 1:
        ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(target_tid), None)
        raise SystemError("PyThreadState_SetAsyncExc failed")


class TimeoutException(Exception):
    pass


class Timeout(object):
    """Context manager for limiting in the time the execution of a block

    :param seconds: ``float`` or ``int`` duration enabled to run the context
      manager block
    :param swallow_exc: ``False`` if you want to manage the
      ``TimeoutException`` (or any other) in an outer ``try ... except``
      structure. ``True`` (default) if you just want to check the execution of
      the block with the ``state`` attribute of the context manager.
    """

    # Possible values for the ``state`` attribute, self explanative
    EXECUTED, EXECUTING, TIMED_OUT, INTERRUPTED, CANCELED = range(5)

    def __init__(self, seconds, swallow_exc=True):
        self.seconds = seconds
        self.swallow_exc = swallow_exc
        self.state = Timeout.EXECUTED
        self.target_tid = threading.current_thread().ident

    def __bool__(self):
        return self.state in (Timeout.EXECUTED, Timeout.EXECUTING)

    def stop(self):
        """Called by timer thread at timeout. Raises a Timeout exception in the
        caller thread
        """
        self.state = Timeout.TIMED_OUT
        async_raise(self.target_tid, TimeoutException)

    def cancel(self):
        """In case in the block you realize you don't need anymore
       limitation"""
        self.state = Timeout.CANCELED
        self.timer.cancel()

    def __enter__(self):
        self.state = Timeout.EXECUTING
        self.timer = threading.Timer(self.seconds, self.stop)
        self.timer.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is TimeoutException:
            if self.state != Timeout.TIMED_OUT:
                self.state = Timeout.INTERRUPTED
                self.timer.cancel()
            return self.swallow_exc
        else:
            if exc_type is None:
                self.state = Timeout.EXECUTED
            self.timer.cancel()
        return False

    def __repr__(self):
        """Debug helper
        """
        return "<Timeout in state: {}>".format(self.state)


class timeoutable(object):
    """A function or method decorator that raises a ``TimeoutException`` to
    decorated functions that should not last a certain amount of time.

    Any decorated callable may receive a ``timeout`` optional parameter that
    specifies the number of seconds allocated to the callable execution.

    The decorated functions that exceed that timeout return ``None`` or the
    value provided by the decorator.

    :param default: The default value in case we timed out during the decorated
      function execution. Default is None.

    :param timeout_param: As adding dynamically a ``timeout`` named parameter
      to the decorated callable may conflict with the callable signature, you
      may choose another name to provide that parameter. Your decoration line
      could look like ``@timeoutable(timeout_param='my_timeout')``
    """
    def __init__(self, default=None, timeout_param='timeout'):
        self.default, self.timeout_param = default, timeout_param

    def __call__(self, func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            timeout = kwargs.pop(self.timeout_param, None)
            if timeout:
                with Timeout(timeout, swallow_exc=True):
                    result = self.default
                    # ``result`` may not be assigned below in case of timeout
                    result = func(*args, **kwargs)
                return result
            else:
                return func(*args, **kwargs)
        return wrapper


if __name__ == '__main__':
    import doctest
    doctest.testmod()
