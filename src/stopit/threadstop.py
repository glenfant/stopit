# -*- coding: utf-8 -*-
"""
======
stopit
======

Raise asynchronous exceptions in other thread, control the timeout of blocks
or callables with a context manager or a decorator.
"""

import ctypes
import threading

from .utils import TimeoutException, BaseTimeout, base_timeoutable


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


class ThreadingTimeout(BaseTimeout):
    """Context manager for limiting in the time the execution of a block

    :param seconds: ``float`` or ``int`` duration enabled to run the context
      manager block
    :param swallow_exc: ``False`` if you want to manage the
      ``TimeoutException`` (or any other) in an outer ``try ... except``
      structure. ``True`` (default) if you just want to check the execution of
      the block with the ``state`` attribute of the context manager.
    """

    def __init__(self, seconds, swallow_exc=True):
        super(ThreadingTimeout, self).__init__(seconds, swallow_exc)
        self.target_tid = threading.current_thread().ident
        self.timer = None  # PEP8

    def stop(self):
        """Called by timer thread at timeout. Raises a Timeout exception in the
        caller thread
        """
        self.state = BaseTimeout.TIMED_OUT
        async_raise(self.target_tid, TimeoutException)

    def setup_interrupt(self):
        """Setting up the resource that interrupts the block
        """
        self.timer = threading.Timer(self.seconds, self.stop)
        self.timer.start()

    def suppress_interrupt(self):
        """Removing the resource that interrupts the block
        """
        self.timer.cancel()


class threading_timeoutable(base_timeoutable):  #noqa
    """A function or method decorator that raises a ``TimeoutException`` to
    decorated functions that should not last a certain amount of time.
    this one uses ``ThreadingTimeout`` context manager.

    See :class:`.utils.base_timoutable`` class for further comments.
    """
    to_ctx_mgr = ThreadingTimeout


if __name__ == '__main__':
    import doctest
    doctest.testmod()
