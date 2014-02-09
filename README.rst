======
stopit
======

.. admonition:: About

   Raise asynchronous exceptions in other thread, control the timeout of
   blocks or callables with a context manager or a decorator.


Overview
========

This module provides:

- a function that raises an exception in another thread, including the main
  thread.

- a context manager that may stop its inner block activity on timeout.

- a decorator that may stop its decorated callables on timeout.

There are several recipes that provide timeout related features. This one is
**cross-platforms** and **thread safe**, but due to the GIL management, the
timeout control is not as accurate as the one using signals (see below), and
may wait the end of a long blocking Python atomic instruction to take effect.

You may prefer an alternate solution that is based on signal handling that is
more accurate and takes over the GIL considerations like `this one
<https://gist.github.com/glenfant/7501911>`_ but with some limitations: (a) it
is not thread safe, (b) works only on Unix based OS and (c) does not support
timeout context manager nesting.

Developed and tested with CPython 2.6, 2.7 and 3.3 on MacOSX. Should work on
any OS (xBSD, Linux, Windows).

Installation
============

Using ``stopit`` in your application
------------------------------------

Both work identically:

.. code:: sh

  easy_install stopit
  pip install stopit

Developing ``stopit``
---------------------

.. code:: sh

  git clone https://github.com/glenfant/stopit.git
  cd stopit
  python setup.py develop

  # Does it work for you ?
  python setup.py test

Credits
=======

- This is a NIH package which is mainly a theft of `Gabriel Ahtune's recipe
  <http://gahtune.blogspot.fr/2013/08/a-timeout-context-manager.html>`_ with
  tests, minor improvements and refactorings, documentation and setuptools
  awareness I made since I'm somehow tired to copy/paste this recipe among
  projects that need timeout control.

- `Gilles Lenfant <gilles.lenfant@gmail.com>`_

Caveats and issues
==================

Will not work with other Python implementations (Iron Python, Jython, Pypy,
...) since we use CPython specific low level API.

Will not stop the execution of blocking Python atomic instructions that
acquire the GIL. In example, if the destination thread is actually executing a
``time.sleep(20)``, the asynchronous exception is effective **after** its
execution.

Improvements: set/release a lock where appropriate (timeout may occur when
``__exit__`` runs)

Tests and demos
===============

.. code:: pycon

  >>> from stopit import async_raise, TimeoutException, Timeout, timeoutable
  >>> import threading

Let's define some utilities:

.. code:: pycon

  >>> import time
  >>> def fast_func():
  ...     return 0
  >>> def variable_duration_func(duration):
  ...     t0 = time.time()
  ...     while True:
  ...         dummy = 0
  ...         if time.time() - t0 > duration:
  ...             break
  >>> exc_traces = []
  >>> def variable_duration_func_handling_exc(duration, exc_traces):
  ...     try:
  ...         t0 = time.time()
  ...         while True:
  ...             dummy = 0
  ...             if time.time() - t0 > duration:
  ...                 break
  ...     except Exception as exc:
  ...         exc_traces.append(exc)
  >>> def func_with_exception():
  ...     raise LookupError()

``async_raise`` function raises an exception in another thread
--------------------------------------------------------------

Testing ``async_raise()`` with a thread of 5 seconds:

.. code:: pycon

  >>> five_seconds_threads = threading.Thread(
  ...     target=variable_duration_func_handling_exc, args=(5.0, exc_traces))
  >>> start_time = time.time()
  >>> five_seconds_threads.start()
  >>> thread_ident = five_seconds_threads.ident
  >>> five_seconds_threads.is_alive()
  True

We raise a ``LookupError`` in that thread:

.. code:: pycon

  >>> async_raise(thread_ident, LookupError)

Okay but we must wait few milliseconds the thread death since the exception is
asynchronous:

.. code:: pycon

  >>> while five_seconds_threads.is_alive():
  ...     pass

And we can notice that we stopped the thread before it stopped by itself:

.. code:: pycon

  >>> time.time() - start_time < 0.5
  True
  >>> len(exc_traces)
  1
  >>> exc_traces[-1].__class__.__name__
  'LookupError'

``Timeout`` context manager
---------------------------

The context manager stops the execution of its inner block after a given time.
You may manage the way the timeout occurs using a ``try: ... except: ...``
construct or by inspecting the context manager ``state`` attribute after the
block.

Swallowing Timeout exceptions
.............................

We check that the fast functions return as outside our context manager:

.. code:: pycon

  >>> with Timeout(5.0) as timeout_ctx:
  ...     result = fast_func()
  >>> result
  0
  >>> timeout_ctx.state == timeout_ctx.EXECUTED
  True

We check that slow functions are interrupted:

.. code:: pycon

  >>> start_time = time.time()
  >>> with Timeout(2.0) as timeout_ctx:
  ...     variable_duration_func(5.0)
  >>> time.time() - start_time < 2.1
  True
  >>> timeout_ctx.state == timeout_ctx.TIMED_OUT
  True

Other exceptions are propagated and must be treated as usual:

.. code:: pycon

  >>> try:
  ...     with Timeout(5.0) as timeout_ctx:
  ...         result = func_with_exception()
  ... except LookupError:
  ...     result = 'exception_seen'
  >>> timeout_ctx.state == timeout_ctx.EXECUTING
  True
  >>> result
  'exception_seen'

Propagating ``TimeoutException``
................................

We can choose to propagate the ``TimeoutException`` too. Potential exceptions
have to be handled:

.. code:: pycon

  >>> result = None
  >>> start_time = time.time()
  >>> try:
  ...     with Timeout(2.0, swallow_exc=False) as timeout_ctx:
  ...         variable_duration_func(5.0)
  ... except TimeoutException:
  ...     result = 'exception_seen'
  >>> time.time() - start_time < 2.1
  True
  >>> result
  'exception_seen'
  >>> timeout_ctx.state == timeout_ctx.TIMED_OUT
  True

Other exceptions must be handled too:

.. code:: pycon

  >>> result = None
  >>> start_time = time.time()
  >>> try:
  ...     with Timeout(2.0, swallow_exc=False) as timeout_ctx:
  ...         func_with_exception()
  ... except Exception:
  ...     result = 'exception_seen'
  >>> time.time() - start_time < 0.1
  True
  >>> result
  'exception_seen'
  >>> timeout_ctx.state == timeout_ctx.EXECUTING
  True

``timeoutable`` callable decorator
----------------------------------

This decorator stops the execution of any callable that should not last a
certain amount of time.

You may use a decorated callable without timeout control if you don't provide
the ``timeout`` optional argument:

.. code:: pycon

  >>> @timeoutable()
  ... def fast_double(value):
  ...     return value * 2
  >>> fast_double(3)
  6

You may specify that timeout with the ``timeout`` optional argument.
Interrupted callables return None:

.. code:: pycon

  >>> @timeoutable()
  ... def infinite():
  ...     while True:
  ...         pass
  ...     return 'whatever'
  >>> infinite(timeout=1) is None
  True

Or any other value provided to the ``timeoutable`` decorator parameter:

.. code:: pycon

  >>> @timeoutable('unexpected')
  ... def infinite():
  ...     while True:
  ...         pass
  ...     return 'whatever'
  >>> infinite(timeout=1)
  'unexpected'

If the ``timeout`` parameter name may clash with your callable signature, you
may change it using ``timeout_param``:

.. code:: pycon

  >>> @timeoutable('unexpected', timeout_param='my_timeout')
  ... def infinite():
  ...     while True:
  ...         pass
  ...     return 'whatever'
  >>> infinite(my_timeout=1)
  'unexpected'

It works on instance methods too:

.. code:: pycon

  >>> class Anything(object):
  ...     @timeoutable('unexpected')
  ...     def infinite(self, value):
  ...         assert type(value) is int
  ...         while True:
  ...             pass
  >>> obj = Anything()
  >>> obj.infinite(2, timeout=1)
  'unexpected'


Links
=====

Source code (clone, fork, ...)
  https://github.com/glenfant/stopit

Issues tracker
  https://github.com/glenfant/stopit/issues

PyPI
  https://pypi.python.org/pypi/stopit
